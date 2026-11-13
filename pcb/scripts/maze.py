# SPDX-License-Identifier: GPL-3.0-or-later
"""Grid maze router for the nets route.py places by hand: two copper layers, exact clearance.

Coordinates are board millimetres. A node is (layer, ix, iy) on a GRID lattice. Obstacles are
shapely shapes with a net; a track of another net may come no closer than the clearance.
"""
import heapq
from dataclasses import dataclass,field
from itertools import count
from math import hypot
import shapely
from shapely.geometry import LineString,Point

GRID=0.1
SLACK=0.03            # added to every clearance: a diagonal grid step cuts a corner by less than this
TURN_COST=0.15        # millimetres of detour a bend is worth, so paths run straight
VIA_COST=4.0
ESTIMATE_GOALS=12
MOVES=tuple((dx,dy) for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy)
LAYERS=('F','B')

def node_xy(node):return node[1]*GRID,node[2]*GRID
def nearest(layer,x,y):return layer,round(x/GRID),round(y/GRID)

@dataclass
class Route:
    """One connection: polylines by layer, and via centres."""
    net:str
    width:float
    lines:list=field(default_factory=list)      # (layer, [(x, y), ...])
    vias:list=field(default_factory=list)       # (x, y)
    nodes:list=field(default_factory=list)      # lattice nodes on the copper, for later connections

    def length(self):
        return sum(LineString(points).length for _,points in self.lines if len(points)>1)

class Obstacles:
    """Copper and holes on the two outer layers. Shapes of the routed net itself never block."""
    def __init__(self,clearance,hole_gap):
        self.clearance=clearance+SLACK
        self.shapes={layer:[] for layer in LAYERS};self.nets={layer:[] for layer in LAYERS}
        self.trees={layer:None for layer in LAYERS};self.cache={}
        self.holes=[]                     # (x, y, drill diameter) of every drilled hole, any net
        self.hole_gap=hole_gap

    def add(self,layers,net,shape):
        for layer in layers:
            self.shapes[layer].append(shape);self.nets[layer].append(net);self.trees[layer]=None
        self.cache.clear()

    def add_hole(self,x,y,drill):self.holes.append((x,y,drill))

    def drill_fits(self,node,drill):
        """True when a hole here keeps the fabricator's wall to every other hole. The same spot is a reuse."""
        x,y=node_xy(node)
        return all(hypot(x-hx,y-hy)<1e-6 or hypot(x-hx,y-hy)>=(drill+hd)/2+self.hole_gap for hx,hy,hd in self.holes)

    def mark(self):return {**{layer:len(shapes) for layer,shapes in self.shapes.items()},'holes':len(self.holes)}

    def rollback(self,mark):
        """Forget every shape added since mark()."""
        del self.holes[mark['holes']:]
        for layer in LAYERS:
            del self.shapes[layer][mark[layer]:],self.nets[layer][mark[layer]:]
            self.trees[layer]=None
        self.cache.clear()

    def add_route(self,route,via_d,via_drill):
        for layer,points in route.lines:
            if len(points)>1:self.add(layer,route.net,LineString(points).buffer(route.width/2))
        for x,y in route.vias:
            self.add(LAYERS,route.net,Point(x,y).buffer(via_d/2));self.add_hole(x,y,via_drill)

    def clear(self,layer,node,nets,radius):
        """True when copper of the given nets, radius wide, may sit on this node."""
        key=(layer,node[1],node[2],nets,radius)
        if key not in self.cache:
            if self.trees[layer] is None:self.trees[layer]=shapely.STRtree(self.shapes[layer])
            hits=self.trees[layer].query(Point(node_xy(node)),predicate='dwithin',distance=radius+self.clearance)
            self.cache[key]=all(self.nets[layer][i] in nets for i in hits)
        return self.cache[key]

def _octile(a,b):
    dx,dy=abs(a[1]-b[1]),abs(a[2]-b[2])
    return (max(dx,dy)+0.4142*min(dx,dy))*GRID

@dataclass(frozen=True)
class Job:
    """What one search may do."""
    nets:frozenset                 # nets whose copper does not block
    radius:float                   # half the track width, or half a pair envelope
    via_radius:float
    via_drill:float
    layers:tuple=LAYERS            # layers the track may use
    reach:float=6.0                # search this far outside the box around the terminals

def search(obstacles,job,starts,goals):
    """Cheapest lattice path from any start node to any goal node, or None."""
    goal_set=set(goals)
    box=[f(n[i] for n in list(starts)+list(goals)) for i in (1,2) for f in (min,max)]
    margin=round(job.reach/GRID)
    def inside(n):return box[0]-margin<=n[1]<=box[1]+margin and box[2]-margin<=n[2]<=box[3]+margin
    # A sample of the goals keeps the estimate cheap. It can overestimate, so a path may be slightly long.
    anchor=sorted(goal_set)[::max(1,len(goal_set)//ESTIMATE_GOALS)]
    def estimate(n):return min(_octile(n,g) for g in anchor)
    best={};queue=[];order=count()          # the counter breaks ties before unlike tuples are compared
    for n in starts:
        best[(n,None)]=0.0;heapq.heappush(queue,(estimate(n),0.0,next(order),n,None,None))
    parents={}
    while queue:
        _,cost,_,node,move,parent=heapq.heappop(queue)
        if best.get((node,move),1e9)<cost:continue
        parents.setdefault((node,move),parent)
        if node in goal_set:return _unwind(parents,(node,move))
        layer=node[0]
        steps=[((layer,node[1]+dx,node[2]+dy),(dx,dy),hypot(dx,dy)*GRID+(TURN_COST if move not in (None,(dx,dy)) else 0))
               for dx,dy in MOVES]
        other=LAYERS[1-LAYERS.index(layer)]
        if other in job.layers and move is not None:
            steps.append(((other,node[1],node[2]),None,VIA_COST))
        for nxt,nmove,price in steps:
            if not inside(nxt) or nxt[0] not in job.layers:continue
            if nmove is None:
                if not obstacles.drill_fits(nxt,job.via_drill):continue
                if not all(obstacles.clear(l,nxt,job.nets,job.via_radius) for l in LAYERS):continue
            elif nxt not in goal_set and not obstacles.clear(nxt[0],nxt,job.nets,job.radius):continue
            total=cost+price
            if total<best.get((nxt,nmove),1e9):
                best[(nxt,nmove)]=total
                heapq.heappush(queue,(total+estimate(nxt),total,next(order),nxt,nmove,(node,move)))
    return None

def _unwind(parents,state):
    path=[]
    while state is not None:
        path.append(state[0]);state=parents[state]
    return path[::-1]

def to_route(path,net,width):
    """Lattice path -> polylines with collinear points dropped, and a via at each layer change."""
    route=Route(net,width,nodes=list(path));run=[]
    for i,node in enumerate(path):
        if run and node[0]!=run[-1][0]:
            route.lines.append((run[-1][0],_corners(run)));route.vias.append(node_xy(node));run=[]
        run.append(node)
    route.lines.append((run[-1][0],_corners(run)))
    return route

def _corners(run):
    points=[node_xy(n) for n in run];kept=points[:1]
    for before,here,after in zip(points,points[1:],points[2:]):
        cross=(here[0]-before[0])*(after[1]-here[1])-(here[1]-before[1])*(after[0]-here[0])
        if abs(cross)>1e-9:kept.append(here)
    return kept+points[-1:] if len(points)>1 else kept
