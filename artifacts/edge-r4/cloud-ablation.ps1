$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if(-not(Test-Path "$PSScriptRoot/forest-curtains-mask.complete")){throw 'Finish the current Unity masks first'}
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh -File $slot -Acquire -Pool unity -Owner gpt-edge -PollSeconds 1 -StaleHours 100000
if($LASTEXITCODE -ne 0){throw 'Ablation slot failed'}
try{
    & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -Width 1280 -Height 720 `
        -Gate3 "$PSScriptRoot/proof-cameras.json" -Cameras 'sbs-g3-a-2948595898752384,sbs-g3-a-303305168125936' `
        -Rq 'rq_clearcover=0' -OutputDir "$PSScriptRoot/cloud-ablation"
    if($LASTEXITCODE -ne 0){throw 'Cloud diagnostic ablation failed'}
    foreach($id in @('sbs-g3-a-2948595898752384','sbs-g3-a-303305168125936')){
        & magick -limit thread 1 "$PSScriptRoot/cloud-ablation/$id.png" -resize 960x "$PSScriptRoot/cloud-ablation/$id-preview.jpg"
        if($LASTEXITCODE -ne 0){throw 'Preview failed'}
    }
}finally{
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -File $slot -Release -Pool unity -Owner gpt-edge -StaleHours 100000
}
Add-Content "$PSScriptRoot/STATUS.md" 'Krok 11: diagnostyczna ablacja rq_clearcover=0 ukończona pod Unity. Nie jest rozwiązaniem produkcyjnym ani zmianą światła: wyłącznie dodatkowe obrazy do rozdzielenia geometrii i fotografii chmur. Podstawowe Before pozostaje z chmurami.'
git add -f artifacts/edge-r4/STATUS.md
git commit -m 'WIP edge r4: capture cloud-only diagnostic ablation without source edits'
