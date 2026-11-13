# SPDX-License-Identifier: GPL-3.0-or-later
"""Split Planck, pulled apart like a Microsoft ergonomic board.

Each half is a straight 4×6 ortholinear block, the same grid as one side of
a Planck. The halves are splayed so the front opens toward the typist, with
a clear valley between them. A low rear bay joins the halves for one PCB,
the center USB-C mouth, and the memory LCD. A short palm rest sits in front
of both wells and dips at the center. There is no number pad and no function
row; those keys live on the Lower layer. Coordinates are millimeters: x
right, y toward the typist.
"""
from dataclasses import dataclass, asdict
from functools import lru_cache
from math import cos, sin, radians
from shapely.geometry import Polygon, Point, box, LineString
from shapely.affinity import rotate, translate
from shapely.ops import unary_union

U = 19.05
ANGLE = 10.0
GAP = 24.0
RIM = 9.0
PCB_EDGE_INSET = 3.4    # board edge inside the deck outline: the chassis wall plus 0.2
PCB_HOLE_D = 2.7        # M2.5 clearance
HOLE_WEB_MIN = 1.0      # a hole with less board than this outside it becomes an open edge slot
PORT_SPREAD = 64.0      # side mouths sit on the bay's straight rear edge. A plank rim leaves 5.6 mm between
                        # the board edge and the corner key, and the receptacle with its pads needs 8.5
USB_RECEPTACLE_L = 7.3     # HRO TYPE-C-31-M-12 shell length; its mouth sits flush with the board edge
variants = {
 "mx": {"name": "Cherry MX / Kailh MX hot-swap", "cut": 14.0, "plate": 1.5,
        "plate_to_pcb": 5.0, "pcb_top": 8.0, "cap_height": 11.5},
 "choc": {"name": "Kailh Choc v1 PG1350 hot-swap", "cut": 13.8, "plate": 1.2,
          "plate_to_pcb": 2.2, "pcb_top": 8.0, "cap_height": 5.5},
}
@dataclass(frozen=True)
class Key:
 id: str
 label: str
 code: str
 x: float
 y: float
 w: float
 angle: float
 row: int
 col: int
 side: str
 def polygon(self, inset=0.7):
  p = box(-self.w * U / 2 + inset, -U / 2 + inset, self.w * U / 2 - inset, U / 2 - inset)
  return translate(rotate(p, self.angle, origin=(0, 0)), self.x, self.y)

# Column 0 is the inner column. Every key is 1u, Planck-style.
# Left, rear to front: Tab Q W E R T / Esc A S D F G / Shift Z X C V B / Ctrl Win Alt Lower Space Space
# Right, rear to front: Y U I O P Bksp / H J K L ; ' / N M , . / Shift / Raise Left Down Up Right Enter
_LEFT = [
 [("T", "T", 0), ("R", "R", 1), ("E", "E", 2), ("W", "W", 3), ("Q", "Q", 4), ("Tab", "TAB", 5)],
 [("G", "G", 0), ("F", "F", 1), ("D", "D", 2), ("S", "S", 3), ("A", "A", 4), ("Esc", "ESC", 5)],
 [("B", "B", 0), ("V", "V", 1), ("C", "C", 2), ("X", "X", 3), ("Z", "Z", 4), ("Shift", "LSHFT", 5)],
 [("Space", "SPACE", 0), ("Space", "SPACE", 1), ("Lower", "FN", 2), ("Alt", "LALT", 3), ("Win", "LGUI", 4), ("Ctrl", "LCTRL", 5)],
]
_RIGHT = [
 [("Y", "Y", 0), ("U", "U", 1), ("I", "I", 2), ("O", "O", 3), ("P", "P", 4), ("Bksp", "BSPC", 5)],
 [("H", "H", 0), ("J", "J", 1), ("K", "K", 2), ("L", "L", 3), (";", "SEMI", 4), ("'", "SQT", 5)],
 [("N", "N", 0), ("M", "M", 1), (",", "COMMA", 2), (".", "DOT", 3), ("/", "FSLH", 4), ("Shift", "RSHFT", 5)],
 [("Raise", "RAISE", 0), ("Left", "LEFT", 1), ("Down", "DOWN", 2), ("Up", "UP", 3), ("Right", "RIGHT", 4), ("Enter", "RET", 5)],
]

def _world(side, col, row):
 """Column 0 sits on the inner edge of the well. Rotation opens the front."""
 lx = (col + 0.5) * U
 ly = row * U
 pivot = -GAP / 2.0 if side == "left" else GAP / 2.0
 x = pivot - lx if side == "left" else pivot + lx
 a = radians(ANGLE if side == "left" else -ANGLE)
 dx, dy = x - pivot, ly
 return pivot + dx * cos(a) - dy * sin(a), dx * sin(a) + dy * cos(a)

@lru_cache
def keys():
 result = []
 plan = [("left", row, items) for row, items in enumerate(_LEFT)]
 plan += [("right", row, items) for row, items in enumerate(_RIGHT)]
 for side, row, items in plan:
  for label, code, col in items:
   x, y = _world(side, col, row)
   angle = ANGLE if side == "left" else -ANGLE
   result.append(Key(
    f"K{len(result) + 1:03}", label, code, round(x, 4), round(y, 4), 1.0, angle,
    row, col if side == "left" else col + 6, side))
 return tuple(result)

