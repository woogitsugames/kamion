$root = 'C:\Users\matma\Documents\Claude\kamion'
Set-Location (Join-Path $root '.claude\worktrees\review-0153')
$slot = Join-Path $root 'scripts/unity-slot.ps1'
while (-not (Select-String -Path artifacts/review-0153/render-exit.txt -Pattern 'DONE after' -Quiet)) { Start-Sleep 30 }
foreach ($tier in 'Low','High') {
  & pwsh $slot -Acquire -Owner review-0153
  try {
    if (Test-Path "$root/artifacts/locks/PHONE_RUN") { throw 'PHONE_RUN' }
    & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting clear -Gate3 (Join-Path $root 'artifacts/gpt-s16-r2/qa-cameras.json') -OutputDir "artifacts/review-0154-before/$tier-clear" *> "artifacts/review-0153/b0154-$tier.log"
    "0154 before $tier exit $LASTEXITCODE" | Add-Content artifacts/review-0153/post.txt
  } finally { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings; & pwsh $slot -Release -Owner review-0153 }
}
& pwsh $slot -Acquire -Owner review-0153
try {
  & pwsh scripts/test.ps1 -Platform EditMode *> artifacts/review-0153/editmode.log
  "editmode exit $LASTEXITCODE" | Add-Content artifacts/review-0153/post.txt
} finally { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings; & pwsh $slot -Release -Owner review-0153 }
"DONE post" | Add-Content artifacts/review-0153/post.txt
