param(
    [Parameter(Mandatory)][ValidateSet('World','Materials','Fidelity','TestFile','FinalGis','PrepareSbs','ComposeSbs')][string]$Task,
    [string]$TestFile,
    [string]$Only,
    [string]$RenderDir,
    [string]$OutputDir,
    [switch]$IncludeRejected,
    [switch]$Historical,
    [string]$Inputs,
    [string]$Landmarks,
    [switch]$EndOfRound
)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$slotScript='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
Push-Location $taskRoot
try {
    $owner=(& git branch --show-current).Trim()
    if($Task -eq 'FinalGis' -and !$EndOfRound){throw 'Pełny GIS tylko na końcu rundy: wymagane -EndOfRound'}
    if($Task -eq 'TestFile' -and (!$TestFile -or !(Test-Path -LiteralPath $TestFile -PathType Leaf))){throw 'TestFile musi wskazywać pojedynczy istniejący plik'}
    pwsh -NoProfile -File $slotScript -Acquire -Pool heavy -Owner $owner -PollSeconds 7 -StaleHours 87600
    if($LASTEXITCODE -ne 0){throw 'Nie uzyskano slotu heavy'}
    try {
        $env:PYTHONUNBUFFERED='1'
        switch($Task) {
            World {uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c}
            Materials {
                if($Only){uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only $Only}
                else {uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py}
            }
            Fidelity {uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art artifacts/sbs-r2/fidelity}
            TestFile {uv run --project tools/worldgen python -m pytest $TestFile -q}
            FinalGis {uv run --project tools/worldgen python -m pytest tests/gis -q}
            ComposeSbs {
                if(!$RenderDir -or !$OutputDir){throw 'RenderDir and OutputDir required'}
                $composeArgs=@('compose','--renders',$RenderDir,'--output',$OutputDir)
                if($IncludeRejected){$composeArgs+='--include-rejected'}
                if($Historical){$composeArgs+='--historical'}
                if($Inputs){$composeArgs+=@('--inputs',$Inputs)}
                if($Landmarks){$composeArgs+=@('--landmarks',$Landmarks)}
                uv run --project tools/refs python tools/refs/sbs_gate3.py @composeArgs
            }
            PrepareSbs {uv run --project tools/refs python tools/refs/sbs_gate3.py prepare}
        }
        $taskExit=$LASTEXITCODE
        if($taskExit -ne 0){throw "Zadanie $Task zakończone kodem $taskExit"}
    } finally {pwsh -NoProfile -File $slotScript -Release -Pool heavy -Owner $owner}
} finally {Pop-Location}

