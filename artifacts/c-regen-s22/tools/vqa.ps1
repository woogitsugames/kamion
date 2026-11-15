param([string]$Tag = 'before', [string[]]$Lightings = @('clear','dusk'), [string[]]$Tiers = @('Low','High'))
# visual-qa matrix for c-regen-s22: C + Dojlidy, one unity slot for the whole matrix.
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen-s22'; $main = 'C:\Users\matma\Documents\Claude\kamion'
Set-Location $wt
$out = "artifacts/c-regen-s22/$Tag"; New-Item -ItemType Directory -Force $out | Out-Null
$st = "$out/vqa.status"; Remove-Item "$out/vqa.done" -ErrorAction SilentlyContinue
"start $(Get-Date -Format s)" | Set-Content $st
while (Test-Path "$main\artifacts\locks\PHONE_RUN") { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner c-regen-s22 | Out-Null
"slot $(Get-Date -Format s)" | Add-Content $st
try {
  foreach ($s in @(@('WorldC','bialystok-industrial-c'), @('World_bialystok-dojlidy','bialystok-dojlidy'))) { foreach ($t in $Tiers) { foreach ($l in $Lightings) {
    pwsh scripts/visual-qa.ps1 -Scene $s[0] -Tier $t -Lighting $l -OutputDir "$out/$($s[1])/$t-$l" *> "$out/vqa-$($s[1])-$t-$l.log"
    "$($s[1]) $t $l exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
  } } }
} finally { pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner c-regen-s22 | Out-Null }
git checkout -q -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
"DONE $(Get-Date -Format s)" | Add-Content $st; 'done' | Set-Content "$out/vqa.done"
