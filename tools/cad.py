# SPDX-License-Identifier: GPL-3.0-or-later
import argparse,json,re,zipfile
from copy import copy
from pathlib import Path
import numpy as np
import trimesh
from cad.model import make
from build123d import export_step,export_stl,Mesher,import_step
ROOT=Path(__file__).resolve().parents[1]

def _repair_print_mesh(stl_path, mf_path):
 """Tessellation can leave a zero-area triangle. Drop those, then require a closed mesh."""
 mesh=trimesh.load_mesh(stl_path)
 keep=mesh.area_faces>1e-9
 if not keep.all():
  mesh.update_faces(keep)
  mesh.remove_unreferenced_vertices()
  mesh.export(stl_path)
 _strip_3mf_degenerates(mf_path)
 if not mesh.is_watertight or mesh.volume<=0:
  raise RuntimeError(f'{stl_path.name} is not a watertight print mesh')

def _strip_3mf_degenerates(path):
 with zipfile.ZipFile(path) as archive:
  blobs={name:archive.read(name) for name in archive.namelist()}
 model_name=next(name for name in blobs if name.endswith('.model'))
 text=blobs[model_name].decode()
 vertices=np.array([(float(x),float(y),float(z)) for x,y,z in re.findall(
  r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)" />', text)])
 def degenerate(match):
  index=[int(match.group(i)) for i in (1,2,3)]
  if len(set(index))<3: return True
  a,b,c=vertices[index]
  return np.linalg.norm(np.cross(b-a, c-a))<1e-9
 cleaned=re.sub(r'[ \t]*<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)" />\n',
  lambda match: '' if degenerate(match) else match.group(0), text)
 if cleaned==text: return
 blobs[model_name]=cleaned.encode()
 with zipfile.ZipFile(path,'w') as archive:
  for name,data in blobs.items(): archive.writestr(name,data)
# Each part against everything that must not share volume with it.
FIT_PAIRS={
 'chassis':('pcb_envelope','lcd_envelope','keycap_envelopes','usb_receptacle_envelopes','usb_plug_envelopes','pad_envelopes',
  'plate','top_cover','palm_rest','riser'),
 'plate':('usb_receptacle_envelopes','usb_plug_envelopes','top_cover'),
 'top_cover':('pcb_envelope','lcd_envelope','keycap_envelopes','switch_envelopes','usb_receptacle_envelopes','usb_plug_envelopes'),
 'palm_rest':('keycap_envelopes',),
 'riser':('pad_envelopes',),
}

def fit_report(parts,assembly):
 """Overlap volume in mm3 for each pair that must not collide. The gate is zero for all of them."""
 solid={**parts,**{child.label:child for child in assembly.children}}
 return {f'{other}_vs_{name}':(solid[other]&solid[name]).volume for name,others in FIT_PAIRS.items() for other in others}

def main():
 p=argparse.ArgumentParser();p.add_argument('--variant',choices=['mx','choc','all'],default='all');a=p.parse_args()
 reports=[];fits={}
 for v in (['mx','choc'] if a.variant=='all' else [a.variant]):
  out=ROOT/'cad/exports'/v;out.mkdir(parents=True,exist_ok=True)
  for stale in out.glob('*'):
   if stale.suffix in {'.stl','.step','.3mf'}:
    stale.unlink()
  parts,assembly=make(v)
  fits[v]=fit_report(parts,assembly)
  assert not any(fits[v].values()),(v,'interference',fits[v])
  for name,part in parts.items():
   part=copy(part);part.parent=None
   assert part.is_valid and len(part.solids())==1,(v,name,'invalid topology',len(part.solids()))
   assert part.volume>0
   export_step(part,out/(name+'.step'))
   export_stl(part,out/(name+'.stl'),tolerance=.08,angular_tolerance=.15)
   mesher=Mesher(unit=__import__('build123d').Unit.MM)
   mesher.add_shape(part,linear_deflection=.08,angular_deflection=.15,part_number=name)
   mesher.write(out/(name+'.3mf'))
   _repair_print_mesh(out/(name+'.stl'), out/(name+'.3mf'))
   imported=import_step(out/(name+'.step'))
   assert imported.is_valid and len(imported.solids())==1
   assert abs(imported.volume-part.volume)<max(.001,part.volume*1e-7)
   reports.append({'variant':v,'part':name,'valid_solid':True,'solids':1,'volume_mm3':round(part.volume,5),
    'bounds_mm':[round(x,4) for x in part.bounding_box().size], 'step_roundtrip':True})
   print(v,name,round(part.volume,1),'mm3',flush=True)
  export_step(assembly,out/'assembly.step')
 (ROOT/'cad/validation.json').write_text(json.dumps({'status':'prototype_geometry_checked','parts':reports,'interference_mm3':fits,
  'not_validated':['switch retention','stabilizer fit','LED window cutter access','display supplier measurements','USB plug fit',
   'USB receptacle placement on the PCB: the keep-outs assume a rear-facing jack flush with the board edge',
   'PCB component heights under the plate and the top cover','split-tab print fit','top-cover fit in the rim and screw engagement',
   'pad seating on a desk','magnet fit and pull','palm-rest screw fit','riser fit and stance','physical build']},indent=2)+'\n')
if __name__=='__main__':main()
