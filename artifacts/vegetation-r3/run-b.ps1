$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. artifacts/vegetation-r3/checkpoint.ps1
function Check-Step([string]$Step, [int]$Code) {
    Add-Content artifacts/vegetation-r3/STATUS.md "Wariant B, $Step zakończone kodem $Code. Następny etap zgodnie z run-b.ps1; po probe konieczna ocena obrazów i kosztów."
    Save-VegetationCheckpoint -Message "wip(vegetation): B $Step kod $Code"
    if ($Code -ne 0) { throw "B $Step failed: $Code" }
}
pwsh artifacts/vegetation-r3/heavy-task.ps1 -Task World *> artifacts/vegetation-r3/after-world-b.log
Check-Step 'generator' $LASTEXITCODE
uv run --project tools/worldgen python artifacts/vegetation-r3/verify_world.py *> artifacts/vegetation-r3/verify-b.log
Check-Step 'QA instancji i GLB' $LASTEXITCODE
uv run --project tools/worldgen python artifacts/vegetation-r3/snapshot.py candidate-b
Check-Step 'migawka' $LASTEXITCODE
pwsh artifacts/vegetation-r3/import-safe.ps1 -Log artifacts/vegetation-r3/import-b.log *> artifacts/vegetation-r3/import-b-runner.log
Check-Step 'import' $LASTEXITCODE
pwsh artifacts/vegetation-r3/probe-low.ps1 *> artifacts/vegetation-r3/probe-b-runner.log
Check-Step 'probe Low B120' $LASTEXITCODE
