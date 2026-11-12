param([Parameter(Mandatory)][int]$ControllerId)
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
if((git branch --show-current).Trim() -ne 'gpt-light-r5'){throw 'Wrong round'}
$process=Get-Process -Id $ControllerId -ErrorAction Stop
$heldHandle=$process.Handle # Retain this exact process, never a subsequently reused PID.
$started=$process.StartTime
Write-Output "Waiting for exact baseline controller PID=$ControllerId started=$started"
while(-not $process.WaitForExit(30000)){}
$exitCode=$process.ExitCode
if($null -eq $exitCode -or $exitCode -ne 0){throw "Baseline controller failed or exit unknown: $exitCode"}
$jobs=Get-Content "$PSScriptRoot/baseline.json" -Raw|ConvertFrom-Json
foreach($job in $jobs.jobs){
    $png=@(Get-ChildItem -LiteralPath $job.output -Filter '*.png'|Where-Object {$_.LastWriteTime -ge $started -and $_.Length -gt 0})
    if($png.Count -lt 100){throw "Baseline incomplete: $($job.output) $($png.Count)"}
    $proof=Get-Content (Join-Path $job.output 'lamp-probes.json') -Raw|ConvertFrom-Json
}
if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/unity-slots/gpt-light.slot'){throw 'Own prior Unity slot unexpectedly still held; refuse reentrant acquire'}
Add-Content "$PSScriptRoot/STATUS.md" 'Świeży generator, fidelity, import i baseline zakończyły się kodem 0. Uruchamiam zaplanowaną serię 108 obrazów świata po terminalnym zakończeniu dokładnie tego kontrolera; bez równoległego własnego Unity.'
git add -f artifacts/light-r5/STATUS.md
git commit -m 'WIP light r5: start world grade comparison after verified baseline completion'
& pwsh "$PSScriptRoot/run-light-batch.ps1" -Jobs artifacts/light-r5/tone-world.json -Gate3 artifacts/light-r5/qa-cameras.json -EnvDump
if($LASTEXITCODE){throw 'Tone world batch failed'}
Add-Content "$PSScriptRoot/STATUS.md" 'Seria świata tone-world zakończona. Następny krok: obejrzenie 108 PNG i kostek, niezależna recenzja, budżet wszystkich kamer i decyzja o eksperymencie. Sam kod wyjścia nie oznacza jakości PASS.'
git add -f artifacts/light-r5/STATUS.md
git commit -m 'WIP light r5: record completed world grade ablation for visual review'

