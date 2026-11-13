# SPDX-License-Identifier: GPL-3.0-or-later
"""Laser artwork for the chassis underside: the owner's signature and an edition line.

The mark is a surface engraving. It is not part of the solid model and removes no modelled
material. Outputs are filled vector outlines in millimeters, plus a placement drawing of the
underside seen from below.

fontTools is not a locked project dependency, and the PNG and PDF copies need rsvg-convert:
    uv run --with fonttools==4.55.0 python -m tools.signature
"""
import subprocess
from math import hypot, pi, sin
from pathlib import Path

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

from cad import model as case
from layout import holes, U
from layout.model import _world

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / 'assets/fonts'
OUT = ROOT / 'cad/exports/laser'
NAME, NAME_FONT = 'Oleksandr', FONTS / 'MrsSaintDelafield-Regular.ttf'
EDITION, EDITION_FONT = 'Signature Edition', FONTS / 'Michroma-Regular.ttf'
NAME_WIDTH = 46.0       # the name alone, mm
EDITION_EM = 3.6
EDITION_SLANT = 0.22    # x shear per unit of height
EDITION_BASE = -25.0    # edition baseline below the name baseline
# The B, drawn in one stroke from the end of the name: lower bowl, waist loop, long upper
# bowl, and a tail back across the name. Offsets in mm from the exit stroke of the last letter.
FLOURISH = ((0, 0), (5, -1.9), (10, -6.3), (15, -12.5), (21.3, -16.9), (28.8, -15.6), (33.8, -9.4), (33.1, -2.5),
            (28.8, 1.5), (25.6, 2.8), (25.3, 1), (29.4, 0.8), (33.1, 5), (35.6, 13.8), (38.8, 22), (42.8, 29.5),
            (45.6, 36.3), (42.5, 41.9), (35.6, 41.9), (31.3, 36.9), (30, 30), (26.3, 22.5), (20, 15), (12.5, 10),
            (2.5, 7.5), (-15, 6))
SPLINE_STEPS = 40       # chords between two flourish points
PEN_MAX = 0.75          # widest pen, mm
PEN_START = 0.3         # share of the widest pen where the stroke leaves the name
PEN_TIP = 0.12          # width at the end of the tail, mm
TAPER = 0.18            # share of the stroke over which the tail thins to the tip
ARC_SEGMENTS = 8
SIMPLIFY = 0.004
MARGIN = 2.0
# Placement: centred under the middle of the right well, turned with it, read from below.
SIGN_COL, SIGN_ROW = 2.5, 1.5
SIGN_CLEAR = 5.0        # artwork to the nearest hole, pad or magnet pocket
PNG_WIDTH = 4000
INK, GUIDE = '#000000', '#0a84ff'


def _glyph_run(font_path, text):
    font = TTFont(font_path)
    glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
    return glyphs, [glyphs[cmap[ord(char)]] for char in text], font['head'].unitsPerEm


def _draw_text(run, scale, x0, y0, slant, pen):
    """Draw a glyph run into pen with its baseline starting at (x0, y0). scale is mm per font unit."""
    advance = 0
    for glyph in run:
        glyph.draw(TransformPen(pen, (scale, 0, slant * scale, scale, x0 + advance * scale, y0)))
        advance += glyph.width


def _points(recording):
    """Every outline and control point of a recorded drawing."""
    return [point for _, args in recording.value for point in args if point is not None]


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


def _pen_width(share):
    """Pen width along the flourish: light where it leaves the name, full in the bowls, a fine tail."""
    body = PEN_MAX * (PEN_START + (1 - PEN_START) * sin(pi * min(share / (1 - TAPER), 1) * 0.5) ** 0.8)
    if share <= 1 - TAPER:
        return body
    fade = (1 - share) / TAPER
    return PEN_TIP + (PEN_MAX - PEN_TIP) * fade


def _brush(chain):
    """Filled outline of a stroke whose width follows _pen_width."""
    lengths = [hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(chain, chain[1:])]
    total, run, dabs = sum(lengths), 0.0, []
    for (a, b), length in zip(zip(chain, chain[1:]), lengths):
        dabs.append(LineString([a, b]).buffer(_pen_width((run + length / 2) / total) / 2, quad_segs=ARC_SEGMENTS))
        run += length
    return unary_union(dabs).simplify(SIMPLIFY)


def _ring_path(coords):
    return 'M' + 'L'.join(f'{x:.3f} {y:.3f}' for x, y in coords) + 'Z'


def _polygon_path(shape):
    polygons = shape.geoms if shape.geom_type == 'MultiPolygon' else [shape]
    return ''.join(_ring_path(ring.coords) for polygon in polygons for ring in (polygon.exterior, *polygon.interiors))


