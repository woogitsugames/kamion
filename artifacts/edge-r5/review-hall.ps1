$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if(-not(Test-Path "$PSScriptRoot/After.complete")){throw 'Complete After first'}
$out=Join-Path $PSScriptRoot 'hall-review'
New-Item -ItemType Directory -Force $out|Out-Null
foreach($tier in @('Low','High')){
    foreach($lighting in @('clear','overcast')){
        $config="$tier-$lighting"
        foreach($phase in @('before','after')){
            # Same rectangle in the frozen 2340x1080 image. A diagnostic crop,
            # not an extra camera or a photograph-identification claim.
            & magick -limit thread 1 "$PSScriptRoot/$phase/$config/edge-south.png" `
                -crop 520x260+650+360 +repage -resize 480x240 `
                -background white -fill black -font Arial -pointsize 14 `
                -gravity NorthWest -splice 0x28 -annotate +4+5 "$phase | $config | diagnostic crop" `
                "$out/$config-$phase.png"
            if($LASTEXITCODE -ne0){throw "Crop failed: $phase/$config"}
        }
        & magick -limit thread 1 "$out/$config-before.png" "$out/$config-after.png" +append "$out/$config-pair.jpg"
        if($LASTEXITCODE -ne0){throw "Pair failed: $config"}
    }
}
@{source_dimensions=@(2340,1080);crop_xywh=@(650,360,520,260);panel_dimensions=@(480,268);
  pair_dimensions=@(960,268);note='Diagnostic identical crop; full frames and native photograph pairs remain separate.'}|
  ConvertTo-Json|Set-Content "$out/crop-procedure.json"
