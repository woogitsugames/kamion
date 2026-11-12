#!/usr/bin/env bash
# dbg.sh <out.log> <E,N,R>...: heavy slot -> dbg_rails.py (records every guardrail run to rails.pkl) -> release
cd "$(dirname "$0")/../../.."
MAIN=/c/Users/matma/Documents/Claude/kamion
O=$1; shift
pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner claude-junctions-r7 > /dev/null
uv run --project tools/worldgen python artifacts/junctions-r7/scripts/dbg_rails.py "$@" > $O 2>&1; echo "rc $?" >> $O
pwsh $MAIN/scripts/unity-slot.ps1 -Release -Pool heavy -Owner claude-junctions-r7 > /dev/null
