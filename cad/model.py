# SPDX-License-Identifier: GPL-3.0-or-later
"""Split Planck case, Sculpt-style shell. Dimensions in mm, z up, PCB plane horizontal.

Stack: pocketed chassis, switch plate, top cover, palm rest. One smooth shell wraps both
plank halves and the rear bay. A slot through the valley keeps the two wells apart. The rim
is flat, so the top prints as one face. The top cover drops into the rim, flush with it. It
hides the plate, the rear bay and the eight screws, and carries the display window. A
full-width palm rest sits on the front shelf and falls to a rolled lip. The chassis has no
feet. It sits flat on four pads. A separate magnetic riser under the front edge lifts the
front. Split meshes share a rear registration tab; that joint is not a printed fit approval.

Frame. Every part is built in layout coordinates, y toward the typist, as KiCad draws the
board from the top. With z up that frame is left-handed, so make() mirrors every solid once
at the end. Exported y runs away from the typist. cad_xy() maps a layout point into that frame.

This is envelope CAD, revision A0.
"""
from dataclasses import dataclass
from math import asin, cos, hypot, pi, radians, sin, sqrt, tan
from build123d import (Polyline, Polygon, Face, Wire, Plane, Axis, extrude, revolve, fillet, chamfer, Spline, Line,
                       ThreePointArc, TangentArc, RectangleRounded, Pos, Rot, Box, Cylinder, Align, Compound)
from build123d.topology.shape_core import downcast
from OCP.ShapeCustom import ShapeCustom
from shapely.geometry import LineString, Point, Polygon as PlanPolygon
from layout import (keys, outline, board_outline, holes, variants, DISPLAY, PORTS, U,
                    PCB_EDGE_INSET, PCB_HOLE_D, USB_RECEPTACLE_L)
from layout.model import RIM, _world

A = (Align.CENTER, Align.CENTER, Align.MIN)
REARWARD = (Align.CENTER, Align.MAX, Align.MIN)   # runs from its anchor away from the typist
FORWARD = (Align.CENTER, Align.MIN, Align.MIN)    # runs from its anchor toward the typist
EPS = 0.01          # overcut, so a pocket shares no face with the surface it opens on
OVERCUT = 0.2       # a through cut passes both faces by this much
CUT_UP = 60.0       # taller than any part; a cut this high leaves the top open
FLOOR = 2.4
PCB_T = 1.6
PCB_TOP = 8.0
WALL = 3.2
SHELF = 6.0
PLATE_INSET = 0.7
CAP_LIFT = 3.0      # keycap envelope underside above the plate top, at rest
# Nominal switch data, not measured: body side, housing top above the plate top, travel.
SWITCH = {'mx': (15.6, 6.6, 4.0), 'choc': (15.0, 2.8, 3.0)}

# Shell plan. Right half; the left is mirrored. The lip and the rear are arcs about the centre line.
AXIS_Y, LIP_Y = -250.0, 145.0     # the front lip is a circle about the vertical axis at (0, AXIS_Y)
LIP_X = 116.0                     # where the lip arc ends and the side starts
WING = ((151.5, 48.0), (138.5, -38.0))   # waypoints of the side guide spline: wing tip, rear shoulder
REAR_Y, REAR_X, REAR_SAG = -78.0, 90.0, 12.0   # rear arc: centre y, half width, how far the ends sit forward
SIDE_SPANS = 8                    # each span of the side becomes two tangent arcs
DECK_FRONT = 3.5 * U + RIM        # deck front edge in plank-local y
GULL_REACH = 8 * U                # plank-local x past the wing, so the gull line leaves the shell
FAR_FRONT = 200.0                 # world y in front of everything
PLAN_SAMPLES = 400
SKIN_MIN, VALLEY_CLEAR, FENCE_CLEAR, WEB_MIN = 4.0, 2.3, 2.2, 2.5   # plan guards

# Chassis
TOP_R = 2.0         # starts above the USB tunnel roof, so the roof keeps a full lintel
BOT_C = 4.5         # 45 degree sweep under the side wall; it prints without support and stays under SHELF
RIM_H = 2.5         # flat rim above the plate top; the top cover fills it flush, under the keycaps
RECESS = 0.35       # plate recess, radial, outside the deck outline inset
RIM_FRONT = 2.4     # front fence, deck front edge to gull line
BOSS_R = 3.6

