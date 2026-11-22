$o='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-7-s24\artifacts\regen-wave-7-s24'
while ($true) {
  Start-Sleep 900
  $n = @(Select-String 'chain=. DONE' "$o\chain.status" -ErrorAction SilentlyContinue).Count
  pwsh -NoProfile -File "$o\commit.ps1" *>> "$o\autocommit.log"
  if ($n -ge 3) { break }
}
