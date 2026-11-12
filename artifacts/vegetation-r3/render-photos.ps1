param([string]$Stage='before')
$ErrorActionPreference='Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. artifacts/vegetation-r3/checkpoint.ps1
foreach($tier in @('Low','High')) {
 $scene=if($tier -eq 'High') {'WorldC_High'} else {'WorldC'}
 foreach($lighting in @('clear','overcast')) {
 foreach($group in Get-ChildItem artifacts/vegetation-r3 -Filter 'photo-cameras-*.json') {
  $dims=($group.BaseName -replace 'photo-cameras-','') -split 'x'
  $height=[int][Math]::Round(1024*[double]$dims[1]/[double]$dims[0])
  $ids=((Get-Content $group.FullName -Raw | ConvertFrom-Json).cameras.id) -join ','
  $folder="$tier-$lighting-photo-$($dims -join 'x')"
  pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-vegetation -StaleHours 1000000 -PollSeconds 10
  if($LASTEXITCODE -ne 0) {throw 'Slot acquisition failed'}
  try {
   pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $lighting -Width 1024 -Height $height -Gate3 $group.FullName -Cameras $ids -OutputDir "artifacts/vegetation-r3/$Stage/$folder" *> "artifacts/vegetation-r3/$Stage-$folder.log"
   if($LASTEXITCODE -ne 0) {throw "Photo rendering failed: $folder"}
  } finally {
   pwsh scripts/unity-slot.ps1 -Release -Owner gpt-vegetation
   git restore --worktree -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  }
  Add-Content artifacts/vegetation-r3/STATUS.md "Zapisano pary foto $Stage $folder. Następny krok: porównać z photo-references.json."
  Save-VegetationCheckpoint -Message "wip(vegetation): fotografie $Stage $folder"
 }
}
}
"Pary foto $Stage zakończone" | Set-Content "artifacts/vegetation-r3/$Stage-photos-done.txt"