def artwork():
    """SVG path data in signature coordinates (mm, y up, name baseline at y = 0) and its bounds."""
    glyphs, run, _ = _glyph_run(NAME_FONT, NAME)
    name_scale = NAME_WIDTH / sum(glyph.width for glyph in run)
    name_record, name_pen = DecomposingRecordingPen(glyphs), SVGPathPen(glyphs)
    for pen in (name_record, name_pen):
        _draw_text(run, name_scale, 0, 0, 0, pen)
    name_points = _points(name_record)
    exit_x, exit_y = max(name_points)
    flourish = _brush(_catmull_rom([(exit_x + dx, exit_y + dy) for dx, dy in FLOURISH]))

    glyphs, run, em = _glyph_run(EDITION_FONT, EDITION)
    edition_record, edition_pen = DecomposingRecordingPen(glyphs), SVGPathPen(glyphs)
    _draw_text(run, EDITION_EM / em, 0, EDITION_BASE, EDITION_SLANT, edition_record)
    shift = flourish.bounds[2] - max(x for x, _ in _points(edition_record))
    _draw_text(run, EDITION_EM / em, shift, EDITION_BASE, EDITION_SLANT, edition_pen)

    marks = [*name_points, *[(x + shift, y) for x, y in _points(edition_record)]]
    xs, ys = [x for x, _ in marks], [y for _, y in marks]
    bounds = box(min(xs), min(ys), max(xs), max(ys)).union(flourish).bounds
    return name_pen.getCommands() + _polygon_path(flourish) + edition_pen.getCommands(), bounds


def _svg(width, height, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.3f}mm" height="{height:.3f}mm" '
            f'viewBox="0 0 {width:.3f} {height:.3f}">\n{body}\n</svg>\n')


def _under(x, y):
    """A layout point as seen from below with the rear edge up."""
    return -x, y


def _placement(centre):
    """SVG matrix that carries signature coordinates onto the underside view, and the same map as a function."""
    def place(u, v):
        return _under(*_world('right', SIGN_COL - (u - centre[0]) / U, SIGN_ROW - (v - centre[1]) / U))
    (ox, oy), (ux, uy), (vx, vy) = place(0, 0), place(1, 0), place(0, 1)
    return f'matrix({ux - ox:.6f} {uy - oy:.6f} {vx - ox:.6f} {vy - oy:.6f} {ox:.4f} {oy:.4f})', place


def _check_clear(place, bounds):
    left, bottom, right, top = bounds
    footprint = LineString([place(left, bottom), place(right, bottom), place(right, top), place(left, top)]).convex_hull
    pockets = [*holes(), *case.mirrored(case.PADS), *case.mirrored(case.MAGNETS), *case.mirrored(case.PALM_SCREWS)]
    nearest = min(footprint.distance(Point(_under(x, y))) for x, y in pockets)
    if nearest < SIGN_CLEAR:
        raise RuntimeError(f'signature is {nearest:.1f} mm from a pocket; {SIGN_CLEAR} mm is required')
    return nearest


def _underside(path, bounds):
    shell = case.plan_ring(case.shell_face())
    slot = case.plan_ring(case.valley_face())
    matrix, place = _placement(((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2))
    nearest = _check_clear(place, bounds)
    left, top, right, bottom = shell.bounds[0], shell.bounds[1], shell.bounds[2], shell.bounds[3]
    shift = f'translate({right + MARGIN:.3f} {-top + MARGIN:.3f})'
    rings = ''.join(_ring_path([_under(x, y) for x, y in ring.exterior.coords]) for ring in (shell, slot))
    circles = ''.join(
        f'<circle cx="{-x:.3f}" cy="{y:.3f}" r="{d / 2:.2f}"/>'
        for d, spots in ((case.HEAD_D, [*holes(), *case.mirrored(case.PALM_SCREWS)]),
                         (case.PAD_D, case.mirrored(case.PADS)), (case.MAGNET_D, case.mirrored(case.MAGNETS)))
        for x, y in spots)
    body = (f'<g transform="{shift}">\n'
            f'<g id="reference-do-not-engrave" fill="none" stroke="{GUIDE}" stroke-width="0.2">'
            f'<path d="{rings}"/>{circles}</g>\n'
            f'<path id="engrave" transform="{matrix}" fill="{INK}" d="{path}"/>\n</g>')
    return _svg(right - left + 2 * MARGIN, bottom - top + 2 * MARGIN, body), nearest


def _convert(svg, suffix, *options):
    subprocess.run(['rsvg-convert', *options, '-o', str(svg.with_suffix(suffix)), str(svg)], check=True)


def main():
    path, bounds = artwork()
    left, bottom, right, top = bounds
    OUT.mkdir(parents=True, exist_ok=True)
    alone = OUT / 'signature.svg'
    alone.write_text(_svg(right - left + 2 * MARGIN, top - bottom + 2 * MARGIN,
                          f'<path fill="{INK}" transform="matrix(1 0 0 -1 {MARGIN - left:.3f} {MARGIN + top:.3f})" '
                          f'd="{path}"/>'))
    placed = OUT / 'chassis-underside.svg'
    drawing, nearest = _underside(path, bounds)
    placed.write_text(drawing)
    for svg in (alone, placed):
        _convert(svg, '.png', '-w', str(PNG_WIDTH), '-b', 'white')
        _convert(svg, '.pdf', '-f', 'pdf')
    print(f'signature {right - left:.1f} x {top - bottom:.1f} mm, {nearest:.1f} mm from the nearest pocket')


if __name__ == '__main__':
    main()
