# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify schematic/PCB pad-net parity; report routing readiness separately."""
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for v in ['mx','choc']:
 data=json.loads((root/f'pcb/reports/{v}-connectivity.json').read_text())
 assert not data['mismatches'],(v,data['mismatches'])
 assert data['switches']==87
 print(v,'schematic/PCB pad assignments match;',data['tracks'],'tracks; unrouted design seed')
