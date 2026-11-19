$wt='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\seams-p3-s24'
$st="$wt\artifacts\seams-p3-s24\libcopy.status"
while ($true) {
  $u = Get-CimInstance Win32_Process -Filter "Name='Unity.exe'" | Where-Object { $_.CommandLine -match 'worktrees\\win-build\\game' }
  if (-not $u) { break }
  Add-Content $st "$(Get-Date -Format s) waiting win-build Unity"
  Start-Sleep 60
}
robocopy C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\win-build\game\Library "$wt\game\Library" /E /MT:16 /NFL /NDL /NP /LOG:"$wt\artifacts\seams-p3-s24\logs\libcopy.log"
Add-Content $st "$(Get-Date -Format s) exit=$LASTEXITCODE"
