# SPDX-License-Identifier: GPL-3.0-or-later
import argparse,json
from copy import copy
from pathlib import Path
from cad.model import make
from build123d import export_step,export_stl,Mesher,import_step
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--variant',choices=['mx','choc','all'],default='all');a=p.parse_args()
 reports=[]
 for v in (['mx','choc'] if a.variant=='all' else [a.variant]):
  out=ROOT/'cad/exports'/v;out.mkdir(parents=True,exist_ok=True)
  parts,assembly=make(v)
  for name,part in parts.items():
   part=copy(part);part.parent=None
   assert part.is_valid and len(part.solids())==1,(v,name,'invalid topology',len(part.solids()))
   assert part.volume>0
   export_step(part,out/(name+'.step'))
   export_stl(part,out/(name+'.stl'),tolerance=.08,angular_tolerance=.15)
   mesher=Mesher(unit=__import__('build123d').Unit.MM)
   mesher.add_shape(part,linear_deflection=.08,angular_deflection=.15,part_number=name)
   mesher.write(out/(name+'.3mf'))
   imported=import_step(out/(name+'.step'))
   assert imported.is_valid and len(imported.solids())==1
   assert abs(imported.volume-part.volume)<max(.001,part.volume*1e-7)
   reports.append({'variant':v,'part':name,'valid_solid':True,'solids':1,'volume_mm3':round(part.volume,5),
    'bounds_mm':[round(x,4) for x in part.bounding_box().size], 'step_roundtrip':True})
   print(v,name,round(part.volume,1),'mm3',flush=True)
  export_step(assembly,out/'assembly.step')
 (ROOT/'cad/validation.json').write_text(json.dumps({'status':'prototype_geometry_checked','parts':reports,
  'not_validated':['switch retention','stabilizer fit','display supplier measurements','USB plug fit','print tile joinery','physical build']},indent=2)+'\n')
if __name__=='__main__':main()
