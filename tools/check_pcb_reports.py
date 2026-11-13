# SPDX-License-Identifier: GPL-3.0-or-later
"""Gate the generated boards: pad-net parity, ERC, DRC, unconnected items and KiCad's schematic parity.

Zero here means the design files agree with each other. It does not mean a board works.
"""
import json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VARIANTS=('mx','choc')

def findings(variant):
 """Blocking findings of one variant as text lines, and its warning counts by type."""
 reports=ROOT/'pcb/reports'
 pads=json.loads((reports/f'{variant}-connectivity.json').read_text())
 erc=json.loads((reports/f'{variant}-erc.json').read_text())
 drc=json.loads((reports/f'{variant}-drc.json').read_text())
 erc_items=[item for sheet in erc.get('sheets',[]) for item in sheet.get('violations',[])]
 errors=Counter(item['type'] for item in erc_items+drc['violations'] if item['severity']=='error')
 warnings=Counter(item['type'] for item in erc_items+drc['violations'] if item['severity']!='error')
 blocking=[f'{variant}: {count} x {kind}' for kind,count in sorted(errors.items())]
 for name,count in (('pad-net mismatches',len(pads['mismatches'])),('unconnected items',len(drc['unconnected_items'])),
                    ('schematic parity findings',len(drc.get('schematic_parity',[]))),('missing switches',48-pads['switches'])):
  if count:blocking.append(f'{variant}: {count} {name}')
 return blocking,warnings

def main():
 failed=[]
 for variant in VARIANTS:
  blocking,warnings=findings(variant);failed+=blocking
  routing=json.loads((ROOT/f'pcb/reports/{variant}-routing.json').read_text())
  print(variant,routing['tracks'],'tracks,',routing['vias'],'vias,',routing['zones'],'zones;',
        'warnings:',dict(sorted(warnings.items())) or 'none')
 if failed:
  print('PCB checks failed:\n'+'\n'.join(failed));sys.exit(1)
 print('ERC, DRC, connectivity and schematic parity are clean. No hardware has been built or tested.')
if __name__=='__main__':main()
