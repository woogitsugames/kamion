param([string]$Tag = 'r2')
& "$PSScriptRoot/world.ps1"
& "$PSScriptRoot/import.ps1" -Tag $Tag
