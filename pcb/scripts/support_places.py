# SPDX-License-Identifier: GPL-3.0-or-later
"""Seats for everything that is not a key or a mounting hole.

The split Planck deck is much smaller than the old TKL apron. These
coordinates keep the controller on the rear spine and the USB clamps next
to their own receptacles. place.py is the only consumer.
"""
from shapely.geometry import Point, box
from shapely.ops import unary_union
from layout.model import outline, keys, DISPLAY, PORTS

def _deck():
    return outline().buffer(-2.8)

def _blocked():
    d = DISPLAY
    shapes = [k.polygon().buffer(1.8) for k in keys()]
    shapes.append(box(d["x"] - 20, d["y"] - 11, d["x"] + 20, d["y"] + 11))
    for x, y in PORTS.values():
        shapes.append(box(x - 7, y - 3, x + 7, y + 16))
    return unary_union(shapes)

def placements():
    """ref -> (x, y) in layout millimeters. USB jacks included."""
    left, center, right = (PORTS[name] for name in ("left", "center", "right"))
    fixed = {
        "U1": (-34.0, -48.0), "U2": (-34.0, -36.0), "Y1": (-22.0, -50.0),
        "U3": (-22.0, -40.0), "U7": (-22.0, -30.0),
        "SW1": (-40.0, -34.0), "SW2": (-40.0, -24.0),
        "J6": (-40.0, -46.0), "J7": (-40.0, -56.0),
        "J4": (28.0, -18.0), "J5": (38.0, -26.0),
        "J1": (left[0], left[1] + 6), "J2": (center[0], center[1] + 6), "J3": (right[0], right[1] + 6),
        "U4": (-108.0, -30.0), "D1": (-100.0, -30.0),
        "U6": (108.0, -30.0), "D3": (100.0, -30.0),
        "U5": (20.0, -48.0), "D2": (28.0, -48.0),
    }
    deck, blocked = _deck(), _blocked()
    taken = []
    for ref, (x, y) in fixed.items():
        on_deck = deck.contains(Point(x, y))
        in_keepout = blocked.contains(Point(x, y)) and ref not in {"J1", "J2", "J3"}
        if not on_deck or in_keepout:
            raise RuntimeError(f"{ref} at {(x, y)} is off the deck")
        taken.append(Point(x, y).buffer(6.5 if ref[0] in "UJSY" or ref.startswith("SW") else 3.2))
    occupied = unary_union(taken)
    sites = []
    minx, miny, maxx, maxy = outline().bounds
    x = minx
    while x <= maxx:
        y = miny
        while y <= -12:
            p = Point(x, y)
            if deck.contains(p) and not blocked.contains(p) and not occupied.contains(p):
                sites.append((round(x, 2), round(y, 2)))
            y += 4.0
        x += 4.0
    # Prefer the spine, then the rear rim, left to right and rear to front.
    sites.sort(key=lambda p: (0 if abs(p[0]) < 50 else 1, p[1], abs(p[0])))
    return fixed, sites
