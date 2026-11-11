#!/usr/bin/env bash
# cycle2.sh <tag>: loop.sh <tag> in the background; when the world is exported: imp.sh <tag> (import + Low clear + High overcast)
set -u
cd "$(dirname "$0")/../../.."
TAG=$1
(bash artifacts/junctions-r5/scripts/loop.sh $TAG > artifacts/junctions-r5/logs/${TAG}_loop.out 2>&1 &)
while ! grep -q "world ready\|build rc [1-9]" artifacts/junctions-r5/logs/${TAG}_loop.out 2>/dev/null; do sleep 10; done
grep -q "build rc 0" artifacts/junctions-r5/logs/${TAG}_loop.out && bash artifacts/junctions-r5/scripts/imp.sh $TAG
while ! grep -q "loop done" artifacts/junctions-r5/logs/${TAG}_loop.out; do sleep 10; done
cat artifacts/junctions-r5/logs/${TAG}_loop.out
