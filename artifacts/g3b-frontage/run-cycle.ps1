# build_world -> import -> SBS render (Low overcast) -> control cameras -> artifacts/g3b-frontage/<Name>
param([string]$Name = 'baseline', [string]$Tag = '0')
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-build.ps1') -Log "build-world-$Tag.log"
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-import.ps1') -Log "import-$Tag.log"
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-sbs.ps1') -Name $Name
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-control.ps1') -Name $Name
