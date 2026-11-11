param([ValidateSet('before','after')][string]$Stage)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$shader='game/Assets/_Project/Environment/Shaders/WorldPBR.shader'
if($Stage -eq 'before') { git restore --source=main --worktree -- $shader }
try {
 foreach($tier in @('Low','High')) { foreach($light in @('clear','overcast')) {
  $scene=if($tier -eq 'High'){'WorldC_High'}else{'WorldC'}
  & pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-life
  if($LASTEXITCODE -ne 0){throw 'Nie udało się pozyskać slotu Unity'}
  try {
   & pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Gate3 artifacts/life-r1/cameras.json -OutputDir "artifacts/life-r1/$Stage/$tier-$light" *> "artifacts/life-r1/$Stage-$tier-$light.log"
   if($LASTEXITCODE -ne 0){throw "Błąd renderu $Stage $tier $light"}
  } finally {
   & pwsh scripts/unity-slot.ps1 -Release -Owner gpt-life
   git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  }
 }
 }
} finally { if($Stage -eq 'before') { git restore --worktree -- $shader } }
