param([string]$Tag = 'red', [string]$Filter = 'Game.Tests.StartClearanceTests', [string]$Platform = 'EditMode')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\spawn-fix-0262'
$out = Join-Path $wt "artifacts\spawn-fix-0262\editmode-$Tag"
Remove-Item "$out.done" -ErrorAction SilentlyContinue
Set-Location $wt
pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner spawn-fix-0262 *> "$out.slot.log"
try { pwsh scripts/test.ps1 -Platform $Platform -Filter $Filter *> "$out.log"; $code = $LASTEXITCODE }
finally { pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner spawn-fix-0262 *>> "$out.slot.log" }
$xml = Get-ChildItem (Join-Path $wt ("artifacts\tests\{0}-*.xml" -f $Platform.ToLower())) | Sort-Object LastWriteTime | Select-Object -Last 1
if ($xml) { Copy-Item $xml.FullName "$out.xml" -Force }
"exit=$code" | Set-Content "$out.done"
