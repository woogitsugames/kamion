$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if(!(Get-Content artifacts/life-r4/SELECTED.json -Raw|ConvertFrom-Json).selected){throw 'Select geometry first'}
$ref='artifacts/life-r4/refs/yard-34-reference.jpg'
$rear='artifacts/life-r4/after-a2/Low-overcast/yard_trailer_curtain_0_rear34.png'
$wheel='artifacts/life-r4/after-a2/Low-overcast/yard_trailer_curtain_0_wheel2.png'
$out='artifacts/life-r4/refs'
function Pair([string]$photo,[string]$render,[string]$name,[string]$note){
 & magick -limit thread 2 -limit memory 256MiB -size 960x360 'xc:#252525' `
  '(' $photo -resize 480x300 -background '#252525' -gravity center -extent 480x300 ')' -gravity northwest -geometry +0+30 -composite `
  '(' $render -resize 480x300 -background '#252525' -gravity center -extent 480x300 ')' -gravity northwest -geometry +480+30 -composite `
  -font Arial -fill white -pointsize 14 -gravity northwest -annotate +10+8 'Foto: Cekay / CC0 1.0' `
  -annotate +490+8 'Render A2 / Low overcast' -pointsize 12 -annotate +10+338 $note "$out/$name.jpg"
 if($LASTEXITCODE){throw 'SBS failed'}
}
& magick -limit thread 2 -limit memory 256MiB $rear -crop 860x520+820+250 +repage "$out/rear-render-crop.png"
if($LASTEXITCODE){throw 'Rear crop failed'}
Pair $ref "$out/rear-render-crop.png" 'sbs-yard-rim-a2' 'Inny model, miejsce, obiektyw i światło. Analiza konstrukcji koła; bez kalibracji koloru/GPS.'
& magick -limit thread 2 -limit memory 256MiB $ref -crop 92x102+523+407 +repage "$out/wheel-photo-crop.png"
if($LASTEXITCODE){throw 'Photo crop failed'}
& magick -limit thread 2 -limit memory 256MiB $wheel -crop 600x500+870+0 +repage "$out/wheel-render-crop.png"
if($LASTEXITCODE){throw 'Wheel crop failed'}
Pair "$out/wheel-photo-crop.png" "$out/wheel-render-crop.png" 'sbs-wheel-detail-a2' 'Różna skala i kierunek obserwacji. Generyczna geometria; śruby, zużycie i okrągłość nadal PARTIAL.'
@{photo=@{path=$ref;sha=(Get-FileHash $ref).Hash};render_rear=@{path=$rear;sha=(Get-FileHash $rear).Hash;crop=@(820,250,860,520)};
 render_wheel=@{path=$wheel;sha=(Get-FileHash $wheel).Hash;crop=@(870,0,600,500)};
 photo_wheel_crop=@(523,407,92,102);canvas=@(960,360);calibrated=$false}|ConvertTo-Json -Depth 5|Set-Content "$out/sbs-a2-inputs.json"
