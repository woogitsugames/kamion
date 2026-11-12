$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$out='artifacts/asphalt-r2/material-review-960'
New-Item $out -ItemType Directory -Force | Out-Null
$manifest=@()
foreach($condition in 'Low-overcast','Low-clear','High-overcast','High-clear') {
 foreach($id in 'asphalt_kerb_andersa_close','asphalt_paving_andersa_close') {
  $before="artifacts/asphalt-r2/baseline/$condition/$id.png"
  $after="artifacts/asphalt-r2/candidate/$condition/$id.png"
  foreach($entry in @(@($before,'before'),@($after,'after'))) {
   magick -limit thread 2 $entry[0] -resize 960x "$out/$condition-$id-$($entry[1]).jpg"
   if($LASTEXITCODE -ne 0){throw 'Image preview failed'}
  }
  magick -limit thread 2 "$out/$condition-$id-before.jpg" "$out/$condition-$id-after.jpg" -append -background '#202020' -fill white -font Arial -pointsize 18 -gravity North -splice 0x28 -annotate +0+4 "$condition / BEFORE above, CANDIDATE below" "$out/$condition-$id-pair.jpg"
  $crop=if($id -like '*kerb*'){'960x300+650+350'}else{'960x360+650+650'}
  magick -limit thread 2 '(' $before -crop $crop +repage ')' '(' $after -crop $crop +repage ')' -append -background '#202020' -fill white -font Arial -pointsize 18 -gravity North -splice 0x28 -annotate +0+4 "$condition / native crop BEFORE above, CANDIDATE below" "$out/$condition-$id-crop-pair.jpg"
  if($LASTEXITCODE -ne 0){throw 'Image crop failed'}
  $manifest += [pscustomobject]@{condition=$condition;camera=$id;before=$before;after=$after;crop=$crop;crop_scaled=$false}
 }
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content "$out/sources.json"
