param([switch]$FinalRound)
$ErrorActionPreference='Stop'
if(!$FinalRound){throw 'Full GIS is permitted only at the end of the round; use -FinalRound'}
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$owner=(git branch --show-current).Trim()
if($owner -notmatch '^gpt-life-r\d+$'){throw 'Unexpected heavy-slot owner'}
if(Test-Path -LiteralPath "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/$owner.slot") { throw 'This branch already holds a heavy slot; do not overlap own jobs' }
$manifest='Data/Regions/bialystok-industrial-c/generated/world_manifest.json'
$snapshot='artifacts/life-r1/manifest-before-gis.json'
Copy-Item $manifest $snapshot
$before=(Get-FileHash $manifest -Algorithm SHA256).Hash
& pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $owner -StaleHours 1000000
if($LASTEXITCODE -ne 0){throw 'Heavy slot acquisition failed'}
try {
 & uv run --project tools/worldgen python -m pytest tests/gis -q *> artifacts/life-r1/gis.log
 $testCode=$LASTEXITCODE
} finally {
 & pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner
}
$after=(Get-FileHash $manifest -Algorithm SHA256).Hash
$restored=$false
if($before -ne $after) { Copy-Item $snapshot $manifest; $restored=$true }
@{exit_code=$testCode;manifest_before=$before;manifest_after=$after;manifest_restored=$restored} | ConvertTo-Json | Set-Content artifacts/life-r1/gis-result.json
if($testCode -ne 0){throw "GIS failed ($testCode)"}
