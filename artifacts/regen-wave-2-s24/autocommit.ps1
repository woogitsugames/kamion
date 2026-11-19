$o='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-2-s24\artifacts\regen-wave-2-s24'
while ($true) {
  Start-Sleep 900
  $n = (Get-Content "$o\chain.status" | Select-String 'DONE').Count
  pwsh -NoProfile -File "$o\commit.ps1" *>> "$o\autocommit.log"
  if ($n -ge 2) { break }
}
