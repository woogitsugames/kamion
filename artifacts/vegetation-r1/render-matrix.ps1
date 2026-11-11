param([string]$Stage='before')
$ErrorActionPreference='Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. artifacts/vegetation-r1/checkpoint.ps1
foreach($tier in @('Low','High')) { foreach($lighting in @('overcast','clear')) {
  $scene=if($tier -eq 'High') {'WorldC_High'} else {'WorldC'}
  pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-vegetation -StaleHours 1000000
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


