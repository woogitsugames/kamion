param([ValidateSet('Import','Capture','Test','Probe')][string]$Stage, [string]$Label = 'baseline',
    [string]$Cameras='', [ValidateSet('Low','High')][string]$ProbeTier='Low',
    [ValidateSet('clear','overcast')][string]$ProbeLighting='overcast')
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $repo
$env:KAMION_ARTIFACTS_DIR = Join-Path $repo 'artifacts'
$slotScript = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
function Invoke-Slotted([scriptblock]$Action) {
    & pwsh $slotScript -Acquire -Owner gpt-asphalt -PollSeconds 5
    if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
    try {
        & $Action
        if ($LASTEXITCODE -ne 0) { throw "Unity stage failed: $LASTEXITCODE" }
    } finally {
        & pwsh $slotScript -Release -Owner gpt-asphalt
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
}
if ($Stage -eq 'Import') {
    # import-region.ps1 can silently invoke Python builders. Require their outputs before taking a Unity slot.
    if (-not (Test-Path Data/raw/derived/bialystok-industrial-c/world/chunk_0_0.glb) -or
        -not (Test-Path Data/Regions/bialystok-industrial-c/route_start.json)) {
        throw 'Run the world producer under a heavy slot before importing.'
    }
    $matRoot = 'art-source/world/materials'
    $spec = Get-Content "$matRoot/materials_spec.json" -Raw | ConvertFrom-Json
    $srcTime = (Get-ChildItem "$matRoot/_src" -Filter '*.py' | Measure-Object LastWriteTimeUtc -Maximum).Maximum
    foreach ($p in $spec.sets.PSObject.Properties) {
        $files = $p.Value.files.Medium
        if (-not $files) { continue }
        foreach ($name in $files.files) {
            $png = Join-Path $matRoot "$($files.dir)/$name"
            if (-not (Test-Path $png) -or (Get-Item $png).LastWriteTimeUtc -lt $srcTime) {
                throw 'Run the required material producer under a heavy slot before importing.'
            }
        }
    }
    Invoke-Slotted { & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c }
} elseif ($Stage -eq 'Test') {
    Invoke-Slotted { & pwsh scripts/test.ps1 -Platform EditMode }
} elseif ($Stage -eq 'Probe') {
    if (-not $Cameras) { throw 'Specify the exact camera IDs for a pose probe.' }
    $out = "artifacts/asphalt-r3/$Label/$ProbeTier-$ProbeLighting"
    $env:KAMION_ASPHALT_QA_STATE = '1'
    $env:KAMION_ASPHALT_QA_DIRECTORY = [IO.Path]::GetFullPath($out, $repo)
    try {
        Invoke-Slotted {
            & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $ProbeTier -Lighting $ProbeLighting -Cameras $Cameras -Gate3 artifacts/asphalt-r3/cameras.json -OutputDir $out
        }
    } finally {
        $env:KAMION_ASPHALT_QA_STATE = $null
        $env:KAMION_ASPHALT_QA_DIRECTORY = $null
    }
    Add-Content artifacts/asphalt-r3/STATUS.md "$(Get-Date -Format o): Zapisano próbę pozy $out dla $Cameras; nie jest to pełny baseline ani końcowy komplet kamer."
    git add -f artifacts/asphalt-r3/STATUS.md
    git commit -m "wip(asphalt): checkpoint selected-camera pose probe $Label"
} else {
    foreach ($tier in @('Low','High')) {
        foreach ($lighting in @('overcast','clear')) {
            $out = "artifacts/asphalt-r3/$Label/$tier-$lighting"
            $env:KAMION_ASPHALT_QA_STATE = '1'
            $env:KAMION_ASPHALT_QA_DIRECTORY = [IO.Path]::GetFullPath($out, $repo)
            try {
                Invoke-Slotted {
                    & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $lighting -Gate3 artifacts/asphalt-r3/cameras.json -OutputDir $out
                }
            } finally {
                $env:KAMION_ASPHALT_QA_STATE = $null
                $env:KAMION_ASPHALT_QA_DIRECTORY = $null
            }
            Add-Content artifacts/asphalt-r3/STATUS.md "$(Get-Date -Format o): zapisano $out. Następny krok: pozostałe serie lub porównanie wariantu."
            git add -f artifacts/asphalt-r3/STATUS.md
            git commit -m "wip(asphalt): checkpoint $Label $tier $lighting capture"
        }
    }
}
