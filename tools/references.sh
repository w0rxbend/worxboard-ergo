#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
git submodule update --init references/system76-launch
git -C references/system76-launch submodule update --init firmware
# This retrieves all Launch files and the pinned QMK source. QMK's own build-time
# submodules are only needed to build that reference firmware, not this project.
