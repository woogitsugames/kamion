[CmdletBinding(SupportsShouldProcess, DefaultParameterSetName='Chain')]
param(
    [Parameter(ParameterSetName='Chain')][ValidateSet('A','B','C','D','E')][string]$Chain = 'A',
    [Parameter(Mandatory, ParameterSetName='Tile')][string]$Tile
)

. "$PSScriptRoot/common.ps1"
$plan = @(if ($Tile) { $queue | Where-Object tile -CEQ $Tile } else { $queue | Where-Object chain -EQ $Chain })
if (-not $plan.Count) { throw "Kafel poza kolejką: $Tile" }
foreach ($entry in $plan) {
    Write-Host "$($entry.chain) $($entry.tile): build_s=$($entry.build_s) total_s=$($entry.total_s) fala=$($entry.source_wave)"
}
Write-Host 'Plan: po prepare.ps1 -> heavy: build_world --context, far_field, export-route, fidelity -> import serializowany: heavy, Win64, High.'
Write-Host "Zakres: $scope. Python: $python"
if (-not $PSCmdlet.ShouldProcess(($plan.tile -join ', '), 'Uruchom regenerację i import')) { return }

Initialize-WaveRuntime
if (-not (Test-Path -LiteralPath "$stateDir/prepare.done")) { throw 'Najpierw uruchom prepare.ps1.' }
foreach ($entry in $plan) {
    if (Test-Path -LiteralPath "$waveDir/STOP") { throw 'STOP: zatrzymano przed następnym kaflem.' }
    Invoke-WaveTile $entry.tile
    & "$waveDir/commit.ps1" -Tile $entry.tile
}
