# ADR 0140: render one probe round (Low by default) through the FIFO Unity slot; restores Unity side effects.
param([string]$Round='r1',[string]$Tier='Low',[string]$Lighting='overcast',[string]$OutName='')
$ErrorActionPreference='Stop'
$w=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')); $m='C:\Users\matma\Documents\Claude\kamion'
Set-Location $w
$camFile="artifacts/sbs-poses-r3/$Round/cameras.json"
if(!$OutName){$OutName="$Tier-$Lighting"}
while(Test-Path "$m\artifacts\locks\PHONE_RUN"){Write-Host 'PHONE_RUN; waiting 60 s'; Start-Sleep 60}
& pwsh -NoProfile -File "$m/scripts/unity-slot.ps1" -Acquire -Owner claude-sbs-poses-r3 -PollSeconds 15
if($LASTEXITCODE -ne 0){throw 'slot'}
try{
  foreach($g in @(@{f='ids-4x3.txt';w=1280;h=960},@{f='ids-16x9.txt';w=1280;h=720})){
    $idf="artifacts/sbs-poses-r3/$Round/$($g.f)"; if(!(Test-Path $idf)){continue}
    $ids="$(Get-Content $idf -Raw)".Trim(); if(!$ids){continue}
    $out="artifacts/sbs-poses-r3/$Round/renders/$OutName"
    & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $Tier -Lighting $Lighting -Width $g.w -Height $g.h -Gate3 $camFile -Cameras $ids -OutputDir $out
    if($LASTEXITCODE -ne 0){throw "render failed $($g.f)"}
  }
} finally {
  & git -C $w checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  if(Test-Path "$w/game/Assets/Resources"){ if(!(Get-ChildItem "$w/game/Assets/Resources" -Recurse -File)){Remove-Item -Recurse -Force "$w/game/Assets/Resources","$w/game/Assets/Resources.meta" -ErrorAction SilentlyContinue}}
  & pwsh -NoProfile -File "$m/scripts/unity-slot.ps1" -Release -Owner claude-sbs-poses-r3
}
