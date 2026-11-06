#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
image=$(python3 -c 'import json; print(json.load(open("toolchain.lock.json"))["images"]["kicad"])')
mkdir -p pcb/.tools
if [ ! -d pcb/.tools/site313/kicad_sch_api ]; then
 uv pip install --python-version 3.13 --target pcb/.tools/site313 --require-hashes -r pcb/requirements.lock
fi
docker run --rm --network none -u "$(id -u):$(id -g)" -e HOME=/tmp -e PYTHONHASHSEED=0 \
 -e PYTHONPATH=/w:/w/pcb/.tools/site313 -v "$PWD:/w" -w /w "$image" bash -c '
 set -euo pipefail
 bash tools/kicad_env.sh
 for v in mx choc; do
  f=pcb/$v/worxboard-ergo-$v
  python3 pcb/scripts/gen_sch.py "$v"
  kicad-cli sch export netlist --format kicadxml -o "$f.net" "$f.kicad_sch"
  python3 pcb/scripts/place.py "$v"
  python3 pcb/scripts/check.py "$v"
  kicad-cli sch erc --format json -o "pcb/reports/$v-erc.json" "$f.kicad_sch"
  kicad-cli pcb drc --format json -o "pcb/reports/$v-drc.json" "$f.kicad_pcb"
  kicad-cli sch export svg --output "pcb/$v/schematic-preview" "$f.kicad_sch"
 done
 '
