param([string]$Stage='before', [switch]$Resume)
$ErrorActionPreference='Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
if ($Stage -eq 'before' -and (Test-Path artifacts/vegetation-r1/REIMPORT-REQUIRED.txt)) {
 throw 'Baseline reimport required: restore the missing photographic asphalt dependency before comparison.'
}
. artifacts/vegetation-r1/checkpoint.ps1
foreach($tier in @('Low','High')) { foreach($lighting in @('overcast','clear')) {
  $scene=if($tier -eq 'High') {'WorldC_High'} else {'WorldC'}
  $captureLog = "artifacts/vegetation-r1/$Stage-$tier-$lighting.log"
  $captureDir = "artifacts/vegetation-r1/$Stage/$tier-$lighting"
  if ($Resume -and (Test-Path $captureLog) -and (Test-Path "$captureDir/stats.txt")) {
    $complete = Select-String -Path $captureLog -Pattern 'VISUALQA_RESULT: OK rendered=(\d+)' | Select-Object -Last 1
    if ($complete -and $complete.Line -match 'VISUALQA_RESULT: OK rendered=(\d+)') {
      $expectedFrames = [int]$Matches[1]
      $frames = @(Get-ChildItem $captureDir -Filter *.png | Where-Object { $_.Name -notlike '*_mask.png' }).Count
      if ($expectedFrames -gt 0 -and $frames -eq $expectedFrames) {
        Write-Host "Resume: verified $expectedFrames existing frames $tier $lighting"
        continue
      }
    }
  }
  pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-vegetation -StaleHours 1000000 -PollSeconds 10
  if($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
  try {
    pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $lighting -Gate3 Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json -OutputDir "artifacts/vegetation-r1/$Stage/$tier-$lighting" *> "artifacts/vegetation-r1/$Stage-$tier-$lighting.log"
    if($LASTEXITCODE -ne 0) {throw "Visual QA failed: $Stage $tier $lighting"}
  } finally {
    pwsh scripts/unity-slot.ps1 -Release -Owner gpt-vegetation
    git restore --worktree -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  }
  Add-Content artifacts/vegetation-r1/STATUS.md "Zapisano $Stage $scene $tier $lighting. Następny krok: obejrzenie arkuszy i porównanie statystyk."
  Save-VegetationCheckpoint -Message "wip(vegetation): render $Stage $tier $lighting"
} }
"Macierz $Stage zakończona" | Set-Content "artifacts/vegetation-r1/$Stage-done.txt"




