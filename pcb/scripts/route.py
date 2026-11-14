# SPDX-License-Identifier: GPL-3.0-or-later
"""Add copper to the placed seed.

    route.py <variant> critical   seed -> USB pairs, crystal, QSPI, power, planes, RP2040 fan-out
    route.py <variant> grid       critical board -> every other net by the grid router (resumable); writes the DSN
    route.py <variant> finish     grid board + the committed autorouter session -> stitched, filled, final board

Every stage is deterministic. The autorouter only sees what the grid router could not join.
"""
import hashlib,json,os,shutil,sys
from fnmatch import fnmatch
from math import atan2,copysign,cos,hypot,radians,sin
from pathlib import Path
import pcbnew as p
import shapely
from shapely.affinity import translate
from shapely.geometry import LineString,Point,Polygon,box
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from layout import board_outline
from pcb.scripts import maze,rules
from pcb.scripts.place import OFFSET
from pcb.scripts.support_places import KEEP_CLEAR,SATELLITES
from pcb.scripts.maze import Job,Route
from pcb.scripts.design import GPIO_NETS

LAYER={'F':p.F_Cu,'B':p.B_Cu}
PLANE_ISLAND=(150.0,3.0,250.0,48.0)   # 3V3 island on In2.Cu in board mm: the controller bay, open to the rear edge. GND fills the rest
PAIR_PITCH=rules.USB_TRACK+rules.USB_GAP
END_RINGS=(3.5,4.5,5.5)   # millimetres from the mux centre
END_TURNS=(0,30,-30,60,-60,90,-90)
END_KEEP=1.0
END_TRIES=6
ESCAPE=1.0               # escape stub length from the pad centre
GAP_SAMPLE=40
PAIR_NECK=1.0            # past the pad tips: from the pad centres to here the tracks close from pad pitch to pair pitch
PAIR_EXIT=2.2            # a pair leaves its pads this far along their axis before it turns
VIA_PAD_GAP=0.1          # a plane via keeps this much mask between itself and any pad
STUB_REACH=8.0
SHARE_REACH=2.0          # a supply pin with no room for its own via joins a neighbour's via this close
ESCAPE_PITCH=rules.VIA_D+2*rules.CLEARANCE+rules.TRACK+0.1   # one track fits between two escape vias, with margin
EP_VIA_PITCH=1.6         # thermal vias in the RP2040 exposed pad, a 2 x 2 grid
ZONE_CLEARANCE=0.2
ZONE_MIN_WIDTH=0.2
B_ONLY=('B',)
ORDER_TRIES=12
JACK_TAP_REACH=6.0       # a clamp or the second receptacle pad may tap a pair line this close to its pad
JACK_REACH=10.0          # pads of a pair net this close to the receptacle are joined near it: pads and clamp
MUX_REACH=8.0            # and this close to the mux, near the mux
# (states one join may expand before it counts as blocked, weight on the estimate): a weighted search finds
# a slightly longer path in far fewer states.
COMPLETE_SEARCH=(1_500_000,1.5)
RIP_LIMIT=3              # a net torn up this often stays where it is
CHECKPOINT_EVERY=5       # grid-stage joins between saved checkpoints
COMPLETE_REACH=10.0     # a join after the autorouter may stray this far outside the box of its two ends
STITCH_PITCH=10.0        # ground stitching grid
STITCH_REACH=2.0         # a stitching via may move this far off its grid point to find room
STITCH_HOLE_MARGIN=0.1   # stitching vias keep this much more than the minimum wall to other holes
RETURN_VIA_OFFSETS=((0.0,-1.2),(0.0,1.2),(-1.2,0.0),(1.2,0.0))   # where a return via is first tried beside a USB via
RETURN_VIA_REACH=0.8
LOCAL_MARGIN=1.5         # a local join may use this much room around the pads it joins
# Nets routed here, in order. (net patterns joined by |, track width, layers). One row is one reorderable group.
CONTROLLER_NETS=(
    ('XIN',rules.TRACK,maze.LAYERS),('XTAL_OUT',rules.TRACK,maze.LAYERS),('XOUT',rules.TRACK,maze.LAYERS),   # a via if a supply via is in the way
    ('QSPI_*',rules.TRACK,B_ONLY),('USB_D[PM]',rules.TRACK,B_ONLY),             # 0.4 mm pitch pads: these few millimetres stay at pad width
    ('USB_MUX_D[PM]',rules.TRACK,B_ONLY),
)
CORE_STUB_PINS=('23',)   # DVDD pin 23 sits between IOVDD and SWCLK, in front of the crystal routes
CORE_VIA_AT_CAP=()       # 1V1 pins whose via sits beside their capacitor rather than inside the pad row
CORE_LOCAL=1.0           # a 1V1 pin meets its capacitor within this much of the two pads
CORE_MARGIN=5.0          # 1V1 stays this close to the RP2040 courtyard: across the package on F.Cu, not around it
SUPPLY_NETS=(
    ('VBUS_LEFT',rules.POWER_TRACK,maze.LAYERS),('VBUS_CENTER',rules.POWER_TRACK,maze.LAYERS),
    ('VBUS_RIGHT',rules.POWER_TRACK,maze.LAYERS),('VSYS',rules.POWER_TRACK,maze.LAYERS),
)
USB_PORTS=(('J1','USB_LEFT'),('J2','USB_CENTER'),('J3','USB_RIGHT'))
MUX='U7'
MCU,EXPOSED_PAD='U1','57'

