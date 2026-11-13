# SPDX-License-Identifier: GPL-3.0-or-later
import json,subprocess
from pathlib import Path
import pytest,trimesh
from build123d import Align
from shapely.geometry import Point,box
from math import cos,sin,radians
from layout import keys,outline,holes,variants,DISPLAY,PORTS,ANGLE,GAP,U
from pcb.scripts.design import design,GPIO_NETS
ROOT=Path(__file__).resolve().parents[1]
def test_layout_mechanical_clearances():
 ks=keys()
 assert len(ks)==48 and len({k.id for k in ks})==48
 assert not any(k.code.startswith('KP_') for k in ks)
 for i,a in enumerate(ks):
  assert outline().contains(a.polygon())
  for b in ks[i+1:]:assert a.polygon().intersection(b.polygon()).area<.01
 for h in holes():
  assert outline().boundary.distance(Point(h))>4
  assert min(Point(h).distance(k.polygon()) for k in ks)>4
 for x,y in PORTS.values():
  connector=box(x-5,y-1,x+5,y+12)
  assert min(connector.distance(Point(h)) for h in holes())>3.5
 d=DISPLAY
 display=box(d['x']-d['module_width']/2,d['y']-d['module_depth']/2,d['x']+d['module_width']/2,d['y']+d['module_depth']/2)
 assert min(display.distance(k.polygon()) for k in ks)>2

def test_keywells_are_orthogonal():
 """After unsplaying, each well's columns are an integer number of key pitches apart."""
 from collections import defaultdict
 cols=defaultdict(list)
 for k in keys():
  pivot=-GAP/2 if k.side=='left' else GAP/2
  a=-radians(k.angle)
  dx,dy=k.x-pivot,k.y
  lx=dx*cos(a)-dy*sin(a); ly=dx*sin(a)+dy*cos(a)
  assert abs(ly/U-k.row)<0.02
  if k.w==1: cols[k.side].append(lx)
 for side, xs in cols.items():
  grid=[]
  for x in sorted(xs):
   if not grid or abs(x-grid[-1])>0.05: grid.append(x)
  assert len(grid)>=3
  for a,b in zip(grid,grid[1:]):
   steps=(b-a)/U
   assert abs(steps-round(steps))<0.02 and round(steps)>=1
 assert ANGLE==10.0

def test_electronics_and_firmware_contract():
 assert len(GPIO_NETS)==30 and len(set(GPIO_NETS))==30
 for variant in variants:
  parts=design(variant);byref={p.ref:p for p in parts}
  assert len(parts)==len(byref)
  switches=[p for p in parts if p.ref.startswith('SK')]
  assert len(switches)==48
  positions=set()
  for i,p in enumerate(switches):
   row,col=divmod(i,15)
   assert p.pins['1']==f'COL{col}'
   d=byref['D'+p.ref[2:]]
   assert d.pins=={'A':p.pins['2'],'K':f'ROW{row}'}
   positions.add((row,col))
  assert len(positions)==48
  for i,port in enumerate(['LEFT','CENTER','RIGHT'],1):
   assert byref[f'J{i}'].pins['VBUS']==f'VBUS_{port}'
   assert byref[f'D{i}'].pins=={'A':f'VBUS_{port}','K':'VSYS'}
  assert byref['U7'].pins['3']!=byref['U7'].pins['5']!=byref['U7'].pins['7']
  assert byref['R40'].pins=={'1':'MUX_S0','2':'3V3'}
  assert byref['R41'].pins=={'1':'MUX_S1','2':'3V3'}
  assert byref['J6'].pins=={'1':'MUX_S0_FW','2':'MUX_S0','3':'3V3'}
  assert byref['J7'].pins=={'1':'MUX_S1_FW','2':'MUX_S1','3':'GND'}
 text=(ROOT/'firmware/boards/worxbend/worxboard_ergo/worxboard-ergo-layout.dtsi').read_text()
 assert text.count('RC(')==48
 for i in range(48):assert f'RC({i//15},{i%15})' in text

def test_usb_input_selection_behavior(tmp_path):
 exe=tmp_path/'selection'
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I',str(ROOT/'firmware/src'),str(ROOT/'tests/usb_priority.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)

