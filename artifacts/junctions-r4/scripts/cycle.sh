#!/usr/bin/env bash
# full iteration: loop.sh <tag> (build ... pytest) and, as soon as the world is exported, unity.sh <tag> [low]
set -u
cd "$(dirname "$0")/../../.."
TAG=$1
(bash artifacts/junctions-r4/scripts/loop.sh $TAG > artifacts/junctions-r4/logs/${TAG}_loop.out 2>&1 &)
while ! grep -q "world ready\|build rc [1-9]" artifacts/junctions-r4/logs/${TAG}_loop.out 2>/dev/null; do sleep 10; done
if grep -q "build rc 0" artifacts/junctions-r4/logs/${TAG}_loop.out; then
  bash artifacts/junctions-r4/scripts/unity.sh $TAG ${2:-} > artifacts/junctions-r4/logs/${TAG}_unity.out 2>&1
fi
