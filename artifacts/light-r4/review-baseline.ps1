param([string]$JobsFile='baseline.json',[string]$Prefix='baseline',[string]$Preset)
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$jobs=(Get-Content (Join-Path $PSScriptRoot $JobsFile) -Raw|ConvertFrom-Json).jobs
if($Preset){$jobs=@($jobs|Where-Object lighting -eq $Preset)}
$out="$PSScriptRoot/native-review"
New-Item -ItemType Directory -Force $out|Out-Null
$inventory=@()
foreach($job in $jobs){
    $files=@(Get-ChildItem -LiteralPath $job.output -Filter '*.png'|Sort-Object Name)
    $probes=(Get-Content (Join-Path $job.output 'lamp-probes.json') -Raw|ConvertFrom-Json).cameras
    if($files.Count -eq 0 -or $probes.Count -ne $files.Count){throw 'Missing complete baseline/probe set'}
    foreach($probe in $probes){if([Math]::Abs($probe.actualWetness) -gt .0001 -or $probe.projectedHeadlamps){throw 'Baseline state mismatch'}}
    for($start=0;$start -lt $files.Count;$start+=12){
        $args=@('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB')
        $end=[Math]::Min($start+12,$files.Count)
        for($row=$start;$row -lt $end;$row+=3){
            $args+='('
            for($i=$row;$i -lt [Math]::Min($row+3,$end);$i++){
                $args+=@('(',$files[$i].FullName,'-resize','318x147','-background','#202020','-gravity','south','-splice','0x24',
                    '-fill','white','-pointsize','10','-annotate','0',"$($job.tier) $($job.lighting) / $($files[$i].BaseName)",')')
            }
            $args+=@('+append',')')
        }
        $page=1+[int][Math]::Floor($start/12)
        $contact="$out/$Prefix-$($job.tier)-$($job.lighting)-$page.jpg"
        $args+=@('-append','+repage',$contact)
        & magick @args
        if($LASTEXITCODE){throw 'Contact generation failed'}
        $inventory+=@{contact=$contact;tier=$job.tier;preset=$job.lighting;inputs=@($files[$start..($end-1)].FullName)}
    }
}
$inventory|ConvertTo-Json -Depth 6|Set-Content "$out/$Prefix-inventory.json" -Encoding utf8
Write-Output "Prepared$($inventory.Count) contacts covering all baseline PNGs. Inspect every page; no visual verdict from this script."

