# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate an UNROUTED KiCad board from the schematic XML netlist.
Footprint fields and pad nets are copied from the schematic, never guessed.
"""
import json,sys,uuid,xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from layout import keys,outline,holes,PORTS,DISPLAY
from pcb.scripts.design import design
OFFSET=(200,60)
NS=uuid.UUID('a40b4a5d-7dfe-4659-baea-2f023ee1c88a')
def vec(x,y):return p.VECTOR2I(p.FromMM(x+OFFSET[0]),p.FromMM(y+OFFSET[1]))
def main(v):
 folder=ROOT/'pcb'/v;name='worxboard-ergo-'+v
 root=ET.parse(folder/(name+'.net')).getroot()
 p.KIID.SeedGenerator(719001 if v=="mx" else 719002)
 board=p.BOARD();board.GetDesignSettings().SetCopperLayerCount(4)
 board.GetDesignSettings().m_BoardThickness=p.FromMM(1.6)
 nets={};padnets={}
 for n in root.findall('nets/net'):
  net=p.NETINFO_ITEM(board,n.attrib['name']);board.Add(net);nets[n.attrib['name']]=net
  for node in n.findall('node'):padnets[node.attrib['ref'],node.attrib['pin']]=net
 comp={c.attrib['ref']:c for c in root.findall('components/comp')}
 key_map={k.id:k for k in keys()}
 group_counts={};placements={}
 fixed={'U1':(0,0),'U2':(0,18),'U3':(18,-24),'U7':(0,-18),'Y1':(11,0),
        'SW1':(-12,75),'SW2':(12,75),'J4':(-5.08,53),'J5':(0,83),'J6':(-6,94),'J7':(6,94),
         'U4':(-135,-35),'U5':(0,-35),'U6':(135,-35),
        'C1':(14,-24),'C2':(14,-20),'C3':(18,-18),'C4':(22,-24),
        'C5':(5,18),'C6':(10,-4),'C7':(14,-4),
        'R7':(14,4),'R8':(-5,18),'R9':(-12,69),'R10':(12,69),
        'R3':(-5,-8),'R4':(5,-8),'C20':(0,-22),
        'R40':(-4,-18),'R41':(4,-18),'R42':(-4,-14),'R43':(4,-14),
        'TP8':(-4,27),'TP9':(0,27),'TP10':(4,27)}
 for n,xy in zip(range(8,20),[(-6,-6),(0,-6),(6,-6),(6,0),(6,6),(0,6),(-6,6),(-6,0),(-6,10),(6,10),(-9,-3),(9,-3)]):
  fixed[f'C{n}']=xy
 for i,x in enumerate([-135,0,135],1):
  for delta,dx in [(0,-8),(1,-5),(2,5),(3,8)]:fixed[f'R{20+i*5+delta}']=(x+dx,-35)
  fixed[f'D{i}']=(x+12,-35)
 for i,(port,(x,y)) in enumerate(PORTS.items(),1):fixed[f'J{i}']=(x,y+7)
 for part in design(v):
  lib,fpname=part.footprint.split(':',1)
  libpath=ROOT/'pcb/lib/worxboard.pretty' if lib=='worxboard' else Path('/usr/share/kicad/footprints')/(lib+'.pretty')
  fp=p.FootprintLoad(str(libpath),fpname)
  if fp is None:raise RuntimeError((lib,fpname))
  board.Add(fp)
  fp.SetReference(part.ref);fp.SetValue(part.value)
  if part.key:
   k=key_map[part.key]
   if part.ref.startswith('SK'):
    x,y=k.x,k.y
    fp.Flip(p.VECTOR2I(0,0),p.FLIP_DIRECTION_LEFT_RIGHT)
   else:
    # Diodes occupy the gap above each switch, on F.Cu.
    from math import sin,cos,radians
    x=k.x+sin(radians(k.angle))*8.8;y=k.y-cos(radians(k.angle))*8.8
   angle=-k.angle
  elif part.ref.startswith('H'):
   x,y=holes()[int(part.ref[1:])-1];angle=0
  elif part.ref in fixed:
   x,y=fixed[part.ref];angle=0
  else:
   # Initial component placement in the rear service strip. Refine before routing.
   idx=group_counts.get('service',0);group_counts['service']=idx+1
   x=-166+(idx%26)*12.5;y=-17+(idx//26)*7;angle=0
  fp.SetPosition(vec(x,y));fp.SetOrientationDegrees(angle)
  fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
  c=comp[part.ref];stamp=c.findtext('tstamps','').strip()
  fp.SetPath(p.KIID_PATH('/'+__import__('re').search(r'\(uuid \"([^\"]+)\"\)',(folder/(name+'.kicad_sch')).read_text()).group(1)+'/'+stamp))
  for pad in fp.Pads():
   net=padnets.get((part.ref,pad.GetNumber()))
   if net is not None:pad.SetNet(net)
  placements[part.ref]={'x':x,'y':y,'angle':angle,'footprint':part.footprint}
 pts=list(outline().buffer(-3.4).exterior.coords)
 for a,b in zip(pts,pts[1:]):
  edge=p.PCB_SHAPE();edge.SetShape(p.SHAPE_T_SEGMENT);edge.SetLayer(p.Edge_Cuts)
  edge.SetStart(vec(*a));edge.SetEnd(vec(*b));edge.SetWidth(p.FromMM(.05));board.Add(edge)
 label=p.PCB_TEXT(board);label.SetText('worxboard ergo '+v+' A0 — UNROUTED / DO NOT FABRICATE')
 label.SetPosition(vec(30,120));label.SetLayer(p.F_SilkS);label.SetTextSize(p.VECTOR2I(p.FromMM(1.2),p.FromMM(1.2)));board.Add(label)
 p.SaveBoard(str(folder/(name+'.kicad_pcb')),board)
 (folder/'placement.json').write_text(json.dumps(placements,indent=2)+'\n')
 print(v,len(list(board.GetFootprints())),'footprints, UNROUTED')
if __name__=='__main__':main(sys.argv[1])
