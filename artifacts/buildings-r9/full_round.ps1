param([string]$Round, [string]$Configs = 'Low:overcast,High:overcast', [switch]$NoExtraLow, [switch]$SkipImport)
# import + control cameras (run_round) + review cameras High (extra) and Low (extra_low). Run from anywhere.
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
if ($SkipImport) { pwsh artifacts/buildings-r9/run_round.ps1 -Round $Round -Configs $Configs -SkipImport *> "artifacts/buildings-r9/$Round.round.out" }
else { pwsh artifacts/buildings-r9/run_round.ps1 -Round $Round -Configs $Configs *> "artifacts/buildings-r9/$Round.round.out" }
uv run --project tools/worldgen python artifacts/buildings-r9/cams_r16.py *>> "artifacts/buildings-r9/$Round.round.out"   # r2: cameras follow the plots of this world
# NOTE (r2): -Scene WorldC is the LOW-content scene; 'High' here = Low content at High quality (comparable with base / r1).
# extra_hc = the real High content (WorldC_High).
pwsh artifacts/buildings-r9/extra.ps1 -Round $Round -Tier High -Sub extra *>> "artifacts/buildings-r9/$Round.round.out"
if (-not $NoExtraLow) { pwsh artifacts/buildings-r9/extra.ps1 -Round $Round -Tier Low -Sub extra_low *>> "artifacts/buildings-r9/$Round.round.out" }
pwsh artifacts/buildings-r9/extra.ps1 -Round $Round -Scene WorldC_High -Tier High -Sub extra_hc *>> "artifacts/buildings-r9/$Round.round.out"
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings 2>$null
'full round done' | Tee-Object -Append "artifacts/buildings-r9/$Round/round.log"
