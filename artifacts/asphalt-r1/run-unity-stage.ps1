param([ValidateSet('Import','Capture','Test')][string]$Stage, [string]$Label = 'baseline')
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $repo
$env:KAMION_ARTIFACTS_DIR = Join-Path $repo 'artifacts'
function Invoke-Slotted([scriptblock]$Action) {
    & pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-asphalt -PollSeconds 5
    if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
    try {
        & $Action
        if ($LASTEXITCODE -ne 0) { throw "Unity stage failed: $LASTEXITCODE" }
    } finally {
        & pwsh scripts/unity-slot.ps1 -Release -Owner gpt-asphalt
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
}
if ($Stage -eq 'Import') {
    Invoke-Slotted { & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c }
} elseif ($Stage -eq 'Test') {
    Invoke-Slotted { & pwsh scripts/test.ps1 -Platform EditMode }
} else {
    foreach ($tier in @('Low','High')) {
        foreach ($lighting in @('overcast','clear')) {
            $out = "artifacts/asphalt-r1/$Label/$tier-$lighting"
            Invoke-Slotted {
                & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $lighting -Gate3 artifacts/asphalt-r1/cameras.json -OutputDir $out
            }
            Add-Content artifacts/asphalt-r1/STATUS.md "$(Get-Date -Format o): zapisano $out. Następny krok: pozostałe serie lub porównanie wariantu."
            git add -f artifacts/asphalt-r1/STATUS.md
            git commit -m "wip(asphalt): checkpoint $Label $tier $lighting capture"
        }
    }
}
