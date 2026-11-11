param([ValidateSet('before','after')][string]$Stage)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
# Source state is prepared explicitly by source-mode.ps1. Do not mix a shader
# from a moving main branch with a canonical world generated from a fixed base.
 foreach($tier in @('Low','High')) { foreach($light in @('clear','overcast')) {
  $scene=if($tier -eq 'High'){'WorldC_High'}else{'WorldC'}
  & pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-life -StaleHours 1000000
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
