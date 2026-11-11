param([string]$Rounds = 'base,r1', [string]$Configs = 'Low:overcast,High:overcast,High:clear')
# For every round: restore its generator snapshot (snap.ps1) -> import + control cameras (run_round.ps1) -> review
# cameras (extra.ps1). Waits for the Unity locks inside. Do not run the generator while this runs.
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
foreach ($r in $Rounds.Split(',')) {
    pwsh artifacts/buildings-r15/snap.ps1 -Name $r -Restore
    pwsh artifacts/buildings-r15/run_round.ps1 -Round $r -Configs $Configs *> "artifacts/buildings-r15/$r.out"
    pwsh artifacts/buildings-r15/extra.ps1 -Round $r *>> "artifacts/buildings-r15/$r.out"
}
'seq done'
