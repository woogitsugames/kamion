$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. artifacts/vegetation-r4/checkpoint.ps1
function Check-Step([string]$Step,[int]$Code) {
    Add-Content artifacts/vegetation-r4/STATUS.md "Świeży baseline r4: $Step kod $Code. Produkcja bez zmian; kolejny etap zgodnie z baseline.ps1."
    Save-VegetationCheckpoint -Message "wip(vegetation): r4 baseline $Step kod $Code"
    if ($Code -ne 0) { throw "R4 baseline $Step failed: $Code" }
}
uv run --project tools/worldgen python artifacts/vegetation-r4/prepare_photo_cameras.py *> artifacts/vegetation-r4/prepare-photos.log
Check-Step 'przygotowanie fotografii i kamer' $LASTEXITCODE
pwsh artifacts/vegetation-r4/heavy-task.ps1 -Task Materials *> artifacts/vegetation-r4/before-materials.log
Check-Step 'materiały przez heavy' $LASTEXITCODE
pwsh artifacts/vegetation-r4/heavy-task.ps1 -Task World *> artifacts/vegetation-r4/before-world.log
Check-Step 'świat przez heavy' $LASTEXITCODE
uv run --project tools/worldgen python artifacts/vegetation-r4/snapshot.py baseline
Check-Step 'migawka świata i źródeł' $LASTEXITCODE
uv run --project tools/worldgen python artifacts/vegetation-r4/verify_baseline.py *> artifacts/vegetation-r4/verify-baseline.log
Check-Step 'QA Megascans i wejść' $LASTEXITCODE
pwsh artifacts/vegetation-r4/import-safe.ps1 -Log artifacts/vegetation-r4/import-before.log *> artifacts/vegetation-r4/import-before-runner.log
Check-Step 'import przez Unity slot' $LASTEXITCODE
pwsh artifacts/vegetation-r4/render-matrix.ps1 -Stage before *> artifacts/vegetation-r4/before-matrix.log
Check-Step 'świeże kamery kontrolne' $LASTEXITCODE
pwsh artifacts/vegetation-r4/render-photos.ps1 -Stage before *> artifacts/vegetation-r4/before-photos.log
Check-Step 'świeże kamery fotograficzne B' $LASTEXITCODE
Set-Content artifacts/vegetation-r4/baseline.done 'Fresh baseline ready; review frames before applying candidate.'
