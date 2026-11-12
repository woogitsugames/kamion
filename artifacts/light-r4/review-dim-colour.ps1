$ErrorActionPreference='Stop'
$jobs=(Get-Content "$PSScriptRoot/dim-colour-v2.json" -Raw|ConvertFrom-Json).jobs
foreach($tier in @('Low','High')){
    foreach($id in $jobs[0].cameras.Split(',')){
        $args=@('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB')
        foreach($strength in @(0,.35,.65,1)){
            $job=$jobs|Where-Object {$_.tier -eq $tier -and $_.dimColourDesaturation -eq $strength}
            $probe=(Get-Content (Join-Path $job.output 'lamp-probes.json') -Raw|ConvertFrom-Json).cameras|Where-Object camera -eq $id
            if($null -eq $probe -or [Math]::Abs($probe.actualDimColourDesaturation-$strength) -gt .0001){throw 'Dim-colour actual uniform mismatch'}
            $args+=@('(',(Join-Path $job.output "$id.png"),'-resize','478x221','-background','#202020','-gravity','south','-splice','0x22',
                '-fill','white','-pointsize','11','-annotate','0',"$tier dim$strength / $id",')')
        }
        $args+=@('-append','+repage',"$PSScriptRoot/native-review/dim-colour-$tier-$id.jpg")
        & magick @args
        if($LASTEXITCODE){throw 'Contact failed'}
    }
}