def mm(v):return p.ToMM(v.x),p.ToMM(v.y)
def iu(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def ref_of(pad):return pad.GetParentFootprint().GetReference()

def polygon_of(pad,layer):
    outline=pad.GetEffectivePolygon(layer,p.ERROR_OUTSIDE).Outline(0)
    return Polygon([mm(outline.CPoint(i)) for i in range(outline.PointCount())])

class Unroutable(RuntimeError):
    """The maze router found no path for one connection."""

class Copper:
    """The board, its obstacle model, and the copper added so far."""
    def __init__(self,board):
        self.board=board;self.obstacles=maze.Obstacles(rules.CLEARANCE,rules.HOLE_TO_HOLE)
        self.pads={};self.pad_shapes=[];self.routes=[];self.escapes=[]
        self.base=[]               # (layers, net, shape) or (x, y, drill): everything that is not a route
        for fp in board.GetFootprints():
            for pad in fp.Pads():self._register(fp.GetReference(),pad)
        edge=board.GetBoardEdgesBoundingBox()
        ring=_edge_ring().buffer(rules.EDGE_CLEARANCE-rules.CLEARANCE)
        self._fixed(maze.LAYERS,None,ring)
        self.bounds=(*mm(edge.GetOrigin()),*mm(edge.GetEnd()))
        self.pad_tree=shapely.STRtree(self.pad_shapes)
        self.no_plane_via=unary_union([_keep_clear_box(board,ref,reach) for ref,reach,_ in KEEP_CLEAR])
        for jack,_ in USB_PORTS:self._fixed(('F',),None,_shell_body(board,jack))

    def _fixed(self,layers,net,shape):
        self.base.append((layers,net,shape));self.obstacles.add(layers,net,shape)

    def _fixed_hole(self,x,y,drill):
        self.base.append((x,y,drill));self.obstacles.add_hole(x,y,drill)

    def obstacles_for(self,routes):
        """A fresh obstacle model: everything fixed plus these routes."""
        model=maze.Obstacles(rules.CLEARANCE,rules.HOLE_TO_HOLE)
        for item in self.base:
            if len(item)==3 and isinstance(item[0],tuple):model.add(*item)
            else:model.add_hole(*item)
        for route in routes:model.add_route(route,rules.VIA_D,rules.VIA_DRILL)
        return model

    def rip(self,nets):
        """Tear up the rippable routes of these nets; their pads become open islands again."""
        self.routes=[r for r in self.routes if not (r.net in nets and r.rippable)]
        self.obstacles=self.obstacles_for(self.routes)

    def _register(self,ref,pad):
        if pad.GetDrillSizeX()>0:self._fixed_hole(*mm(pad.GetPosition()),max(mm(pad.GetDrillSize())))
        if pad.GetAttribute()==p.PAD_ATTRIB_NPTH:
            keep=max(mm(pad.GetDrillSize()))/2+rules.HOLE_CLEARANCE-rules.CLEARANCE
            self._fixed(maze.LAYERS,None,Point(mm(pad.GetPosition())).buffer(keep))
            return
        layers=tuple(name for name,layer in LAYER.items() if pad.IsOnLayer(layer))
        if not layers:return                      # paste-only apertures carry no copper
        shape=polygon_of(pad,LAYER[layers[0]])
        self._fixed(layers,pad.GetNetname(),shape)
        self.pad_shapes.append(shape)
        if pad.GetNumber():self.pads.setdefault((ref,pad.GetNumber()),[]).append((pad,layers,shape))

    def pad(self,ref,number):
        """(pad, layers, shape) of the first pad with this number."""
        return self.pads[ref,number][0]

    def pads_on(self,net):
        return [entry for entries in self.pads.values() for entry in entries if entry[0].GetNetname()==net]

    def terminal(self,entry):
        """Lattice nodes inside a pad, on each of its layers."""
        pad,layers,shape=entry
        cx,cy=mm(pad.GetPosition());x0,y0,x1,y1=shape.bounds
        inside=[(ix,iy) for ix in range(round(x0/maze.GRID),round(x1/maze.GRID)+1)
                for iy in range(round(y0/maze.GRID),round(y1/maze.GRID)+1)
                if shape.covers(Point(ix*maze.GRID,iy*maze.GRID))]
        inside=inside or [maze.nearest(None,cx,cy)[1:]]
        return [(layer,ix,iy) for layer in layers for ix,iy in inside]

    def commit(self,route):
        if self.board.FindNet(route.net) is None:raise RuntimeError(f'no net {route.net}')
        self.obstacles.add_route(route,rules.VIA_D,rules.VIA_DRILL);self.routes.append(route)

    def mark(self):return len(self.routes),self.obstacles.mark()

    def rollback(self,mark):
        del self.routes[mark[0]:];self.obstacles.rollback(mark[1])

    def write(self,locked=False):
        """Turn every committed route into board tracks and vias. Locked items go to the DSN as protected
        wiring, so the autorouter cannot rip up the scripted copper. locked=None locks every route the grid
        router may not tear up, and leaves the rest unlocked so a later stage knows it may."""
        for route in self.routes:
            lock=(not route.rippable) if locked is None else locked
            net=self.board.FindNet(route.net)
            for layer,points in route.lines:
                for a,b in zip(points,points[1:]):
                    track=p.PCB_TRACK(self.board);track.SetStart(iu(*a));track.SetEnd(iu(*b))
                    track.SetWidth(p.FromMM(route.width));track.SetLayer(LAYER[layer]);track.SetNet(net)
                    track.SetLocked(lock);self.board.Add(track)
            for x,y in route.vias:
                via=p.PCB_VIA(self.board);via.SetPosition(iu(x,y));via.SetWidth(p.F_Cu,p.FromMM(rules.VIA_D))
                via.SetDrill(p.FromMM(rules.VIA_DRILL));via.SetNet(net);via.SetLocked(lock);self.board.Add(via)

def _shell_body(board,ref):
    """The F.Cu side of a receptacle between its signal pad row and its mouth. Its metal shell sits on the
    board there, so no track of any net runs under it."""
    fp=board.FindFootprintByReference(ref);fp.BuildCourtyardCaches()
    yard=fp.GetCourtyard(p.F_CrtYd).BBox()
    pads=unary_union([polygon_of(pad,p.F_Cu) for pad in fp.Pads() if pad.GetDrillSizeX()==0 and pad.IsOnLayer(p.F_Cu)])
    cx,cy=pads.centroid.x,pads.centroid.y;fx,fy=mm(fp.GetPosition())
    ux,uy=fx-cx,fy-cy;norm=hypot(ux,uy);ux,uy=ux/norm,uy/norm;vx,vy=-uy,ux
    tip=max(ux*(x-cx)+uy*(y-cy) for x,y in pads.convex_hull.exterior.coords)   # pad tip nearest the mouth
    far=2*hypot(p.ToMM(yard.GetWidth()),p.ToMM(yard.GetHeight()))
    beyond=Polygon([(cx+ux*d+vx*s,cy+uy*d+vy*s) for d,s in ((tip,-far),(tip+far,-far),(tip+far,far),(tip,far))])
    return box(*mm(yard.GetOrigin()),*mm(yard.GetEnd())).intersection(beyond)

def _keep_clear_box(board,ref,reach):
    """A support_places.KEEP_CLEAR box in board millimetres: plane vias stay out of it as well."""
    x,y=mm(board.FindFootprintByReference(ref).GetPosition())
    return box(x+reach[0],y+reach[1],x+reach[2],y+reach[3])

def _edge_ring():
    """Board outline as one closed line in board millimetres."""
    return translate(board_outline().exterior,*OFFSET)

def job_for(nets,width,layers,reach=6.0,greed=1.0,budget=None):
    return Job(frozenset(nets),width/2,rules.VIA_D/2,rules.VIA_DRILL,layers,reach,greed,budget)

def _merged(islands):
    """Union the node sets that share a node."""
    merged=[]
    for island in islands:
        touching=[m for m in merged if not m.isdisjoint(island)]
        for m in touching:
            island=island|m;merged.remove(m)
        merged.append(island)
    return sorted(merged,key=min)

def _gap(island,main):
    """Roughly how far apart two node sets are, from a sample of each."""
    a,b=(sorted(nodes)[::max(1,len(nodes)//GAP_SAMPLE)] for nodes in (island,main))
    return min(hypot(m[1]-n[1],m[2]-n[2]) for m in a for n in b)

def islands_of(copper,net,within=None):
    """Node sets of a net that are not yet joined: its pads and its copper, optionally only inside a window."""
    islands=[set(route.nodes) for route in copper.routes if route.net==net and route.nodes]
    islands+=[set(copper.terminal(entry)) for entry in copper.pads_on(net)]
    if within is not None:
        islands=[{n for n in nodes if within.covers(Point(maze.node_xy(n)))} for nodes in islands]
    return _merged([nodes for nodes in islands if nodes])

def connect_net(copper,net,width,layers,within=None,reach=6.0,greed=1.0,budget=None,root=None):
    """Join every pad and every piece of copper of a net into one tree, nearest piece first.
    With a window, only the pieces inside it are joined, and the search stays near them."""
    islands=islands_of(copper,net,within)
    if not islands:return
    if root is not None:              # grow from the piece nearest this point instead of the first one
        islands.sort(key=lambda nodes:min(hypot(maze.node_xy(n)[0]-root[0],maze.node_xy(n)[1]-root[1]) for n in nodes))
    tree=islands.pop(0);job=job_for({net},width,layers,reach,greed,budget)
    while islands:
        island=min(islands,key=lambda nodes:_gap(nodes,tree));islands.remove(island)
        path=maze.search(copper.obstacles,job,sorted(island),tree)
        if path is None:
            raise Unroutable(f'{net}: no path from the copper at {maze.node_xy(min(island))} to the rest of the net')
        copper.commit(maze.to_route(path,net,width))
        tree|=island;tree.update(path)

def escape_stubs(copper,ref,nets,numbers=None):
    """A short straight track out of each fine-pitch pad, so a neighbour's route cannot bend across its exit.
    With numbers, only those pads of the part."""
    cx,cy=mm(copper.board.FindFootprintByReference(ref).GetPosition())
    for entry in (e for net in nets for e in copper.pads_on(net) if ref_of(e[0])==ref
                  and (numbers is None or e[0].GetNumber() in numbers)):
        pad,layers,_=entry;x,y=mm(pad.GetPosition())
        dx,dy=(copysign(1,x-cx),0) if abs(x-cx)>abs(y-cy) else (0,copysign(1,y-cy))
        line=LineString([(x,y),(x+dx*ESCAPE,y+dy*ESCAPE)])
        if not _stub_clear(copper,layers[0],pad.GetNetname(),line):continue   # a part sits in front of the pin
        nodes=[maze.nearest(layers[0],*point) for point in line.coords]      # only the ends: a join mid-stub leaves a spur
        copper.commit(Route(pad.GetNetname(),rules.TRACK,[(layers[0],list(line.coords))],[],nodes))

def _stub_clear(copper,layer,net,line):
    """True when a track along this line keeps the clearance to every other net's copper."""
    stub=line.buffer(rules.TRACK/2)
    shapes=copper.obstacles.shapes[layer];owners=copper.obstacles.nets[layer]
    return all(owners[i]==net or shapes[i].distance(stub)>=rules.CLEARANCE
               for i in shapely.STRtree(shapes).query(stub,predicate='dwithin',distance=rules.CLEARANCE))

def route_groups(copper,groups):
    names=sorted(str(net) for net in copper.board.GetNetsByName().keys())
    for pattern,width,layers in groups:
        _route_group(copper,[n for n in names if any(fnmatch(n,one) for one in pattern.split('|'))],width,layers)

def _route_group(copper,nets,width,layers,**window):
    """Route a bus. There is no rip-up, so when one order boxes a net in, the next order is tried.
    window: the within and reach arguments of connect_net."""
    mark=copper.mark();order=list(nets)
    for _ in range(ORDER_TRIES):
        failure=next(filter(None,(_failure(copper,net,width,layers,**window) for net in order)),None)
        if failure is None:return
        copper.rollback(mark)
        order.remove(failure.net);order.insert(0,failure.net)      # the boxed-in net goes first next time
    raise RuntimeError(f'{nets}: no routing order worked in {ORDER_TRIES} tries; last: {failure}')

def _failure(copper,net,width,layers,**window):
    """The Unroutable raised while routing one net, or None when it went in."""
    try:
        connect_net(copper,net,width,layers,**window)
    except Unroutable as failure:
        failure.net=net
        return failure
    return None

def _steps(length):
    """Distances 0, GRID, 2 GRID ... up to length."""
    return [i*maze.GRID for i in range(int(length/maze.GRID)+1)]

def _window(copper,nets,centre,reach):
    """Box around the pads and copper ends of these nets that lie within reach of a point, plus a working margin."""
    def close(xy):return hypot(xy[0]-centre[0],xy[1]-centre[1])<=reach
    near=[e[2] for net in nets for e in copper.pads_on(net) if close(mm(e[0].GetPosition()))]
    near+=[Point(maze.node_xy(n)) for route in copper.routes if route.net in nets for n in route.nodes
           if close(maze.node_xy(n))]
    return box(*unary_union(near).bounds).buffer(LOCAL_MARGIN,join_style='mitre')

def join_pair_locally(copper,jack,stem):
    """Second receptacle pad, ESD clamp and mux pins of each line, each joined inside its own small window.
    A join that has to leave its window is a design problem to fix by placement, not a long detour."""
    nets=(stem+'_DP',stem+'_DM')
    # CC1 (A5) sits beside the second D- pad: both want the same room behind the pad row, so the CC nets of
    # this receptacle share the jack window and its order retries.
    cc=[f'CC{jack[1:]}{side}' for side in 'AB']
    jack_window=_window(copper,nets+tuple(cc),mm(copper.board.FindFootprintByReference(jack).GetPosition()),JACK_REACH)
    _route_group(copper,list(nets)+cc,rules.TRACK,maze.LAYERS,within=jack_window,reach=LOCAL_MARGIN)
    mux_window=_window(copper,nets,mm(copper.board.FindFootprintByReference(MUX).GetPosition()),MUX_REACH)
    _route_group(copper,list(nets),rules.TRACK,maze.LAYERS,within=mux_window,reach=LOCAL_MARGIN)
    for net in list(nets)+cc:
        left=islands_of(copper,net)
        if len(left)>1:
            raise Unroutable(f'{net}: {len(left)} pieces stay apart after the local joins at {jack} and {MUX}')

def _pair_point(copper,ref,numbers,away_from):
    """Two points on the axis out of a pad pair: where the tracks have closed to pair pitch, and where they may turn."""
    (ax,ay),(bx,by)=(mm(copper.pad(ref,n)[0].GetPosition()) for n in numbers)
    mx,my=(ax+bx)/2,(ay+by)/2
    dx,dy=mx-away_from[0],my-away_from[1];norm=hypot(dx,dy)
    return (mx+dx/norm*PAIR_NECK,my+dy/norm*PAIR_NECK),(mx+dx/norm*PAIR_EXIT,my+dy/norm*PAIR_EXIT)

def _pair_ends(copper,nets,mux_at,outward):
    """Where a pair may stop on F.Cu near the mux, best first: on rings around it, as near the pads' side as
    there is room. Each spot is clear on both layers for END_KEEP around, so the two vias and their tails to
    the pads fit. The first spot can lie behind another pair, so the caller tries a few."""
    base=atan2(outward[1],outward[0]);found=[]
    for radius in END_RINGS:
        for turn in END_TURNS:
            angle=base+radians(turn)
            node=maze.nearest('F',mux_at[0]+radius*cos(angle),mux_at[1]+radius*sin(angle))
            if all(copper.obstacles.clear(layer,node,nets,END_KEEP) for layer in maze.LAYERS):
                found.append(maze.node_xy(node))
    if not found:raise Unroutable(f'no room for a pair end near {MUX}')
    return found[:END_TRIES]

def route_usb_pair(copper,jack,stem):
    """One receptacle pair on F.Cu over the In1 ground plane, as two offsets of a routed centre line."""
    dp,dm=stem+'_DP',stem+'_DM'
    jack_at=mm(copper.board.FindFootprintByReference(jack).GetPosition())
    mux_at=mm(copper.board.FindFootprintByReference(MUX).GetPosition())
    mux_pads={net:next(e for e in copper.pads_on(net) if ref_of(e[0])==MUX) for net in (dp,dm)}
    (px,py),(nx,ny)=(mm(mux_pads[net][0].GetPosition()) for net in (dp,dm))
    ends=_pair_ends(copper,frozenset((dp,dm)),mux_at,((px+nx)/2-mux_at[0],(py+ny)/2-mux_at[1]))
    # The row reads B6 A7 A6 B7. Either centre pad pairs with its outer neighbour, so one choice never twists.
    rejected=[]
    for end,numbers in ((end,numbers) for end in ends for numbers in (('A6','A7'),('B6','A7'),('A6','B7'))):
        neck,start=_pair_point(copper,jack,numbers,(jack_at[0],jack_at[1]-10.0))
        job=job_for({dp,dm},2*rules.USB_TRACK+rules.USB_GAP,('F',),reach=10.0)
        path=maze.search(copper.obstacles,job,[maze.nearest('F',*start)],[maze.nearest('F',*end)])
        if path is None:
            rejected.append((end,numbers,'no path'));continue
        # The lead-in from the pads fixes the direction the two tracks leave in.
        centre=LineString([neck]+maze.to_route(path,dp,rules.USB_TRACK).lines[0][1])
        sides=[list(centre.offset_curve(sign*PAIR_PITCH/2,join_style='mitre').coords) for sign in (1,-1)]
        sides=[side if Point(side[0]).distance(Point(neck))<Point(side[-1]).distance(Point(neck)) else side[::-1]
               for side in sides]                    # GEOS versions disagree on the direction of a right-hand offset
        pads=[mm(copper.pad(jack,n)[0].GetPosition()) for n in numbers]
        if hypot(sides[0][0][0]-pads[0][0],sides[0][0][1]-pads[0][1])>hypot(sides[1][0][0]-pads[0][0],sides[1][0][1]-pads[0][1]):
            sides.reverse()
        if LineString([pads[0],sides[0][0]]).distance(LineString([pads[1],sides[1][0]]))<PAIR_PITCH-1e-6:
            rejected.append((end,numbers,'fan too tight'));continue
        if hypot(sides[0][-1][0]-px,sides[0][-1][1]-py)>hypot(sides[1][-1][0]-px,sides[1][-1][1]-py):
            rejected.append((end,numbers,'twisted at the mux'));continue
        lines=[LineString([pad_at]+points) for pad_at,points in ((pads[0],sides[0]),(pads[1],sides[1]))]
        for net,line,partner in ((dp,lines[0],lines[1]),(dm,lines[1],lines[0])):
            other=partner.buffer(rules.USB_TRACK/2)
            def apart(node):return other.distance(Point(maze.node_xy(node)))>=rules.TRACK/2+rules.CLEARANCE
            # The line ends on the lattice node off its end that leans away from the partner, so the join to the
            # mux starts outside the pair gap. Joins may also tap the line near the receptacle, where its clamp
            # and second pad are, at nodes outside the gap.
            x,y=line.coords[-1]
            corners=[('F',ix,iy) for ix in (int(x/maze.GRID),int(x/maze.GRID)+1) for iy in (int(y/maze.GRID),int(y/maze.GRID)+1)]
            last=max(corners,key=lambda n:other.distance(Point(maze.node_xy(n))))
            if not apart(last):raise Unroutable(f'{net}: no lattice end clear of its partner line')
            taps=[line.interpolate(d) for d in _steps(min(JACK_TAP_REACH,line.length))]
            nodes=[last]+[n for n in (maze.nearest('F',t.x,t.y) for t in taps) if apart(n)]
            copper.commit(Route(net,rules.USB_TRACK,[('F',list(line.coords)+[maze.node_xy(last)])],[],nodes))
        return LineString(sides[0]).length,LineString(sides[1]).length
    raise RuntimeError(f'{jack}: no {stem} pair: {rejected}')

def exposed_pad_vias(copper):
    """Thermal and ground vias inside the RP2040 exposed pad."""
    ex,ey=mm(copper.pad(MCU,EXPOSED_PAD)[0].GetPosition())
    grid=[(ex+sx*EP_VIA_PITCH/2,ey+sy*EP_VIA_PITCH/2) for sx in (-1,1) for sy in (-1,1)]
    copper.commit(Route('GND',rules.TRACK,[],grid,[]))

def plane_vias(copper):
    """A short stub and one via to the planes for every SMD pad on a plane net. A pad with no room for its own
    via joins a neighbour's stub on the second pass, or a neighbouring pad of its net that has one."""
    island=box(*PLANE_ISLAND)
    drilled_nodes={net:[n for e in copper.pads_on(net) if len(e[1])>1 for n in copper.terminal(e)] for net in rules.PLANE_NETS}
    for net in rules.PLANE_NETS:
        job=job_for({net},rules.TRACK,maze.LAYERS,reach=STUB_REACH)
        pending=[e for e in sorted(copper.pads_on(net),key=lambda e:mm(e[0].GetPosition()))
                 if (ref_of(e[0]),e[0].GetNumber())!=(MCU,EXPOSED_PAD) and len(e[1])==1]   # drilled pads reach the planes
        for last_pass in (False,True):
            pending=[entry for entry in pending if not _plane_via(copper,net,job,island,drilled_nodes[net],entry,last_pass)]
        if pending:
            raise Unroutable(f'{net}: no plane via for '+', '.join(f'{ref_of(e[0])} pad {e[0].GetNumber()}' for e in pending))

def _plane_via(copper,net,job,island,drilled_nodes,entry,shared_ok):
    """Give one pad its stub and via, or with shared_ok join the stub of a pad that has one. True when done."""
    pad,_,shape=entry
    starts=copper.terminal(entry);layer=starts[0][0]
    def near(n):return n[0]==layer and shape.distance(Point(maze.node_xy(n)))<=STUB_REACH
    sites=[n for n in _via_sites(copper,job,layer,shape) if net=='GND' or island.covers(Point(maze.node_xy(n)))]
    if ref_of(pad)==MCU:   # RP2040 supply pins take their vias inside the pad row: outside, a via blocks a neighbour's exit
        package=_package(copper,MCU);sites=[n for n in sites if package.covers(Point(maze.node_xy(n)))]
    joined=[n for n in drilled_nodes if near(n)]
    if shared_ok:
        def close(n):return n[0]==layer and shape.distance(Point(maze.node_xy(n)))<=SHARE_REACH
        joined+=[n for route in copper.routes if route.net==net and route.vias for n in route.nodes if close(n)]
        joined+=[n for e in copper.pads_on(net) if e is not entry and any(set(r.nodes)&set(copper.terminal(e))
                 for r in copper.routes if r.net==net and r.vias) for n in copper.terminal(e) if close(n)]
    goals=sites+joined
    path=maze.search(copper.obstacles,Job(job.nets,job.radius,job.via_radius,job.via_drill,(layer,),STUB_REACH),starts,goals) if goals else None
    if path is None:return False
    route=maze.to_route(path,net,rules.TRACK)
    shared=any(hypot(vx-maze.node_xy(path[-1])[0],vy-maze.node_xy(path[-1])[1])<1e-6 for vx,vy,_ in copper.obstacles.holes)
    if path[-1] not in joined and not shared:route.vias.append(maze.node_xy(path[-1]))   # else the hole is there already
    copper.commit(route)
    return True

def route_core(copper):
    """1V1 joins pins 23, 45 and 50 on opposite sides of the RP2040, and their capacitors, through vias joined on
    F.Cu across the package. Each pin takes a via between the pad row and the exposed pad (a pin listed in
    CORE_VIA_AT_CAP meets its capacitor on B.Cu instead), and each capacitor takes its own via. A 1V1 track
    around the package would fence every other escape in."""
    package=_package(copper,MCU)
    for cap,host,number,_ in SATELLITES:
        if host!=MCU or copper.pad(MCU,number)[0].GetNetname()!='1V1':continue
        pin=copper.pad(MCU,number);cap_pad=next(e for e in copper.pads_on('1V1') if ref_of(e[0])==cap)
        if number in CORE_VIA_AT_CAP:
            window=box(*unary_union([pin[2],cap_pad[2]]).bounds).buffer(CORE_LOCAL,join_style='mitre')
            connect_net(copper,'1V1',rules.TRACK,B_ONLY,within=window,reach=CORE_LOCAL)
        elif number in CORE_STUB_PINS:
            _via_out(copper,'1V1',pin,outside=package)   # at the end of its stub: inside, it takes IOVDD's spot
        else:
            try:
                _via_out(copper,'1V1',pin,inside=package)    # inward first: outside, a via blocks neighbours' exits
            except Unroutable:
                _via_out(copper,'1V1',pin)
        _via_out(copper,'1V1',cap_pad)
    # The joins grow from the package centre, so each capacitor via takes the shortest way in, a spoke. Grown
    # from the first piece, the capacitor vias could join each other around the package and fence it.
    window=package.buffer(CORE_MARGIN,join_style='mitre');centre=package.centroid
    connect_net(copper,'1V1',rules.TRACK,('F',),within=window,reach=CORE_MARGIN,root=(centre.x,centre.y))
    if len(islands_of(copper,'1V1'))>1:raise Unroutable('1V1: pieces stay apart inside the RP2040 window')

def _package(copper,ref):
    """Courtyard box of a part in board millimetres."""
    fp=copper.board.FindFootprintByReference(ref);fp.BuildCourtyardCaches()
    yard=fp.GetCourtyard(p.B_CrtYd if fp.IsFlipped() else p.F_CrtYd).BBox()
    return box(*mm(yard.GetOrigin()),*mm(yard.GetEnd()))

def _via_out(copper,net,entry,inside=None,outside=None):
    """A short stub from a pad to a new via, optionally only to a via inside, or outside, a region."""
    pad,_,shape=entry;starts=copper.terminal(entry);layer=starts[0][0]
    job=job_for({net},rules.TRACK,maze.LAYERS,reach=STUB_REACH)
    sites=[n for n in _via_sites(copper,job,layer,shape)
           if (inside is None or inside.covers(Point(maze.node_xy(n))))
           and (outside is None or not outside.covers(Point(maze.node_xy(n))))]
    path=maze.search(copper.obstacles,Job(job.nets,job.radius,job.via_radius,job.via_drill,(layer,),STUB_REACH),starts,sites) if sites else None
    if path is None:raise Unroutable(f'{net}: no via beside {ref_of(pad)} pad {pad.GetNumber()}')
    route=maze.to_route(path,net,rules.TRACK);route.vias.append(maze.node_xy(path[-1]))
    route.nodes=route.nodes+[('F' if layer=='B' else 'B',)+path[-1][1:]]
    copper.commit(route)

def escape_vias(copper,ref,nets=None,pitch=ESCAPE_PITCH):
    """Fan the open signal pins of a fine-pitch part out to vias, nearest free spot first, so the autorouter
    starts on the open F.Cu side instead of between 0.4 mm pads and their decoupling. Returns the pins that
    found no spot; the autorouter gets those as they are."""
    blocked=[];placed=copper.escapes
    for entry in sorted((e for es in copper.pads.values() for e in es if ref_of(e[0])==ref),key=lambda e:int(e[0].GetNumber())):
        pad,layers,shape=entry;net=pad.GetNetname()
        if len(layers)>1 or not net or net in rules.PLANE_NETS or net.startswith('unconnected-'):continue
        if nets is not None and net not in nets:continue
        if len(islands_of(copper,net))<2:continue                  # the net is whole already
        pad_nodes=set(copper.terminal(entry));layer=next(iter(pad_nodes))[0]
        touching=[route for route in copper.routes if route.net==net and pad_nodes&set(route.nodes)]
        if any(route.vias for route in touching):continue          # it has its via
        # Start from the pin's straight stub when it has one, so the way out stays straight.
        starts=sorted(pad_nodes|{n for route in touching for n in route.nodes if n[0]==layer})
        job=job_for({net},rules.TRACK,maze.LAYERS,reach=STUB_REACH)
        # Escape vias keep room for a track between any two of them, so the inner ones are not walled in.
        sites=[n for n in _via_sites(copper,job,layer,shape)
               if all(hypot(maze.node_xy(n)[0]-x,maze.node_xy(n)[1]-y)>=pitch for x,y in placed)]
        path=maze.search(copper.obstacles,Job(job.nets,job.radius,job.via_radius,job.via_drill,(layer,),STUB_REACH),starts,sites) if sites else None
        if path is None:
            blocked.append(f'{ref}.{pad.GetNumber()} {net}');continue
        placed.append(maze.node_xy(path[-1]))
        route=maze.to_route(path,net,rules.TRACK);route.vias.append(maze.node_xy(path[-1]))
        route.rippable=True        # a boxed-in neighbour may take its spot; this pin then joins from its stub
        route.nodes=route.nodes+[('F' if layer=='B' else 'B',)+path[-1][1:]]
        copper.commit(route)
    return blocked

def _via_sites(copper,job,layer,shape):
    """Lattice nodes near a pad where a via clears every other net and sits off every pad."""
    x0,y0,x1,y1=shape.buffer(STUB_REACH).bounds
    keep_off=rules.VIA_D/2+VIA_PAD_GAP;found=[]
    for ix in range(round(x0/maze.GRID),round(x1/maze.GRID)+1,2):
        for iy in range(round(y0/maze.GRID),round(y1/maze.GRID)+1,2):
            node=(layer,ix,iy);spot=Point(maze.node_xy(node))
            if copper.obstacles.drill_fits(node,job.via_drill) \
               and all(copper.obstacles.clear(l,node,job.nets,job.via_radius) for l in maze.LAYERS) \
               and not len(copper.pad_tree.query(spot,predicate='dwithin',distance=keep_off)) \
               and not copper.no_plane_via.covers(spot):
                found.append(node)
    return found

def add_zone(board,net,layer,corners,priority):
    zone=p.ZONE(board);zone.SetLayer(layer);zone.SetNet(board.FindNet(net));zone.SetAssignedPriority(priority)
    zone.SetLocalClearance(p.FromMM(ZONE_CLEARANCE));zone.SetMinThickness(p.FromMM(ZONE_MIN_WIDTH))
    zone.SetPadConnection(p.ZONE_CONNECTION_THT_THERMAL)   # SMD pads and vias solid, hand-soldered pins relieved
    outline=zone.Outline();outline.NewOutline()
    for x,y in corners:outline.Append(p.FromMM(x),p.FromMM(y))
    board.Add(zone)

def plane_island(copper):
    """The 3V3 area of In2.Cu: PLANE_ISLAND carried out to the rear edge of the board box."""
    ix0,_,ix1,iy1=PLANE_ISLAND
    return box(ix0,copper.bounds[1],ix1,iy1)

def add_shell_keepouts(copper):
    """Rule areas over the receptacle shells on F.Cu, so that no autorouted track or via goes under one either,
    and DRC proves the scripted copper keeps out too."""
    for jack,_ in USB_PORTS:
        zone=p.ZONE(copper.board);zone.SetLayer(p.F_Cu);zone.SetIsRuleArea(True)
        zone.SetDoNotAllowTracks(True);zone.SetDoNotAllowVias(True);zone.SetDoNotAllowZoneFills(True)
        zone.SetDoNotAllowPads(False);zone.SetDoNotAllowFootprints(False)
        outline=zone.Outline();outline.NewOutline()
        for x,y in _shell_body(copper.board,jack).exterior.coords[:-1]:outline.Append(p.FromMM(x),p.FromMM(y))
        copper.board.Add(zone)

def add_planes(copper):
    """In1 solid ground. In2 ground with the 3V3 island cut out of it as a notch from the rear edge, so the
    two In2 areas never overlap and the autorouter reads two clean planes."""
    x0,y0,x1,y1=copper.bounds;whole=box(x0,y0,x1,y1);island=plane_island(copper)
    add_zone(copper.board,'GND',p.In1_Cu,whole.exterior.coords[:-1],0)
    add_zone(copper.board,'GND',p.In2_Cu,whole.difference(island.buffer(ZONE_CLEARANCE,join_style='mitre')).exterior.coords[:-1],0)
    add_zone(copper.board,'3V3',p.In2_Cu,island.exterior.coords[:-1],0)
    for layer in (p.In1_Cu,p.In2_Cu):copper.board.SetLayerType(layer,p.LT_POWER)

def stem(v):return ROOT/'pcb'/v/('worxboard-ergo-'+v)
def work(v):return ROOT/'pcb/.work'/v

def load_with_rules(v,name):
    """Load a work board with the project's design rules and net classes. LoadBoard reads the .kicad_pro
    beside the board; without it the board falls back to KiCad's defaults and the DSN carries those."""
    shutil.copyfile(str(stem(v))+'.kicad_pro',work(v)/(name+'.kicad_pro'))
    return p.LoadBoard(str(work(v)/(name+'.kicad_pcb')))

def critical(v):
    board=load_with_rules(v,'seed');copper=Copper(board)
    try:
        escape_stubs(copper,MUX,[net for _,name in USB_PORTS for net in (name+'_DP',name+'_DM')]+['USB_MUX_DP','USB_MUX_DM'])
        # Every RP2040 GPIO, debug, reset and DVDD pin leaves straight first, so no later route (the crystal's
        # in particular) bends across a neighbour's exit.
        escape_stubs(copper,MCU,[net for net in GPIO_NETS if net]+['SWCLK','SWDIO','RUN'])
        escape_stubs(copper,MCU,['1V1'],numbers=CORE_STUB_PINS)
        # Crystal, QSPI and the RP2040-side USB first, from straight pin stubs. Then the supply vias, inside the
        # RP2040 pad row so they block no exit, before a receptacle pair can fence a clamp's ground pad. Then 1V1.
        route_core(copper)                        # 1V1 vias before the crystal routes can fence pin 23
        route_groups(copper,CONTROLLER_NETS)      # the receptacle pairs then run around the controller
        exposed_pad_vias(copper);plane_vias(copper)
        lengths={}
        for jack,name in USB_PORTS:
            lengths[name]=route_usb_pair(copper,jack,name)
            # Then the second pad of each line, the ESD clamp and the mux pads, before the next pair can fence them in.
            join_pair_locally(copper,jack,name)
        route_groups(copper,SUPPLY_NETS)
        escapes_blocked=escape_vias(copper,MCU)
        add_planes(copper);add_shell_keepouts(copper)
    finally:
        copper.write(locked=None)      # escape vias stay unlocked: the grid stage may move them
        p.SaveBoard(str(work(v)/'critical.kicad_pcb'),board)     # a failed run leaves the copper so far to look at
    net_mm={}
    for route in copper.routes:net_mm[route.net]=round(net_mm.get(route.net,0)+route.length(),2)
    report={'usb_pair_mm':{name:[round(a,2),round(b,2)] for name,(a,b) in lengths.items()},
            'scripted_tracks':len(board.GetTracks()),'scripted_net_mm':net_mm,'escape_vias_not_placed':escapes_blocked}
    (ROOT/f'pcb/reports/{v}-routing.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(v,'critical nets routed;',report['scripted_tracks'],'tracks and vias')

def grid(v):
    """Critical board -> every remaining non-plane net joined by the grid router with rip-up, then the DSN.

    The 4 x 15 matrix is not laid out by physical rows: every row and column net spans both halves, and
    Freerouting 2.5.0 oscillated on it (94 to 141 of 328 connections open in passes 1 to 8 of each trial).
    This stage takes about an hour per board. It works in segments of CHECKPOINT_EVERY joins; each segment
    starts from the board the last one saved, so a run that is cut off resumes where it stopped and ends
    with the same copper as one that was not. The checkpoint is valid only for the critical board it began from."""
    source=work(v)/'critical.kicad_pcb';done_board=work(v)/'grid.kicad_pcb';stamp=work(v)/'grid.json'
    key=hashlib.sha256(source.read_bytes()).hexdigest()
    saved=json.loads(stamp.read_text()) if stamp.exists() and done_board.exists() else {}
    if saved.get('critical_sha256')!=key:saved={'critical_sha256':key,'state':{'ripped':{},'failed':{}},'done':False,'joined':[]}
    print(v,'grid stage','resumes from its checkpoint' if saved['joined'] or saved['done'] else 'starts from the critical board',flush=True)
    board=load_with_rules(v,'grid' if saved['joined'] or saved['done'] else 'critical')
    if not saved['done']:
        copper=Copper(board);adopt_board_copper(copper)
        joined,_,saved['done']=complete(copper,saved['state'],CHECKPOINT_EVERY)
        saved['joined']+=joined
        for item in list(board.GetTracks()):board.Remove(item)
        copper.write(locked=None);p.SaveBoard(str(done_board),board)
        stamp.write_text(json.dumps(saved,indent=1,sort_keys=True)+'\n')
        if not joined and not saved['done']:raise RuntimeError('grid stage made no progress')
        # pcbnew cannot load a second board into the same process, so the next segment is a fresh process.
        sys.stdout.flush();os.execv(sys.executable,[sys.executable]+sys.argv)
    if not p.ExportSpecctraDSN(board,str(work(v)/'board.dsn')):raise RuntimeError('DSN export failed')
    left_open=list(saved['state']['failed'].values())
    report_path=ROOT/f'pcb/reports/{v}-routing.json';report=json.loads(report_path.read_text())
    report.update({'grid_joined':saved['joined'],'left_for_autorouter':left_open})
    report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(v,'grid stage done;',len(left_open),'nets left for the autorouter',flush=True)

def adopt_board_copper(copper):
    """Make every track and via already on the board known to the router: as obstacles, and as nodes that
    later joins may land on. write() leaves them alone."""
    for item in copper.board.GetTracks():
        net=item.GetNetname()
        if item.Type()==p.PCB_VIA_T:
            x,y=mm(item.GetPosition())
            route=Route(net,rules.TRACK,[],[(x,y)],[maze.nearest(layer,x,y) for layer in maze.LAYERS])
        else:
            layer={p.F_Cu:'F',p.B_Cu:'B'}.get(item.GetLayer())
            if layer is None:raise SystemExit(f'{net}: track on {item.GetLayerName()}, a plane layer')
            line=LineString([mm(item.GetStart()),mm(item.GetEnd())])
            nodes=[maze.nearest(layer,*line.interpolate(d).coords[0]) for d in _steps(line.length)+[line.length]]
            route=Route(net,p.ToMM(item.GetWidth()),[(layer,list(line.coords))],[],nodes)
        route.rippable=not item.IsLocked()
        copper.obstacles.add_route(route,rules.VIA_D,rules.VIA_DRILL);copper.routes.append(route)
    copper.adopted=len(copper.routes)

def complete(copper,state=None,max_joins=None):
    """Join every open net that is not a plane net, short nets first, with the grid router. A net that finds
    no way gets one: the grid routes of the nets in its way are torn up and routed again after it.
    state carries the tear-up counts and the given-up nets across calls; with max_joins the call stops after
    that many joins. Returns (nets joined, reasons for the nets given up, True when nothing is left to try)."""
    state=state if state is not None else {'ripped':{},'failed':{}}
    ripped,failed=state['ripped'],state['failed']
    names=sorted(str(net) for net in copper.board.GetNetsByName().keys() if str(net))
    queue=[net for net in names if net not in rules.PLANE_NETS and net not in failed and not net.startswith('unconnected-')
           and len(islands_of(copper,net))>1]
    queue.sort(key=lambda net:_span(copper,net))      # short local nets first, so long ones go around them
    joined=[]
    while queue:
        if max_joins is not None and len(joined)>=max_joins:return joined,list(failed.values()),False
        net=queue.pop(0)
        if len(islands_of(copper,net))<2:continue
        try:
            victims=_join_ripping(copper,net,ripped)
        except Unroutable as failure:
            failed[net]=str(failure);print(' open  ',net,'-',failure,flush=True);continue
        print(' joined',net,('after tearing up '+' '.join(sorted(victims))) if victims else '',flush=True)
        joined.append(net)
        for victim in sorted(victims):
            ripped[victim]=ripped.get(victim,0)+1
            if victim not in queue:queue.append(victim)
    return joined,list(failed.values()),True

def _width(net):
    return rules.POWER_TRACK if any(fnmatch(net,one) for one in rules.POWER_NETS) else rules.TRACK

def _join_ripping(copper,net,ripped):
    """Join one net island by island. When an island has no way, find one through the completion routes
    only, tear up the nets on it (each at most RIP_LIMIT times) and take it. Returns the torn-up nets."""
    width=_width(net);victims=set()
    budget,greed=COMPLETE_SEARCH
    job=job_for({net},width,maze.LAYERS,COMPLETE_REACH,greed,budget)
    islands=islands_of(copper,net);tree=islands.pop(0)
    while islands:
        island=min(islands,key=lambda nodes:_gap(nodes,tree));islands.remove(island)
        path=maze.search(copper.obstacles,job,sorted(island),tree)
        if path is None:
            fixed=[r for r in copper.routes if not r.rippable or r.net==net]
            path=maze.search(copper.obstacles_for(fixed),job,sorted(island),tree)
            if path is None:
                why='search budget spent' if maze.last_search['budget_hit'] else 'enclosed by fixed copper'
                raise Unroutable(f'{net}: no path from {maze.node_xy(min(island))} even through the grid routes ({why})')
            blockers=_blockers(copper,net,width,path)
            stuck=[b for b in blockers if ripped.get(b,0)>=RIP_LIMIT]
            if stuck:raise Unroutable(f'{net}: the way is held by {" ".join(sorted(stuck))}, torn up {RIP_LIMIT} times already')
            copper.rip(blockers);victims|=blockers
        route=maze.to_route(path,net,width);route.rippable=True;copper.commit(route)
        tree|=island;tree.update(path)
    return victims

def _blockers(copper,net,width,path):
    """Nets whose completion routes come too close to a path."""
    model=maze.Obstacles(rules.CLEARANCE,rules.HOLE_TO_HOLE)
    trial=maze.to_route(path,net,width);model.add_route(trial,rules.VIA_D,rules.VIA_DRILL)
    found=set()
    for route in copper.routes:
        if route.net==net or not route.rippable:continue
        shapes=[(layer,LineString(points).buffer(route.width/2)) for layer,points in route.lines if len(points)>1]
        shapes+=[(layer,Point(x,y).buffer(rules.VIA_D/2)) for x,y in route.vias for layer in maze.LAYERS]
        for layer,shape in shapes:
            if any(other.distance(shape)<rules.CLEARANCE+maze.SLACK for other in model.shapes[layer]):
                found.add(route.net);break
    return found

def _span(copper,net):
    """Half the perimeter of the box around a net's pads."""
    x0,y0,x1,y1=unary_union([e[2] for e in copper.pads_on(net)]).bounds
    return (x1-x0)+(y1-y0)

def stitch(copper):
    """Ground vias tying In1, the In2 ground and the B.Cu pour together: a grid over the board, and one beside
    every via of a USB line so the return current has a short way between the two ground layers."""
    island=plane_island(copper);outline=translate(board_outline(),*OFFSET).buffer(-rules.EDGE_CLEARANCE-rules.VIA_D/2)
    x0,y0,x1,y1=copper.bounds
    grid=[(x0+i*STITCH_PITCH,y0+j*STITCH_PITCH) for i in range(int((x1-x0)/STITCH_PITCH)+1)
          for j in range(int((y1-y0)/STITCH_PITCH)+1)]
    beside=[[(x+dx,y+dy) for dx,dy in RETURN_VIA_OFFSETS]
            for route in copper.routes if fnmatch(route.net,'USB_*') for x,y in route.vias]
    placed=[]
    for choices,search in [(spots,RETURN_VIA_REACH) for spots in beside]+[([spot],STITCH_REACH) for spot in grid]:
        spot=next(filter(None,(_stitch_site(copper,outline,island,x,y,search) for x,y in choices)),None)
        if spot is None:continue
        copper.commit(Route('GND',rules.TRACK,[],[spot],[]));placed.append(spot)
    return placed

def _stitch_site(copper,outline,island,x,y,search):
    """Nearest lattice spot to (x, y) within search where a ground via clears everything, or None."""
    for dx,dy in sorted(((i*maze.GRID,j*maze.GRID) for i in range(-round(search/maze.GRID),round(search/maze.GRID)+1)
                         for j in range(-round(search/maze.GRID),round(search/maze.GRID)+1)),key=lambda d:hypot(*d)):
        node=maze.nearest('F',x+dx,y+dy);spot=Point(maze.node_xy(node))
        if not outline.covers(spot) or island.covers(spot):continue
        if copper.obstacles.drill_fits(node,rules.VIA_DRILL+2*STITCH_HOLE_MARGIN) \
           and all(copper.obstacles.clear(layer,node,frozenset(),rules.VIA_D/2) for layer in maze.LAYERS):
            return maze.node_xy(node)
    return None

def add_pour(board):
    """Ground pour on B.Cu over the whole board, under the scripted and autorouted copper."""
    x0,y0,x1,y1=(lambda e:(*mm(e.GetOrigin()),*mm(e.GetEnd())))(board.GetBoardEdgesBoundingBox())
    add_zone(board,'GND',p.B_Cu,box(x0,y0,x1,y1).exterior.coords[:-1],0)

def finish(v):
    """Critical board plus the committed autorouter session, the rest joined by the maze router, stitched,
    poured and filled, saved as the project board."""
    record=json.loads((ROOT/'pcb'/v/'autoroute.json').read_text())
    if hashlib.sha256((work(v)/'board.dsn').read_bytes()).hexdigest()!=record['dsn_sha256']:
        raise SystemExit(f'{v}: placement or scripted copper changed since the autorouter ran. Run make pcb-autoroute.')
    board=load_with_rules(v,'grid')
    if not p.ImportSpecctraSES(board,str(ROOT/'pcb'/v/'autoroute.ses')):raise RuntimeError('session import failed')
    copper=Copper(board);adopt_board_copper(copper)
    autorouted=len(list(board.GetTracks()))
    try:
        completed,left_open,_=complete(copper);stitches=stitch(copper)
    finally:
        del copper.routes[:copper.adopted]       # the board holds these already
        copper.write()
    add_pour(board)
    p.ZONE_FILLER(board).Fill(board.Zones())
    p.SaveBoard(str(stem(v))+'.kicad_pcb',board)
    report_path=ROOT/f'pcb/reports/{v}-routing.json';report=json.loads(report_path.read_text())
    tracks=list(board.GetTracks())
    report.update({'tracks':sum(t.Type()==p.PCB_TRACE_T for t in tracks),'vias':sum(t.Type()==p.PCB_VIA_T for t in tracks),
                   'zones':board.GetAreaCount(),'track_mm':round(sum(p.ToMM(t.GetLength()) for t in tracks if t.Type()==p.PCB_TRACE_T),1),
                   'scripted_and_autorouted_items':autorouted,'nets_joined_after_autorouter':completed,
                   'nets_left_open':left_open,
                   'stitching_vias':len(stitches)})
    report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(v,'routed:',report['tracks'],'tracks,',report['vias'],'vias,',report['zones'],'zones;',
          len(completed),'nets joined after the autorouter,',len(stitches),'stitching vias')
    if left_open:print(v,'LEFT OPEN, the DRC report and the gate will show them:','; '.join(left_open))

if __name__=='__main__':
    {'critical':critical,'grid':grid,'finish':finish}[sys.argv[2]](sys.argv[1])
