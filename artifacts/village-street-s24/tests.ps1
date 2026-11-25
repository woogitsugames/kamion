# village-street-s24: pytest tests/gis for roads under a heavy slot. -Set quick | long
param([ValidateSet('quick', 'long')][string]$Set = 'quick')
$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\agent-a4f5b23b7d6760aa7'
$a = 'artifacts/village-street-s24'
New-Item -ItemType Directory -Force "$a/logs" | Out-Null
$quick = @('test_village_street_0349.py', 'test_ring_0231.py', 'test_rural_xsec_0272.py', 'test_lanes_audit_0301.py',
           'test_knyszyn_look_s23.py', 'test_pavements_0237.py', 'test_knyszyn_sidewalks_d38.py', 'test_seam_taper_0275.py',
           'test_seams_0224.py', 'test_seams_fix_s23.py', 'test_seams_p3_0304.py', 'test_road_widen_0306.py',
           'test_hero_bridge.py', 'test_truss_bridge_0320.py', 'test_unit_determinism.py', 'test_dom_klattow_0305.py')
$long = @('test_world_roads.py', 'test_budget_0221.py', 'test_determinism.py')
$files = (($Set -eq 'quick') ? $quick : $long) | ForEach-Object { "tests/gis/$_" }
$owner = "village-street-s24-t$Set"
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $owner
try {
    uv run --project tools/worldgen pytest @files -q -p no:cacheprovider *> "$a/logs/pytest-$Set.log"
    "pytest $Set exit $LASTEXITCODE"
} finally { pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner }
Get-Content "$a/logs/pytest-$Set.log" -Tail 25
"DONE tests $Set"
