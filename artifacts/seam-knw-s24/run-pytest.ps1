$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\seam-knw-s24'
Set-Location $wt
$log = "$wt\artifacts\seam-knw-s24\pytest.log"
$env:PYTHONIOENCODING = 'utf-8'
pwsh C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1 -Acquire -Pool heavy -Owner seam-knw-s24-pytest *>> $log
try {
  uv run --project tools/worldgen python -m pytest -q -p no:cacheprovider tests/gis/test_seam_shear_knw.py tests/gis/test_seams_0224.py tests/gis/test_seam_taper_0275.py tests/gis/test_seams_fix_s23.py tests/gis/test_seams_p3_0304.py tests/gis/test_roundabout_0274.py tests/gis/test_road_widen_0306.py tests/gis/test_compact_roundabout_0218.py tests/gis/test_lane_edges.py tests/gis/test_dk65_seam_knyszyn_0233.py tests/gis/test_route_links_s23.py tests/gis/test_road_consistency.py tests/gis/test_unit_meshing_chunks.py *>> $log
  "pytest exit $LASTEXITCODE" | Add-Content $log
} finally {
  pwsh C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1 -Release -Pool heavy -Owner seam-knw-s24-pytest *>> $log
  Set-Content "$wt\artifacts\seam-knw-s24\pytest.exit" 'done'
}
