# c-regen-s22: EditMode (compile gate) -> import C + Dojlidy -> visual-qa "after" matrix. One unity slot.
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen-s22'; $main = 'C:\Users\matma\Documents\Claude\kamion'
Set-Location $wt
$o = 'artifacts/c-regen-s22/unity'; New-Item -ItemType Directory -Force $o | Out-Null
$st = "$o/unity.status"; Remove-Item "$o/unity.done" -ErrorAction SilentlyContinue
"start $(Get-Date -Format s)" | Set-Content $st
while (Test-Path "$main\artifacts\locks\PHONE_RUN") { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner c-regen-s22 | Out-Null
"slot $(Get-Date -Format s)" | Add-Content $st
try {
  pwsh scripts/test.ps1 -Platform EditMode *> "$o/editmode.log"; "editmode exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
  foreach ($r in 'bialystok-industrial-c', 'bialystok-dojlidy') {
    pwsh scripts/import-region.ps1 -Region $r *> "$o/import-$r.log"; "import-$r exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
  }
} finally { pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner c-regen-s22 | Out-Null }
git checkout -q -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
Copy-Item artifacts/tests/*.xml $o -ErrorAction SilentlyContinue
"IMPORT DONE $(Get-Date -Format s)" | Add-Content $st
pwsh -NoProfile -File artifacts/c-regen-s22/tools/vqa.ps1 -Tag after
"DONE $(Get-Date -Format s)" | Add-Content $st; 'done' | Set-Content "$o/unity.done"
