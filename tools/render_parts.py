# SPDX-License-Identifier: GPL-3.0-or-later
"""Render-only geometry: keycaps, switches, USB shells, PCB pads and riser pads.

Nothing here is exported, validated or printed. The shapes are generic look-alikes drawn from
nominal public dimensions, so the product pictures do not show envelope blocks. Dimensions in
mm. Keycaps and switches are built in a key frame: origin on the key axis, x right, y away
from the typist. The other parts are built in the exported CAD frame.
"""
from dataclasses import dataclass
from math import cos, radians

from build123d import Align, Axis, Box, Compound, Cylinder, Plane, Pos, RectangleRounded, Rot, Sphere, extrude, fillet, loft

from cad.model import (PAD_D, PAD_DEPTH, PAD_PROUD, PCB_TOP, REAR_PAD_Y, RISER_MID_R, RISER_PAD_X, RISER_TILT,
                       _desk, _on_arc, cad_xy, mirrored, to_cad_frame)
from layout import keys

A = (Align.CENTER, Align.CENTER, Align.MIN)
EPS = 0.01


@dataclass(frozen=True)
class CapProfile:
    """One uniform 1u keycap. The dish is a sphere cut into the top."""
    base: tuple        # skirt footprint: width, depth
    top: tuple         # top face before the edge radius: width, depth
    height: float
    base_r: float
    top_r: float
    edge_r: float      # roll-over from the sides into the top
    dish: float        # dish depth on the key axis
    dish_r: float      # dish sphere radius
    wall: float


# MX: DSA/XDA-like uniform spherical profile. Choc: MBK-like low profile.
CAPS = {
    'mx': CapProfile((17.6, 17.6), (12.9, 12.9), 7.6, 1.6, 2.6, 0.9, 0.9, 42.0, 1.4),
    'choc': CapProfile((17.5, 16.5), (15.1, 14.1), 4.2, 1.8, 2.4, 0.9, 0.4, 90.0, 1.1),
}


def keycap(profile):
    """Hollow cap, underside at z = 0."""
    crown = Pos(0, 0, profile.height) * RectangleRounded(*profile.top, profile.top_r)
    body = loft([RectangleRounded(*profile.base, profile.base_r), crown])
    body = fillet(body.edges().group_by(Axis.Z)[-1], profile.edge_r)
    body -= Pos(0, 0, profile.height + profile.dish_r - profile.dish) * Sphere(profile.dish_r)
    inset = 2 * profile.wall
    ceiling = profile.height - profile.dish - profile.wall
    cavity = loft([
        Pos(0, 0, -EPS) * RectangleRounded(profile.base[0] - inset, profile.base[1] - inset, profile.base_r),
        Pos(0, 0, ceiling) * RectangleRounded(profile.top[0] - inset, profile.top[1] - inset, profile.top_r),
    ])
    return body - cavity


def _mx_switch(plate_to_pcb):
    base = Pos(0, 0, -plate_to_pcb) * Box(14.0, 14.0, plate_to_pcb, align=A) + Box(15.6, 15.6, 1.0, align=A)
    top = loft([Pos(0, 0, 1.0) * RectangleRounded(15.0, 15.0, 0.8), Pos(0, 0, 6.6) * RectangleRounded(11.2, 10.2, 0.8)])
    stem = Pos(0, 0, 6.6) * Box(7.2, 5.6, 0.4, align=A)
    stem += Pos(0, 0, 7.0) * (Box(4.1, 1.3, 3.2, align=A) + Box(1.1, 4.1, 3.2, align=A))
    return {'switch_base': base, 'switch_top': top, 'switch_stem': stem}


def _choc_switch(plate_to_pcb):
    base = Pos(0, 0, -plate_to_pcb) * Box(13.8, 13.8, plate_to_pcb, align=A) + Box(15.0, 15.0, 0.8, align=A)
    top = loft([Pos(0, 0, 0.8) * RectangleRounded(14.4, 14.4, 1.0), Pos(0, 0, 3.0) * RectangleRounded(13.2, 13.2, 1.0)])
    stem = Pos(0, 0, 3.0) * Box(10.3, 4.5, 2.8, align=A)
    for x in (-2.85, 2.85):
        stem -= Pos(x, 0, 3.4) * Box(1.2, 3.0, 2.8, align=A)
    return {'switch_base': base, 'switch_top': top, 'switch_stem': stem}


SWITCHES = {'mx': _mx_switch, 'choc': _choc_switch}

# Through-hole pads on the PCB top, in the key frame: (x, y, pad diameter, hole diameter).
PADS = {
    'mx': ((0.0, 0.0, 5.0, 4.0), (-3.81, 2.54, 2.6, 1.5), (2.54, 5.08, 2.6, 1.5)),
    'choc': ((0.0, 0.0, 4.4, 3.4), (0.0, 5.9, 2.4, 1.2), (-5.0, 3.8, 2.4, 1.2)),
}
PAD_T = 0.04


def _at_keys(shapes):
    """One copy of each key-frame shape at every key, on the PCB top, in the CAD frame."""
    return Compound([Pos(*cad_xy(k.x, k.y), PCB_TOP) * Rot(0, 0, -k.angle) * shape for k in keys() for shape in shapes])


def pcb_pads(variant):
    """Gold annular pads and the dark holes in them, by finish."""
    pads = _at_keys([Pos(x, y, 0) * Cylinder(d / 2, PAD_T, align=A) for x, y, d, _ in PADS[variant]])
    bores = _at_keys([Pos(x, y, 0) * Cylinder(d / 2, 2 * PAD_T, align=A) for x, y, _, d in PADS[variant]])
    return {'gold': pads, 'hole': bores}


USB_WALL, USB_R, USB_TONGUE = 0.3, 1.5, (6.7, 0.7)


def usb_shells(receptacle_envelopes):
    """A stamped shell and tongue inside each receptacle envelope. The mouth is the rear face."""
    shells = []
    for envelope in receptacle_envelopes.solids():
        box = envelope.bounding_box()
        width, length, height = box.size.X, box.size.Y, box.size.Z
        mouth = Pos(box.center().X, box.max.Y, box.center().Z)
        bore = (width - 2 * USB_WALL, height - 2 * USB_WALL, USB_R - USB_WALL)
        shell = extrude(Plane.XZ * RectangleRounded(width, height, USB_R), amount=length)
        shell -= Pos(0, EPS, 0) * extrude(Plane.XZ * RectangleRounded(*bore), amount=length - USB_WALL)
        tongue = Pos(0, -length / 2 - 0.5, 0) * Box(USB_TONGUE[0], length - 1.0, USB_TONGUE[1])
        shells.append(mouth * (shell + tongue))
    return Compound(shells)


def riser_pads():
    """The two pads under the riser, which the CAD leaves as recesses. They stand on the stance desk."""
    pads = []
    for x, y in mirrored([_on_arc(RISER_MID_R, RISER_PAD_X)]):
        along_desk = (y - REAR_PAD_Y) / cos(radians(RISER_TILT))
        pads.append(_desk() * Pos(x, along_desk, 0) * Cylinder(PAD_D / 2 - 0.1, PAD_PROUD + PAD_DEPTH, align=A))
    return to_cad_frame(Compound(pads))
