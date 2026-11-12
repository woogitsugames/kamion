$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-edge-r6'){throw 'Wrong round'}
$canonical='Data/Regions/bialystok-industrial-c/sbs_cameras.json'
$referencePath='Data/Regions/bialystok-industrial-c/sbs_references.json'
$cams=(Get-Content $canonical -Raw|ConvertFrom-Json).cameras
$refs=(Get-Content $referencePath -Raw|ConvertFrom-Json).references
$oldProof=(Get-Content artifacts/edge-r5/proof-cameras.json -Raw|ConvertFrom-Json).cameras
# The old NW tripod is below the archived conformed terrain. Preserve it in
# separate ownership/height diagnostics, never as a valid ground-view camera.
$extra=@($oldProof|Where-Object {$_.id -eq 'edge-pietrasze-driver'})
$proof=@($extra)+@($cams)
if(@($proof.id|Sort-Object -Unique).Count -ne$proof.Count){throw 'Duplicate proof camera'}
@{cameras=$proof}|ConvertTo-Json -Depth 30|Set-Content "$PSScriptRoot/proof-cameras.json"
Copy-Item artifacts/edge-r5/native-camera-groups.json "$PSScriptRoot/native-camera-groups.json"
$groups=(Get-Content "$PSScriptRoot/native-camera-groups.json" -Raw|ConvertFrom-Json).groups
$oldIndex=Get-Content artifacts/edge-r5/reference-photos.json -Raw|ConvertFrom-Json
New-Item -ItemType Directory -Force "$PSScriptRoot/reference-photos"|Out-Null
$index=@(foreach($ref in $refs){
    $cam=@($cams|Where-Object {$_.id -eq $ref.camera})
    if($cam.Count -ne1 -or $cam[0].pose_confidence -ne $ref.pose_confidence){throw "Reference/camera class mismatch: $($ref.camera)"}
    if($ref.pose_confidence -notin @('A','B')){continue}
    $old=@($oldIndex|Where-Object {$_.camera -eq $ref.camera})
    if($old.Count -ne1){throw "Frozen reference unavailable: $($ref.camera)"}
    $old=$old[0]
    $source="artifacts/edge-r5/reference-photos/$($old.file)"
    if((Get-FileHash $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ref.comparison_sha256){throw 'Reference changed; obtain new canonical frozen photo before continuing'}
    $target=Join-Path "$PSScriptRoot/reference-photos" $old.file
    Copy-Item $source $target
    if((Get-FileHash $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ref.comparison_sha256){throw 'Frozen copy hash mismatch'}
    $stream=[IO.File]::OpenRead($target)
    try{$header=[byte[]]::new(24);if($stream.Read($header,0,24) -ne24){throw 'Truncated PNG'}}finally{$stream.Dispose()}
    if(($header[0..7] -join ',') -ne '137,80,78,71,13,10,26,10'){throw 'Not a PNG'}
    $width=$header[16]*16777216+$header[17]*65536+$header[18]*256+$header[19]
    $height=$header[20]*16777216+$header[21]*65536+$header[22]*256+$header[23]
    $group=@($groups|Where-Object {$ref.camera -in $_.photo_ids})
    if($group.Count -ne1 -or $group[0].width -ne$width -or $group[0].height -ne$height){throw 'Native group no longer matches photo'}
    @{camera=$ref.camera;file=$old.file;width=$width;height=$height;sha256=$ref.comparison_sha256;
      author=$ref.author;license=$ref.license;license_url=$ref.license_url;source=$ref.page_url;pose=$ref.pose_confidence}
})
if($index.Count -ne25){throw 'Accepted reference inventory changed; revise matrix before freezing'}
$index|ConvertTo-Json -Depth 6|Set-Content "$PSScriptRoot/reference-photos.json"
foreach($group in $groups){foreach($id in $group.camera_ids){if($id -notin $cams.id){throw 'Native camera absent from canonical source'}}}
$inputPaths=@($canonical,$referencePath,'artifacts/edge-r6/proof-cameras.json',
    'artifacts/edge-r6/native-camera-groups.json','artifacts/edge-r6/reference-photos.json')
@{files=@(foreach($path in $inputPaths){@{path=$path;sha256=(Get-FileHash $path -Algorithm SHA256).Hash}});
  frozen=(Get-Date -Format o);note='Canonical merged-main poses; no framing/calibration changes within R6'}|
  ConvertTo-Json -Depth 6|Set-Content "$PSScriptRoot/evidence-inputs.json"
$changed=@(foreach($cam in $cams){
    $old=@($oldProof|Where-Object {$_.id -eq $cam.id})
    $fields=@('pos','look_at','fov_deg','seat','kind')
    $different=@($fields|Where-Object {($old[0].$_|ConvertTo-Json -Compress) -ne ($cam.$_|ConvertTo-Json -Compress)})
    if($different.Count){@{camera=$cam.id;changed_fields=$different;reason='Adopted reviewed merged-main pose; no local calibration'}}
})
@{canonical_cameras=$cams.Count;proof_cameras=$proof.Count;retained_edge_diagnostics=$extra.Count;
  accepted_photos=$index.Count;native_cameras_per_configuration=(@($groups.camera_ids).Count);
  canonical_geometry_changes_since_r5=$changed;source_sha256=(Get-FileHash $canonical -Algorithm SHA256).Hash}|
  ConvertTo-Json -Depth 8|Set-Content "$PSScriptRoot/camera-baseline-inventory.json"
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Macierz dowodowa r6 zamrożona z bieżącego main: $($cams.Count) kamer kanonicznych, $($extra.Count) zachowane diagnostyczne edge, $($index.Count) fotografii B z SHA i zgodnymi grupami native. Przyjęto zrecenzowane pozy main; nie edytowano kalibracji ani klas. Oryginalne fotografie pozostają poza gitem."
git add -f artifacts/edge-r6/STATUS.md artifacts/edge-r6/proof-cameras.json artifacts/edge-r6/native-camera-groups.json artifacts/edge-r6/reference-photos.json artifacts/edge-r6/evidence-inputs.json artifacts/edge-r6/camera-baseline-inventory.json artifacts/edge-r6/setup-evidence.ps1
git commit -m 'WIP edge r6: freeze current canonical poses and verified reference inventory'
if($LASTEXITCODE -ne0){throw 'Evidence checkpoint failed'}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/Evidence.ready"
