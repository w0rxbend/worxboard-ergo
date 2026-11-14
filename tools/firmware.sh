#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
image=$(python3 -c 'import json; print(json.load(open("toolchain.lock.json"))["images"]["zmk"])')
repo=$PWD
mkdir -p build/zmk-ws/config build/firmware
cp firmware/config/west.yml build/zmk-ws/config/west.yml
# Set ERGO_ZMK_WORKSPACE to an already initialized, pinned west workspace to avoid re-fetching.
ws=${ERGO_ZMK_WORKSPACE:-$repo/build/zmk-ws}
docker run --rm --cpus "${FIRMWARE_CPUS:-4}" -u "$(id -u):$(id -g)" -e HOME=/tmp -e ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk-0.16.9 \
 -v "$repo:/repo" -v "$ws:/ws" -w /ws "$image" bash -c '
 set -euo pipefail
 if [ ! -d .west ]; then west init -l config; fi
 if [ ! -d zmk ]; then west update --fetch-opt=--filter=tree:0; fi
 expected=$(python3 -c "import yaml; print(yaml.safe_load(open(\"/repo/firmware/config/west.yml\"))[\"manifest\"][\"projects\"][0][\"revision\"])")
 test "$(git -C zmk rev-parse HEAD)" = "$expected"
 west zephyr-export
 west build -p always -S studio-rpc-usb-uart -s zmk/app -d /repo/build/firmware -b worxboard_ergo/rp2040 -- \
  -DZMK_CONFIG=/repo/firmware/config -DZMK_EXTRA_MODULES=/repo
 '
cp build/firmware/zephyr/zmk.uf2 firmware/artifacts/worxboard-ergo.uf2

python3 tools/verify_firmware.py
