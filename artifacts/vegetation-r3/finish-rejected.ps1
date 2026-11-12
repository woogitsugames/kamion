$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. artifacts/vegetation-r3/checkpoint.ps1
function Check-Step([string]$Step, [int]$Code) {
    Add-Content artifacts/vegetation-r3/STATUS.md "Zamknięcie odrzuconej r3: $Step kod $Code. Kod produkcyjny przywrócony do r1; brak akceptowanej korekty B8."
    Save-VegetationCheckpoint -Message "wip(vegetation): zamknięcie r3 $Step kod $Code"
    if ($Code -ne 0) { throw "R3 $Step failed: $Code" }
}
pwsh artifacts/vegetation-r3/heavy-task.ps1 -Task World *> artifacts/vegetation-r3/final-world.log
Check-Step 'generator przywróconego kodu' $LASTEXITCODE
uv run --project tools/worldgen python artifacts/vegetation-r3/snapshot.py restored
Check-Step 'migawka przywróconego świata' $LASTEXITCODE
pwsh artifacts/vegetation-r3/heavy-task.ps1 -Task GisFinal *> artifacts/vegetation-r3/pytest-final.log
$gisExit = $LASTEXITCODE
Add-Content artifacts/vegetation-r3/STATUS.md "Pełny końcowy GIS kod $gisExit; szczegóły pytest-final.log. Znana porażka starego fidelity wymaga osobnej weryfikacji, nie naprawiania cudzej dziedziny."
Save-VegetationCheckpoint -Message "wip(vegetation): końcowy GIS r3 kod $gisExit"
pwsh artifacts/vegetation-r3/import-safe.ps1 -Log artifacts/vegetation-r3/import-restored.log *> artifacts/vegetation-r3/import-restored-runner.log
Check-Step 'import przywróconego świata' $LASTEXITCODE
pwsh artifacts/vegetation-r3/probe-restored.ps1 *> artifacts/vegetation-r3/probe-restored-runner.log
Check-Step 'probe przywróconego świata' $LASTEXITCODE
pwsh artifacts/vegetation-r3/editmode-safe.ps1 *> artifacts/vegetation-r3/editmode-final.log
Check-Step 'EditMode' $LASTEXITCODE
Set-Content artifacts/vegetation-r3/finish-rejected.done 'Done; inspect logs and restored hashes before REPORT.'
