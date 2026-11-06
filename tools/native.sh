#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -n "${FREECAD_CMD:-}" ]; then
 ERGO_CAD_ROOT="$PWD" "$FREECAD_CMD" "$PWD/tools/freecad_worker.py"
else
 flatpak run --filesystem="$PWD" --command=FreeCADCmd --env=ERGO_CAD_ROOT="$PWD" org.freecad.FreeCAD "$PWD/tools/freecad_worker.py"
fi
