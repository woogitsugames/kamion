param([string]$Round, [string]$Configs = 'Low:overcast,High:overcast', [switch]$NoExtraLow, [switch]$SkipImport)
# import + control cameras (run_round) + review cameras High (extra) and Low (extra_low). Run from anywhere.
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
if ($SkipImport) { pwsh artifacts/buildings-r16/run_round.ps1 -Round $Round -Configs $Configs -SkipImport *> "artifacts/buildings-r16/$Round.round.out" }
else { pwsh artifacts/buildings-r16/run_round.ps1 -Round $Round -Configs $Configs *> "artifacts/buildings-r16/$Round.round.out" }
pwsh artifacts/buildings-r16/extra.ps1 -Round $Round -Tier High -Sub extra *>> "artifacts/buildings-r16/$Round.round.out"
if (-not $NoExtraLow) { pwsh artifacts/buildings-r16/extra.ps1 -Round $Round -Tier Low -Sub extra_low *>> "artifacts/buildings-r16/$Round.round.out" }
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings 2>$null
'full round done' | Tee-Object -Append "artifacts/buildings-r16/$Round/round.log"
