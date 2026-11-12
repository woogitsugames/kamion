param([int]$WaitPid=0,[string]$MaskSpec='Apron',[string]$OutputName='apron')
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-edge-r6'){throw 'Wrong round'}
if($OutputName -notmatch '^[a-z][a-z0-9-]{0,40}$'){throw 'Invalid output name'}
while(-not(Test-Path "$PSScriptRoot/Baseline.ready")){
    if($WaitPid -le0 -or -not(Get-Process -Id $WaitPid -ErrorAction SilentlyContinue)){throw 'Baseline stopped without frozen evidence'}
    Start-Sleep -Seconds 5
}
. "$PSScriptRoot/evidence.ps1"
Assert-EdgeEvidenceInputs
$tier='High'
$scene='WorldC_High'
$ids=@('edge-nw-ground','edge-north')
$output="$PSScriptRoot/ownership-mask/$OutputName/High-clear"
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh -File $slot -Acquire -Pool unity -Owner gpt-edge -PollSeconds 7 -StaleHours 100000
if($LASTEXITCODE -ne0){throw 'Mask Unity acquisition failed'}
try{
    $inputs=@("game/Assets/_Generated/World/bialystok-industrial-c/$scene.unity",
        'game/Assets/_Generated/World/bialystok-industrial-c/Meshes/world_edge.asset',
        'game/Assets/_Generated/World/bialystok-industrial-c/Meshes/High/world_edge_far.asset',
        'game/Assets/_Project/Rendering/Shaders/Sky.shader',
        'game/Assets/_Project/Environment/Shaders/WorldPBR.shader',
        'game/Assets/_Project/Rendering/Shaders/WorldSurface.shader',
        'game/Assets/_Project/Rendering/Settings/Lighting/LP_Clear.asset',
        'game/Assets/_Project/Rendering/Resources/QualityProfile.asset',
        'game/Assets/_Project/Rendering/Resources/Sky/T_ClearClouds.png',
        'game/Assets/_Project/Rendering/Resources/Sky/ClearCloudsSource.json',
        'game/Assets/_Project/World/Import/WorldEdgeBuilder.cs',
        'tools/worldgen/streetscape/far_field.py','artifacts/edge-r6/proof-cameras.json')
    $hashes=@{};foreach($file in $inputs){$hashes[$file]=(Get-FileHash $file -Algorithm SHA256).Hash}
    & pwsh scripts/visual-qa.ps1 -Scene $scene -Tier High -Lighting clear -Width 1280 -Height 720 `
        -Gate3 "$PSScriptRoot/proof-cameras.json" -Cameras ($ids -join ',') -Mask $MaskSpec -OutputDir $output
    if($LASTEXITCODE -ne0){throw 'Ownership mask capture failed'}
    $log=Get-ChildItem artifacts/logs -Filter 'visual-qa-WorldC_High-*.log'|Sort-Object LastWriteTime -Descending|Select-Object -First 1
    $hits=@(Select-String -LiteralPath $log.FullName -SimpleMatch "[VISUALQA] mask '$MaskSpec':")
    if($hits.Count -ne$ids.Count){throw 'Missing mask-selection evidence'}
    foreach($hit in $hits){if($hit.Line -notmatch ': (\d+) slots on (\d+) renderers' -or [int]$Matches[1] -le0){throw 'Empty material selection'}}
    foreach($id in $ids){foreach($suffix in @('','_mask')){
        $file="$output/$id$suffix.png"
        if(-not(Test-Path $file)){throw "Missing frame: $file"}
        & magick -limit thread 1 $file -resize 960x "$output/$id$suffix-preview.jpg"
        if($LASTEXITCODE -ne0){throw 'Mask preview failed'}
    }}
    foreach($file in $inputs){if((Get-FileHash $file -Algorithm SHA256).Hash -ne$hashes[$file]){throw "Input changed during mask: $file"}}
    @{tier=$tier;lighting='clear';width=1280;height=720;spec=$MaskSpec;camera_ids=$ids;
      input_sha256=$hashes;selection_lines=@($hits.Line);log=$log.FullName;finished=(Get-Date -Format o);
      note='Ownership diagnostic, not photographic calibration or production change. Alpha curtains use a separate mask to avoid false opaque occlusion.'}|
      ConvertTo-Json -Depth 6|Set-Content "$output/mask-inputs.json"
}finally{
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -File $slot -Release -Pool unity -Owner gpt-edge -StaleHours 100000
}
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Maska własności $OutputName High-clear gotowa dla NW i north; selekcję potwierdzono w logu, źródła niezmienione. To diagnoza przed edycją, nie deklaracja rozwiązania problemu."
git add -f artifacts/edge-r6/STATUS.md
git commit -m "WIP edge r6: capture $OutputName ownership mask on fresh baseline"
if($LASTEXITCODE -ne0){throw 'Mask checkpoint failed'}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/$OutputName-mask.complete"
