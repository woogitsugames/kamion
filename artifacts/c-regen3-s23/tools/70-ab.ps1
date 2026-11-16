param([Parameter(Mandatory)][string]$Region, [Parameter(Mandatory)][string]$Cell, [string[]]$Cameras)
# Side-by-side before|after JPG (each 800 px wide, <= 1600 px total; view at <= 960 px with Read) for chosen cameras.
#   pwsh artifacts/c-regen3-s23/tools/70-ab.ps1 -Region bialystok-industrial-c -Cell Low-clear -Cameras stretch-04,kwadrat-park-gate
# Without -Cameras: every PNG present in both folders. Also prints RMSE per pair (ImageMagick compare) and the stats.txt tris.
. "$PSScriptRoot/_common.ps1"
$b = "$Art/before/$Region/$Cell"; $a = "$Art/after/$Region/$Cell"; $v = "$Art/view"; New-Item -ItemType Directory -Force $v | Out-Null
if (-not $Cameras) { $Cameras = Get-ChildItem $a -Filter *.png | Where-Object { $_.Name -notlike '*_mask.png' -and (Test-Path "$b/$($_.Name)") } | ForEach-Object BaseName }
foreach ($c in $Cameras) {
    if (-not ((Test-Path "$b/$c.png") -and (Test-Path "$a/$c.png"))) { "missing pair $c"; continue }
    magick "$b/$c.png" -resize 800x "$a/$c.png" -resize 800x +append -quality 85 "$v/ab_${Region}_${Cell}_$c.jpg"
    $rmse = (magick compare -metric RMSE "$b/$c.png" "$a/$c.png" null: 2>&1 | Out-String).Trim()
    "{0,-40} rmse {1}" -f $c, $rmse
}
foreach ($t in @(@('before', $b), @('after', $a))) { if (Test-Path "$($t[1])/stats.txt") { "--- $($t[0]) stats.txt"; Get-Content "$($t[1])/stats.txt" | Select-Object -First 60 } }
