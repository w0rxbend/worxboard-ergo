# SPDX-License-Identifier: GPL-3.0-or-later
"""Case geometry gates. They build cad/model.py, so they do not depend on the committed exports.

Envelope checks only. Nothing here measures a printed or machined part. Points are given in
layout coordinates and mapped into the exported frame by case.cad_xy.
"""
from math import pi
import pytest
from build123d import Pos, Cylinder
from shapely.geometry import Point
from layout import keys, outline, holes, variants
from cad import model as case
from tools.cad import fit_report, FIT_PAIRS

PROBE_R = 0.5        # thin vertical probe, mm
PROBE_REACH = 50.0   # above and below every part
VOLUME_TOL = 1e-6    # mm3, numerical zero for a boolean
MIN_SKIN = 5.0       # shell outside the deck outline
MIN_WALL = 2.5       # valley wall, front fence and slot web
MIN_COVER = 1.0      # material left over a blind pocket
MIN_PALM_DEPTH = 60.0
MIRROR_MISS = 5.0    # a hole further than this from its mirror image tells the two frames apart
SPLIT = ('chassis', 'plate', 'top_cover', 'palm_rest')
PART_NAMES = {*SPLIT, 'riser'} | {f'{name}_{side}' for name in SPLIT for side in ('left', 'right')}

@pytest.fixture(scope='module', params=['mx', 'choc'])
def built(request):
    parts, assembly = case.make(request.param)
    return request.param, parts, assembly

def overlap(a, b):
    return (a & b).volume

def pin(x, y, z, height, d):
    """Vertical cylinder at a layout point."""
    return Pos(*case.cad_xy(x, y), z) * Cylinder(d / 2, height, align=case.A)

def material(part, x, y):
    """Height of material on a vertical line through a layout point: probe overlap volume over probe area."""
    return overlap(part, pin(x, y, -PROBE_REACH, 2 * PROBE_REACH, 2 * PROBE_R)) / (pi * PROBE_R ** 2)

def test_every_part_is_one_valid_solid(built):
    variant, parts, _ = built
    assert set(parts) == PART_NAMES
    for name, part in parts.items():
        assert part.is_valid and len(part.solids()) == 1 and part.volume > 0, (variant, name)

def test_nothing_collides(built):
    variant, parts, assembly = built
    fit = fit_report(parts, assembly)
    assert len(fit) == sum(len(others) for others in FIT_PAIRS.values()) == 22
    assert not any(fit.values()), (variant, fit)
    # Control: the same boolean must see a real collision. Push the palm back through its reveal.
    shoved = Pos(*case.cad_xy(0, -(case.PALM_GAP + 1)), 0) * parts['palm_rest']
    assert overlap(shoved, parts['chassis']) > 1

def test_plan_walls():
    deck = outline()
    recess = deck.buffer(-case.RECESS)
    shell = case.plan_ring(case.shell_face())
    slot, zone = case.plan_ring(case.valley_face()), case.plan_ring(case.break_face())
    assert shell.contains(deck)
    assert shell.exterior.distance(deck.exterior) >= MIN_SKIN
    assert slot.distance(recess) >= MIN_WALL
    assert zone.distance(recess) >= MIN_WALL
    assert slot.distance(zone) >= MIN_WALL

def test_outline_has_no_straight_and_no_corner():
    edges = case.shell_face().outer_wire().edges()
    assert all(edge.geom_type.name == 'CIRCLE' for edge in edges)
    for edge, following in zip(edges, edges[1:] + edges[:1]):
        assert (edge % 1).get_angle(following % 0) < 0.01, 'neighbouring arcs must be tangent'

def test_exported_frame_is_right_handed(built):
    """Layout y runs toward the typist, as KiCad draws the board from the top. The exported solids
    must put each screw hole where that view puts it. The shell is symmetric left to right, so a
    mirrored export would show each hole at -x instead."""
    variant, parts, _ = built
    telling = [(x, y) for x, y in holes() if min(Point(-x, y).distance(Point(h)) for h in holes()) > MIRROR_MISS]
    assert len(telling) >= 4
    for name in ('chassis', 'plate'):
        for x, y in holes():
            assert material(parts[name], x, y) < VOLUME_TOL, (variant, name, 'hole', x, y)
        for x, y in telling:
            assert material(parts[name], -x, y) >= MIN_COVER, (variant, name, 'mirror image of', x, y)
    # The left keys have negative x in the layout. The left half must carry them.
    left_key = next(k for k in keys() if k.side == 'left')
    assert material(parts['chassis_left'], left_key.x, left_key.y) > 0
    assert material(parts['chassis_right'], left_key.x, left_key.y) < VOLUME_TOL

