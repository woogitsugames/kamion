# ADR 0160: Low-clear control cameras (budget) + EditMode tests in this worktree; Unity slot; restores side effects.
$ErrorActionPreference='Stop'
$w=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')); $m='C:\Users\matma\Documents\Claude\kamion'
Set-Location $w
while(Test-Path "$m\artifacts\locks\PHONE_RUN"){Write-Host 'PHONE_RUN; waiting 60 s'; Start-Sleep 60}
& pwsh -NoProfile -File "$m/scripts/unity-slot.ps1" -Acquire -Owner g3a-0160 -PollSeconds 15
try {
  & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -OutputDir (Join-Path $w 'artifacts/g3a-0160/vqa/Low-clear')
  "VQA_EXIT $LASTEXITCODE"
  & git -C $w checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  & pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode
  "TEST_EXIT $LASTEXITCODE"
} finally {
  & git -C $w checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  & pwsh -NoProfile -File "$m/scripts/unity-slot.ps1" -Release -Owner g3a-0160
}
