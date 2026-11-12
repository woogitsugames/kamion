param([Parameter(Mandatory)][ValidatePattern('^[a-z][a-z0-9-]*$')][string]$Stage)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$luma=Get-Content "artifacts/life-r3/$Stage-black-roi.json" -Raw|ConvertFrom-Json
$rows=@()
foreach($row in $luma.rows) {
 if((Get-FileHash $row.source).Hash -ne $row.source_sha){throw 'ROI source changed'}
 $areas=[ordered]@{}
 foreach($region in $luma.rois.PSObject.Properties) {
  $text=& magick -limit thread 2 -limit memory 256MiB $row.source -crop $region.Value +repage -alpha off -channel RGB -separate -format '%[fx:mean*255] ' info:
  if($LASTEXITCODE){throw 'RGB extraction failed'}
  $rgb=@((($text -join ' ').Trim() -split '\s+')|ForEach-Object {[double]::Parse($_,[Globalization.CultureInfo]::InvariantCulture)})
  if($rgb.Count -ne 3){throw 'Expected three RGB channel means'}
  $areas[$region.Name]=$rgb
 }
 $rows+=@{condition=$row.condition;source=$row.source;source_sha=$row.source_sha;door_rgb=$areas.door;asphalt_rgb=$areas.asphalt}
}
@{stage=$Stage;method='Display-encoded RGB means over the same manually inspected fixed rectangles as the luminance ROI; not albedo or linear photometry.';rois=$luma.rois;rows=$rows}|ConvertTo-Json -Depth 5|Set-Content "artifacts/life-r3/$Stage-black-rgb.json"
$rows|ForEach-Object {"$($_.condition): door RGB $($_.door_rgb -join '/')"}
