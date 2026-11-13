# SPDX-License-Identifier: GPL-3.0-or-later
import csv
from pathlib import Path
from pcb.scripts.design import design,sourcing
VERIFIED='MPN_READ_2026-11-13_STOCK_AND_PRICE_UNKNOWN'
UNVERIFIED='UNVERIFIED_NOT_FOR_ORDER'

def main():
 root=Path(__file__).resolve().parents[1]
 with (root/'docs/bom.csv').open('w',newline='') as f:
  writer=csv.writer(f,lineterminator='\n')
  writer.writerow(['variant','reference','value','footprint','manufacturer','mpn','LCSC_reference_only','group','fitted_by','status'])
  for variant in ['mx','choc']:
   for part in design(variant):
    if part.in_bom:
     maker,mpn,verified=sourcing(part)
     writer.writerow([variant,part.ref,part.value,part.footprint,maker,mpn,part.lcsc,part.group,
      'customer' if part.dnp else 'assembler',VERIFIED if verified else UNVERIFIED])
if __name__=='__main__':main()
