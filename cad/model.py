# SPDX-License-Identifier: GPL-3.0-or-later
"""Split Planck case. Dimensions in mm, assembly z up, PCB plane horizontal.

Launch-style stack: pocketed chassis, switch plate, removable display bezel.
Two plank halves share a rear spine. A short palm rest sits on the front shelf
and does not fill the valley. Rear feet are taller than the front feet, so the
deck tilts back when the soles are on a desk. The PCB stays flat. Split meshes
share a rear registration tab; that joint is not a printed fit approval.
"""
from build123d import (Polyline, Face, extrude, Pos, Rot, Box, Cylinder,
                       Align, Compound)
from shapely.geometry import box as sbox
from shapely.ops import unary_union
from layout import keys, outline, palm_outline, holes, variants, DISPLAY, PORTS
from layout.model import palm_screws

A = (Align.CENTER, Align.CENTER, Align.MIN)
FLOOR = 2.4
PCB_T = 1.6
PCB_TOP = 8.0
WALL = 3.2
SHELF = 4.2
FRONT_FOOT = 3.0
REAR_FOOT = 14.0

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

def _cut_mask():
    """Left keeps x<=0 plus a tab that registers into the right rear apron."""
    half = Pos(-800, -500, -40) * Box(800, 1200, 200, align=(Align.MIN, Align.MIN, Align.MIN))
    tab = Pos(0, -36, -40) * Box(18, 18, 200, align=(Align.MIN, Align.MIN, Align.MIN))
    return half + tab

def make(variant):
    v = variants[variant]
    deck = outline()
    palm = palm_outline()
    plate_top = PCB_TOP + v['plate_to_pcb']
    plate_bot = plate_top - v['plate']
    outside = palm.difference(deck.buffer(-0.6))
    cushion_poly = palm.difference(deck.buffer(0.4))

    chassis = prism(deck, 0, plate_bot) - prism(deck.buffer(-WALL), FLOOR, plate_bot)
    chassis += prism(outside, 0, SHELF)
    for x, y in holes():
        chassis += Pos(x, y, FLOOR) * Cylinder(3.6, max(PCB_TOP - PCB_T - FLOOR, 0.8), align=A)
        chassis = drill(chassis, x, y, -0.2, plate_bot + 2, 2.1)
    for x, y in PORTS.values():
        # Mouth opens through the rear wall. The plug envelope continues outside the deck.
        chassis -= Pos(x, y, PCB_TOP - 1.6) * Box(12.5, 18, 6.2, align=A)
    # Measured on this deck so each sole is on a plank and clear of the USB mouths.
    # Rear soles are taller, so the deck tips back about 7 degrees. The valley has
    # no center-front foot.
    for x, y, h in (
        (-67.0, 63.0, FRONT_FOOT), (65.0, 63.0, FRONT_FOOT),
        (-96.0, -22.0, REAR_FOOT), (96.0, -22.0, REAR_FOOT),
    ):
        chassis += Pos(x, y, 0) * Box(22, 11, h, align=(Align.CENTER, Align.CENTER, Align.MAX))
    for x, y in palm_screws():
        chassis = drill(chassis, x, y, -0.2, SHELF + 1.2, 2.2)

    pcb = prism(deck.buffer(-WALL - 0.4), PCB_TOP - PCB_T, PCB_T)
    plate = prism(deck.buffer(-0.7), plate_bot, v['plate'])
    for k in keys():
        loc = Pos(k.x, k.y, plate_bot - 0.1) * Rot(0, 0, k.angle)
        plate -= loc * Box(v['cut'], v['cut'], v['plate'] + 0.2, align=A)
        # South window for a per-key LED. The web between switches stays about 1.8 mm.
        plate -= loc * Pos(0, 9.35, 0) * Box(2.6, 1.1, v['plate'] + 0.2, align=A)
        if k.w >= 2:
            for sx in (-11.938, 11.938):
                plate -= loc * Pos(sx, 0, 0) * Box(6.75, 14.2, v['plate'] + 0.2, align=A)
    for x, y in holes():
        plate = drill(plate, x, y, plate_bot - 0.1, v['plate'] + 0.2, 2.7)
        pcb = drill(pcb, x, y, PCB_TOP - PCB_T - 0.1, PCB_T + 0.2, 2.7)
    dx, dy = DISPLAY['x'], DISPLAY['y']
    plate -= Pos(dx, dy, plate_bot - 0.1) * Box(38, 20, v['plate'] + 0.2, align=A)

    bezel = Pos(dx, dy, plate_top) * Box(46, 28, 2.2, align=A)
    bezel -= Pos(dx, dy, plate_top - 0.1) * Box(DISPLAY['window_width'], DISPLAY['window_depth'], 2.8, align=A)
    bezel += Pos(dx, dy, plate_bot) * Box(37.2, 19.2, v['plate'] + 0.35, align=A)
    bezel -= Pos(dx, dy, plate_bot - 0.1) * Box(DISPLAY['window_width'], DISPLAY['window_depth'], v['plate'] + 0.6, align=A)

    palm_part = prism(cushion_poly, SHELF + 0.35, 8.0)
    for x, y in palm_screws():
        palm_part = drill(palm_part, x, y, SHELF, 14, 2.8)

    mask = _cut_mask()
    parts = {
        'chassis': chassis,
        'plate': plate,
        'display_bezel': bezel,
        'palm_rest': palm_part,
    }
    for name in ('chassis', 'plate', 'palm_rest'):
        parts[name + '_left'] = parts[name] & mask
        parts[name + '_right'] = parts[name] - mask
    for name, part in parts.items():
        part.label = name
    pcb.label = 'pcb_envelope'
    display = Pos(dx, dy, plate_top - 1) * Box(DISPLAY['module_width'], DISPLAY['module_depth'], 1.2, align=A)
    display.label = 'lcd_envelope'
    caps = []
    for k in keys():
        caps.append(Pos(k.x, k.y, plate_top + 3) * Rot(0, 0, k.angle)
                    * Box(k.w * 19.05 - 1.4, 17.65, v['cap_height'], align=A))
    cap_compound = Compound(caps)
    cap_compound.label = 'keycap_envelopes'
    assembly = Compound(children=[parts[n] for n in ('chassis', 'plate', 'display_bezel', 'palm_rest')]
                        + [pcb, display, cap_compound])
    assembly.label = 'worxboard_ergo_' + variant
    return parts, assembly
