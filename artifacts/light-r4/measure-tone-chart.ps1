param([string]$InputFolder='tone-chart')
$ErrorActionPreference='Stop'
$folder=Join-Path $PSScriptRoot $InputFolder
$rows=@()
foreach($preset in @('Clear','Overcast','Dusk','Night')){
    $measure=@{}
    foreach($tier in @('Low','High')){
        $proof=Get-Content "$folder/$tier-$preset.json" -Raw|ConvertFrom-Json
        $format=''
        foreach($patch in $proof.patches){
            $x=[int][Math]::Round($patch.centrePixel.x);$y=[int][Math]::Round($patch.centrePixel.y)
            $format+="$($patch.id)|%[fx:p{$x,$y}.r*255]|%[fx:p{$x,$y}.g*255]|%[fx:p{$x,$y}.b*255]`n"
        }
        $args=@('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB',"$folder/$tier-$preset.png",'-format',$format,'info:')
        $lines=@(& magick @args)
        if($LASTEXITCODE -or $lines.Count -ne 24){throw 'Missing measured chart samples'}
        $measure[$tier]=@{}
        foreach($line in $lines){
            $v=$line.Split('|');if($v.Count -ne 4){throw 'Bad sample line'}
            $rgb=@($v[1..3]|ForEach-Object{[double]::Parse($_,[Globalization.CultureInfo]::InvariantCulture)})
            $measure[$tier][$v[0]]=$rgb
        }
    }
    foreach($id in $measure.Low.Keys|Sort-Object){
        $low=$measure.Low[$id];$high=$measure.High[$id]
        $rows+=@{preset=$preset;patch=$id;low_rgb=$low;high_rgb=$high;high_minus_low=@(($high[0]-$low[0]),($high[1]-$low[1]),($high[2]-$low[2]))}
    }
}
@{scope='One centre pixel per flat chart patch; code values0..255; exposed-linear input, not physical photometry or a source-photo comparison';samples=$rows}|ConvertTo-Json -Depth 6|Set-Content "$folder/centre-samples.json" -Encoding utf8
$rows|Where-Object {$_.patch -in @('grey-5','grey-7','grey-8','colour-6')}|ConvertTo-Json -Depth 5