# Valley slot
V_INSET, V_REAR, V_WEB = 2.4, 20.0, 5.3
V_APEX_R, V_FRONT_R, V_TOP_R, V_BOT_C = 3.5, 6.0, 1.5, 1.5

# USB. The receptacle sits on the PCB top, mouth flush with the PCB rear edge, facing rearward.
RECEPTACLE = (8.94, USB_RECEPTACLE_L, 3.26)    # body: width, length, height
PLUG_AXIS = 1.58                  # plug centre line above the PCB top
PLUG_BODY = (12.35, 30.0, 6.5)    # overmold: width, length outside the mouth, height
PLUG_TIP = (8.34, 6.65, 2.56)     # shell that enters the receptacle
RELIEF_W = 14.0
RELIEF_DROP = 2.5   # tunnel floor below the PCB top
RELIEF_RISE = 5.3   # tunnel ceiling above the PCB top; the overmold tops out at 4.83
RELIEF_R = 1.5      # corner radius of the tunnel section
RELIEF_IN = 3.0     # the tunnel starts this far inside the mouth, so a slanted wall is cleared too
ROOF_MIN = 1.0      # thinner than this, the rim over a tunnel is cut open instead
NOTCH_FWD = 8.0     # plate notch in front of the mouth: the receptacle body plus 0.7
CUT_BACK = 40.0

# Top cover
COVER_FIT = 0.2     # gap to the rim, radial
COVER_SKIN = 0.8    # unbroken top left over a blind screw pilot
COVER_BOSS_D = 5.0  # boss from the cover down through the plate to the PCB top
PLATE_HOLE_D = 5.4
WINDOW_CLEAR, WINDOW_R = 1.0, 2.0   # key block opening outside the 1u cells, and its corner radius
LCD_T, LCD_SINK = 1.2, 1.0          # module envelope thickness, and how far it sits below the plate top
LCD_FIT = 0.2

# Screws from below: clearance hole and a counterbore that hides the head. Pilots are blind.
SCREW_D = 2.8
HEAD_D, HEAD_DEPTH = 5.2, 2.2
PILOT_D = 2.1
PALM_PILOT_DEPTH = 6.0

# Palm rest
PALM_GAP = 0.8      # deliberate reveal between chassis fence and palm
PALM_FOOT_C = 0.8   # shadow line where the palm meets the shelf
PALM_STOCK = 40.0
B_R, WING_R = 20.0, 4.0
CAP_CLEAR = 2.5     # palm rear edge below the keycap tops
LIP_DROP = 6.0      # the top falls this much from the rear edge to the lip
PALM_R, ROLL_N, CROWN_N = 3.0, 16, 32
LIP_INSET, REAR_OFF = 0.4, 0.3
TOOL_FLOOR = -5.0
CROWN_SWEEP = 100.0   # degrees of revolve, centred on +y
PALM_SCREWS = ((40.0, 95.0), (95.0, 84.0), (135.0, 80.0))   # right half

# Underside hardware and riser. Right half; the left is mirrored.
RISER_SETBACK, RISER_DEPTH, RISER_HALF_X, RISER_R = 6.0, 18.0, 112.0, 6.0
RISER_MID_R = LIP_Y - AXIS_Y - RISER_SETBACK - RISER_DEPTH / 2
RISER_TILT = 6.7    # degrees the riser lifts the front
RISER_STOCK = 40.0
MAGNET_D, MAGNET_DEPTH = 6.1, 3.1
PAD_D, PAD_DEPTH = 10.2, 1.0
PAD_PROUD = 2.0     # pad face below the chassis underside
STANCE_CLEAR = 0.5  # chassis rear above the desk when it stands on the riser
NEST_D, NEST_DEPTH = PAD_D + 0.6, PAD_PROUD + 0.4   # riser pocket that drops over a front pad
RISER_PAD_X = 80.0
HALF_SPACE = (800.0, 800.0, 200.0)

def _on_arc(radius, x):
    """The point at x on a circle about the lip axis."""
    return x, AXIS_Y + sqrt(radius ** 2 - x ** 2)

