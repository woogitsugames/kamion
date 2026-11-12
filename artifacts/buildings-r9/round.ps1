param([string]$Round, [switch]$SkipWorld, [switch]$SkipImport, [switch]$NoLowExtra, [string]$Only = '')
# One full visual round: build_world (heavy slot) -> import + control cameras Low overcast -> review cameras
# (extra_hc = High content, extra_low = Low tier). Run from anywhere. Log: <round>/round.log, <round>.round.out
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
$A = 'artifacts/buildings-r9'
New-Item -ItemType Directory -Force "$A/$Round" | Out-Null
if (-not $SkipWorld) {
    pwsh $A/world.ps1 -Round $Round *> "$A/$Round.world.out"
    if (-not (Select-String -Path "$A/$Round/round.log" -Pattern 'build_world exit 0' -Quiet)) { 'ROUND STOP: build_world failed' | Tee-Object -Append "$A/$Round/round.log"; exit 1 }
    'WORLD DONE' | Add-Content "$A/$Round/round.log"
}
if ($SkipImport) { pwsh $A/run_round.ps1 -Round $Round -Configs 'Low:overcast' -SkipImport *> "$A/$Round.round.out" }
else { pwsh $A/run_round.ps1 -Round $Round -Configs 'Low:overcast' *> "$A/$Round.round.out" }
'IMPORT DONE' | Add-Content "$A/$Round/round.log"
uv run --project tools/worldgen python $A/cams_r16.py *>> "$A/$Round.round.out"
if ($Only) { pwsh $A/extra.ps1 -Round $Round -Scene WorldC_High -Tier High -Sub extra_hc -Only $Only *>> "$A/$Round.round.out" }
else { pwsh $A/extra.ps1 -Round $Round -Scene WorldC_High -Tier High -Sub extra_hc *>> "$A/$Round.round.out" }
if (-not $NoLowExtra) { pwsh $A/extra.ps1 -Round $Round -Tier Low -Sub extra_low *>> "$A/$Round.round.out" }
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings 2>$null
'ROUND DONE' | Tee-Object -Append "$A/$Round/round.log"