@pytest.mark.parametrize('variant',['mx','choc'])
def test_exported_manifold_meshes_and_native_reopen(variant):
 paths=list((ROOT/'cad/exports'/variant).glob('*.stl'))
 assert len(paths)==13
 for p in paths:
  m=trimesh.load_mesh(p)
  assert m.is_watertight and m.volume>0,p
  assert p.with_suffix('.step').stat().st_size>1000
  assert p.with_suffix('.3mf').stat().st_size>1000
 report=json.loads((ROOT/'cad/freecad-validation.json').read_text())
 v=next(x for x in report if x['variant']==variant)
 assert v['save_reopen_passed'] and v['solid_count']==4
 assert (ROOT/v['native_file']).is_file()
 # The native report must name this export. A leftover tray file must not pass.
 cad=json.loads((ROOT/'cad/validation.json').read_text())
 whole={p['part']:p['volume_mm3'] for p in cad['parts'] if p['variant']==variant and p['part'] in {'chassis','plate','top_cover','palm_rest'}}
 assert set(v['volumes_mm3'])==set(whole)
 for name,vol in v['volumes_mm3'].items():
  assert abs(vol-whole[name])<max(1.0,abs(whole[name])*1e-4),(variant,name,vol,whole[name])

CASE_BOUNDS={
 'mx':{'chassis':(303.03,223.00,15.50),'chassis_left':(169.51,223.00,15.50),'chassis_right':(151.51,223.00,15.50),
  'top_cover':(288.87,136.40,7.50),'palm_rest':(302.74,88.33,19.00),'riser':(224.0,33.21,21.25)},
 'choc':{'chassis':(303.03,223.00,12.70),'chassis_left':(169.51,223.00,12.70),'chassis_right':(151.51,223.00,12.70),
  'top_cover':(288.87,136.40,4.70),'palm_rest':(302.74,88.33,10.20),'riser':(224.0,33.21,21.25)}}
PLATE_VOLUME={'mx':29812.902,'choc':24170.577}
FIT_PAIR_COUNT=21

@pytest.mark.parametrize('variant',['mx','choc'])
def test_exported_case_envelope(variant):
 """The committed export is the Sculpt-style shell with its top cover, the plate has the USB notches, and nothing collides."""
 cad=json.loads((ROOT/'cad/validation.json').read_text())
 parts={p['part']:p for p in cad['parts'] if p['variant']==variant}
 for name,expected in CASE_BOUNDS[variant].items():
  assert parts[name]['bounds_mm']==pytest.approx(expected,abs=.1),(variant,name)
 assert parts['plate']['volume_mm3']==pytest.approx(PLATE_VOLUME[variant],abs=.001)
 fit=cad['interference_mm3'][variant]
 assert len(fit)==FIT_PAIR_COUNT and not any(fit.values()),(variant,fit)

@pytest.mark.parametrize('variant',['mx','choc'])
def test_exported_holes_match_the_pcb_top_view(variant):
 """KiCad draws the board from the top with y toward the typist. The exported STEP is right-handed
 with y away from the typist, so a PCB hole at (x, y) must be open at (x, -y) in the chassis and the plate."""
 from build123d import import_step,Pos,Cylinder
 def shared(solid,x,y):
  hit=solid&(Pos(x,y,-20)*Cylinder(1.0,60,align=(Align.CENTER,Align.CENTER,Align.MIN)))
  return 0 if hit is None else hit.volume   # build123d returns None when an imported solid shares nothing
 placed=json.loads((ROOT/'pcb'/variant/'placement.json').read_text())
 pcb_holes=[(part['x'],part['y']) for ref,part in placed.items() if ref.startswith('H')]
 assert len(pcb_holes)==8
 for name in ('chassis','plate'):
  solid=import_step(ROOT/'cad/exports'/variant/(name+'.step'))
  for x,y in pcb_holes:
   assert shared(solid,x,-y)<1e-6,(variant,name,'hole closed at',x,-y)
  # Control: at the mirror image of the first hole there is material, so the probe can tell the two apart.
  x,y=pcb_holes[0]
  assert shared(solid,-x,-y)>1,(variant,name)

@pytest.mark.parametrize('variant',['mx','choc'])
def test_3mf_units_and_geometry(variant):
 import zipfile,xml.etree.ElementTree as ET
 ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
 for p in (ROOT/'cad/exports'/variant).glob('*.3mf'):
  with zipfile.ZipFile(p) as z:
   name=next(n for n in z.namelist() if n.endswith('.model'))
   model=ET.fromstring(z.read(name))
  assert model.attrib['unit']=='millimeter'
  assert len(model.findall('.//m:vertex',ns))>3
  assert len(model.findall('.//m:triangle',ns))>3
