param([ValidateSet('Import','PreparedImport','EditMode')][string]$Phase)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if ($Phase -eq 'PreparedImport') {
 # Maps were generated canonically and source switches change mtimes without
 # changing their content. Validate every actual map and raw product instead of
 # rebuilding all unrelated sets solely because git restore touched a .py file.
 $stamp=Get-Date -Format yyyyMMdd-HHmmss
 & pwsh artifacts/life-r1/heavy.ps1 -Task Script -Tag "prepared-proof-$stamp" -ScriptPath artifacts/life-r1/source-proof.py -ScriptArguments "prepared-import-$stamp"
 if ($LASTEXITCODE -ne 0) { throw 'Prepared input verification failed' }
}
& pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-life -StaleHours 1000000
if($LASTEXITCODE -ne 0){throw 'Brak slotu Unity'}
try {
 if($Phase -eq 'PreparedImport') {
  . scripts/env.ps1
  $log=[IO.Path]::GetFullPath("artifacts/life-r1/prepared-import-$stamp.log")
  $result=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.World.Import.RegionImporter.ImportBatch','-region','bialystok-industrial-c','-tiers','Low,High','-materialTier','Medium')
  if ($result -ne 0 -or !(Select-String -Path $log -Pattern 'IMPORT_RESULT: OK' -Quiet)) { throw "Import failed: $log" }
 } elseif($Phase -eq 'Import') {
  & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> artifacts/life-r1/import-wrapper.log
 } else {
  & pwsh scripts/test.ps1 -Platform EditMode *> artifacts/life-r1/editmode-wrapper.log
 }
 if($Phase -ne 'PreparedImport') { $result=$LASTEXITCODE }
} finally {
 & pwsh scripts/unity-slot.ps1 -Release -Owner gpt-life
 git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
if($result -ne 0){throw "Niepowodzenie $Phase ($result)"}
