# c-regen3-s23: after the OD-005 override (added after the rebuild, no rebuild of C): refresh the fidelity report of C
# (its inputs hash covers overrides.yaml) and run the full pytest again on the final tree.
. "$PSScriptRoot/_common.ps1"
Init-Status "$Art/regen" 'final.status'
Assert-Branch
Slot-Acquire heavy "$Name-final"
try {
    Step 'fidelity2-bialystok-industrial-c' { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c }
    Step 'pytest-gis2' { uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider -o faulthandler_timeout=600 -rfEs }
} finally { Slot-Release heavy "$Name-final" }
git status --porcelain *> "$O/git-status-final.txt"
"DONE $(Get-Date -Format s)" | Add-Content $St
