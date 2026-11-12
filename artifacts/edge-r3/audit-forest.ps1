$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$slot = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$owner = (git branch --show-current).Trim()
if ($owner -ne 'gpt-edge-r3') { throw 'Unexpected owner' }
& pwsh -File $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 2 -StaleHours 100000
if ($LASTEXITCODE -ne 0) { throw 'Heavy acquisition failed' }
$code = 1
try {
    & uv run --project tools/worldgen python "$PSScriptRoot/audit_forest_bases.py"
    $code = $LASTEXITCODE
} finally {
    & pwsh -File $slot -Release -Pool heavy -Owner $owner -StaleHours 100000
    @{task='CorrectedForestBaseAudit';owner=$owner;pool='heavy';exit_code=$code;finished=(Get-Date -Format o)} |
        ConvertTo-Json | Set-Content "$PSScriptRoot/corrected-forest-receipt.json"
}
exit $code
