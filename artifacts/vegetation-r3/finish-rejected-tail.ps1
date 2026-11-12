$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. artifacts/vegetation-r3/checkpoint.ps1
function Check-Step([string]$Step,[int]$Code) {
    Add-Content artifacts/vegetation-r3/STATUS.md "Dokończenie r3: $Step kod $Code. Produkcja przywrócona do r1, brak zaakceptowanej korekty B8."
    Save-VegetationCheckpoint -Message "wip(vegetation): końcówka r3 $Step kod $Code"
    if ($Code -ne 0) { throw "R3 tail $Step failed: $Code" }
}
pwsh artifacts/vegetation-r3/probe-restored.ps1 *> artifacts/vegetation-r3/probe-restored-runner.log
Check-Step 'ponowiony probe przywróconego świata' $LASTEXITCODE
uv run --project tools/worldgen python artifacts/vegetation-r3/verify_restored.py probe *> artifacts/vegetation-r3/verify-restored-probe.log
Check-Step 'zgodność obrazu z baseline' $LASTEXITCODE
pwsh artifacts/vegetation-r3/editmode-safe.ps1 *> artifacts/vegetation-r3/editmode-final.log
Check-Step 'EditMode' $LASTEXITCODE
Set-Content artifacts/vegetation-r3/finish-rejected.done 'Done; inspect final logs and proofs before REPORT.'
