# c-regen2-s23 stage 2, step 4: full pytest tests/gis after the regeneration (heavy slot; c-regen-s22: 32 min) + perf tests.
# Expected after the rebuild: test_gate3_landmarks::test_every_gate3_sign_is_placed RUNS (no skip, ADR 0236).
# Known red on main (not regressions): forest_0187 edge texture, road_fidelity stale, world_v31 forest HLOD - compare by name.
. "$PSScriptRoot/_common.ps1"
Init-Status "$Art/regen" 'pytest.status'
Slot-Acquire heavy "$Name-pytest"
try {
    Step 'pytest-gis' { uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider -o faulthandler_timeout=600 -rfEs }
    Step 'pytest-perf' { uv run --project tools/perf python -m pytest tools/perf/tests -q -p no:cacheprovider }
} finally { Slot-Release heavy "$Name-pytest" }
Select-String -Path "$O/pytest-gis.log" -Pattern '^(FAILED|ERROR|SKIPPED)|passed|failed' | Select-Object -Last 40 | ForEach-Object { $_.Line } | Set-Content "$O/pytest-gis.summary.txt"
"DONE $(Get-Date -Format s)" | Add-Content $St
