$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$slotScript='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
Push-Location $taskRoot
try {
    $owner=(& git branch --show-current).Trim()
    $history='artifacts/sbs-r2/history/sbs-r1/evidence'
    $inputs=Join-Path $history 'inputs'
    New-Item -ItemType Directory -Force $inputs | Out-Null
    # ZIP contains the original captured bytes, unaffected by Git newline conversion.
    Expand-Archive -LiteralPath artifacts/sbs-r1/evidence/inputs.zip -DestinationPath $inputs -Force
    Copy-Item -LiteralPath Data/Regions/bialystok-industrial-c/sbs_photometry.json -Destination (Join-Path $inputs 'sbs_photometry.json')
    $photometry=Join-Path $inputs 'sbs_photometry.json'
    pwsh -NoProfile -File $slotScript -Acquire -Pool heavy -Owner $owner -PollSeconds 7 -StaleHours 87600
    if($LASTEXITCODE -ne 0){throw 'Heavy acquisition failed'}
    try {
        foreach($state in @('Low-overcast','Low-clear','High-overcast','High-clear')){
            $raw=Join-Path artifacts/sbs-r1/evidence/renders $state
            uv run --project tools/refs python tools/refs/sbs_gate3.py compose --renders $raw --output (Join-Path $history "sheets/$state") --historical --inputs $inputs --photometry $photometry
            if($LASTEXITCODE -ne 0){throw "Historical metrics failed: $state"}
            uv run --project tools/refs python tools/refs/sbs_gate3.py compose --renders $raw --output (Join-Path $history "diagnostics/$state") --historical --inputs $inputs --photometry $photometry --include-rejected
            if($LASTEXITCODE -ne 0){throw "Historical diagnostics failed: $state"}
        }
        Compress-Archive -Path "$inputs/*" -DestinationPath (Join-Path $history 'inputs.zip') -Force
    } finally {pwsh -NoProfile -File $slotScript -Release -Pool heavy -Owner $owner}
} finally {Pop-Location}
