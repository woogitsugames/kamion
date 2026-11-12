$ErrorActionPreference = 'Stop'
$jobs = @()
foreach ($tier in @('Low','High')) {
    foreach ($wet in @(0,1)) {
        foreach ($useLocal in @($false,$true)) {
            $scene = if ($tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
            $state = if ($useLocal) { 'on' } else { 'off' }
            $jobs += @{
                scene=$scene; tier=$tier; lighting='overcast'
                cameras='light-night-driver,sbs-g3-a-2948595898752384'
                output="artifacts/light-r3/wet-local/$tier-wet$wet-$state"
                width=2340; height=1080; lampProbe=$true; actualDriverEye=$true
                verifyWetness=$true; expectedWetness=$wet
                rq="rq_wet=$wet,rq_headlamps=0"; expectedHeadlamps=1
                overrideWetLocalReflections=$true; wetLocalReflections=$useLocal
            }
        }
    }
}
@{jobs=$jobs} | ConvertTo-Json -Depth 8 | Set-Content "$PSScriptRoot/wet-local.json" -Encoding utf8
