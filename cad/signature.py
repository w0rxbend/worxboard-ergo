# SPDX-License-Identifier: GPL-3.0-or-later
"""Owner's signature for the chassis underside: the name, a one-stroke flourish for the B,
and an edition line. Dimensions in mm.

Every stroke is a tool centre line with a constant groove width, so a cutter of that
diameter follows it in one pass. Letter strokes come from the Hershey single-line fonts.
"""
from HersheyFonts import HersheyFonts
from shapely.geometry import LineString
from shapely.ops import unary_union

NAME = 'Oleksandr'
EDITION = 'Signature Edition'
NAME_FONT, EDITION_FONT = 'scripts', 'futural'
NAME_H = 10.0
EDITION_H = 4.5
EDITION_SLANT = 0.25    # x shear per unit of height
EDITION_DROP = 24.0     # edition baseline below the name baseline
NAME_GROOVE = 0.8       # cutter diameter for the name and the flourish
EDITION_GROOVE = 0.5
# The B, drawn in one stroke from the end of the name: lower bowl, waist loop, long upper
# bowl, and a tail back across the name. Offsets from the last point of the name.
FLOURISH = ((0, 0), (4, -1.5), (8, -5), (12, -10), (17, -13.5), (23, -12.5), (27, -7.5), (26.5, -2), (23, 1.2),
            (20.5, 2.2), (20.2, 0.8), (23.5, 0.6), (26.5, 4), (28.5, 11), (31.5, 18), (35.5, 23.5), (37, 29),
            (34, 33.5), (28.5, 33.5), (25, 29.5), (24, 24), (21, 18), (16, 12), (10, 8), (2, 6), (-12, 4.8))
SPLINE_STEPS = 12       # chords between two flourish points
ARC_SEGMENTS = 6        # per quarter turn at a groove end
SIMPLIFY = 0.02


def _text(font_name, text, height):
    font = HersheyFonts()
    font.load_default_font(font_name)
    font.normalize_rendering(height)
    return [list(stroke) for stroke in font.strokes_for_text(text)]


def _catmull_rom(points):
    """Smooth chord chain through every point."""
    padded = [points[0], *points, points[-1]]
    chain = []
    for i in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[i - 1:i + 3]
        for step in range(SPLINE_STEPS):
            t = step / SPLINE_STEPS
            chain.append(tuple(
                0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t ** 2 + (3 * b - a - 3 * c + d) * t ** 3)
                for a, b, c, d in zip(p0, p1, p2, p3)))
    chain.append(points[-1])
    return chain


def centre_lines():
    """(groove width, polyline) pairs in signature coordinates: x right, y up, centred on the origin."""
    name = _text(NAME_FONT, NAME, NAME_H)
    right = max(x for stroke in name for x, _ in stroke)
    end = min((p for stroke in name for p in stroke), key=lambda p: (right - p[0]) ** 2 + p[1] ** 2)
    flourish = _catmull_rom([(end[0] + dx, end[1] + dy) for dx, dy in FLOURISH])
    edition = [[(x + EDITION_SLANT * y, y - EDITION_DROP) for x, y in stroke]
               for stroke in _text(EDITION_FONT, EDITION, EDITION_H)]
    shift = max(x for x, _ in flourish) - max(x for stroke in edition for x, _ in stroke)
    edition = [[(x + shift, y) for x, y in stroke] for stroke in edition]
    lines = [(NAME_GROOVE, stroke) for stroke in (*name, flourish)] + [(EDITION_GROOVE, stroke) for stroke in edition]
    xs = [x for _, stroke in lines for x, _ in stroke]
    ys = [y for _, stroke in lines for _, y in stroke]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    return [(width, [(x - cx, y - cy) for x, y in stroke]) for width, stroke in lines]


def grooves(place):
    """Groove plan as shapely polygons. place maps a signature point to a plan point."""
    swept = [LineString([place(x, y) for x, y in stroke]).buffer(width / 2, quad_segs=ARC_SEGMENTS)
             for width, stroke in centre_lines() if len(stroke) > 1]
    merged = unary_union(swept).simplify(SIMPLIFY)
    return list(merged.geoms) if merged.geom_type == 'MultiPolygon' else [merged]
