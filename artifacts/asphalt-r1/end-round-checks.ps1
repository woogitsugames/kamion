$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
# Start only after the metric/comparison queue has terminated: no parallel jobs with the same heavy owner.
$slot = 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/gpt-asphalt-r1.slot'
if (Test-Path $slot) { throw 'Own heavy slot is still active; finish the earlier queue first.' }
if (-not (Test-Path artifacts/asphalt-r1/comparison-candidate2.json)) { throw 'Finish candidate2 comparisons first.' }
$results = [ordered]@{}
& pwsh artifacts/asphalt-r1/run-heavy.ps1 -Stage Fidelity -Label candidate2
$results.fidelity = $LASTEXITCODE
& pwsh artifacts/asphalt-r1/run-heavy.ps1 -Stage PhysicsGate3 -Label candidate2 -EndOfRound
$results.physics_gate3 = $LASTEXITCODE
& pwsh artifacts/asphalt-r1/run-gis.ps1 -Label candidate2-final -EndOfRound
$results.gis = $LASTEXITCODE
$results.finished_at = Get-Date -Format o
$results | ConvertTo-Json | Set-Content artifacts/asphalt-r1/end-round-checks.json
Add-Content artifacts/asphalt-r1/STATUS.md "$(Get-Date -Format o): Końcowa kolejka sprawdzeń zakończona. Kody wyjścia zapisane w end-round-checks.json; nie są wizualnym PASS. Następny krok: końcowy REPORT, robocopy do main i r2."
git add -f artifacts/asphalt-r1/end-round-checks.json artifacts/asphalt-r1/STATUS.md
git commit -m 'wip(asphalt): checkpoint all final round checks'
