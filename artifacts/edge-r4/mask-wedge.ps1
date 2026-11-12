param([int]$WaitPid=0,[string]$MaskSpec='Apron;FarField_far:far_field_buildings',
      [string]$OutputName='own-opaque',[ValidateSet('Low','High')][string[]]$Tiers=@('Low','High'))
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-edge-r4'){throw 'Wrong round'}
if($OutputName -notmatch '^[a-z][a-z0-9-]{0,40}$'){throw 'Invalid output name'}
while(-not(Test-Path "$PSScriptRoot/Baseline.ready")){
    if($WaitPid -le 0 -or -not(Get-Process -Id $WaitPid -ErrorAction SilentlyContinue)){throw 'Baseline is not ready; inspect its active process/log'}
    Start-Sleep -Seconds 5
}
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$ids=@('sbs-g3-a-2948595898752384','sbs-g3-a-303305168125936')
foreach($tier in $Tiers){
    $scene=if($tier -eq 'High'){'WorldC_High'}else{'WorldC'}
    $output="$PSScriptRoot/wedge-mask/$OutputName/$tier-clear"
    & pwsh -File $slot -Acquire -Pool unity -Owner gpt-edge -PollSeconds 1 -StaleHours 100000
    if($LASTEXITCODE -ne 0){throw 'Mask Unity slot failed'}
    try{
        $inputs=@("game/Assets/_Generated/World/bialystok-industrial-c/$scene.unity",
            'game/Assets/_Generated/World/bialystok-industrial-c/Meshes/world_edge.asset',
            "game/Assets/_Generated/World/bialystok-industrial-c/Meshes/$tier/world_edge_far.asset",
            'game/Assets/_Project/Rendering/Shaders/Sky.shader',
            'game/Assets/_Project/Rendering/Resources/Sky/T_ClearClouds.png',
            'artifacts/edge-r4/proof-cameras.json')
        $hashes=@{};foreach($file in $inputs){$hashes[$file]=(Get-FileHash $file -Algorithm SHA256).Hash}
        & pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting clear -Width 1280 -Height 720 `
            -Gate3 "$PSScriptRoot/proof-cameras.json" -Cameras ($ids -join ',') -Mask $MaskSpec -OutputDir $output
        if($LASTEXITCODE -ne 0){throw 'Mask capture failed'}
        $log=Get-ChildItem artifacts/logs -Filter "visual-qa-$scene-*.log"|Sort-Object LastWriteTime -Descending|Select-Object -First 1
        $hits=@(Select-String -LiteralPath $log.FullName -SimpleMatch "[VISUALQA] mask '$MaskSpec':")
        if($hits.Count -ne $ids.Count){throw 'Missing successful mask-selection evidence'}
        foreach($hit in $hits){if($hit.Line -notmatch ': (\d+) slots on (\d+) renderers' -or [int]$Matches[1] -le 0){throw 'Mask selected no material'}
            if($MaskSpec -eq 'Apron;FarField_far:far_field_buildings' -and [int]$Matches[1] -lt 6){throw 'Expected apron and four opaque sectors'}}
        foreach($id in $ids){foreach($suffix in @('','_mask')){
            if(-not(Test-Path "$output/$id$suffix.png")){throw 'Missing mask/original PNG'}
            & magick -limit thread 1 "$output/$id$suffix.png" -resize 960x "$output/$id$suffix-preview.jpg"
            if($LASTEXITCODE -ne 0){throw 'Mask preview failed'}
        }}
        foreach($file in $inputs){if((Get-FileHash $file -Algorithm SHA256).Hash -ne $hashes[$file]){throw "Source changed during mask: $file"}}
        @{tier=$tier;lighting='clear';width=1280;height=720;spec=$MaskSpec;
          input_sha256=$hashes;selection_lines=@($hits.Line);log=$log.FullName;
          note='Diagnostic only. Opaque own materials avoid an alpha-curtain becoming an artificial occluder. 2948 is class C.';
          finished=(Get-Date -Format o)}|ConvertTo-Json -Depth 6|Set-Content "$output/mask-inputs.json"
    }finally{
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
        & pwsh -File $slot -Release -Pool unity -Owner gpt-edge -StaleHours 100000
    }
    Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Maska $OutputName $tier-clear gotowa dla 2948/303305 w1280×720; materiały rzeczywiście wybrane, analiza obrazu nadal otwarta."
    git add -f artifacts/edge-r4/STATUS.md
    git commit -m "WIP edge r4: capture $OutputName $tier cloud-wedge mask"
    if($LASTEXITCODE -ne 0){throw 'Mask checkpoint failed'}
}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/$OutputName-mask.complete"