def _largest(shape):
 if shape.geom_type == "Polygon":
  return shape
 if shape.geom_type == "MultiPolygon":
  shape = max(shape.geoms, key=lambda g: g.area)
 if shape.geom_type != "Polygon":
  raise RuntimeError(f"outline is {shape.geom_type}")
 return shape

def _smooth(shape, tol=0.2):
 """Drop the tiny buffer facets that leave an open seam in the case mesh."""
 shape = _largest(shape.buffer(0))
 shape = shape.simplify(tol, preserve_topology=True)
 def ring(coords):
  pts = []
  for x, y in coords:
   if not pts or (x - pts[-1][0]) ** 2 + (y - pts[-1][1]) ** 2 > 0.08 ** 2:
    pts.append((round(float(x), 3), round(float(y), 3)))
  if len(pts) > 2 and (pts[0][0] - pts[-1][0]) ** 2 + (pts[0][1] - pts[-1][1]) ** 2 < 0.08 ** 2:
   pts.pop()
  if len(pts) < 3:
   raise RuntimeError("degenerate ring")
  return pts
 holes = [ring(r.coords) for r in shape.interiors]
 return Polygon(ring(shape.exterior.coords), [h for h in holes if len(h) >= 3])

@lru_cache
def outline():
 """Two rounded Planck slabs and a low rear bay. The palm rest is not part of the PCB.

 Each slab is the 4×6 block plus a rim. The bay is only deep enough for the
 center USB-C mouth, the memory LCD, and the controller. It blends into both
 slabs so the valley between the wells stays open toward the typist.
 """
 planks = []
 for side in ("left", "right"):
  block = unary_union([k.polygon(0) for k in keys() if k.side == side])
  planks.append(block.buffer(RIM, join_style=1, quad_segs=3))
 bay = box(-78, -56, 78, -6).buffer(7, join_style=1, quad_segs=3)
 body = unary_union(planks + [bay])
 deck = body.buffer(1.6, join_style=1, quad_segs=2).buffer(-1.6, join_style=1, quad_segs=2)
 return _smooth(deck)

def _display_dict():
 """Seat the LCD on the rear spine, clear of every key."""
 deck = outline()
 best = None
 y = deck.bounds[1] + 11
 while y < 5:
  rect = box(-18, y - 9, 18, y + 9)
  if deck.contains(rect):
   gap = min(rect.distance(k.polygon()) for k in keys())
   if gap > 2.4 and (best is None or y > best[1]):
    best = (gap, y)
  y += 1.0
 if best is None:
  raise RuntimeError("no display seat on the rear spine")
 return {"x": 0.0, "y": round(best[1], 2), "width": 36.0, "depth": 14.0,
         "module_width": 36.0, "module_depth": 18.0, "window_width": 32.0, "window_depth": 12.0}

DISPLAY = _display_dict()

def _rear_y(poly, x):
 line = LineString([(x, poly.bounds[1] - 20), (x, poly.bounds[3] + 20)])
 hit = poly.intersection(line)
 if hit.is_empty:
  raise RuntimeError(f"no rear edge at x={x}")
 return hit.bounds[1]

@lru_cache
def ports():
 """Three USB-C mouths on the bay's rear edge, opening away from the typist."""
 deck = outline()
 found = {}
 for name, x in (("left", -PORT_SPREAD), ("center", 0.0), ("right", PORT_SPREAD)):
  y = _rear_y(deck, x) + 2.2
  found[name] = (round(x, 2), round(y, 2))
 return found

def _safe_region():
 deck = outline()
 d = DISPLAY
 blocked = [k.polygon().buffer(4.3) for k in keys()]
 blocked.append(box(d["x"] - d["module_width"] / 2 - 1.5, d["y"] - d["module_depth"] / 2 - 1.5,
                     d["x"] + d["module_width"] / 2 + 1.5, d["y"] + d["module_depth"] / 2 + 1.5))
 for x, y in ports().values():
  blocked.append(box(x - 6.5, y - 2.5, x + 6.5, y + 14))
 return deck.buffer(-4.6).difference(unary_union(blocked))