MAGNETS = (_on_arc(RISER_MID_R, 25.0), _on_arc(RISER_MID_R, 62.0))
PADS = (_on_arc(RISER_MID_R, 100.0), (118.0, -42.0))   # front pair under the riser, rear pair on the tilt line
REAR_PAD_Y = PADS[1][1]

@dataclass(frozen=True)
class Stack:
    """Heights of one variant and the USB mouths as (x, mouth y)."""
    spec: dict
    switch: tuple
    plate_top: float
    mouths: tuple

    @property
    def plate_bot(self):
        return self.plate_top - self.spec['plate']

    @property
    def rim_top(self):
        return self.plate_top + RIM_H

    @property
    def roofed(self):
        """True when the rim is tall enough to bridge the USB tunnels."""
        return self.rim_top - (PCB_TOP + RELIEF_RISE) >= ROOF_MIN

def cad_xy(x, y):
    """A layout point in the exported, right-handed frame."""
    return x, -y

def to_cad_frame(shape):
    """Mirror a solid built in layout coordinates into the exported frame. A mirror leaves left-handed
    surface frames. STEP cannot store those, and OCC integrates a different volume over them, so they
    are made direct here."""
    flipped = shape.mirror(Plane.XZ)
    flipped.wrapped = downcast(ShapeCustom.DirectFaces_s(flipped.wrapped))
    return flipped

def _ring(coords, tol=0.05):
    """Drop the repeated point a closed ring picks up. It tessellates as a hole."""
    pts = []
    for x, y in coords:
        x, y = float(x), float(y)
        if pts and (x - pts[-1][0]) ** 2 + (y - pts[-1][1]) ** 2 < tol * tol:
            continue
        pts.append((x, y))
    if len(pts) >= 2 and (pts[0][0] - pts[-1][0]) ** 2 + (pts[0][1] - pts[-1][1]) ** 2 < tol * tol:
        pts.pop()
    if len(pts) < 3:
        raise RuntimeError('degenerate ring')
    return pts

def prism(poly, z, height):
    if poly.is_empty or height <= 0:
        raise RuntimeError('empty prism')
    if poly.geom_type == 'MultiPolygon':
        poly = max(poly.geoms, key=lambda g: g.area)
    if poly.geom_type != 'Polygon':
        raise RuntimeError(poly.geom_type)
    outer = Face(Polyline(*_ring(poly.exterior.coords), close=True))
    part = Pos(0, 0, z) * extrude(outer, amount=height, dir=(0, 0, 1))
    for ring in poly.interiors:
        part -= Pos(0, 0, z - 0.1) * extrude(
            Face(Polyline(*_ring(ring.coords), close=True)), amount=height + 0.2, dir=(0, 0, 1))
    return part

def drill(shape, x, y, z, h, d):
    return shape - Pos(x, y, z) * Cylinder(d / 2, h, align=A)

def _sink(shape, x, y, depth, d):
    """Blind round pocket in the underside, which is at z = 0."""
    return drill(shape, x, y, -EPS, depth + EPS, d)

def _screw_from_below(shape, x, y, reach):
    """Clearance hole up from the underside to z = reach, with a counterbore for the head."""
    shape = drill(shape, x, y, -OVERCUT, reach + 2 * OVERCUT, SCREW_D)
    return _sink(shape, x, y, HEAD_DEPTH, HEAD_D)

def _cut_mask():
    """Left keeps x<=0 plus a tab that registers into the right rear apron."""
    half = Pos(-800, -500, -40) * Box(800, 1200, 200, align=(Align.MIN, Align.MIN, Align.MIN))
    tab = Pos(0, -36, -40) * Box(18, 18, 200, align=(Align.MIN, Align.MIN, Align.MIN))
    return half + tab

def mirrored(right_half):
    """Both sides of a right-half point list."""
    return [(side * x, y) for side in (-1, 1) for x, y in right_half]

def _plank(lx, ly):
    """Right plank local mm to world, through the layout's own transform."""
    return _world('right', lx / U - 0.5, ly / U)

def _face(sketch):
    """fillet() hands back a Sketch. Take its one Face."""
    return sketch if isinstance(sketch, Face) else sketch.faces()[0]

def plan_ring(face):
    """A plan face as a shapely polygon, for distance guards."""
    wire = _face(face).outer_wire()
    return PlanPolygon([(p.X, p.Y) for p in (wire.position_at(i / PLAN_SAMPLES) for i in range(PLAN_SAMPLES))])

