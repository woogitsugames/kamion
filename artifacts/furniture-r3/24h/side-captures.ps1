param([ValidateSet('before-side','after-side','after2-side')][string]$Phase='before-side')
$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r3/24h'
$ownedPause=$Phase -eq 'before-side'
if($ownedPause){'Owned extra baseline corner captures'|Set-Content "$ev/PAUSE_UNITY"}
try{
    foreach($tier in @('Low','High')){
        foreach($light in @('clear','overcast')){
            # This capture is the scheduling marker owner; regular import/render waits on it.
            # Use a separate method invocation below with a scoped bypass, never another Unity process.
            & pwsh "$ev/unity-step.ps1" -Step side-render -Phase $Phase -Tier $tier -Lighting $light -CameraFile "$ev/side-cameras.json" -Cameras 'furniture-shelter-anders-1000-reverse,furniture-shelter-factory-reverse'
            if($LASTEXITCODE -ne 0){throw "Second corner capture failed:$tier $light"}
        }
    }
}finally{
    if($ownedPause){Remove-Item -LiteralPath "$ev/PAUSE_UNITY" -ErrorAction SilentlyContinue}
}
