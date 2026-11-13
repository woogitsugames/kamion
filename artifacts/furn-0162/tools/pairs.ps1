# ADR 0162 pairs (<= 960 px): photo | before Low | after Low | after High for the sbs subset; reference crop | probe Low |
# probe High for the probes. References: Mapillary CC BY-SA 4.0 / Commons (QA only, not in the game).
$W = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\furn-0162'
$A = "$W\artifacts\furn-0162"
$main = 'C:\Users\matma\Documents\Claude\kamion'
$P = "$A\pairs"; New-Item -ItemType Directory -Force $P | Out-Null
$sbs = (Get-Content "$A\sbs_subset.json" -Raw | ConvertFrom-Json).cameras
foreach ($c in $sbs) {
    $key = $c.id -replace '^sbs-g3-[ab]-', ''
    $ph = "$main\artifacts\sbs-gate3\rectified\$key.png"
    $parts = @()
    foreach ($f in @($ph, "$A\base-sbs-Low-clear\$($c.id).png", "$A\after-sbs-Low-clear\$($c.id).png", "$A\after-sbs-High-clear\$($c.id).png")) {
        if (Test-Path $f) { $parts += $f }
    }
    if ($parts.Count -lt 2) { continue }
    $lab = @('photo', 'before Low', 'after Low', 'after High')
    $tiles = @()
    for ($i = 0; $i -lt $parts.Count; $i++) {
        $t = "$P\_t$i.png"
        magick $parts[$i] -resize '480x270!' -fill white -undercolor '#000a' -pointsize 14 -gravity northwest -annotate +4+4 "$($lab[$i]) $key" $t
        $tiles += $t
    }
    while ($tiles.Count % 2) { magick -size 480x270 xc:'#222' "$P\_pad.png"; $tiles += "$P\_pad.png" }
    $rows = @()
    for ($i = 0; $i -lt $tiles.Count; $i += 2) { magick $tiles[$i] $tiles[$i + 1] +append "$P\_r$i.png"; $rows += "$P\_r$i.png" }
    magick @rows -append -quality 88 "$P\sbs-$key.jpg"
    Remove-Item "$P\_*.png"
}
$refs = @{
    'f162-p40-g3p001' = "$main\research\gptpro\3-s8-signs\files\G3-P001.jpg"
    'f162-approach-g3p012' = "$main\research\gptpro\3-s8-signs\files\G3-P013.jpg"
    'f162-tys-e1-g3p009' = "$main\research\gptpro\3-s8-signs\files\G3-P009.jpg"
    'f162-tys-vms-g3p010' = "$main\research\gptpro\3-s8-signs\files\G3-P010.jpg"
    'f162-tys-portal-g3p005' = "$main\research\gptpro\3-s8-signs\files\G3-P005.jpg"
    'f162-shelter-bus_shelter' = "$main\research\g5-street-furniture\files\G5-021_foto_wiata_zwyciestwa_commons.jpg"
    'f162-shelter-bus_shelter_5m' = "$main\research\g5-street-furniture\files\G5-001_bkm_wzor_plastyczny_wiaty_2020.jpg"
    'f162-shelter-bus_shelter_black' = "$main\research\g5-street-furniture\files\G5-020_foto_wiata_lipowa_commons.jpg"
    'f162-lamp-door' = $null
}
foreach ($k in $refs.Keys) {
    $row = @()
    if ($refs[$k]) { $row += @('(', $refs[$k], '-resize', '320x270', '-background', '#222', '-gravity', 'center', '-extent', '320x270', ')') }
    foreach ($d in 'base-probes-Low', 'after-probes-Low', 'after-probes-High') {
        $f = "$A\$d\$k.png"
        if (Test-Path $f) { $row += @('(', $f, '-resize', '320x270^', '-gravity', 'center', '-extent', '320x270', '-fill', 'white', '-undercolor', '#000a', '-pointsize', '13', '-gravity', 'northwest', '-annotate', '+4+4', ($d -replace '-probes', ''), ')') }
    }
    if ($row.Count) {
        magick @row +append -resize '960x>' -quality 88 "$P\probe-$k.jpg"
    }
}
Get-ChildItem $P | Select-Object Name, Length
