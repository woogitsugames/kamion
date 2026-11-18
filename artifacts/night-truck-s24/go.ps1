# pwsh go.ps1 -Name <step> -Cmd '<powershell>' [-Unity]  -> detached; poll <step>.status for exit=N
param([string]$Name, [string]$Cmd, [switch]$Unity)
Set-Content (Join-Path $PSScriptRoot "$Name.cmd.ps1") $Cmd
Remove-Item (Join-Path $PSScriptRoot "$Name.status"),(Join-Path $PSScriptRoot "$Name.log") -ea 0
$a = "-NoProfile -File `"$PSScriptRoot\run.ps1`" -Name $Name" + $(if ($Unity) { ' -Unity' } else { '' })
Start-Process pwsh -WindowStyle Hidden -ArgumentList $a
