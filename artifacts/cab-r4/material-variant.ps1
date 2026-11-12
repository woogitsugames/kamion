param([Parameter(Mandatory)][ValidateSet('hp03','hp06')][string]$Variant)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-cab-r4'){throw 'Wrong branch'}
$stage="result-0112-$Variant-quick"
if(Test-Path "artifacts/cab-r4/$stage"){throw 'Existing variant output; do not duplicate a live/completed run'}
$verify=Get-Content artifacts/cab-r4/material-prep/fine-verification.json -Raw | ConvertFrom-Json
if($verify.status -ne 'PASS'){throw 'Offline candidate not verified'}
$rows=@($verify.rows | Where-Object variant -eq $Variant)
if($rows.Count -ne 3){throw 'Expected three verified tiers'}
foreach($row in $rows){
  $p="artifacts/cab-r4/material-prep/candidate-$Variant/$($row.tier)/T_Cab_Plastic_Normal.png"
  if((Get-FileHash $p).Hash.ToLower() -ne $row.normal_sha256){throw 'Candidate SHA mismatch'}
}
foreach($row in $rows){
  Copy-Item -LiteralPath "artifacts/cab-r4/material-prep/candidate-$Variant/$($row.tier)/T_Cab_Plastic_Normal.png" -Destination "art-source/truck/interior/export/textures/$($row.tier)/T_Cab_Plastic_Normal.png"
}
$p='art-source/truck/interior/cab_material_scans.json'
$config=Get-Content $p -Raw | ConvertFrom-Json
$config.plastic.normal_highpass_mm=$rows[0].sigma_mm
$config | ConvertTo-Json -Depth 20 | Set-Content $p -Encoding utf8
Add-Content artifacts/cab-r4/STATUS.md ("Po weryfikacji offline i obejrzeniu mapy integrujemy do krótkiej ablacji $Variant, sigma="+$rows[0].sigma_mm+' mm. Tylko trzy normalne Plastic i pole config; reszta map, Leather i bias legend bez zmian. To kandydat, nie końcowa akceptacja.')
git add -- art-source/truck/interior/cab_material_scans.json
git add -f -- artifacts/cab-r4/STATUS.md art-source/truck/interior/export/textures/High/T_Cab_Plastic_Normal.png art-source/truck/interior/export/textures/Medium/T_Cab_Plastic_Normal.png art-source/truck/interior/export/textures/Low/T_Cab_Plastic_Normal.png
git commit -m "WIP cab r4: integrate $Variant for isolated image review"
if($LASTEXITCODE -ne 0){throw 'Checkpoint commit failed'}
pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/cab-r4/build-0112.ps1 -Label $Variant
if($LASTEXITCODE -ne 0){throw 'Variant build failed'}
. ./scripts/env.ps1
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
foreach($state in @('High-clear','Low-overcast')){
  $tier,$light=$state.Split('-')
  $scene=if($tier -eq 'High'){'WorldC_High'}else{'WorldC'}
  $output="$PWD/artifacts/cab-r4/$stage/$state"
  $log="$PWD/artifacts/cab-r4/$Variant-quick-$state.log"
  pwsh $slot -Acquire -Owner gpt-cab -PollSeconds 5 -StaleHours 1000000
  if($LASTEXITCODE -ne 0){throw 'No Unity slot'}
  try {
    $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.VisualQaRunner.RenderControlCameras','-qaScene',$scene,'-qaWidth','1920','-qaHeight','1080','-qaTier',$tier,'-qaOutput',$output,'-qaLighting',$light,'-qaCameras','cab-grain,cab-dash')
  } finally {
    pwsh $slot -Release -Owner gpt-cab
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  }
  if($code -ne 0 -or -not (Select-String -LiteralPath $log -SimpleMatch 'VISUALQA_RESULT: OK rendered=2' -Quiet)){throw ('Variant capture failed '+$state)}
  Add-Content artifacts/cab-r4/STATUS.md "Zapisano dwa kadry krótkiej ablacji $Variant $state; obejrzeć przed wyborem. Nie zastępuje pełnego gate."
  git add -f -- artifacts/cab-r4/STATUS.md
  git commit -m "WIP cab r4: capture $Variant quick $state"
}
