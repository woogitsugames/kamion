param([string]$Jobs='artifacts/light-r6/horizon-triage.json')
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));Set-Location $repo
$spec=Get-Content -LiteralPath $Jobs -Raw|ConvertFrom-Json
$proof=@()
function NearZero($value,$context){
    $number=[double]$value
    if($null -eq $value -or [double]::IsNaN($number) -or [double]::IsInfinity($number) -or [Math]::Abs($number) -gt .0001){throw "Unexpected actual state: $context = $value"}
}
foreach($job in $spec.jobs){
    $file=Join-Path $job.output 'lamp-probes.json'
    $document=Get-Content -LiteralPath $file -Raw|ConvertFrom-Json
    $rows=@($document.cameras)
    $ids=@($job.cameras.Split(',')|ForEach-Object Trim|Select-Object -Unique)
    if($rows.Count -ne $ids.Count -or $rows.Count -ne [int]$spec.expectedCamerasPerJob){throw "Incomplete probe count: $file"}
    if(@($rows.camera|Select-Object -Unique).Count -ne $rows.Count){throw "Duplicate camera probes: $file"}
    $rq=@{};foreach($pair in $job.rq.Split(',')){$keyValue=$pair.Split('=');$rq[$keyValue[0].Trim()]=$keyValue[1].Trim()}
    foreach($row in $rows){
        if($ids -notcontains $row.camera){throw "Unexpected camera: $($row.camera)"}
        foreach($name in 'actualClearCloudCover','actualClearCloudPhoto','actualCloud','actualHaze','actualSkyCap','actualCloudRotationUp','requestedHorizonLock'){
            if($row.PSObject.Properties.Name -notcontains $name){throw "Missing current diagnostic field $name in $file"}
        }
        if(($rq.ContainsKey('rq_clearcover') -and [double]$rq.rq_clearcover -eq 0) -or $rq.rq_clouds -eq '-1'){
            NearZero $row.actualClearCloudCover "$($row.camera) clear coverage"
            NearZero $row.actualClearCloudPhoto "$($row.camera) photographic branch"
        }
        if($rq.rq_clouds -eq '-1'){NearZero $row.actualCloud.x "$($row.camera) procedural contrast"}
        if($rq.rq_haze -eq '0'){NearZero $row.actualHaze.y "$($row.camera) ground layer factor"}
        if($job.overrideSunElevation){NearZero ([double]$row.sunElevation-[double]$job.sunElevationDeg) "$($row.camera) actual sun elevation"}
        if($rq.ContainsKey('rq_cloudhorizon')){
            $requested=$rq.rq_cloudhorizon -eq '1'
            if([bool]$row.requestedHorizonLock -ne $requested){throw 'Horizon override was not retained'}
            # Rotation is only an active-path proof when Push actually used the photographic branch.
            if($requested -and [double]$row.actualClearCloudPhoto -gt .5 -and [double]$row.actualClearCloudCover -gt 0){
                NearZero $row.actualCloudRotationUp.x 'horizon rotation up.x'
                NearZero ([double]$row.actualCloudRotationUp.y-1) 'horizon rotation up.y'
                NearZero $row.actualCloudRotationUp.z 'horizon rotation up.z'
            }
        }
    }
    $proof+=@{folder=$job.output;probeSha=(Get-FileHash -LiteralPath $file).Hash;cameras=$rows.Count;status='Actual state agrees with explicit ablations; visual and GPU review still required'}
}
$output=[IO.Path]::ChangeExtension($Jobs,'.state-proof.json')
$proof|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $output -Encoding utf8
Write-Output "Verified actual ablation state in $($proof.Count) jobs. Not a visual PASS."
