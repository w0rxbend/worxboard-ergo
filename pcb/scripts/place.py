# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate an UNROUTED KiCad board from the schematic XML netlist.
Footprint fields and pad nets are copied from the schematic, never guessed.
"""
import json,sys,uuid,xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from layout import keys,outline,holes
from pcb.scripts.design import design
from pcb.scripts.support_places import placements
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
 placed={}
 fixed, sites = placements()
 used=[xy for xy in fixed.values()]
 def take_site():
  while sites:
   xy=sites.pop(0)
   if all((xy[0]-x)**2+(xy[1]-y)**2>3.4**2 for x,y in used):
    used.append(xy)
    return xy
  raise RuntimeError('no support-part seat left on the deck')
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
   # 0402 and test points pack into the rear spine. Refine before routing.
   x,y=take_site();angle=0
  fp.SetPosition(vec(x,y));fp.SetOrientationDegrees(angle)
  fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
  c=comp[part.ref];stamp=c.findtext('tstamps','').strip()
  fp.SetPath(p.KIID_PATH('/'+__import__('re').search(r'\(uuid \"([^\"]+)\"\)',(folder/(name+'.kicad_sch')).read_text()).group(1)+'/'+stamp))
  for pad in fp.Pads():
   net=padnets.get((part.ref,pad.GetNumber()))
   if net is not None:pad.SetNet(net)
  placed[part.ref]={'x':x,'y':y,'angle':angle,'footprint':part.footprint}
 pts=list(outline().buffer(-3.4).exterior.coords)
 for a,b in zip(pts,pts[1:]):
  edge=p.PCB_SHAPE();edge.SetShape(p.SHAPE_T_SEGMENT);edge.SetLayer(p.Edge_Cuts)
  edge.SetStart(vec(*a));edge.SetEnd(vec(*b));edge.SetWidth(p.FromMM(.05));board.Add(edge)
 label=p.PCB_TEXT(board);label.SetText('worxboard ergo '+v+' A0 — UNROUTED / DO NOT FABRICATE')
 label.SetPosition(vec(36,-48));label.SetLayer(p.F_SilkS);label.SetTextSize(p.VECTOR2I(p.FromMM(1.2),p.FromMM(1.2)));board.Add(label)
 p.SaveBoard(str(folder/(name+'.kicad_pcb')),board)
 (folder/'placement.json').write_text(json.dumps(placed,indent=2)+'\n')
 print(v,len(list(board.GetFootprints())),'footprints, UNROUTED')
if __name__=='__main__':main(sys.argv[1])
