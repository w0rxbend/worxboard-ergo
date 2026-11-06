# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 paths=[]
 for directory in ['cad/exports','firmware/artifacts','pcb/mx','pcb/choc','pcb/reports']:
  paths.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and p.suffix not in {'.kicad_prl','.FCBak','.FCStd1'})
 paths.extend([ROOT/'cad/validation.json',ROOT/'cad/freecad-validation.json'])
 records=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]
 (ROOT/'assets/artifact-manifest.json').write_text(json.dumps({'revision':'A0 engineering starter','artifacts':records},indent=2)+'\n')
 (ROOT/'assets/SHA256SUMS').write_text(''.join(x['sha256']+'  '+x['path']+'\n' for x in records))
 print(len(records),'artifacts inventoried')
if __name__=='__main__':main()
