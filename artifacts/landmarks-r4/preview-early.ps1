$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Split-Path (Split-Path $PSScriptRoot))
if((& git branch --show-current).Trim() -ne 'gpt-landmarks-r4'){throw 'Unexpected preview branch'}
$flag=Join-Path $PSScriptRoot 'DIAGNOSTICS_RUNNING'
if(Test-Path $flag){throw 'Existing diagnostics marker; inspect before proceeding'}
$token=[guid]::NewGuid().ToString()
New-Item -ItemType File -Path $flag -ErrorAction Stop | Out-Null
@{owner_pid=$PID;token=$token;purpose='Early8-frame preview while read-only GIS tests queue; no model edits'} |
    ConvertTo-Json | Set-Content -LiteralPath $flag -Encoding utf8
$slot='C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
function Run-PreviewUnity([string]$Script, [hashtable]$Params) {
    & pwsh $slot -Acquire -Owner gpt-landmarks -PollSeconds 10 -StaleHours 876000
    if($LASTEXITCODE -ne 0){throw 'Early preview Unity acquisition failed'}
    try {
        & pwsh $Script @Params
        if($LASTEXITCODE -ne 0){throw "Early preview failed: $Script"}
    } finally {
        & pwsh $slot -Release -Owner gpt-landmarks
        & git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
}
try {
    Run-PreviewUnity 'artifacts/landmarks-r4/import-prepared.ps1' @{}
    $counts=@{}
    foreach($tier in @('Low','High')){
        $scene=if($tier -eq 'Low'){'WorldC'}else{'WorldC_High'}
        Run-PreviewUnity 'scripts/visual-qa.ps1' @{Scene=$scene;Tier=$tier;Lighting='overcast';
            OutputDir="artifacts/landmarks-r4/preview-crowns-early/$tier-overcast";
            Cameras='fire-station-ref7197,fire-station-abeam,fire-station-route,fire-station-above';
            Gate3='artifacts/landmarks-r4/cameras.json'}
        $count=@(Get-ChildItem "$PSScriptRoot/preview-crowns-early/$tier-overcast" -Filter '*.png').Count
        if($count -ne 4){throw 'Incomplete early preview inventory'}
        $counts["$tier-overcast"]=$count
    }
    @{complete=$true;scope='Early diagnostic8 PNG only; no completed GIS or full-camera claim';camera_counts=$counts;
      asset_sha256=(Get-FileHash art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2.glb).Hash;
      manifest_sha256=(Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash;
      cameras_sha256=(Get-FileHash artifacts/landmarks-r4/cameras.json).Hash;utc=(Get-Date).ToUniversalTime().ToString('o')} |
      ConvertTo-Json | Set-Content "$PSScriptRoot/preview-early-result.json" -Encoding utf8
} finally {
    if(Test-Path $flag){
        $marker=Get-Content -LiteralPath $flag -Raw | ConvertFrom-Json
        if($marker.owner_pid -eq $PID -and $marker.token -eq $token){Remove-Item -LiteralPath $flag}
        else {throw 'Diagnostics marker changed owner; left untouched'}
    }
}
exit 0
