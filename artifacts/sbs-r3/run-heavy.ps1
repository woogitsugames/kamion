param(
    [Parameter(Mandatory)][ValidateSet('PrepareDiagnostics','ComposeDiagnostics','PrepareRefinement','ComposeRefinement','TestFile','Audit','Fidelity','FinalGis')][string]$Task,
    [string]$TestFile,
    [switch]$EndOfRound
)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Push-Location $root
try {
    $owner=(& git branch --show-current).Trim()
    if($owner -ne 'gpt-sbs-r3'){throw 'Expected r3 branch'}
    if($Task -eq 'FinalGis' -and !$EndOfRound){throw 'Full GIS only at end of round'}
    if($Task -eq 'TestFile' -and (!$TestFile -or !(Test-Path -LiteralPath $TestFile -PathType Leaf))){throw 'Single existing test file required'}
    $slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
    pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 1 -StaleHours 87600
    if($LASTEXITCODE -ne 0){throw 'Heavy lease failed'}
    try {
        $env:PYTHONUNBUFFERED='1'
        switch($Task) {
            PrepareDiagnostics {
                uv run --project tools/refs python artifacts/sbs-r3/make-gantry-probes.py
                if($LASTEXITCODE -ne 0){throw 'Gantry preparation failed'}
                uv run --project tools/worldgen python artifacts/sbs-r3/sample-bridge-surfaces.py
            }
            ComposeDiagnostics {uv run --project tools/refs python artifacts/sbs-r3/compose-gantry-probes.py}
            PrepareRefinement {uv run --project tools/refs python artifacts/sbs-r3/make-refinement1.py}
            ComposeRefinement {uv run --project tools/refs python artifacts/sbs-r3/compose-refinement1.py}
            TestFile {uv run --project tools/worldgen python -m pytest $TestFile -q}
            Audit {uv run --project tools/refs python artifacts/sbs-r3/audit_final.py}
            Fidelity {
                uv run --project tools/refs python artifacts/sbs-r3/audit_sheets.py
                if($LASTEXITCODE -ne 0){throw 'Sheet audit failed'}
                uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art artifacts/sbs-r3/fidelity
            }
            FinalGis {uv run --project tools/worldgen python -m pytest tests/gis -q}
        }
        if($LASTEXITCODE -ne 0){throw "Task $Task failed with $LASTEXITCODE"}
    } finally {pwsh -NoProfile -File $slot -Release -Pool heavy -Owner $owner}
} finally {Pop-Location}


