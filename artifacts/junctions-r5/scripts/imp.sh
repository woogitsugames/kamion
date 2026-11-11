#!/usr/bin/env bash
# imp.sh <tag> : wait for locks -> import-region -> Low clear + High overcast renders of the junction cameras
set -u
cd "$(dirname "$0")/../../.."
TAG=$1
L=artifacts/junctions-r5/logs
LOCKS=/c/Users/matma/Documents/Claude/kamion/artifacts/locks
while [ -e $LOCKS/PHONE_RUN ] || [ -e $LOCKS/GPT_UNITY_HOLD ]; do sleep 60; done
echo "import start $(date +%H:%M)"
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c > $L/${TAG}_import.log 2>&1; echo "import rc $? $(date +%H:%M)"
bash artifacts/junctions-r5/scripts/qa.sh $TAG Low clear
bash artifacts/junctions-r5/scripts/qa.sh $TAG High overcast
