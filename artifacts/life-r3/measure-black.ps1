param([Parameter(Mandatory)][ValidatePattern('^[a-z][a-z0-9-]*$')][string]$Stage)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$rois=[ordered]@{door='134x61+1199+563';asphalt='134x61+1213+862'}
$rows=@()
foreach($condition in @('Low-clear','Low-overcast','High-clear','High-overcast')) {
 $source="artifacts/life-r3/$Stage/$condition/life3_black_side5.png"
 $values=[ordered]@{}
 foreach($entry in $rois.GetEnumerator()) {
  $value=& magick -limit thread 2 -limit memory 256MiB $source -crop $entry.Value +repage -alpha off -fx '0.2126*r+0.7152*g+0.0722*b' -format '%[fx:mean*255]' info:
  if($LASTEXITCODE){throw 'ROI calculation failed'}
  $values[$entry.Key]=[double]::Parse(($value -join '').Trim(),[Globalization.CultureInfo]::InvariantCulture)
 }
 $rows+=@{condition=$condition;source=$source;source_sha=(Get-FileHash $source).Hash;door_mean=$values.door;asphalt_mean=$values.asphalt;ratio=$values.door/$values.asphalt}
}
@{stage=$Stage;note='Display-encoded RGB weighted mean, not linear photometry/albedo. New side camera and manually inspected fixed ROIs; no comparison to historical overcast ROI.';rois=$rois;rows=$rows}|ConvertTo-Json -Depth 5|Set-Content "artifacts/life-r3/$Stage-black-roi.json"
$rows|ForEach-Object {"$($_.condition): door=$($_.door_mean) asphalt=$($_.asphalt_mean) ratio=$($_.ratio)"}
