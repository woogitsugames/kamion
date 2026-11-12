$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
function Read-Budget([string]$Path){
    $items=@{}
    foreach($line in Get-Content -LiteralPath $Path){
        if($line -match '^(?<id>[^:]+): objects=(?<objects>\d+) drawsEst=(?<draws>\d+) shadowDrawsEst=(?<shadow>\d+) trisK=(?<tris>\d+)'){
            $items[$Matches.id]=@{objects=[int]$Matches.objects;draws=[int]$Matches.draws;shadow=[int]$Matches.shadow;triangles=[int]$Matches.tris*1000;instancedDraws=0;instancedTriangles=0;instances=0}
        }elseif($line -match '^\s+(?<id>\S+) instanced .*draws (?<draws>\d+), instances (?<instances>\d+), triangles (?<tris>\d+)k'){
            if(-not $items.ContainsKey($Matches.id)){throw 'Missing primary budget'}
            $items[$Matches.id].instancedDraws=[int]$Matches.draws;$items[$Matches.id].instances=[int]$Matches.instances;$items[$Matches.id].instancedTriangles=[int]$Matches.tris*1000
        }
    }
    return $items
}
$entries=@();$pixels=@()
foreach($preset in @('clear','overcast','night')){foreach($tier in @('Low','High')){
    $before="$PSScriptRoot/baseline/$tier-$preset"
    $after=if($preset -eq 'night'){"$PSScriptRoot/final-v2/$tier-$preset"}else{"$PSScriptRoot/final-v1/$tier-$preset"}
    $b=Read-Budget "$before/stats.txt";$a=Read-Budget "$after/stats.txt"
    if($a.Count -ne 109 -or $b.Count -ne 109){throw 'Expected all109 cameras'}
    $probes=(Get-Content "$after/lamp-probes.json" -Raw|ConvertFrom-Json).cameras
    if($probes.Count -ne 109){throw 'Missing actual state'}
    foreach($id in $a.Keys|Sort-Object){
        if(-not $b.ContainsKey($id)){throw 'Camera mismatch'}
        $x=$b[$id];$y=$a[$id]
        $drawDelta=$y.draws+$y.shadow+$y.instancedDraws-$x.draws-$x.shadow-$x.instancedDraws
        $triDelta=100.0*($y.triangles+$y.instancedTriangles-$x.triangles-$x.instancedTriangles)/[Math]::Max(1,$x.triangles+$x.instancedTriangles)
        $probe=$probes|Where-Object camera -eq $id;$expected=if($preset -eq 'night'){.65}else{0}
        if([Math]::Abs($probe.actualDimColourDesaturation-$expected) -gt .0001){throw 'Wrong final dim uniform'}
        $entries+=@{tier=$tier;preset=$preset;camera=$id;before=$x;after=$y;totalDrawDelta=$drawDelta;totalTriangleDeltaPercent=$triDelta;actualDimColour=$probe.actualDimColourDesaturation}
        if($preset -ne 'night'){
            $args=@('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB',"$before/$id.png","$after/$id.png",'-compose','difference','-composite','-format','%[fx:mean*255] %[fx:maxima*255]','info:')
            $metric=& magick @args
            if($LASTEXITCODE){throw 'Day pixel comparison failed'}
            $values=$metric.Split(' ');$pixels+=@{tier=$tier;preset=$preset;camera=$id;meanAbsoluteRgb=[double]::Parse($values[0],[Globalization.CultureInfo]::InvariantCulture);maximumRgb=[double]::Parse($values[1],[Globalization.CultureInfo]::InvariantCulture)}
        }
    }
}}
@{scope='Rounded CPU scene estimates before SRP batching, instancing separately included; not GPU or A16';entries=$entries}|ConvertTo-Json -Depth 8|Set-Content "$PSScriptRoot/final-budget-all.json" -Encoding utf8
@{scope='All436 unchanged-preset camera PNG comparisons, codevalues0..255; any residual difference reported, no blanket pixel-identity claim';entries=$pixels}|ConvertTo-Json -Depth 6|Set-Content "$PSScriptRoot/day-pixel-deltas.json" -Encoding utf8
if($entries.Count -ne 654 -or @($entries|Where-Object {$_.totalDrawDelta -gt 0 -or $_.totalTriangleDeltaPercent -gt 2}).Count){throw 'Incomplete/regressed budget'}
$entries|Group-Object totalDrawDelta,totalTriangleDeltaPercent|Select-Object Count,Name
$pixels|Measure-Object meanAbsoluteRgb,maximumRgb -Maximum|Select-Object Property,Maximum
