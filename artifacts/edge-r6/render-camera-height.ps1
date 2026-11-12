$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-edge-r6'){throw 'Wrong round'}
if(-not(Test-Path "$PSScriptRoot/OwnershipMasks.ready")){throw 'Complete baseline ownership masks first'}
. "$PSScriptRoot/evidence.ps1"
Assert-EdgeEvidenceInputs
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/unity-slots/gpt-edge.slot'){throw 'Another own Unity lease exists; do not reuse it concurrently'}
$output="$PSScriptRoot/camera-height/High-clear"
$ids=@('edge-nw-ground','edge-nw-ground-reseated')
$inputs=@('artifacts/edge-r6/height-cameras.json',
    'game/Assets/_Generated/World/bialystok-industrial-c/WorldC_High.unity',
    'game/Assets/_Generated/World/bialystok-industrial-c/Meshes/world_edge.asset',
    'game/Assets/_Generated/World/bialystok-industrial-c/Meshes/High/world_edge_far.asset',
    'game/Assets/_Generated/World/bialystok-industrial-c/Materials/M_terrain_grass.mat',
    'game/Assets/_Project/Gameplay/Gate3Cameras.cs',
    'game/Assets/_Project/Rendering/Shaders/Sky.shader',
    'game/Assets/_Project/Environment/Shaders/WorldPBR.shader',
    'game/Assets/_Project/Rendering/Shaders/WorldSurface.shader',
    'game/Assets/_Project/Rendering/Settings/Lighting/LP_Clear.asset',
    'game/Assets/_Project/Rendering/Resources/QualityProfile.asset',
    'Data/raw/derived/bialystok-industrial-c/world/terrain_conformed.npy')
& pwsh -File "$PSScriptRoot/acquire-slot.ps1" -Pool unity -Owner gpt-edge
if($LASTEXITCODE -ne0){throw 'Height diagnostic Unity acquisition failed'}
try{
    $hashes=@{};foreach($file in $inputs){$hashes[$file]=(Get-FileHash $file -Algorithm SHA256).Hash}
    & pwsh scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Lighting clear -Width 1280 -Height 720 `
        -Gate3 "$PSScriptRoot/height-cameras.json" -Cameras ($ids -join ',') -Mask Apron -OutputDir $output
    if($LASTEXITCODE -ne0){throw 'Camera-height diagnostic render failed'}
    $log=Get-ChildItem artifacts/logs -Filter 'visual-qa-WorldC_High-*.log'|Sort-Object LastWriteTime -Descending|Select-Object -First 1
    $seating=@(Select-String -LiteralPath $log.FullName -SimpleMatch '[GATE3] 2 cameras created, 1 re-seated on the road collision')
    if(-not$seating.Count){throw 'Expected actual collider re-seating evidence missing'}
    foreach($id in $ids){foreach($suffix in @('','_mask')){
        & magick -limit thread 1 "$output/$id$suffix.png" -resize 960x "$output/$id$suffix-preview.jpg"
        if($LASTEXITCODE -ne0){throw 'Height preview failed'}
    }}
    for($i=0;$i -lt2;$i++){
        $label=if($i -eq0){'Oryginalny statyw: wysokosc z pliku'}else{'Diagnostyka: raycast collider + nominalne 2,5 m'}
        & magick -limit thread 1 "$output/$($ids[$i]).png" -resize 480x270 -background white -fill black `
            -font Arial -pointsize 12 -gravity NorthWest -splice 0x28 -annotate +4+5 $label "$output/panel-$i.png"
        if($LASTEXITCODE -ne0){throw 'Height pair panel failed'}
    }
    & magick -limit thread 1 "$output/panel-0.png" "$output/panel-1.png" +append "$output/file-vs-collider-pair.jpg"
    if($LASTEXITCODE -ne0){throw 'Height pair failed'}
    foreach($file in $inputs){if((Get-FileHash $file -Algorithm SHA256).Hash -ne$hashes[$file]){throw "Diagnostic source changed: $file"}}
    @{camera_ids=$ids;input_sha256=$hashes;reseating_log=@($seating.Line);log=$log.FullName;
      note='Separate diagnosis of an invalid archival tripod. Same E/N and pitch; existing diagnostic-kind policy re-seats at nominal collider +2.5 m. No canonical camera or production geometry changed.';
      finished=(Get-Date -Format o)}|ConvertTo-Json -Depth 6|Set-Content "$output/capture-inputs.json"
}finally{
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -File $slot -Release -Pool unity -Owner gpt-edge -StaleHours 100000
}
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Osobne porównanie wysokości statywu NW gotowe, z potwierdzeniem jednej operacji re-seat na colliderze. To diagnostyka pozy, bez zmiany głównych kamer lub świata; obrazy wymagają obejrzenia przed wnioskiem o szarej płaszczyźnie."
git add -f artifacts/edge-r6/STATUS.md
git commit -m 'WIP edge r6: capture file-height versus collider-seated NW tripod'
if($LASTEXITCODE -ne0){throw 'Height diagnostic checkpoint failed'}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/CameraHeight.ready"
