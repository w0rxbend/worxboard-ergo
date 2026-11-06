# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass, asdict
from functools import lru_cache
from math import cos, sin, radians
from shapely.geometry import Polygon, box
from shapely.affinity import rotate, translate
from shapely.ops import unary_union
U = 19.05
ANGLE = 10.0
GAP = 48.0
DISPLAY = {"x": 0.0, "y": 43.0, "width": 36.0, "depth": 14.0,
           "module_width": 36.0, "module_depth": 18.0, "window_width": 32.0, "window_depth": 12.0}
# Three USB-C mouths on the rear edge, pointing away from the typist.
PORTS = {"left": (-135.0, -47.0), "center": (0.0, -47.0), "right": (135.0, -47.0)}
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
  p=box(-self.w*U/2+inset,-U/2+inset,self.w*U/2-inset,U/2-inset)
  return translate(rotate(p,self.angle,origin=(0,0)),self.x,self.y)
# left groups are specified outer -> inner; right groups inner -> outer.
ROWS = [
 ([('Esc','ESC',1),('F1','F1',1),('F2','F2',1),('F3','F3',1),('F4','F4',1),('F5','F5',1),('F6','F6',1)],
  [('F7','F7',1),('F8','F8',1),('F9','F9',1),('F10','F10',1),('F11','F11',1),('F12','F12',1)]),
 ([('`','GRAVE',1),('1','N1',1),('2','N2',1),('3','N3',1),('4','N4',1),('5','N5',1),('6','N6',1)],
  [('7','N7',1),('8','N8',1),('9','N9',1),('0','N0',1),('-','MINUS',1),('=','EQUAL',1),('Bksp','BSPC',2)]),
 ([('Tab','TAB',1.5),('Q','Q',1),('W','W',1),('E','E',1),('R','R',1),('T','T',1)],
  [('Y','Y',1),('U','U',1),('I','I',1),('O','O',1),('P','P',1),('[','LBKT',1),(']','RBKT',1),('\\','BSLH',1.5)]),
 ([('Caps','CAPS',1.75),('A','A',1),('S','S',1),('D','D',1),('F','F',1),('G','G',1)],
  [('H','H',1),('J','J',1),('K','K',1),('L','L',1),(';','SEMI',1),("'",'SQT',1),('Enter','RET',2.25)]),
 ([('Shift','LSHFT',2.25),('Z','Z',1),('X','X',1),('C','C',1),('V','V',1),('B','B',1)],
  [('N','N',1),('M','M',1),(',','COMMA',1),('.','DOT',1),('/','FSLH',1),('Shift','RSHFT',2.75)]),
 ([('Ctrl','LCTRL',1.25),('Win','LGUI',1.25),('Alt','LALT',1.25),('Space','SPACE',2)],
  [('Space','SPACE',2),('Alt','RALT',1.25),('Fn','FN',1.25),('Ctrl','RCTRL',1.25)]),
]
@lru_cache
def keys():
 result=[]
 for row,(left,right) in enumerate(ROWS):
  for side,items in [('left',left),('right',right)]:
   total=sum(v[2] for v in items)*U
   cursor=-GAP/2-total if side=='left' else GAP/2
   angle=ANGLE if side=='left' else -ANGLE
   # rotate about each inner top edge; the halves open toward the rear.
   pivot=-GAP/2 if side=='left' else GAP/2
   for col,(label,code,w) in enumerate(items):
    x=cursor+w*U/2; y=row*U
    a=radians(angle); dx=x-pivot
    xx=pivot+dx*cos(a)-y*sin(a); yy=dx*sin(a)+y*cos(a)
    result.append(Key(f'K{len(result)+1:03}',label,code,round(xx,4),round(yy,4),w,angle,row,col+(0 if side=='left' else 8),side))
    cursor+=w*U
 # The compact TKL navigation block is separate from the angled alpha section.
 for row,labels in [(0,[('PrtSc','PSCRN'),('ScrLk','SLCK'),('Pause','PAUSE_BREAK')]),
                    (1,[('Ins','INS'),('Home','HOME'),('PgUp','PG_UP')]),
                    (2,[('Del','DEL'),('End','END'),('PgDn','PG_DN')]),
                    (4,[('Up','UP')]),
                    (5,[('Left','LEFT'),('Down','DOWN'),('Right','RIGHT')])]:
  for j,(label,code) in enumerate(labels):
   col=(1 if row==4 else j)
   result.append(Key(f'K{len(result)+1:03}',label,code,214+col*U,row*U,1,0,row,16+col,'nav'))
 return tuple(result)
@lru_cache
def outline():
 # Rounded single-piece enclosure; union bridges the central display and electronics bay.
 groups=[k.polygon(0).buffer(7,join_style=1) for k in keys()]
 groups += [box(-185,-45,272,140)]
 return unary_union(groups).buffer(2).buffer(-2)
@lru_cache
def holes():
 # M2.5 case screws outside keycap sweep; values measured by layout validator.
 return ((-176,-34),(-70,-34),(70,-34),(260,-34),(-176,130),(-70,130),(70,130),(260,130),(0,130),(35,-34))
def serializable():
 return {'units':'mm','angle_deg':ANGLE,'gap_mm':GAP,'matrix':{'rows':6,'cols':15},
  'keys':[asdict(k) for k in keys()], 'outline':[list(p) for p in outline().exterior.coords],
  'holes':holes(),'display':DISPLAY,'ports':PORTS,'variants':variants}
