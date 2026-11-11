param([ValidateSet('Import','EditMode')][string]$Phase)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
& pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-life
if($LASTEXITCODE -ne 0){throw 'Brak slotu Unity'}
try {
 if($Phase -eq 'Import') {
  & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> artifacts/life-r1/import-wrapper.log
 } else {
  & pwsh scripts/test.ps1 -Platform EditMode *> artifacts/life-r1/editmode-wrapper.log
 }
 $result=$LASTEXITCODE
} finally {
 & pwsh scripts/unity-slot.ps1 -Release -Owner gpt-life
 git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
if($result -ne 0){throw "Niepowodzenie $Phase ($result)"}
