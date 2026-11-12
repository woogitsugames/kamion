param([ValidateSet('before','after')][string]$Phase)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
. "$PSScriptRoot/evidence.ps1"
Assert-EdgeEvidenceInputs
if((git branch --show-current).Trim() -ne 'gpt-edge-r5'){throw 'Wrong round'}
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$groups=(Get-Content "$PSScriptRoot/native-camera-groups.json" -Raw|ConvertFrom-Json).groups
foreach($tier in @('Low','High')){
    foreach($lighting in @('clear','overcast')){
        foreach($group in $groups){
            $output="$PSScriptRoot/$Phase-photo/$tier-$lighting/$($group.id)"
            $scene=if($tier -eq 'High'){'WorldC_High'}else{'WorldC'}
            & pwsh -File $slot -Acquire -Pool unity -Owner gpt-edge -PollSeconds 1 -StaleHours 100000
            if($LASTEXITCODE -ne 0){throw 'Native capture slot failed'}
            try{
                $inputs=@('Data/Regions/bialystok-industrial-c/sbs_references.json',
                    'art-source/world/materials/materials_spec.json',
                    "game/Assets/_Generated/World/bialystok-industrial-c/$scene.unity",
                    'game/Assets/_Generated/World/bialystok-industrial-c/Meshes/world_edge.asset',
                    "game/Assets/_Generated/World/bialystok-industrial-c/Meshes/$tier/world_edge_far.asset",
                    'game/Assets/_Project/Rendering/Shaders/Sky.shader',
                    'game/Assets/_Project/Environment/Shaders/WorldPBR.shader',
                    'game/Assets/_Project/Rendering/Shaders/WorldSurface.shader',
                    'game/Assets/_Project/Rendering/Settings/Lighting/LP_Clear.asset',
                    'game/Assets/_Project/Rendering/Settings/Lighting/LP_Overcast.asset',
                    'tools/worldgen/streetscape/far_field.py',
                    'game/Assets/_Project/World/Import/WorldEdgeBuilder.cs',
                    'game/Assets/_Project/Rendering/Resources/Sky/T_ClearClouds.png',
                    'game/Assets/_Project/Rendering/Resources/Sky/ClearCloudsSource.json',
                    'game/Assets/_Project/Rendering/Resources/QualityProfile.asset',
                    'artifacts/edge-r5/proof-cameras.json','artifacts/edge-r5/native-camera-groups.json')
                $hashes=@{};foreach($file in $inputs){$hashes[$file]=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash}
                $capture=@{branch='gpt-edge-r5';commit=(git rev-parse HEAD).Trim();phase=$Phase;
                    matrix='photo-native';tier=$tier;lighting=$lighting;width=$group.width;height=$group.height;
                    camera_ids=$group.camera_ids;diagnostic_ids=$group.diagnostic_ids;
                    input_sha256=$hashes;started=(Get-Date -Format o)}
                & pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $lighting `
                    -Width $group.width -Height $group.height -Gate3 "$PSScriptRoot/proof-cameras.json" `
                    -Cameras ($group.camera_ids -join ',') -OutputDir $output
                if($LASTEXITCODE -ne 0){throw "Native render failed: $tier/$lighting/$($group.id)"}
                $ids=@(Select-String -LiteralPath "$output/stats.txt" -Pattern '^(.+): objects='|
                    ForEach-Object {$_.Matches[0].Groups[1].Value})
                if($ids.Count -ne $group.camera_ids.Count -or @($group.camera_ids|Where-Object {$_ -notin $ids}).Count){throw 'Native stats camera mismatch'}
                foreach($id in $group.camera_ids){
                    $stream=[IO.File]::OpenRead("$output/$id.png")
                    try{$header=[byte[]]::new(24);if($stream.Read($header,0,24) -ne 24){throw 'Truncated PNG'}}finally{$stream.Dispose()}
                    $width=$header[16]*16777216+$header[17]*65536+$header[18]*256+$header[19]
                    $height=$header[20]*16777216+$header[21]*65536+$header[22]*256+$header[23]
                    if($width -ne $group.width -or $height -ne $group.height){throw "Native PNG dimensions differ: $id"}
                }
                foreach($file in $inputs){if((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $hashes[$file]){throw "Input changed during capture: $file"}}
                $capture.finished=Get-Date -Format o
                $capture|ConvertTo-Json -Depth 7|Set-Content "$output/capture-inputs.json"
            }finally{
                git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
                & pwsh -File $slot -Release -Pool unity -Owner gpt-edge -StaleHours 100000
            }
            Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Native $Phase $tier-$lighting $($group.id): $($ids.Count) kamer, każdy PNG ma proporcje źródłowej fotografii; diagnostyczna 2948 pozostaje C."
            git add -f artifacts/edge-r5/STATUS.md
            git commit -m "WIP edge r5: capture $Phase native $tier-$lighting $($group.id)"
            if($LASTEXITCODE -ne 0){throw 'Native checkpoint failed'}
        }
    }
}