@lru_cache
def holes():
 """M2.5 bosses in the plank corners and on the spine. Clear of keys, LCD, and USB."""
 region = _safe_region()
 minx, miny, maxx, maxy = outline().bounds
 cands = []
 x = minx
 while x <= maxx:
  y = miny
  while y <= maxy:
   if region.contains(Point(x, y)):
    cands.append((x, y))
   y += 2.5
  x += 2.5
 if len(cands) < 8:
  raise RuntimeError(f"only {len(cands)} screw sites")

 def take(pred):
  pool = [c for c in cands if pred(c) and all((c[0] - p[0]) ** 2 + (c[1] - p[1]) ** 2 > 16 ** 2 for p in picked)]
  if not pool:
   return None
  return pool[0]

 picked = []
 seeds = [
  lambda c: c[0] < minx + 28 and c[1] < miny + 28,
  lambda c: c[0] > maxx - 28 and c[1] < miny + 28,
  lambda c: c[0] < minx + 28 and c[1] > maxy - 28,
  lambda c: c[0] > maxx - 28 and c[1] > maxy - 28,
  lambda c: c[0] < -20 and c[1] < 0,
  lambda c: c[0] > 20 and c[1] < 0,
  lambda c: abs(c[0]) < 30 and c[1] < DISPLAY["y"],
  lambda c: abs(c[0]) < 40 and c[1] > 20,
 ]
 for pred in seeds:
  hit = take(pred)
  if hit:
   picked.append(hit)
 # Fill to eight with the points farthest from those already chosen.
 while len(picked) < 8:
  nxt = max(cands, key=lambda c: min((c[0] - p[0]) ** 2 + (c[1] - p[1]) ** 2 for p in picked))
  if min((nxt[0] - p[0]) ** 2 + (nxt[1] - p[1]) ** 2 for p in picked) < 15 ** 2:
   break
  picked.append(nxt)
 if len(picked) < 6:
  raise RuntimeError(f"only {len(picked)} screws")
 return tuple(sorted((round(x, 2), round(y, 2)) for x, y in picked))

@lru_cache
def palm_outline():
 """One short rest across both planks, with a center dip so the valley still reads."""
 deck = outline()
 keys_block = unary_union([k.polygon().buffer(1.0) for k in keys()])
 lobes = []
 for side in ("left", "right"):
  band = unary_union([k.polygon(0) for k in keys() if k.side == side and k.row == 3])
  minx, _, maxx, maxy = band.bounds
  lobes.append(box(minx - 8, maxy - 8, maxx + 10, maxy + 13))
 link = box(-32, deck.bounds[3] - 10, 32, deck.bounds[3] + 4)
 shape = unary_union(lobes + [link]).difference(keys_block)
 shape = shape.buffer(3.2, join_style=1, quad_segs=2).buffer(-2.8, join_style=1, quad_segs=2)
 shape = shape.difference(keys_block)
 return _smooth(shape, 0.22)

@lru_cache
def palm_screws():
 """Two screws in the palm overhang, one on each side. They do not go through the PCB."""
 deck = outline()
 shelf = palm_outline().difference(deck.buffer(0.3))
 found = []
 minx, miny, maxx, maxy = shelf.bounds
 for sign in (-1, 1):
  best = None
  target = sign * max(40.0, (maxx - minx) * 0.28)
  x = minx
  while x <= maxx:
   y = miny
   while y <= maxy:
    if sign * x > 12 and shelf.contains(Point(x, y)) and shelf.boundary.distance(Point(x, y)) > 2.4:
     score = abs(x - target) + abs(y - (miny + maxy) / 2) * 0.4
     if best is None or score < best[0]:
      best = (score, (round(x, 2), round(y, 2)))
    y += 1.5
   x += 1.5
  if best is None:
   raise RuntimeError(f"no palm screw on {'left' if sign < 0 else 'right'}")
  found.append(best[1])
 return tuple(found)

# Imported name used by the PCB placer and the case. Computed once from the deck.
PORTS = ports()

@lru_cache
def mouths():
 """Where each receptacle mouth sits: the inset board's rear edge at the port x."""
 board = outline().buffer(-PCB_EDGE_INSET)
 return {name: (x, round(_rear_y(board, x), 3)) for name, (x, _) in PORTS.items()}

def _edge_slot(board, hole):
 """Capsule from a hole out through the nearest board edge."""
 centre = Point(hole)
 edge = board.exterior.interpolate(board.exterior.project(centre))
 reach = PCB_HOLE_D / max(centre.distance(edge), 1e-6)
 beyond = (edge.x + (edge.x - hole[0]) * reach, edge.y + (edge.y - hole[1]) * reach)
 return LineString([hole, beyond]).buffer(PCB_HOLE_D / 2, quad_segs=8)

@lru_cache
def edge_slots():
 """Mounting holes too close to the wall to be enclosed. The rim leaves no room to move them in."""
 board = outline().buffer(-PCB_EDGE_INSET)
 return tuple(h for h in holes() if board.exterior.distance(Point(h)) - PCB_HOLE_D / 2 < HOLE_WEB_MIN)

@lru_cache
def board_outline():
 """PCB edge: the deck inset, with an open slot at each edge hole."""
 board = outline().buffer(-PCB_EDGE_INSET)
 return _largest(board.difference(unary_union([_edge_slot(board, h) for h in edge_slots()])))

def serializable():
 return {"units": "mm", "angle_deg": ANGLE, "gap_mm": GAP, "matrix": {"rows": 6, "cols": 15},
  "keys": [asdict(k) for k in keys()],
  "outline": [list(p) for p in outline().exterior.coords],
  "palm": [list(p) for p in palm_outline().exterior.coords],
  "holes": holes(), "display": DISPLAY, "ports": PORTS, "variants": variants,
  "palm_screws": palm_screws()}
