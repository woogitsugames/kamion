$wt='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\forest2-s24'; Set-Location $wt; $a="$wt\artifacts\forest2-s24"
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner forest2-s24
try {
  uv run --project tools/worldgen python -m pytest tests/gis/test_forest_chm_0339.py tests/gis/test_forest_0187.py tests/gis/test_world_v31.py tests/gis/test_world_v34.py tests/gis/test_house_greenery_0163.py tests/gis/test_budget_0221.py tests/gis/test_trees_0308.py tests/gis/test_streetscape.py tests/gis/test_dense_lod_0282.py (Get-ChildItem tests/gis -Filter *0173*.py | % FullName) -q -p no:cacheprovider *> "$a\pytest-forest-r1.log"
  "pytest exit $LASTEXITCODE" >> "$a\pytest-forest-r1.status"
} finally { pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner forest2-s24 }
