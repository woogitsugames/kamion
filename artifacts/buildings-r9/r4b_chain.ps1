param([string]$Round = 'r4b')
# s15 r4b (leader: garden trees "tier": "high" not drawn on Low): re-import only (products of r4), Low overcast control
# cameras, Low + High review cameras, EditMode. Log: <round>/round.log (ends with CHAIN DONE).
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
$A = 'artifacts/buildings-r9'
New-Item -ItemType Directory -Force "$A/$Round" | Out-Null
pwsh $A/run_round.ps1 -Round $Round -Configs 'Low:overcast' *> "$A/$Round.round.out"
pwsh $A/extra.ps1 -Round $Round -Tier Low -Sub extra_low -Only 'r17_street_0a,r17_street_1a,r17_street_3a,r17_over_0,r16_drive_0,r16_garden_2,r16_cab_1,r14_plots_aerial_low' *>> "$A/$Round.round.out"
pwsh $A/extra.ps1 -Round $Round -Scene WorldC_High -Tier High -Sub extra_hc -Only 'r17_street_0a,r17_over_0,r17_street_3a' *>> "$A/$Round.round.out"
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings 2>$null
'ROUND DONE' | Tee-Object -Append "$A/$Round/round.log"
pwsh $A/editmode.ps1 -Round $Round
'CHAIN DONE' | Add-Content "$A/$Round/round.log"
