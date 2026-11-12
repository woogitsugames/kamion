$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((git branch --show-current) -ne 'gpt-cab-r3') { throw 'Tylko runda cab r3.' }
. ./scripts/env.ps1
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
foreach ($tier in @('Low','High')) {
    $log="$PWD/artifacts/cab-r3/occlusion-gpu-$tier.log"
    pwsh $slot -Acquire -Owner gpt-cab -PollSeconds 5 -StaleHours 1000000
    if ($LASTEXITCODE -ne 0) { throw 'Brak slotu Unity.' }
    try { $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.CabBezelInspection.Run','-cabTier',$tier,'-cabLighting','clear','-cabOutput',"$PWD/artifacts/cab-r3/occlusion-gpu-preflight/$tier",'-qaMask','MIRROR_WideR_LOD0') }
    finally { pwsh $slot -Release -Owner gpt-cab; git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
    if ($code -ne 0 -or -not (Select-String -LiteralPath $log -Pattern 'CAB_BEZEL_INSPECTION_RESULT: OK' -SimpleMatch -Quiet)) { Show-UnityLogErrors $log; throw "Błąd maski GPU $tier, exit $code" }
    Add-Content artifacts/cab-r3/STATUS.md "Zapisano odczytowy GPU preflight $tier z oka kierowcy. before to tymczasowa ablacja ramki, after to bieżący model; nie jest to zmiana geometrii gry. Maskuje wyłącznie MIRROR_WideR_LOD0; wynik wymaga obejrzenia i kontroli niezerowej maski."
    git add -f artifacts/cab-r3/STATUS.md
    git commit -m "WIP cab: capture $tier right mirror GPU surface mask"
}
