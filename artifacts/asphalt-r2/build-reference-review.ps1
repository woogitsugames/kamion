param([ValidatePattern('^candidate[0-9]*$')][string]$After='candidate2')
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$out="artifacts/asphalt-r2/$After-reference-960"
New-Item $out -ItemType Directory -Force | Out-Null
$rows=@()
foreach($tier in 'Low','High'){
 foreach($id in '3970163613102941','177786140912399'){
  $photo="artifacts/asphalt-r2/references/$id-rectified.png"
  $render="artifacts/asphalt-r2/$After/$tier-clear/sbs-g3-a-$id.png"
  magick -limit thread 2 '(' $photo -resize 480x360! ')' '(' $render -gravity Center -crop 1440x1080+0+0 +repage -resize 480x360! ')' +append -background '#202020' -fill white -font Arial -pointsize 14 -gravity North -splice 0x28 -annotate +0+4 "$tier clear | PHOTO / RENDER | POSE MISMATCH - material example only" "$out/$tier-$id.jpg"
  if($LASTEXITCODE -ne 0){throw 'Reference sheet failed'}
  $rows += [pscustomobject]@{tier=$tier;id=$id;photo=$photo;render=$render;render_centre_crop=@(1440,1080);note='Same aspect/vertical FOV; visible pose/model mismatch. Not photometric calibration.'}
 }
}
$rows | ConvertTo-Json -Depth 4 | Set-Content "$out/crops.json"
