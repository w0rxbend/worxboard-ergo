# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate the placed, UNROUTED KiCad board from the schematic XML netlist.

Footprint fields and pad nets are copied from the schematic, never guessed.
route.py adds copper to this seed; nothing here draws a track.
"""
import json,re,sys,xml.etree.ElementTree as ET
from math import sin,cos,radians,hypot
from pathlib import Path
import pcbnew as p
from shapely.geometry import box
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from layout import keys,board_outline,holes
from pcb.scripts.design import design
from pcb.scripts.rules import project_settings
from pcb.scripts.support_places import anchors,SATELLITES,CORRIDORS,KEEP_CLEAR,TOP_SIDE,DIODE_NORTH,BOSS_CLEAR
OFFSET=(200,60)
EDGE_KEEP_IN=1.0        # part bodies stay this far inside the board edge
BODY_MARGIN=0.35        # courtyard allowance around the pads of a part
SEARCH_STEP=0.2
LATTICE=0.1             # maze.GRID; SEARCH_STEP is a multiple of it
SEARCH_REACH=14.0       # give up when no seat exists this close to the host pad
BOTH='*'
def vec(x,y):return p.VECTOR2I(p.FromMM(x+OFFSET[0]),p.FromMM(y+OFFSET[1]))
def xy(v):return p.ToMM(v.x)-OFFSET[0],p.ToMM(v.y)-OFFSET[1]

def _net_name(name):
    """KiCad's own spelling of a netlist net name: an unconnected pin's net escapes the '/' of its pin name."""
    if name.startswith('unconnected-('):return 'unconnected-('+name[len('unconnected-('):].replace('/','{slash}')
    return name

def pose(fp,x,y,angle):
 fp.SetPosition(vec(x,y));fp.SetOrientationDegrees(angle)

def pad_at(fp,number):
 for pad in fp.Pads():
  if pad.GetNumber()==number:return pad
 raise RuntimeError(f'{fp.GetReference()} has no pad {number}')

def body(fp,margin=BODY_MARGIN):
 """Seat rectangle and the sides it blocks: pads and courtyard plus a margin. Drilled pads block both sides."""
 fp.BuildCourtyardCaches()
 boxes=[pad.GetBoundingBox() for pad in fp.Pads()]
 boxes+=[yard.BBox() for yard in (fp.GetCourtyard(p.F_CrtYd),fp.GetCourtyard(p.B_CrtYd)) if yard.OutlineCount()]
 x0,y0=xy(p.VECTOR2I(min(b.GetLeft() for b in boxes),min(b.GetTop() for b in boxes)))
 x1,y1=xy(p.VECTOR2I(max(b.GetRight() for b in boxes),max(b.GetBottom() for b in boxes)))
 drilled=any(pad.GetDrillSizeX()>0 for pad in fp.Pads())
 side=BOTH if drilled else ('B' if fp.IsFlipped() else 'F')
 return (x0-margin,y0-margin,x1+margin,y1+margin),side

class Seats:
 """Occupied rectangles per side, and the test a new seat has to pass."""
 def __init__(self):
  self.taken=[];self.keep_in=board_outline().buffer(-EDGE_KEEP_IN)
  for x,y in holes():
   for side,r in BOSS_CLEAR.items():self.taken.append(((x-r,y-r,x+r,y+r),side))
 def add(self,fp):self.taken.append(body(fp))
 def reserve(self,pads,side):
  """Keep the box around these pads empty on one side."""
  boxes=[pad.GetBoundingBox() for pad in pads]
  x0,y0=xy(p.VECTOR2I(min(b.GetLeft() for b in boxes),min(b.GetTop() for b in boxes)))
  x1,y1=xy(p.VECTOR2I(max(b.GetRight() for b in boxes),max(b.GetBottom() for b in boxes)))
  self.taken.append(((x0,y0,x1,y1),side))
 def free(self,fp):
  (x0,y0,x1,y1),side=body(fp)
  if not self.keep_in.contains(box(x0,y0,x1,y1)):return False
  return not any((side==BOTH or other==BOTH or side==other) and x0<c and a<x1 and y0<d and b<y1
                 for (a,b,c,d),other in self.taken)

def spiral(reach,step):
 """Grid offsets around the origin, nearest first."""
 n=int(reach/step)
 cells=[(i*step,j*step) for i in range(-n,n+1) for j in range(-n,n+1)]
 return sorted((c for c in cells if hypot(*c)<=reach),key=lambda c:hypot(*c))

def seat_satellite(fp,host_pad,least,seats):
 """Nearest free seat to the host pad, turned so the pad that shares its net is the close one."""
 hx,hy=xy(host_pad.GetPosition());net=host_pad.GetNetname()
 ox,oy=round(hx/LATTICE)*LATTICE,round(hy/LATTICE)*LATTICE   # fine-pitch pads must land on the router lattice
 mine=[pad for pad in fp.Pads() if pad.GetNetname()==net]
 if not mine:raise RuntimeError(f'{fp.GetReference()} shares no net with {net}')
 for dx,dy in spiral(SEARCH_REACH,SEARCH_STEP):
  if hypot(dx,dy)<least:continue
  best=None
  for angle in (0,90,180,270):
   pose(fp,ox+dx,oy+dy,angle)
   if not seats.free(fp):continue
   gap=min(hypot(px-hx,py-hy) for px,py in (xy(pad.GetPosition()) for pad in mine))
   if best is None or gap<best[0]:best=(gap,angle)
  if best:
   pose(fp,ox+dx,oy+dy,best[1]);return
 raise RuntimeError(f'no seat for {fp.GetReference()} within {SEARCH_REACH} mm of its host pad')

def load(part):
 lib,name=part.footprint.split(':',1)
 path=ROOT/'pcb/lib/worxboard.pretty' if lib=='worxboard' else Path('/usr/share/kicad/footprints')/(lib+'.pretty')
 fp=p.FootprintLoad(str(path),name)
 if fp is None:raise RuntimeError((lib,name))
 fp.SetFPID(p.LIB_ID(lib,name))
 return fp

def copy_schematic_identity(fp,part,component,sheet_uuid):
 """Reference, value, fields, attributes and the symbol link, so KiCad's parity check has nothing to report."""
 fp.SetReference(part.ref);fp.SetValue(part.value)
 fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
 for field in component.findall('fields/field'):
  if field.attrib['name'] not in ('Footprint','Datasheet','Description'):
   fp.SetField(field.attrib['name'],field.text or '')
   fp.GetField(field.attrib['name']).SetVisible(False)
 if not part.in_bom:fp.SetAttributes(fp.GetAttributes()|p.FP_EXCLUDE_FROM_BOM)
 fp.SetDNP(part.dnp)
 fp.SetPath(p.KIID_PATH('/'+sheet_uuid+'/'+component.findtext('tstamps','').strip()))
 fp.SetSheetname(component.find('sheetpath').attrib['names'])
 fp.SetSheetfile(component.find("property[@name='Sheetfile']").attrib['value'])

