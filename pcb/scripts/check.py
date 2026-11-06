# SPDX-License-Identifier: GPL-3.0-or-later
import sys,json,xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as p
root=Path(__file__).resolve().parents[2]
v=sys.argv[1];stem=root/'pcb'/v/('worxboard-ergo-'+v)
board=p.LoadBoard(str(stem.with_suffix('.kicad_pcb')))
xml=ET.parse(stem.with_suffix('.net')).getroot();expected={}
for net in xml.findall('nets/net'):
 for node in net.findall('node'):expected[node.attrib['ref'],node.attrib['pin']]=net.attrib['name']
actual={};mismatches=[]
for fp in board.GetFootprints():
 for pad in fp.Pads():
  if pad.GetNumber():actual[fp.GetReference(),pad.GetNumber()]=pad.GetNetname()
for key,net in expected.items():
 if actual.get(key)!=net:mismatches.append({'ref':key[0],'pin':key[1],'expected':net,'actual':actual.get(key)})
result={'variant':v,'assigned_schematic_pins':len(expected),'pcb_numbered_pads':len(actual),
 'mismatches':mismatches,'switches':sum(fp.GetReference().startswith('SK') for fp in board.GetFootprints()),
 'tracks':len(list(board.GetTracks())),'fabrication_ready':False}
(root/f'pcb/reports/{v}-connectivity.json').write_text(json.dumps(result,indent=2)+'\n')
if mismatches:raise SystemExit(f'{len(mismatches)} pad-net mismatches')
print(v,'connectivity matches source')