def _biarc(start, t_start, end, t_end):
    """Two tangent arcs from start to end that match the unit tangents at both ends."""
    chord, both = end - start, t_start + t_end
    spread = 2 * (1 - t_start.dot(t_end))
    if spread < 1e-12:
        reach = chord.dot(chord) / (4 * chord.dot(t_end))
    else:
        reach = (sqrt(chord.dot(both) ** 2 + spread * chord.dot(chord)) - chord.dot(both)) / spread
    joint = (start + t_start * reach + end - t_end * reach) / 2
    first = TangentArc(start, joint, tangent=t_start)
    return [first, TangentArc(joint, end, tangent=first % 1)]

def shell_face():
    """Outer plan. The lip and the rear are arcs. A spline through the WING waypoints, tangent to both
    arcs, guides each side. The side itself is a chain of tangent arcs fitted to that spline: no straight,
    no corner, and every wall, sweep and fillet face stays analytic for the STEP volume round trip."""
    lip_end = _on_arc(LIP_Y - AXIS_Y, LIP_X)
    rear_r = (REAR_X ** 2 + REAR_SAG ** 2) / (2 * REAR_SAG)
    rear_end = (REAR_X, REAR_Y + REAR_SAG)
    along_lip = (lip_end[1] - AXIS_Y, -lip_end[0])                 # leaving the lip, moving outward
    along_rear = (rear_end[1] - (REAR_Y + rear_r), -rear_end[0])   # entering the rear arc, moving inward
    guide = Spline(lip_end, *WING, rear_end, tangents=[along_lip, along_rear])
    stations = [(guide @ (i / SIDE_SPANS), guide % (i / SIDE_SPANS)) for i in range(SIDE_SPANS + 1)]
    side = [arc for near, far in zip(stations, stations[1:]) for arc in _biarc(*near, *far)]
    lip = ThreePointArc((-LIP_X, lip_end[1]), (0, LIP_Y), lip_end)
    rear = ThreePointArc(rear_end, (0, REAR_Y), (-REAR_X, rear_end[1]))
    return Face(Wire([lip, *side, rear, *(arc.mirror(Plane.YZ) for arc in side)]))

def valley_face():
    """Slot between the wells. Its sides run parallel to the plank inner edges, V_INSET clear of them."""
    lx = -RIM - V_INSET
    (x0, y0), (x1, y1) = _plank(lx, 0), _plank(lx, 1)
    rear = (x0 + (V_REAR - y0) * (x1 - x0) / (y1 - y0), V_REAR)   # where the inset line crosses world y = V_REAR
    front = _plank(lx, DECK_FRONT + RIM_FRONT - V_WEB)
    slot = Polygon(rear, front, (-front[0], front[1]), (-rear[0], rear[1]), align=None)
    slot = fillet(slot.vertices().sort_by(Axis.Y)[:2], V_APEX_R)
    return fillet(slot.vertices().sort_by(Axis.Y)[-2:], V_FRONT_R)

def _gull(lx):
    """A point on the gull line, RIM_FRONT in front of the right plank's deck front edge."""
    return _plank(lx, DECK_FRONT + RIM_FRONT)

def break_face():
    """The palm zone: everything in front of the gull line, with B_R on the two centre kinks."""
    centre, wing = _gull(0), _gull(GULL_REACH)
    zone = Polygon(wing, centre, (-centre[0], centre[1]), (-wing[0], wing[1]),
                   (-wing[0], FAR_FRONT), (wing[0], FAR_FRONT), align=None)
    kinks = sorted(zone.vertices(), key=lambda v: abs(v.X))[:2]
    # Stays a Sketch. As a bare Face the palm boolean comes out about 1 mm3 lopsided on Choc.
    return fillet(kinks, B_R)

