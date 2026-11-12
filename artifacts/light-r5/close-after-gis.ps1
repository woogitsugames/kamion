param([Parameter(Mandatory)][int]$GisProcessId)
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$identity=Get-CimInstance Win32_Process -Filter "ProcessId=$GisProcessId"
if($null -eq $identity -or $identity.Name -ne 'pwsh.exe' -or $identity.CommandLine -notmatch '-File artifacts/light-r5/run-heavy\.ps1 -Task GisFinal -RoundEnd\s*$'){throw 'Not the exact live round5 GIS controller'}
$process=Get-Process -Id $GisProcessId
$null=$process.Handle
Write-Output "Waiting on real GIS controller PID $GisProcessId, created $($identity.CreationDate); no additional Python/Unity."
while(-not $process.WaitForExit(1000)){}
$code=$process.ExitCode
if($null -eq $code -or $code -ne 0){throw "GIS controller not terminal0 ($code); inspect original session, do not close"}
$logs=@(Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'heavy-GisFinal-*.log'|Where-Object Name -Match '^heavy-GisFinal-\d{8}-\d{6}\.log$')
if($logs.Count -ne 1){throw 'Require unique round5 final GIS log'}
& pwsh -NoProfile -File "$PSScriptRoot/close-round.ps1" -GisExitCode $code -GisLog $logs[0].FullName
if($LASTEXITCODE){throw 'Round5 guarded close failed; inspect state, never blindly repeat mutations'}
git diff --quiet HEAD
if($LASTEXITCODE){throw 'Unexpected tracked changes after close'}
git switch -c gpt-light-r6
if($LASTEXITCODE){throw 'Next round branch creation failed'}
# Main advances independently; preserve exact new base and stop for manual conflict union when needed.
$main=(git rev-parse main).Trim()
New-Item -ItemType Directory -Force artifacts/light-r6|Out-Null
@("Start rundy6 od zakończonej rundy5. Aktualny main: $main.",'Zakres: wyłącznie light. Najpierw merge main i ponowna lektura HANDOVER/feedback. Kandydat runtime native grade domyślnie OFF według artifacts/light-r5/NEXT-ROUND-CANDIDATE.md.','Unity wyłącznie slot gpt-light; ciężki Python przez heavy gpt-light-r6. Bez telefonów, push i merge do main. Cel24h trwa do12.11 21:30:47 Warszawa.')|Set-Content artifacts/light-r6/STATUS.md -Encoding utf8
Get-Content 'C:/Users/matma/Documents/Claude/kamion/HANDOVER.md' -Head 35
Get-Content 'C:/Users/matma/Documents/Claude/kamion/docs/owner/GPT-FEEDBACK-S10.md' -Tail 55
git merge main
if($LASTEXITCODE){Add-Content artifacts/light-r6/STATUS.md 'Merge aktualnego main wymaga ręcznego rozwiązania konfliktów; nie uruchomiono generatora/Unity. Następny krok: git status i unia kodu w light, generated z main.';throw 'Round6 main merge conflict; resolve explicitly'}
git add -f artifacts/light-r6/STATUS.md
git commit -m 'wip(light): start round6 after latest main merge'
Write-Output "ROUND6_READY: branch=$((git branch --show-current).Trim()) main=$main; continue preparation and next round immediately."
