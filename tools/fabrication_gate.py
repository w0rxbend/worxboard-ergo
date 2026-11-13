# SPDX-License-Identifier: GPL-3.0-or-later
"""Release gate. Design-file checks can pass; the items only a person or a built board can close cannot."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.check_pcb_reports import VARIANTS,findings
# AGENTS.md: release needs manual USB/ground review and hardware prototype evidence. Nothing in the
# repository can supply either, so this list is closed by editing it in a reviewed commit, not by a script.
OUTSTANDING=(
 'manual review of the USB pairs, ground planes and return paths by a person',
 'manual review of every Gerber layer and the drill files by a person',
 'hardware prototype evidence: rails, crystal start-up, USB enumeration on all three ports, key matrix',
 'hardware validation of the J6/J7 centre-port ROM override',
 'physical fit of the assembled board in the printed case',
)
def main():
 failed=[line for variant in VARIANTS for line in findings(variant)[0]]
 failed+=[f'A0: outstanding: {item}' for item in OUTSTANDING]
 print('Fabrication release blocked:\n'+'\n'.join(failed));sys.exit(1)
if __name__=='__main__':main()
