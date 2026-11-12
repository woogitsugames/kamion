param(
 [Parameter(Mandatory)][ValidateSet('World','Materials','Fidelity','TestFile','Script')][string]$Task,
 [Parameter(Mandatory)][ValidatePattern('^[a-z0-9-]+$')][string]$Tag,
 [string]$TestPath='',
 [string]$ScriptPath='',
 [string[]]$ScriptArguments=@()
)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$owner=(git branch --show-current).Trim()
if($owner -notmatch '^gpt-life-r\d+$'){throw 'Unexpected heavy-slot owner'}
if($Task -eq 'TestFile' -and $TestPath -notmatch '^tests/(gis|physics|gate3)/[^/]+\.py(?:::[A-Za-z0-9_]+)?$') {
 throw 'During a round, select one explicit test file or test case'
}
if($Task -eq 'Script') {
 if($ScriptPath -notmatch '^artifacts/life-r\d+/[^/]+\.py$' -or !(Test-Path -LiteralPath $ScriptPath)){throw 'Select an existing own life Python helper'}
}
$ownSlot="C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/$owner.slot"
if(Test-Path -LiteralPath $ownSlot){throw 'This branch already holds a heavy slot; do not overlap own jobs'}
$log="artifacts/life-r3/$Tag.log"
if(Test-Path -LiteralPath $log){throw "Refuse overwriting evidence: $log"}
# Never let the common slot helper prune another session's old slot.
& pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $owner -StaleHours 1000000 -PollSeconds 1
if($LASTEXITCODE -ne 0){throw 'Heavy slot acquisition failed'}
$code=1
try {
 switch($Task) {
  'World' { & uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> $log }
  'Materials' { & uv run --project tools/worldgen python -u art-source/world/materials/_src/build_all.py *> $log }
  'Fidelity' { & uv run --project tools/worldgen python -u tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art "artifacts/life-r3/$Tag" *> $log }
  'TestFile' { & uv run --project tools/worldgen python -m pytest $TestPath -q *> $log }
  'Script' { & uv run --project tools/worldgen python -u $ScriptPath @ScriptArguments *> $log }
 }
 $code=$LASTEXITCODE
} finally {
 & pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner
 @{task=$Task;owner=$owner;pool='heavy';exit_code=$code;finished=(Get-Date -Format o);log=$log} |
  ConvertTo-Json | Set-Content -Encoding utf8 "artifacts/life-r3/$Tag-result.json"
}
if($code -ne 0){throw "$Task failed ($code): $log"}

