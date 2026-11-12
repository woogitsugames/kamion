param([string]$Phase='first')
$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r2/24h'
& pwsh "$ev/unity-step.ps1" -Step sign-probe -Phase $Phase
$code=$LASTEXITCODE
if ($code -eq 0) {
    Remove-Item -LiteralPath "$ev/PAUSE_UNITY" -ErrorAction SilentlyContinue
} else {
    Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): próba znaków nie przeszła (exit=$code). Własny import/render pozostaje wstrzymany przez PAUSE_UNITY do odczytu logu i naprawy. NASTĘPNY KROK: odczytać sign-probe-first.log oraz XML, usunąć marker dopiero po usunięciu błędu kompilacji."
    Copy-Item "$ev/STATUS.md" artifacts/furniture-r2/STATUS.md
}
exit $code
