# SPDX-License-Identifier: GPL-3.0-or-later
import json,sys
from pathlib import Path
r=Path(__file__).resolve().parents[1]
failed=[]
for v in ['mx','choc']:
 for kind in ['erc','drc']:
  report=r/f'pcb/reports/{v}-{kind}.json'
  if not report.exists():failed.append(f'{v}: missing {kind}');continue
  data=json.loads(report.read_text())
  problems=data.get('violations',[])+data.get('unconnected_items',[])+data.get('schematic_parity',[])
  if kind=='erc':
   problems=[x for sheet in data.get('sheets',[]) for x in sheet.get('violations',[])]
  if problems:failed.append(f'{v}: {len(problems)} {kind} findings')
# These are physical engineering gates; zero reports alone cannot approve A0.
failed.append('A0: USB override validation, routing review and physical fit/bring-up approvals outstanding')
print('Fabrication blocked:\n'+'\n'.join(failed));sys.exit(1)
