# base (= main import copied from the main checkout): control cameras Low + review cameras (High content, Low)
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
pwsh artifacts/buildings-r9/run_round.ps1 -Round base -Configs 'Low:overcast' -SkipImport *> artifacts/buildings-r9/base.round.out
uv run --project tools/worldgen python artifacts/buildings-r9/cams_r16.py *>> artifacts/buildings-r9/base.round.out
pwsh artifacts/buildings-r9/extra.ps1 -Round base -Scene WorldC_High -Tier High -Sub extra_hc *>> artifacts/buildings-r9/base.round.out
pwsh artifacts/buildings-r9/extra.ps1 -Round base -Tier Low -Sub extra_low *>> artifacts/buildings-r9/base.round.out
'BASE DONE' | Tee-Object -Append artifacts/buildings-r9/base/round.log
