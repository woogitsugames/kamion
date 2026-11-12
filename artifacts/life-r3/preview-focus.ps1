param([Parameter(Mandatory)][ValidatePattern('^[a-z][a-z0-9-]*$')][string]$Stage)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$packet=Get-Content artifacts/life-r3/cameras.json -Raw|ConvertFrom-Json
$ids=@($packet.cameras|Where-Object {$_.id -match '^(life3_|sheet_far_)'}|ForEach-Object {$_.id})
foreach($condition in @('Low-clear','Low-overcast','High-clear','High-overcast')) {
 $out="artifacts/life-r3/$Stage-preview/$condition"
 New-Item -ItemType Directory -Force $out|Out-Null
 $frames=@()
 foreach($id in $ids) {
  $source="artifacts/life-r3/$Stage/$condition/$id.png"
  if(!(Test-Path -LiteralPath $source)){throw "Missing frame: $source"}
  $frame="$out/$id.jpg"
  & magick -limit thread 2 -limit memory 256MiB $source -resize '960x960>' -quality 92 $frame
  if($LASTEXITCODE){throw "Thumbnail failed: $source"}
  $frames+=$frame
 }
 & magick montage -limit thread 2 -limit memory 256MiB -background '#252525' -fill white -font Arial -pointsize 14 -label '%t' @frames -thumbnail 320x148 -tile 3x3 -geometry +0+18 "$out/new-cameras.jpg"
 if($LASTEXITCODE){throw 'Contact sheet failed'}
}
"Created bounded previews for $($ids.Count) cameras in four conditions"
