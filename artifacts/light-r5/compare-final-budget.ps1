$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
function ReadBudget([string]$path){
    $items=@{}
    foreach($line in Get-Content -LiteralPath $path){
        if($line -match '^(?<id>[^:]+): objects=(?<objects>\d+) drawsEst=(?<draws>\d+) shadowDrawsEst=(?<shadow>\d+) trisK=(?<tris>\d+)'){
            $items[$Matches.id]=@{objects=[int]$Matches.objects;draws=[int]$Matches.draws;shadow=[int]$Matches.shadow;triangles=[int]$Matches.tris*1000;instancedDraws=0;instancedTriangles=0;instances=0}
        }elseif($line -match '^\s+(?<id>\S+) instanced .*draws (?<draws>\d+), instances (?<instances>\d+), triangles (?<tris>\d+)k'){
            if(-not $items.ContainsKey($Matches.id)){throw 'Missing primary budget'}
            $items[$Matches.id].instancedDraws=[int]$Matches.draws;$items[$Matches.id].instances=[int]$Matches.instances;$items[$Matches.id].instancedTriangles=[int]$Matches.tris*1000
        }
    }
    return $items
}
$entries=@();$proofs=@()
foreach($preset in 'clear','overcast','night'){
    $before=ReadBudget "$PSScriptRoot/baseline/Low-$preset/stats.txt"
    $after=ReadBudget "$PSScriptRoot/final-native/Low-$preset/stats.txt"
    if($before.Count -ne 109 -or $after.Count -ne 109){throw 'Require all109 route cameras'}
    $proof=Get-Content "$PSScriptRoot/final-native/Low-$preset/opaque-grade-proof.json" -Raw|ConvertFrom-Json
    $hdr=Get-Content "$PSScriptRoot/final-native/High-$preset/hdr-reference-proof.json" -Raw|ConvertFrom-Json
    if($proof.frames.Count -ne 109 -or $hdr.frames.Count -ne 109){throw 'Require complete actual proof'}
    if(@($proof.frames|Where-Object {$_.enabled -ne 1 -or $_.physicalCaptureBypass -ne 0 -or $_.actualDomainMode -ne 1}).Count){throw 'Native LUT absent/domain/bypass'}
    if(@($hdr.frames|Where-Object {$_.colorBeforePostFormat -ne 'R16G16B16A16_SFloat' -or -not $_.hdrEnabled -or -not $_.postEnabled}).Count){throw 'Actual HDR missing'}
    foreach($id in $before.Keys){
        if(-not $after.ContainsKey($id)){throw "Missing camera $id"}
        $b=$before[$id];$a=$after[$id]
        $d=$a.draws+$a.shadow+$a.instancedDraws-$b.draws-$b.shadow-$b.instancedDraws
        $t=100.0*($a.triangles+$a.instancedTriangles-$b.triangles-$b.instancedTriangles)/[Math]::Max(1,$b.triangles+$b.instancedTriangles)
        $entries+=@{preset=$preset;camera=$id;before=$b;after=$a;totalDrawDelta=$d;totalTriangleDeltaPercent=$t}
    }
    $proofs+=@{preset=$preset;nativeFrames=$proof.frames.Count;hdrFrames=$hdr.frames.Count}
}
@{scope='Rounded CPU estimates before SRP; Low native versus same-round fresh baseline, all109 cameras and3 presets. Instances separately. No GPU/phone claim.';entries=$entries;actualProofCounts=$proofs}|ConvertTo-Json -Depth 8|Set-Content "$PSScriptRoot/final-native-budget-all.json" -Encoding utf8
if($entries.Count -ne 327 -or @($entries|Where-Object {$_.totalDrawDelta -gt 0 -or $_.totalTriangleDeltaPercent -gt 2}).Count){throw 'Budget failed'}
$entries|Group-Object totalDrawDelta,totalTriangleDeltaPercent|Select-Object Count,Name
