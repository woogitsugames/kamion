$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$variants = [ordered]@{
    'camera-off'='rq_dither=0'
    'sky-off'='rq_skydither=0'
    'both-off'='rq_dither=0,rq_skydither=0'
    'sharp-zero'='rq_fsrsharp=0'
    'both-off-sharp-zero'='rq_dither=0,rq_skydither=0,rq_fsrsharp=0'
}
foreach($v in $variants.GetEnumerator()) {
    if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){throw 'Main PHONE_RUN lock'}
    & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Lighting clear -Cameras r10_block_3,r10_block_4,r10_house_2 -Gate3 Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json -OutputDir "artifacts/light-r12/noise/$($v.Key)" -Rq $v.Value
    if($LASTEXITCODE -ne0){throw "Failed: $($v.Key)"}
    git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings
    & uv run --project tools/worldgen python artifacts/light-r12/measure.py "artifacts/light-r12/noise/$($v.Key)" | Out-File -Encoding utf8 "artifacts/light-r12/noise/$($v.Key)/measurements.txt"
}
