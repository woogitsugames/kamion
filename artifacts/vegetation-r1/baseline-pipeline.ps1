$ErrorActionPreference='Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
while(Get-Process -Id 107312 -ErrorAction SilentlyContinue) { Start-Sleep -Seconds 5 }
if(-not (Select-String -Path artifacts/vegetation-r1/baseline-build.log -Pattern '\[world\s+[\d.]+s\] done' -Quiet)) { throw 'Baseline generator did not report completion' }
$qa=Get-Content Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json -Raw | ConvertFrom-Json
if($qa.megascans.fallback -eq $true) {throw 'Megascans fallback in baseline'}
pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-vegetation -StaleHours 1000000
if($LASTEXITCODE -ne 0) {throw 'Slot failed'}
try {
 pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> artifacts/vegetation-r1/baseline-import.log
 if($LASTEXITCODE -ne 0) {throw 'Baseline import failed'}
} finally {
 pwsh scripts/unity-slot.ps1 -Release -Owner gpt-vegetation
 git restore --worktree -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Add-Content artifacts/vegetation-r1/STATUS.md 'Zaimportowano bazę z własnej regeneracji. Następny krok: pwsh artifacts/vegetation-r1/render-matrix.ps1 -Stage before'
git add -f artifacts/vegetation-r1/STATUS.md
git commit -m 'wip(vegetation): import wlasnej regeneracji bazowej'
pwsh artifacts/vegetation-r1/render-matrix.ps1 -Stage before
if($LASTEXITCODE -ne 0) {throw 'Before matrix failed'}

