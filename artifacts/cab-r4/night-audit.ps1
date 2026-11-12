$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-cab-r4'){throw 'Wrong branch'}
. ./scripts/env.ps1
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
foreach($tier in @('Low','High')) {
  $scene=if($tier -eq 'High'){'WorldC_High'}else{'WorldC'}
  $output="$PWD/artifacts/cab-r4/night-current/$tier-night"
  $log="$PWD/artifacts/cab-r4/night-current-$tier.log"
  pwsh $slot -Acquire -Owner gpt-cab -PollSeconds 5 -StaleHours 1000000
  if($LASTEXITCODE -ne 0){throw 'No Unity slot'}
  try {
    $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.VisualQaRunner.RenderControlCameras','-qaScene',$scene,'-qaWidth','1920','-qaHeight','1080','-qaTier',$tier,'-qaOutput',$output,'-qaLighting','night','-qaCameras','cab-driver,cab-dash,cab-grain')
  } finally {
    pwsh $slot -Release -Owner gpt-cab
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  }
  if($code -ne 0 -or -not (Select-String -LiteralPath $log -SimpleMatch 'VISUALQA_RESULT: OK rendered=3' -Quiet)){throw ('Night capture failed '+$tier+' '+$code)}
  Add-Content artifacts/cab-r4/STATUS.md ('Zapisano trzy aktualne kadry '+$tier+' na istniejącym preset Night z ADR 0108, bez zmiany źródeł światła. To dodatkowa ocena kabiny; preset sam opisuje ograniczenie modelu nocnego. Materiał Plastic hp15 i bias Low -0,75. Obejrzeć przed wnioskami.')
  git add -f -- artifacts/cab-r4/STATUS.md
  git commit -m ('WIP cab r4: capture current cab on existing Night preset '+$tier)
}
