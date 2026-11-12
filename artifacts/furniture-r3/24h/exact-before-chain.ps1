$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r3/24h'
try {
    foreach($light in @('clear','overcast')){
        & pwsh "$ev/exact-stats.ps1" -Phase before -Tier Low -Lighting $light
        if($LASTEXITCODE -ne 0){throw "Baseline exact counter failed:$light"}
    }
} finally {
    # This is our local scheduling file, not a machine slot or another owner's marker.
    Remove-Item -LiteralPath "$ev/PAUSE_UNITY" -ErrorAction SilentlyContinue
}
