$ErrorActionPreference = 'Continue'
$main = 'C:\Users\matma\Documents\Claude\kamion'
$wt = Join-Path $main '.claude\worktrees\world-int-s16'
Set-Location $wt
foreach ($j in 'gugik','osm','refs','mapillary','fab') {
  $dst = Join-Path $wt "Data\raw\$j"
  if (-not (Test-Path $dst)) { cmd /c mklink /J "$dst" "$main\Data\raw\$j" | Out-Null }
}
robocopy "$main\Data\raw\derived" "$wt\Data\raw\derived" /E /NFL /NDL /NJH /MT:16 | Out-Null
robocopy "$main\Data\raw\cc0" "$wt\Data\raw\cc0" /E /NFL /NDL /NJH /MT:16 | Out-Null
robocopy "$main\art-source\world\cc0\_raw" "$wt\art-source\world\cc0\_raw" /E /NFL /NDL /NJH /MT:16 | Out-Null
robocopy "$main\art-source\world\megascans" "$wt\art-source\world\megascans" /E /XC /XN /XO /NFL /NDL /NJH /MT:16 | Out-Null
robocopy "$main\game\Assets\_Generated" "$wt\game\Assets\_Generated" /E /NFL /NDL /NJH /MT:16 | Out-Null
git lfs checkout
robocopy "$main\game\Library" "$wt\game\Library" /E /NFL /NDL /NJH /MT:16 /XD "$main\game\Library\Bee\artifacts" | Out-Null
"PREP DONE $(Get-Date -Format s)"