def test_floor_and_pocket_cover(built):
    variant, parts, _ = built
    chassis = parts['chassis']
    for k in keys():
        # Exactly the floor under every switch: no hole below it and nothing standing in the pocket.
        assert material(chassis, k.x, k.y) == pytest.approx(case.FLOOR, abs=0.01), (variant, k.id)
    for x, y in case.mirrored(case.MAGNETS):
        assert material(chassis, x, y) >= MIN_COVER, (variant, 'magnet', x, y)
    pad_reach = case.PAD_D / 2 - PROBE_R
    for x, y in case.mirrored(case.PADS):
        for dx, dy in ((0, 0), (pad_reach, 0), (-pad_reach, 0), (0, pad_reach), (0, -pad_reach)):
            assert material(chassis, x + dx, y + dy) >= MIN_COVER, (variant, 'pad', x, y, dx, dy)

def test_top_cover_hides_the_deck(built):
    variant, parts, _ = built
    cover = parts['top_cover']
    for k in keys():
        assert material(cover, k.x, k.y) < VOLUME_TOL, (variant, 'key window', k.id)
    for x, y in holes():
        # A blind pilot from below: only the skin is left, and it is unbroken.
        assert material(cover, x, y) == pytest.approx(case.COVER_SKIN, abs=0.01), (variant, 'screw', x, y)
    top = case.PCB_TOP + variants[variant]['plate_to_pcb'] + case.RIM_H
    assert cover.bounding_box().max.Z == pytest.approx(parts['chassis'].bounding_box().max.Z) == pytest.approx(top)

def test_usb_plugs_fit(built):
    variant, parts, assembly = built
    plugs = next(child for child in assembly.children if child.label == 'usb_plug_envelopes')
    # The gate reads zero for a seated plug. Control: a plug half a tunnel off its axis must hit the wall.
    assert overlap(parts['chassis'], plugs) < VOLUME_TOL, variant
    assert overlap(parts['chassis'], Pos(case.RELIEF_W / 2, 0, 0) * plugs) > 1, variant

def test_screw_holes_stay_open(built):
    variant, parts, _ = built
    chassis, palm = parts['chassis'], parts['palm_rest']
    shaft = case.SCREW_D - 0.1
    for x, y in holes():
        assert overlap(chassis, pin(x, y, -1, case.PCB_TOP, shaft)) < VOLUME_TOL, (variant, 'cover screw', x, y)
    for x, y in case.mirrored(case.PALM_SCREWS):
        assert overlap(chassis, pin(x, y, -1, case.SHELF + 2, shaft)) < VOLUME_TOL, (variant, x, y)
        assert overlap(palm, pin(x, y, case.SHELF, case.PALM_PILOT_DEPTH - 0.1, case.PILOT_D - 0.1)) < VOLUME_TOL
        assert material(palm, x, y) >= MIN_COVER, (variant, 'blind pilot cover', x, y)

def test_palm_rest_shape(built):
    variant, parts, _ = built
    palm = parts['palm_rest']
    spec = variants[variant]
    cap_top = case.PCB_TOP + spec['plate_to_pcb'] + case.CAP_LIFT + spec['cap_height']
    assert palm.bounding_box().max.Z == pytest.approx(cap_top - case.CAP_CLEAR, abs=0.01)
    # It bears on the shelf: faces touch, no gap and no shared volume.
    assert palm.bounding_box().min.Z == pytest.approx(case.SHELF, abs=1e-6)
    rear = case._gull(0)[1] + case.PALM_GAP + 1
    assert material(palm, 0, rear) > 0 and material(palm, 0, rear + MIN_PALM_DEPTH) > 0, variant
    fall = material(palm, 0, rear) - material(palm, 0, rear + MIN_PALM_DEPTH)
    assert 0 < fall <= case.LIP_DROP, (variant, fall)

def test_riser_stance(built):
    variant, parts, _ = built
    chassis, riser = parts['chassis'], parts['riser']
    desk = case.to_cad_frame(case.below_desk(0))
    assert overlap(chassis, desk) < VOLUME_TOL and overlap(riser, desk) < VOLUME_TOL, variant
    # The rear undercut holds the chassis STANCE_CLEAR off the desk. A desk raised past that must touch it.
    assert overlap(chassis, case.to_cad_frame(case.below_desk(case.STANCE_CLEAR - 0.05))) < VOLUME_TOL, variant
    assert overlap(chassis, case.to_cad_frame(case.below_desk(case.STANCE_CLEAR + 0.3))) > 1, variant
    # The riser sole stands PAD_PROUD off the desk, the height of its own pads.
    assert overlap(riser, case.to_cad_frame(case.below_desk(case.PAD_PROUD - 0.05))) < VOLUME_TOL, variant
    assert overlap(riser, case.to_cad_frame(case.below_desk(case.PAD_PROUD + 0.3))) > 1, variant
