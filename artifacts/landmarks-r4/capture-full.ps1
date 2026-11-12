param([Parameter(Mandatory)][ValidateSet('b','c')][string]$Model,
      [Parameter(Mandatory)][ValidatePattern('^[a-z0-9-]+$')][string]$Phase)
$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
if((& git branch --show-current).Trim() -ne 'gpt-landmarks-r4'){throw 'Unexpected capture branch'}
$binding=Get-Content "$PSScriptRoot/preview-$Model-result.json" -Raw | ConvertFrom-Json
if(-not $binding.complete){throw 'Model preview is incomplete'}
function Check-Inputs {
    if((Get-FileHash art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2.glb).Hash -ne $binding.asset_sha256){throw 'Model changed since preview'}
    if((Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash -ne $binding.manifest_sha256){throw 'Manifest changed since preview'}
    if((Get-FileHash artifacts/landmarks-r4/cameras.json).Hash -ne $binding.cameras_sha256){throw 'Camera definitions changed'}
}
Check-Inputs
& pwsh artifacts/landmarks-r4/unity-step.ps1 -Step Capture -Phase $Phase -Cameras all
if($LASTEXITCODE -ne 0){throw 'Full camera capture failed'}
Check-Inputs
$baseline=Get-Content "$PSScriptRoot/baseline-result.json" -Raw | ConvertFrom-Json
$inventories=@{}
$total=0
foreach($condition in @('Low-overcast','Low-clear','High-overcast','High-clear')){
    $names=@(Get-ChildItem "$PSScriptRoot/$Phase/$condition" -Filter '*.png' | Select-Object -ExpandProperty Name | Sort-Object)
    $expected=@($baseline.camera_inventories.$condition | Sort-Object)
    if(@(Compare-Object $names $expected).Count -ne 0){throw "Incomplete inventory: $condition"}
    $inventories[$condition]=$names
    $total+=$names.Count
}
if($total -ne 244){throw "Unexpected total $total"}
@{complete=$true;phase=$Phase;model=$Model;camera_conditions=$total;camera_inventories=$inventories;
    asset_sha256=$binding.asset_sha256;manifest_sha256=$binding.manifest_sha256;cameras_sha256=$binding.cameras_sha256;
    scope='Full captured inventory; visual review and end-of-round tests still required';utc=(Get-Date).ToUniversalTime().ToString('o')} |
    ConvertTo-Json -Depth 5 | Set-Content "$PSScriptRoot/capture-$Phase-result.json" -Encoding utf8
exit 0
