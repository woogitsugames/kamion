$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if(-not(Test-Path "$PSScriptRoot/After.ready")){throw 'Freeze After first'}
$out=Join-Path $PSScriptRoot 'native-review'
New-Item -ItemType Directory -Force $out|Out-Null
$refs=Get-Content "$PSScriptRoot/reference-photos.json" -Raw|ConvertFrom-Json
$selected=@(
    @('sbs-g3-a-303305168125936','High-clear'),
    @('sbs-g3-a-320215796381417','Low-clear'),
    @('sbs-g3-a-3970163613102941','High-overcast'),
    @('sbs-g3-b-275528677534382','Low-overcast')
)
$index=foreach($item in $selected){
    $camera,$config=$item
    $ref=@($refs|Where-Object camera -eq $camera)
    if($ref.Count -ne1 -or $ref[0].pose -ne 'B'){throw 'Expected one frozen B reference'}
    $ref=$ref[0]
    $photo=Join-Path "$PSScriptRoot/reference-photos" $ref.file
    if((Get-FileHash $photo -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ref.sha256){throw 'Photo changed'}
    $group="$($ref.width)x$($ref.height)"
    $render="$PSScriptRoot/after-photo/$config/$group/$camera.png"
    $size=(& magick identify -format '%wx%h' $render)
    if($LASTEXITCODE -ne0 -or $size -ne $group){throw 'Native render size mismatch'}
    $names=@("$out/$config-$camera-photo.png","$out/$config-$camera-render.png")
    $sources=@($photo,$render)
    $labels=@("Zdjecie | $($ref.author) | $($ref.license)","Render | $config | poza B | fotometria UNVERIFIED")
    for($i=0;$i -lt2;$i++){
        & magick -limit thread 1 $sources[$i] -resize 480x -background white -fill black -font Arial `
            -pointsize 12 -gravity NorthWest -splice 0x28 -annotate +4+5 $labels[$i] $names[$i]
        if($LASTEXITCODE -ne0){throw 'Preview failed'}
    }
    $pair="$config-$camera-pair.jpg"
    & magick -limit thread 1 $names[0] $names[1] +append "$out/$pair"
    if($LASTEXITCODE -ne0){throw 'Pair failed'}
    @{camera=$camera;configuration=$config;pair=$pair;source=$ref.source;author=$ref.author;license=$ref.license;
      source_dimensions=@($ref.width,$ref.height);matching_dimensions=$true;photo_sha256=$ref.sha256;
      pose='B';photometry='UNVERIFIED';note='No calibration changes; not photographic identity of the southern hall.'}
}
$index|ConvertTo-Json -Depth 5|Set-Content "$out/index.json"
