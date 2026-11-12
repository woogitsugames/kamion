param([string]$Source='artifacts/light-r5/final-native-v2/Low-night/lamp-probes.json',
      [string]$Output='artifacts/light-r6/night-selected-pool-centres.json')
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));Set-Location $repo
$document=Get-Content -LiteralPath $Source -Raw|ConvertFrom-Json
$rows=@()
foreach($camera in $document.cameras){
    $visible=0;$valid=0
    if($camera.poolGroundViewport.Count -ne $camera.poolGroundPoints.Count){throw 'Mismatched probe arrays'}
    for($i=0;$i -lt $camera.poolGroundViewport.Count;$i++){
        $v=$camera.poolGroundViewport[$i];$ground=$camera.poolGroundPoints[$i]
        if($ground.w -gt .5){
            $valid++
            if($v.z -gt 0 -and $v.x -ge 0 -and $v.x -le 1 -and $v.y -ge 0 -and $v.y -le 1){$visible++}
        }
    }
    $rows+=@{camera=$camera.camera;selectedPools=$camera.pools;validDownwardRayGroundHits=$valid;
        centresInsideViewport=$visible;nominalLuxNoOcclusion=@($camera.nominalRoadLuxNoOcclusion);exposure=$camera.exposure}
}
@{scope='Only the named source capture. Projected pool centres do not prove illumination or its absence: radius, overlap, normals, occlusion and pixel shading require separate assessment.';
  source=$Source;sourceSha=(Get-FileHash -LiteralPath $Source).Hash;cameras=$rows.Count;
  zeroCentresInsideViewport=@($rows|Where-Object centresInsideViewport -eq 0).Count;
  atLeastOneCentreInsideViewport=@($rows|Where-Object centresInsideViewport -gt 0).Count;rows=$rows
}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $Output -Encoding utf8
Write-Output "Projected selected pool centres recorded for $($rows.Count) cameras. No pixel/light/GPU PASS."
