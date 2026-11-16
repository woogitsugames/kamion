$ErrorActionPreference='Continue'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen2-s23'
function L($m){ "$m $(Get-Date -Format s)" | Add-Content 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen2-s23\artifacts\c-regen2-s23\stage2-chain.status' }
L 'chain start (lider s23)'
pwsh -NoProfile -File 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen2-s23\artifacts\c-regen2-s23\tools\00-prep.ps1'; L "00-prep exit=$LASTEXITCODE"
if (-not (Test-Path 'artifacts/c-regen2-s23/prep/prep.done')) { L 'STOP: brak prep.done'; exit 1 }
pwsh -NoProfile -File 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen2-s23\artifacts\c-regen2-s23\tools\10-before.ps1' -Mode Reuse; L "10-before(Reuse) exit=$LASTEXITCODE"
if (-not (Test-Path 'artifacts/c-regen2-s23/before/before.done')) { L 'STOP: brak before.done'; exit 1 }
pwsh -NoProfile -File 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen2-s23\artifacts\c-regen2-s23\tools\20-regen.ps1'; L "20-regen exit=$LASTEXITCODE"
if (-not (Test-Path 'artifacts/c-regen2-s23/regen/regen.done')) { L 'STOP: regen nie zielony (build_world albo budzet) - decyzja lidera'; exit 1 }
pwsh -NoProfile -File 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen2-s23\artifacts\c-regen2-s23\tools\40-unity.ps1'; L "40-unity exit=$LASTEXITCODE"
pwsh -NoProfile -File 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen2-s23\artifacts\c-regen2-s23\tools\50-pytest.ps1'; L "50-pytest exit=$LASTEXITCODE"
L 'CHAIN END'
