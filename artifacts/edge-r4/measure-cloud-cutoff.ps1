$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$prediction=Get-Content "$PSScriptRoot/cloud-horizon-prediction.json" -Raw|ConvertFrom-Json
$rows=foreach($camera in $prediction.cameras){
    $line=$camera.source_horizon_line
    $slope=($line[2].y-$line[0].y)/($line[2].x-$line[0].x)
    foreach($x in @(960,1020,1080,1140,1200)){
        $predicted=$line[0].y+$slope*$x
        $top=[int][Math]::Floor($predicted)-12
        $results=@{}
        foreach($phase in @('before','cloud-off')){
            $file=if($phase -eq 'before'){"$PSScriptRoot/before-photo/Low-clear/1280x720/$($camera.camera).png"}else{"$PSScriptRoot/cloud-ablation/$($camera.camera).png"}
            $lines=& magick -limit thread 1 $file -crop "1x27+$x+$top" +repage -colorspace Gray -depth 8 txt:-
            if($LASTEXITCODE -ne 0){throw 'Pixel strip failed'}
            $values=@($lines|ForEach-Object {if($_ -match '^0,\d+: \((\d+)') {[int]$Matches[1]}})
            if($values.Count -ne 27){throw 'Unexpected pixel count'}
            $edges=for($i=1;$i -lt $values.Count;$i++){
                [PSCustomObject]@{y=$top+$i-0.5;drop=$values[$i-1]-$values[$i]}
            }
            $worst=$edges|Sort-Object drop -Descending|Select-Object -First 1
            $results[$phase]=@{largest_adjacent_drop_8bit=$worst.drop;drop_midpoint_y=$worst.y;
                residual_from_prediction_px=$worst.y-$predicted;gray_strip=$values}
        }
        @{camera=$camera.camera;x=$x;predicted_y=$predicted;strip_top=$top;strip_height=27;results=$results}
    }
}
@{diagnostic_only=$true;selection='Predefined x=960,1020,1080,1140,1200 in each 1280x720 view; vertical strip predicted cutoff +/-12 pixels';
  method='Largest adjacent downward grayscale step; native PNG converted to 8bit Gray by ImageMagick. No photo measurement.';
  rows=@($rows);threshold_status='No pass threshold; values characterize the source-cutoff hypothesis'}|
    ConvertTo-Json -Depth 9|Set-Content "$PSScriptRoot/cloud-cutoff-measurement.json"
$rows|ForEach-Object {[PSCustomObject]@{camera=$_.camera;x=$_.x;
    baseline_drop=$_.results.before.largest_adjacent_drop_8bit;
    ablation_drop=$_.results.'cloud-off'.largest_adjacent_drop_8bit;
    baseline_residual=$_.results.before.residual_from_prediction_px}}|Format-Table -AutoSize
