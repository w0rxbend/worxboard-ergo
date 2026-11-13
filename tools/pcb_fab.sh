#!/usr/bin/env bash
# PCBWay prototype order package for each routed board, under pcb/fab/<variant>/ and as a zip.
# Run make pcb first: this plots the committed board and does not check it.
set -euo pipefail
cd "$(dirname "$0")/.."
image=$(python3 -c 'import json; print(json.load(open("toolchain.lock.json"))["images"]["kicad_3d"])')
docker run --rm --network none -u "$(id -u):$(id -g)" -e HOME=/tmp -e PYTHONHASHSEED=0 \
 -e PYTHONPATH=/w:/w/pcb/.tools/site313 -v "$PWD:/w" -w /w "$image" bash -c '
 set -euo pipefail
 bash tools/kicad_env.sh
 copper=F.Cu,In1.Cu,In2.Cu,B.Cu
 for v in mx choc; do
  board=pcb/$v/worxboard-ergo-$v.kicad_pcb; out=pcb/fab/$v
  rm -rf "$out"; mkdir -p "$out/gerber"
  kicad-cli pcb export gerbers --no-x2 --no-protel-ext \
   --layers "$copper,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts" -o "$out/gerber/" "$board"
  kicad-cli pcb export drill --format excellon --excellon-separate-th --excellon-units mm \
   --generate-map --map-format pdf -o "$out/gerber/" "$board"
  kicad-cli pcb export ipcd356 -o "$out/netlist.ipc" "$board"
  kicad-cli pcb export pdf --layers F.Fab,F.Silkscreen,Edge.Cuts --black-and-white -o "$out/assembly-top.pdf" "$board"
  kicad-cli pcb export pdf --layers B.Fab,B.Silkscreen,Edge.Cuts --black-and-white --mirror -o "$out/assembly-bottom.pdf" "$board"
  kicad-cli pcb render --side top --width 2400 --height 1200 -o "$out/render-top.png" "$board"
  kicad-cli pcb render --side bottom --width 2400 --height 1200 -o "$out/render-bottom.png" "$board"
  python3 pcb/scripts/fab.py "$v"
  rm -f "$out"/gerber/*.gbrjob
  (cd pcb/fab && rm -f "worxboard-ergo-$v-A0-pcbway.zip" && python3 -m zipfile -c "worxboard-ergo-$v-A0-pcbway.zip" "$v")
 done
 '
