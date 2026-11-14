#!/usr/bin/env bash
# Rerun the autorouter on the nets route.py leaves open: the key matrix and slow GPIO.
# Needed only after placement or scripted copper changes. The session files it writes are committed,
# so make pcb needs neither Java nor the network.
set -euo pipefail
cd "$(dirname "$0")/.."
passes=${AUTOROUTE_PASSES:-40}
threads=${AUTOROUTE_THREADS:-4}   # optimizer threads; Freerouting's routing pass itself is single-threaded
read -r image url sha < <(python3 -c 'import json; t=json.load(open("toolchain.lock.json")); print(t["images"]["java"], t["freerouting"]["url"], t["freerouting"]["sha256"])')
jar=pcb/.tools/$(basename "$url")
mkdir -p pcb/.tools
[ -f "$jar" ] || curl -fsSL --max-time 600 -o "$jar" "$url"
echo "$sha  $jar" | sha256sum -c -
bash tools/pcb.sh critical
for v in ${AUTOROUTE_VARIANTS:-mx choc}; do
 # Fanout is off: route.py has already given every plane pin its via, and Freerouting's fanout stage
 # cannot escape the 0.4 mm QFN pins it has been handed back.
 timeout "${AUTOROUTE_TIMEOUT:-7200}" docker run --rm --cpus "$threads" --network none --add-host router:127.0.0.1 -h router \
  -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD:/w" -w /w "$image" java -jar "/w/$jar" \
  -de "pcb/.work/$v/board.dsn" -do "pcb/.work/$v/autoroute.ses" -mp "$passes" -mt "$threads" --gui.enabled=false \
  --router.fanout.enabled=false --router.max_threads="$threads" --router.optimizer.max_threads="$threads" \
  --router.copper_to_edge_clearance_um=300 --router.automatic_neckdown=false   # rules.EDGE_CLEARANCE; no tracks under rules.TRACK_MIN
 cp "pcb/.work/$v/autoroute.ses" "pcb/$v/autoroute.ses"
 python3 -c 'import hashlib,json,sys; v,passes=sys.argv[1:]; t=json.load(open("toolchain.lock.json"))["freerouting"]
json.dump({"dsn_sha256":hashlib.sha256(open(f"pcb/.work/{v}/board.dsn","rb").read()).hexdigest(),
 "freerouting":t["version"],"max_passes":int(passes)},open(f"pcb/{v}/autoroute.json","w"),indent=2); open(f"pcb/{v}/autoroute.json","a").write("\n")' "$v" "$passes"
done
