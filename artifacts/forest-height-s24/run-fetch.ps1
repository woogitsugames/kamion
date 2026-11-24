# forest-height-s24: canopy height models of the remaining tiles of the Bialystok - Knyszyn - Tykocin route (one at a time)
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\forest-height-s24'
Set-Location $wt
$ids = @('dk65-01','dk65-02','dk65-03','dk65-06','dk65-07','dk65-08','dk65-09','dk65-10','dk65-11','knyszyn','knyszyn-s','knyszyn-w',
         'dw671-tykocin-01','dw671-tykocin-02','dw671-tykocin-04','dw671-tykocin-05','dw671-tykocin-06','dw671-tykocin-07','dw671-tykocin-08','dw671-tykocin-09','tykocin')
foreach ($r in $ids) {
    if (Test-Path "Data/Regions/$r/forest_chm.json") { continue }
    uv run --project tools/worldgen python -u tools/worldgen/streetscape/forest_chm.py --region $r *>> artifacts/forest-height-s24/chm-fetch-route.log
    "$r exit $LASTEXITCODE" >> artifacts/forest-height-s24/chm-fetch-route.status
}
"FETCH DONE" >> artifacts/forest-height-s24/chm-fetch-route.status