def riser_face():
    """Riser plan: a band that follows the lip arc, RISER_SETBACK inside it."""
    r_out = RISER_MID_R + RISER_DEPTH / 2
    r_in = RISER_MID_R - RISER_DEPTH / 2
    right_out, right_in = _on_arc(r_out, RISER_HALF_X), _on_arc(r_in, RISER_HALF_X)
    left_out, left_in = _on_arc(r_out, -RISER_HALF_X), _on_arc(r_in, -RISER_HALF_X)
    band = Face(Wire([ThreePointArc(left_out, (0, AXIS_Y + r_out), right_out), Line(right_out, right_in),
                      ThreePointArc(right_in, (0, AXIS_Y + r_in), left_in), Line(left_in, left_out)]))
    return fillet(band.vertices(), RISER_R)

def _check_plan(shell, valley, zone, deck):
    """A parameter change must not let the shell, the slot, the palm zone or the underside hardware drift."""
    skin, slot, palm = plan_ring(shell), plan_ring(valley), plan_ring(zone)
    flat = skin.buffer(-BOT_C)
    checks = {
        f'shell skin outside the deck is under {SKIN_MIN} mm': skin.contains(deck.buffer(SKIN_MIN)),
        f'valley slot is under {VALLEY_CLEAR} mm from the deck': slot.distance(deck) >= VALLEY_CLEAR,
        f'palm zone is under {FENCE_CLEAR} mm from the deck': palm.distance(deck) >= FENCE_CLEAR,
        f'web between the valley slot and the palm zone is under {WEB_MIN} mm': slot.distance(palm) >= WEB_MIN,
        'the riser leaves the flat underside': flat.contains(plan_ring(riser_face())),
        'a pad recess leaves the flat underside': all(
            flat.contains(Point(pad).buffer(PAD_D / 2)) for pad in mirrored(PADS)),
    }
    failed = [message for message, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError('; '.join(failed))

def _mouths(deck):
    """Where each receptacle mouth sits: the PCB rear edge at the port x."""
    board = deck.buffer(-PCB_EDGE_INSET)
    rear = board.bounds[1] - 1
    return tuple((x, board.intersection(LineString([(x, rear), (x, y + RIM)])).bounds[1]) for x, y in PORTS.values())

def _desk():
    """The desk under the riser stance, as a frame: local z = 0 is the desk, local y runs to the typist.
    The desk touches the rear pads PAD_PROUD under the chassis and falls away toward the front."""
    return Pos(0, REAR_PAD_Y, -PAD_PROUD) * Rot(-RISER_TILT, 0, 0)

def below_desk(lift):
    """Everything under the riser-stance desk plane raised by lift."""
    return _desk() * Pos(0, 0, lift - HALF_SPACE[2]) * Box(*HALF_SPACE, align=A)

def _shell_body(plan, top_z):
    """Flat-topped, dressed shell blank. Dress the clean body first; faceted cuts come after."""
    body = extrude(plan, amount=top_z, dir=(0, 0, 1))
    bottom = body.faces().sort_by(Axis.Z)[0]
    body = chamfer(bottom.outer_wire().edges(), BOT_C)
    body = chamfer([e for wire in body.faces().sort_by(Axis.Z)[0].inner_wires() for e in wire.edges()], V_BOT_C)
    body = fillet(body.faces().sort_by(Axis.Z)[-1].outer_wire().edges(), TOP_R)
    return fillet([e for wire in body.faces().sort_by(Axis.Z)[-1].inner_wires() for e in wire.edges()], V_TOP_R)

def _port_tunnel(x, mouth_y, top):
    """Plug tunnel with a rounded section, from just inside the mouth out through the wall and the skin."""
    floor = PCB_TOP - RELIEF_DROP
    section = Plane.XZ * RectangleRounded(RELIEF_W, top - floor, RELIEF_R)   # Plane.XZ faces rearward
    return Pos(x, mouth_y + RELIEF_IN, (floor + top) / 2) * extrude(section, amount=CUT_BACK)

def _port_notch(x, mouth_y, z, height):
    """Open notch over a receptacle and its plug, from NOTCH_FWD in front of the mouth to the rear."""
    return Pos(x, mouth_y + NOTCH_FWD, z - OVERCUT) * Box(RELIEF_W, CUT_BACK, height + 2 * OVERCUT, align=REARWARD)

def _cut_underside(chassis):
    for x, y in mirrored(PALM_SCREWS):
        chassis = _screw_from_below(chassis, x, y, SHELF)
    for x, y in mirrored(MAGNETS):
        chassis = _sink(chassis, x, y, MAGNET_DEPTH, MAGNET_D)
    for x, y in mirrored(PADS):
        chassis = _sink(chassis, x, y, PAD_DEPTH, PAD_D)
    # Rear undercut. Without it the rear edge, which lies behind the rear pads, meets the desk on the riser.
    return chassis - below_desk(STANCE_CLEAR)

def _chassis(deck, plan, zone, stack):
    chassis = _shell_body(plan, stack.rim_top)
    chassis -= prism(deck.buffer(-WALL), FLOOR, CUT_UP)
    chassis -= prism(deck.buffer(-RECESS), stack.plate_bot, CUT_UP)
    chassis -= Pos(0, 0, SHELF) * extrude(zone, amount=CUT_UP, dir=(0, 0, 1))
    for x, y in holes():
        chassis += Pos(x, y, FLOOR) * Cylinder(BOSS_R, PCB_TOP - PCB_T - FLOOR, align=A)
        chassis = _screw_from_below(chassis, x, y, PCB_TOP - PCB_T)
        # The holes sit close to the wall. Scallop it so the cover boss can pass.
        chassis = drill(chassis, x, y, PCB_TOP, CUT_UP, PLATE_HOLE_D)
    tunnel_top = PCB_TOP + RELIEF_RISE if stack.roofed else CUT_UP
    for x, mouth_y in stack.mouths:
        chassis -= _port_tunnel(x, mouth_y, tunnel_top)
    return _cut_underside(chassis)

def _crown_profile(z_rear, r_near):
    """Palm top in (radius from the lip axis, z). It is level at the rear edge and falls LIP_DROP
    along one arc to the lip, then rolls over. Chords only: CROWN_N on the arc, ROLL_N on the roll."""
    r_out = LIP_Y - AXIS_Y - LIP_INSET
    r_in = r_near - REAR_OFF
    run = r_out - r_in
    crown_r = (run ** 2 + LIP_DROP ** 2) / (2 * LIP_DROP)
    sweep = asin(run / crown_r)         # also the slope of the crown where it reaches the lip
    roll_r = r_out - PALM_R
    roll_z = z_rear - LIP_DROP + PALM_R * tan(sweep) - PALM_R / cos(sweep)
    roll = [(roll_r + PALM_R * cos(t), roll_z + PALM_R * sin(t))
            for t in ((pi / 2 - sweep) * (1 - i / ROLL_N) for i in range(ROLL_N + 1))]
    crown = [(r_in + crown_r * sin(t), z_rear - crown_r * (1 - cos(t)))
             for t in (sweep * i / CROWN_N for i in range(CROWN_N + 1))]
    crown = [point for point in crown if point[0] < roll[0][0]]   # the roll takes over where it touches
    return crown + roll + [(r_out, TOOL_FLOOR), (r_in, TOOL_FLOOR)]

def _crown_tool(z_rear, r_near):
    """Solid of revolution under the palm top. The profile is straight chords only, so every
    revolved face is a cone, cylinder or plane. That keeps the STEP volume round trip in the gate."""
    profile = Face(Wire(Polyline(*_crown_profile(z_rear, r_near), close=True).edges()))
    radial = Plane(origin=(0, AXIS_Y, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))   # local x is radius, local y is z
    axis = Axis((0, AXIS_Y, 0), (0, 0, 1))
    return revolve((radial * profile).rotate(axis, -CROWN_SWEEP / 2), axis, CROWN_SWEEP)

def _palm_rest(shell, zone, z_rear):
    """Clean prism on the shelf, dressed, then one boolean with the crown tool. Nothing is dressed
    after it. In the design sweep, OCC fillets on the crowned palm failed the STEP gate, so the rear
    and wing-side edges stay square."""
    plan = shell & (Pos(0, PALM_GAP, 0) * zone)
    palm = Pos(0, 0, SHELF) * extrude(plan, amount=PALM_STOCK, dir=(0, 0, 1))
    palm = fillet(palm.edges().filter_by(Axis.Z).sort_by(Axis.Y)[:2], WING_R)   # the two wing-rear corners
    palm = chamfer(palm.edges().group_by(Axis.Z)[0], PALM_FOOT_C)
    r_near = min(hypot(x, y - AXIS_Y) for x, y in plan_ring(plan).exterior.coords)
    palm &= _crown_tool(z_rear, r_near)
    for x, y in mirrored(PALM_SCREWS):
        palm = drill(palm, x, y, SHELF - EPS, PALM_PILOT_DEPTH + EPS, PILOT_D)
    return palm

def _plate(deck, stack):
    z, cut = stack.plate_bot - OVERCUT, stack.spec['plate'] + 2 * OVERCUT
    plate = prism(deck.buffer(-PLATE_INSET), stack.plate_bot, stack.spec['plate'])
    for k in keys():
        loc = Pos(k.x, k.y, z) * Rot(0, 0, k.angle)
        plate -= loc * Box(stack.spec['cut'], stack.spec['cut'], cut, align=A)
        # South window for a per-key LED. The web between switches stays about 1.8 mm.
        plate -= loc * Pos(0, 9.35, 0) * Box(2.6, 1.1, cut, align=A)
        if k.w >= 2:
            for sx in (-11.938, 11.938):
                plate -= loc * Pos(sx, 0, 0) * Box(6.75, 14.2, cut, align=A)
    for x, y in holes():
        plate = drill(plate, x, y, z, cut, PLATE_HOLE_D)
    plate -= Pos(DISPLAY['x'], DISPLAY['y'], z) * Box(38, 20, cut, align=A)
    for x, mouth_y in stack.mouths:
        plate -= _port_notch(x, mouth_y, stack.plate_bot, stack.spec['plate'])
    return plate

def _key_window(side):
    """One rounded opening around a whole key block, WINDOW_CLEAR outside its 1u cells."""
    block = [k for k in keys() if k.side == side]
    cols, rows = len({k.col for k in block}), len({k.row for k in block})
    centre = (sum(k.x for k in block) / len(block), sum(k.y for k in block) / len(block))
    return Pos(*centre) * Rot(0, 0, block[0].angle) * RectangleRounded(
        cols * U + 2 * WINDOW_CLEAR, rows * U + 2 * WINDOW_CLEAR, WINDOW_R)

def _top_cover(deck, stack):
    """Flat inlay that fills the rim. Two key windows, the display window, and a boss at each screw
    that passes through the plate to the PCB top. The eight screws come up from the underside into
    blind pilots, so the top face is unbroken."""
    top, dx, dy = stack.plate_top, DISPLAY['x'], DISPLAY['y']
    cover = prism(deck.buffer(-RECESS - COVER_FIT), top, RIM_H)
    for side in ('left', 'right'):
        cover -= Pos(0, 0, top - OVERCUT) * extrude(_key_window(side), amount=RIM_H + 2 * OVERCUT, dir=(0, 0, 1))
    cover -= Pos(dx, dy, top - OVERCUT) * Box(DISPLAY['window_width'], DISPLAY['window_depth'], RIM_H + 2 * OVERCUT, align=A)
    # Pocket for the module, which stands proud of the plate. Only the window lip covers the glass.
    cover -= Pos(dx, dy, top - EPS) * Box(DISPLAY['module_width'] + 2 * LCD_FIT, DISPLAY['module_depth'] + 2 * LCD_FIT,
                                          LCD_T - LCD_SINK + LCD_FIT + EPS, align=A)
    for x, y in holes():
        cover += Pos(x, y, PCB_TOP) * Cylinder(COVER_BOSS_D / 2, top - PCB_TOP + RIM_H / 2, align=A)
        cover = drill(cover, x, y, PCB_TOP - EPS, stack.rim_top - COVER_SKIN - PCB_TOP + EPS, PILOT_D)
    if not stack.roofed:
        for x, mouth_y in stack.mouths:
            cover -= _port_notch(x, mouth_y, top, RIM_H)
    return cover

def _riser():
    """Wedge under the front edge, one piece across the split. Two pockets in its top drop over the
    front pads and locate it; magnets hold it. Its sole is PAD_PROUD above the riser-stance desk,
    with two pad recesses, so its pads and the rear pads meet the desk together."""
    riser = Pos(0, 0, -RISER_STOCK) * extrude(riser_face(), amount=RISER_STOCK, dir=(0, 0, 1))
    riser -= below_desk(PAD_PROUD)
    for x, y in mirrored(MAGNETS):
        riser = drill(riser, x, y, -MAGNET_DEPTH, MAGNET_DEPTH + EPS, MAGNET_D)
    for x, y in mirrored(PADS[:1]):
        riser = drill(riser, x, y, -NEST_DEPTH, NEST_DEPTH + EPS, NEST_D)
    for x, y in mirrored([_on_arc(RISER_MID_R, RISER_PAD_X)]):
        along_desk = (y - REAR_PAD_Y) / cos(radians(RISER_TILT))
        riser -= _desk() * Pos(x, along_desk, PAD_PROUD - EPS) * Cylinder(PAD_D / 2, PAD_DEPTH + EPS, align=A)
    return riser

def _usb_envelopes(stack):
    """Receptacle bodies, and a plug seated in each: the overmold outside the mouth, the tip inside."""
    axis_z = PCB_TOP + PLUG_AXIS
    receptacles = Compound([Pos(x, y, PCB_TOP) * Box(*RECEPTACLE, align=FORWARD) for x, y in stack.mouths])
    plugs = Compound([Pos(x, y, axis_z - PLUG_BODY[2] / 2) * Box(*PLUG_BODY, align=REARWARD)
                      + Pos(x, y, axis_z - PLUG_TIP[2] / 2) * Box(*PLUG_TIP, align=FORWARD) for x, y in stack.mouths])
    return {'usb_receptacle_envelopes': receptacles, 'usb_plug_envelopes': plugs}

def _envelopes(deck, stack):
    """Keep-out solids for the assembly and the fit check, by label. They are not parts."""
    body, housing, travel = stack.switch
    top = stack.plate_top
    pcb = prism(board_outline(), PCB_TOP - PCB_T, PCB_T)
    for x, y in holes():
        pcb = drill(pcb, x, y, PCB_TOP - PCB_T - OVERCUT, PCB_T + 2 * OVERCUT, PCB_HOLE_D)
    at_key = [Pos(k.x, k.y, top) * Rot(0, 0, k.angle) for k in keys()]
    return {
        'pcb_envelope': pcb,
        'lcd_envelope': Pos(DISPLAY['x'], DISPLAY['y'], top - LCD_SINK) * Box(
            DISPLAY['module_width'], DISPLAY['module_depth'], LCD_T, align=A),
        # Swept through the whole key travel, so a pressed cap is checked too.
        'keycap_envelopes': Compound([loc * Pos(0, 0, CAP_LIFT - travel) * Box(
            k.w * U - 1.4, 17.65, stack.spec['cap_height'] + travel, align=A) for loc, k in zip(at_key, keys())]),
        'switch_envelopes': Compound([loc * Box(body, body, housing, align=A) for loc in at_key]),
        'pad_envelopes': Compound([Pos(x, y, -PAD_PROUD) * Cylinder(PAD_D / 2 - 0.1, PAD_PROUD + PAD_DEPTH, align=A)
                                   for x, y in mirrored(PADS)]),
        **_usb_envelopes(stack),
    }

def _labelled(shapes):
    """Mirror each solid into the exported frame and name it."""
    exported = {name: to_cad_frame(shape) for name, shape in shapes.items()}
    for name, shape in exported.items():
        shape.label = name
    return exported

def make(variant):
    spec = variants[variant]
    deck = outline()
    stack = Stack(spec, SWITCH[variant], PCB_TOP + spec['plate_to_pcb'], _mouths(deck))
    shell, valley, zone = shell_face(), valley_face(), break_face()
    _check_plan(shell, valley, zone, deck)
    parts = {
        'chassis': _chassis(deck, shell - valley, zone, stack),
        'plate': _plate(deck, stack),
        'top_cover': _top_cover(deck, stack),
        'palm_rest': _palm_rest(shell, zone, stack.plate_top + CAP_LIFT + spec['cap_height'] - CAP_CLEAR),
    }
    whole = list(parts) + ['riser']
    mask = _cut_mask()
    for name in list(parts):
        parts[name + '_left'] = parts[name] & mask
        parts[name + '_right'] = parts[name] - mask
    parts['riser'] = _riser()   # one piece; it bridges the split
    parts = _labelled(parts)
    assembly = Compound(children=[parts[name] for name in whole] + list(_labelled(_envelopes(deck, stack)).values()))
    assembly.label = 'worxboard_ergo_' + variant
    return parts, assembly
