param([string[]]$Materials=@('M_bridge_concrete','M_road_asphalt'))
$ErrorActionPreference='Stop'
$root='C:\Users\matma\Documents\Claude\kamion'
$slot=Join-Path $root 'scripts/unity-slot.ps1'
. scripts/env.ps1
foreach($name in $Materials) {
 & pwsh $slot -Acquire -Owner gpt-s16
 try {
  if(Test-Path "$root/artifacts/locks/PHONE_RUN"){throw 'PHONE_RUN appeared'}
  $code=Invoke-UnityBatch -LogFile (Join-Path $RepoRoot "artifacts/gpt-s16-r3/patch-$name.log") -Arguments @('-nographics','-executeMethod','Game.World.Import.PutryShadowMaterialAblation.RunBatch','-putryMaterial',$name,'-putryOutput',(Join-Path $RepoRoot 'artifacts/gpt-s16-r3'))
  if($code -ne 0){throw "Native diagnostic failed: $name"}
 } finally {
  git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  & pwsh $slot -Release -Owner gpt-s16
 }
 $dest="artifacts/gpt-s16-r3/material-ablations/$name-Low"
 New-Item -ItemType Directory -Path $dest -Force | Out-Null
 & pwsh $slot -Acquire -Owner gpt-s16
 try {
  if(Test-Path "$root/artifacts/locks/PHONE_RUN"){throw 'PHONE_RUN appeared'}
  & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -Gate3 artifacts/gpt-s16-r3/diagnostic-cameras.json -Cameras 'sbs-g3-a-2818555625124739,sbs-g3-a-3970163613102941,putry-island-1,putry-island-2,putry-island-near' -OutputDir $dest *> "$dest.log"
  if($LASTEXITCODE -ne 0){throw "Diagnostic render failed: $name"}
 } finally {
  git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  & pwsh $slot -Release -Owner gpt-s16
 }
 Add-Content artifacts/gpt-s16-r3/STATUS.md "`nNatywna izolacja materiału $name zapisana; to ablacją cache, nie finalny import. NASTĘPNY KROK: porównać ze starym baseline i wybrać właściwy caster."
 git add -f artifacts/gpt-s16-r3/STATUS.md "artifacts/gpt-s16-r3/material-choice-$name.txt" "$dest/stats.txt" "$dest.log"
 git commit -q -m "wip(s16): isolate Putry caster normal bias on $name"
}
