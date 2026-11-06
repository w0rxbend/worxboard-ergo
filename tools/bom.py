# SPDX-License-Identifier: GPL-3.0-or-later
import csv
from pathlib import Path
from pcb.scripts.design import design

def main():
 root=Path(__file__).resolve().parents[1]
 with (root/'docs/bom.csv').open('w',newline='') as f:
  writer=csv.writer(f,lineterminator='\n')
  writer.writerow(['variant','reference','value','footprint','LCSC_reference_only','group','status'])
  for variant in ['mx','choc']:
   for part in design(variant):
    if part.in_bom:
     writer.writerow([variant,part.ref,part.value,part.footprint,part.lcsc,part.group,'UNVERIFIED_A0_NOT_FOR_ORDER'])
if __name__=='__main__':main()
