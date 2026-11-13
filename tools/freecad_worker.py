# SPDX-License-Identifier: GPL-3.0-or-later
"""Run with FreeCADCmd; no build123d imports in this native runtime."""
import os,json,math
from pathlib import Path
import FreeCAD as App
import Part
root=Path(os.environ['ERGO_CAD_ROOT'])
report=[]
for variant in ['mx','choc']:
 folder=root/'cad/exports'/variant
 doc=App.newDocument('Ergo_'+variant)
 expected={}
 for name in ['chassis','plate','top_cover','palm_rest']:
  shape=Part.read(str(folder/(name+'.step')))
  if not shape.isValid() or len(shape.Solids)!=1:raise RuntimeError('invalid '+name)
  obj=doc.addObject('PartDesign::Feature',name);obj.Label=name;obj.Shape=shape
  expected[name]=shape.Volume
 meta=doc.addObject('App::FeaturePython','Provenance')
 meta.addProperty('App::PropertyString','SourceOfTruth');meta.SourceOfTruth='cad/model.py; named B-rep interchange parts, no native feature history'
 meta.addProperty('App::PropertyString','Revision');meta.Revision='A0 engineering prototype — not manufacturing approved'
 doc.recompute()
 filename=folder/('worxboard-ergo-'+variant+'.FCStd')
 doc.saveAs(str(filename));App.closeDocument(doc.Name)
 reopened=App.openDocument(str(filename));reopened.recompute()
 observed={}
 for obj in reopened.Objects:
  if hasattr(obj,'Shape'):
   if not obj.Shape.isValid() or len(obj.Shape.Solids)!=1:raise RuntimeError('invalid reopened '+obj.Label)
   if not math.isclose(obj.Shape.Volume,expected[obj.Label],rel_tol=1e-8,abs_tol=.001):raise RuntimeError('volume changed')
   observed[obj.Label]=obj.Shape.Volume
 if set(observed)!=set(expected):raise RuntimeError('part identity changed')
 App.closeDocument(reopened.Name)
 report.append({'variant':variant,'native_file':str(filename.relative_to(root)),'freecad_version':'.'.join(App.Version()[:3]),
   'save_reopen_passed':True,'solid_count':len(observed),'volumes_mm3':observed})
(root/'cad/freecad-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('Native FreeCAD save/reopen passed for both variants')
