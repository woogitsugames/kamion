$ErrorActionPreference='Stop'
$tokens=$null; $parseErrors=$null
[System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path scripts/sbs-gate3.ps1),[ref]$tokens,[ref]$parseErrors) | Out-Null
if($parseErrors.Count){$parseErrors | Format-List;exit 1}
Write-Output 'PowerShell parser OK'
