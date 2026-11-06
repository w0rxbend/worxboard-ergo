# SPDX-License-Identifier: GPL-3.0-or-later
"""Parametric engineering prototype. Dimensions in mm, assembly z up.

Model is source of truth; exported FCStd contains named B-rep parts, not a feature history.
"""
from build123d import (Polyline, Face, extrude, Pos, Rot, Box, Cylinder, Align, Compound,
                      export_step, export_stl, Mesher)
from shapely.geometry import box
from layout import keys, outline, holes, variants, DISPLAY, PORTS
A=(Align.CENTER,Align.CENTER,Align.MIN)
FLOOR=2.4
PCB_T=1.6
PCB_TOP=8.0
WALL=3.0
CLEARANCE=.4

def prism(poly,z,height):
 outer=Face(Polyline(*list(poly.exterior.coords),close=True))
 p=Pos(0,0,z)*extrude(outer,amount=height,dir=(0,0,1))
 for ring in poly.interiors:
  p-=Pos(0,0,z-.1)*extrude(Face(Polyline(*list(ring.coords),close=True)),amount=height+.2,dir=(0,0,1))
 return p

def drill(shape,x,y,z,h,d):
 return shape-Pos(x,y,z)*Cylinder(d/2,h,align=A)

def make(variant):
 v=variants[variant];op=outline();inside=op.buffer(-WALL)
 plate_top=PCB_TOP+v['plate_to_pcb'];plate_bot=plate_top-v['plate']
 # Tray floor, wall, and M2.5 clamp pillars; PCB has matching 2.7 mm bores.
 tray=prism(op,0,plate_bot)-prism(inside,FLOOR,plate_bot)
 for x,y in holes():
  tray+=Pos(x,y,FLOOR)*Cylinder(3.5,PCB_TOP-PCB_T-FLOOR,align=A)
  tray=drill(tray,x,y,-.1,PCB_TOP+1,2.1) # tap M2.5 or fit heat-set redesign after coupon
 # USB-C connector mechanical envelopes: 9.2 wide x 3.6 tall, allow plug clearance.
 for x,y in PORTS.values():
  tray-=Pos(x,y,PCB_TOP-1.7)*Box(12,15,5,align=A)
 # PCB is an envelope only, with switch/stabilizer bores represented in KiCad.
 pcb=prism(op.buffer(-WALL-CLEARANCE),PCB_TOP-PCB_T,PCB_T)
 plate=prism(op,plate_bot,v['plate'])
 for k in keys():
  plate-=Pos(k.x,k.y,plate_bot-.1)*Rot(0,0,k.angle)*Box(v['cut'],v['cut'],v['plate']+.2,align=A)
  # Prototype stabilizer openings, >=2u; verify against chosen stabilizer before manufacture.
  if k.w>=2:
   for sx in [-11.938,11.938]:
    plate-=Pos(k.x,k.y,plate_bot-.1)*Rot(0,0,k.angle)*Pos(sx,0,0)*Box(6.75,14.2,v['plate']+.2,align=A)
 for x,y in holes():
  plate=drill(plate,x,y,plate_bot-.1,v['plate']+.2,2.7)
  pcb=drill(pcb,x,y,PCB_TOP-PCB_T-.1,PCB_T+.2,2.7)
 # Center module sits behind plate; two-piece bezel lets display be removed.
 dx,dy=DISPLAY['x'],DISPLAY['y']
 plate-=Pos(dx,dy,plate_bot-.1)*Box(38,20,v['plate']+.2,align=A)
 bezel=Pos(dx,dy,plate_top)*Box(44,26,2.4,align=A)
 bezel-=Pos(dx,dy,plate_top-.1)*Box(32,12,2.6,align=A)
 bezel+=Pos(dx,dy,plate_bot-1.2)*Box(37.4,19.4,1.2,align=A)-Pos(dx,dy,plate_bot-1.3)*Box(32,12,1.4,align=A)
 # Bridge upper and lower sections; bezel skirt must connect to top, but clear screen.
 bezel+=Pos(dx,dy,plate_bot)*Box(37.4,19.4,v['plate'],align=A)-Pos(dx,dy,plate_bot-.1)*Box(32,12,v['plate']+.2,align=A)
 # Detachable palm rest; intentionally a solid blank for foam/cork top, separate from tray.
 x0,y0,x1,y1=op.bounds
 palm=prism(box(x0+7,y1+2,x1-7,y1+58).buffer(9).buffer(-9),0,8)
 caps=[]
 for k in keys():
  cap=Pos(k.x,k.y,plate_top+3)*Rot(0,0,k.angle)*Box(k.w*19.05-1.4,17.65,v['cap_height'],align=A)
  caps.append(cap)
 # Split printable sections at the center: registration and joinery remain an A1 task.
 left_clip=Pos(-500,-200,-10)*Box(500,600,100,align=(Align.MIN,Align.MIN,Align.MIN))
 right_clip=Pos(0,-200,-10)*Box(500,600,100,align=(Align.MIN,Align.MIN,Align.MIN))
 parts={'tray':tray,'plate':plate,'display_bezel':bezel,'palm_rest':palm}
 # Whole parts are canonical; tiled sections are fit models requiring joinery review.
 for name in ['tray','plate','palm_rest']:
  parts[name+'_left']=parts[name]&left_clip
  parts[name+'_right']=parts[name]&right_clip
 for name,part in parts.items(): part.label=name
 pcb.label='pcb_envelope'
 display=Pos(dx,dy,plate_top-1)*Box(36,18,1,align=A);display.label='lcd_envelope'
 cap_compound=Compound(caps);cap_compound.label='keycap_envelopes'
 assembly=Compound(children=[parts[n] for n in ['tray','plate','display_bezel','palm_rest']]+[pcb,display,cap_compound])
 assembly.label='worxboard_ergo_'+variant
 return parts,assembly
