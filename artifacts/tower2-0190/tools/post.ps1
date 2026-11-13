# after the chain: full pytest tests/gis (heavy slot) and EditMode (unity slot); status in logs/chain.status
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\tower2-0190'; $n = 'tower2-0190'
Set-Location $wt
$logs = "artifacts/$n/logs"; $st = "$logs/chain.status"
function Mark($m) { "post $m $(Get-Date -Format s)" | Out-File $st -Append -Encoding utf8 }
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner "$n-pytest"
try {
  & tools/worldgen/.venv/Scripts/python.exe -m pytest tests/gis -q -p no:cacheprovider *> "$logs/pytest-gis.log"
  Mark "pytest gis exit $LASTEXITCODE"
} finally { pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner "$n-pytest" }
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner $n
try {
  pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode *> "$logs/editmode.log"
  Mark "editmode exit $LASTEXITCODE"
} finally {
  pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner $n
  git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>&1 | Out-Null
}
Mark 'POST DONE'
