param([Parameter(Mandatory)][string]$Tile)

. "$PSScriptRoot/common.ps1"
if ($Tile -cnotin $queue.tile) { throw "Kafel poza kolejką: $Tile" }
Initialize-WaveRuntime
if (-not (Test-Path -LiteralPath "$stateDir/prepare.done")) { throw 'Najpierw uruchom prepare.ps1.' }
Invoke-WaveTile $Tile -Redo
& "$waveDir/commit.ps1" -Tile $Tile
