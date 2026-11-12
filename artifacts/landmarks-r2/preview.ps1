$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
$marker="$PSScriptRoot/DIAGNOSTICS_RUNNING"
if(Test-Path $marker){throw 'An existing local diagnostic owns this project'}
New-Item -ItemType File -Path $marker | Out-Null
$slot='C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$mine='C:\Users\matma\Documents\Claude\kamion\artifacts\locks\unity-slots\gpt-landmarks.slot'
# The queued candidate wrapper waits on our marker before every Unity acquire.
# Only this diagnostic owns/ignores this marker, never a shared machine lock.
function Invoke-PreviewUnity([string]$Script,[hashtable]$Parameters) {
    while(Test-Path $mine){Start-Sleep -Seconds 2}
    & pwsh $slot -Acquire -Owner gpt-landmarks -PollSeconds 10 -StaleHours 876000
    if($LASTEXITCODE -ne 0){throw 'Preview Unity acquisition failed'}
    try {
        & pwsh $Script @Parameters
        if($LASTEXITCODE -ne 0){throw "Preview Unity failed: $Script"}
    } finally {
        & pwsh $slot -Release -Owner gpt-landmarks
        & git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
}
try {
    Start-Sleep -Seconds 2
    Invoke-PreviewUnity 'artifacts/landmarks-r2/import-prepared.ps1' @{}
    foreach($tier in @('Low','High')) {
        foreach($light in @('overcast','clear')) {
            $scene=if($tier -eq 'High'){'WorldC_High'}else{'WorldC'}
            Invoke-PreviewUnity 'scripts/visual-qa.ps1' @{
                Scene=$scene; Tier=$tier; Lighting=$light;
                OutputDir="artifacts/landmarks-r2/after-preview/$tier-$light";
                Cameras='dk8-under-span,dk8-bearing,dk8-abutment,dk8-west-interior,dk8-ref7204';
                Gate3='artifacts/landmarks-r2/cameras.json'
            }
        }
    }
} finally {
    Remove-Item -LiteralPath $marker -ErrorAction SilentlyContinue
}
@{complete=$true;camera_conditions=20;purpose='diagnostic subset; not the final all-camera budget'} | ConvertTo-Json | Set-Content -Encoding utf8 "$PSScriptRoot/preview-result.json"