def main(v):
 folder=ROOT/'pcb'/v;name='worxboard-ergo-'+v
 root=ET.parse(folder/(name+'.net')).getroot()
 sheet_uuid=re.search(r'\(uuid "([^"]+)"\)',(folder/(name+'.kicad_sch')).read_text()).group(1)
 p.KIID.SeedGenerator(719001 if v=="mx" else 719002)
 board=p.BOARD();board.GetDesignSettings().SetCopperLayerCount(4)
 board.GetDesignSettings().m_BoardThickness=p.FromMM(1.6)
 padnets={}
 for n in root.findall('nets/net'):
  net=p.NETINFO_ITEM(board,_net_name(n.attrib['name']));board.Add(net)
  for node in n.findall('node'):padnets[node.attrib['ref'],node.attrib['pin']]=net
 comp={c.attrib['ref']:c for c in root.findall('components/comp')}
 key_map={k.id:k for k in keys()}
 parts={part.ref:part for part in design(v)};fps={}
 for part in parts.values():
  fp=load(part);board.Add(fp);fps[part.ref]=fp
  copy_schematic_identity(fp,part,comp[part.ref],sheet_uuid)
  for pad in fp.Pads():
   net=padnets.get((part.ref,pad.GetNumber()))
   if net is not None:pad.SetNet(net)
  if part.ref not in TOP_SIDE and not part.ref.startswith('H'):
   fp.Flip(fp.GetPosition(),p.FLIP_DIRECTION_LEFT_RIGHT)
 seats=Seats();fixed=anchors()
 for ref,fp in fps.items():
  part=parts[ref]
  if part.key:
   k=key_map[part.key]
   north=0 if ref.startswith('SK') else DIODE_NORTH
   pose(fp,k.x+sin(radians(k.angle))*north,k.y-cos(radians(k.angle))*north,-k.angle)
  elif ref.startswith('H'):pose(fp,*holes()[int(ref[1:])-1],0)
  elif ref in fixed:pose(fp,*fixed[ref])
  else:continue
  if not ref.startswith('H'):seats.add(fp)
 for near,numbers,far in CORRIDORS:
  seats.reserve([pad_at(fps[near],n) for n in numbers]+list(fps[far].Pads()),'B')
 for ref,(x0,y0,x1,y1),side in KEEP_CLEAR:
  cx,cy=xy(fps[ref].GetPosition());seats.taken.append(((cx+x0,cy+y0,cx+x1,cy+y1),side))
 for ref,host,host_pad,least in SATELLITES:
  seat_satellite(fps[ref],pad_at(fps[host],host_pad),least,seats);seats.add(fps[ref])
 unplaced=set(fps)-set(fixed)-{row[0] for row in SATELLITES}-{r for r in fps if parts[r].key or r.startswith('H')}
 if unplaced:raise RuntimeError(f'no seat defined for {sorted(unplaced)}')
 pts=list(board_outline().exterior.coords)
 for a,b in zip(pts,pts[1:]):
  edge=p.PCB_SHAPE();edge.SetShape(p.SHAPE_T_SEGMENT);edge.SetLayer(p.Edge_Cuts)
  edge.SetStart(vec(*a));edge.SetEnd(vec(*b));edge.SetWidth(p.FromMM(.05));board.Add(edge)
 label=p.PCB_TEXT(board);label.SetText('worxboard ergo '+v+' A0 prototype - not hardware tested')
 label.SetPosition(vec(0,-8));label.SetLayer(p.F_SilkS);label.SetTextSize(p.VECTOR2I(p.FromMM(1.2),p.FromMM(1.2)));board.Add(label)
 work=ROOT/'pcb/.work'/v;work.mkdir(parents=True,exist_ok=True)
 p.SaveBoard(str(work/'seed.kicad_pcb'),board)
 pro=folder/(name+'.kicad_pro');settings=json.loads(pro.read_text());settings.update(project_settings())
 pro.write_text(json.dumps(settings,indent=2)+'\n')
 placed={ref:{'x':round(xy(fp.GetPosition())[0],3),'y':round(xy(fp.GetPosition())[1],3),'angle':fp.GetOrientationDegrees(),
  'side':'B' if fp.IsFlipped() else 'F','footprint':parts[ref].footprint} for ref,fp in fps.items()}
 (folder/'placement.json').write_text(json.dumps(placed,indent=2)+'\n')
 print(v,len(fps),'footprints placed, UNROUTED seed')
if __name__=='__main__':main(sys.argv[1])
