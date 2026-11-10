$ErrorActionPreference='Stop'
Set-Location "$PSScriptRoot/../.."
function Save-Progress([string]$Text,[string]$Commit) {
    Add-Content artifacts/megascans-r1/STATUS.md "`n$Text"
    git add -f artifacts/megascans-r1/STATUS.md
    git commit -m $Commit
}
function Check-PhoneLock {
    while (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') {
        Write-Host 'PHONE_RUN active; waiting before Unity'
        Start-Sleep -Seconds 45
    }
}
$failed=$false
try {
    $env:KAMION_DISABLE_FAB='1'
    $env:PYTHONUNBUFFERED='1'
    uv run --project tools/worldgen python artifacts/megascans-r1/run-fallback-build.py *> artifacts/megascans-r1/fallback-build-launch.log
    if ($LASTEXITCODE -ne 0) {throw 'Fallback build failed'}
    Save-Progress '- Krok19: build z KAMION_DISABLE_FAB=1 OK. NASTĘPNY: pwsh scripts/import-region.ps1 -Region bialystok-industrial-c (wciąż fallback); kopiaafter zabezpieczona.' 'wip(megascans): verify complete world build with licensed content disabled'
    Check-PhoneLock
    pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> artifacts/megascans-r1/fallback-import.log
    if ($LASTEXITCODE -ne 0) {throw 'Fallback import failed'}
    Save-Progress '- Krok20: import fallback Low+High OK. NASTĘPNY: pwsh artifacts/megascans-r1/run-camera-proof.ps1 -Stage before; potem identyczne kadry before i odtworzenieafter.' 'wip(megascans): verify public-clone material and prototype fallback import'
    Check-PhoneLock
    pwsh artifacts/megascans-r1/run-camera-proof.ps1 -Stage before *> artifacts/megascans-r1/detail-before-proof.log
    if ($LASTEXITCODE -ne 0) {throw 'Before camera ground proof failed'}
    Check-PhoneLock
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Gate3 artifacts/megascans-r1/detail-cameras.json -Cameras 'megascans_eye_manhole_s0928,megascans_eye_gully_s0482,megascans_eye_verge_s0523' -OutputDir artifacts/megascans-r1/detail-before/Low-overcast *> artifacts/megascans-r1/detail-before-Low.log
    if ($LASTEXITCODE -ne 0) {throw 'Before Low capture failed'}
    Check-PhoneLock
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting overcast -Gate3 artifacts/megascans-r1/detail-cameras.json -Cameras 'megascans_eye_manhole_s0928,megascans_eye_gully_s0482,megascans_eye_verge_s0523' -OutputDir artifacts/megascans-r1/detail-before/High-overcast *> artifacts/megascans-r1/detail-before-High.log
    if ($LASTEXITCODE -ne 0) {throw 'Before High capture failed'}
    Check-PhoneLock
    pwsh scripts/test.ps1 -Platform EditMode *> artifacts/megascans-r1/editmode-without-fab.log
    if ($LASTEXITCODE -ne 0) {throw 'EditMode without Fab failed'}
    Save-Progress '- Krok21: prawdziwe kadry before i EditMode fallback zakończone. NASTĘPNY: restore prywatnej kopiiafter; nie pozostawiać scenyfallback jako wyniku.' 'wip(megascans): capture genuine no-Fab driving views and run fallback EditMode'
}
catch {
    $failed=$true
    Write-Error $_ -ErrorAction Continue
}
finally {
    $env:KAMION_DISABLE_FAB=$null
    uv run --project tools/worldgen python artifacts/megascans-r1/reversible_qa_state.py restore
    if ($LASTEXITCODE -ne 0) {throw 'Cannot restore final after state; stop and inspect project lock'}
    Copy-Item artifacts/megascans-r1/round3/import-report.json artifacts/world/bialystok-industrial-c-import.json
    Save-Progress '- Krok22: odtworzono wygenerowany światafter (archiwum1989plików); KAMION_DISABLE_FAB wyłączone. NASTĘPNY: powtórny raycast i sanityrender after, walidacja SHA192plików.' 'wip(megascans): restore final licensed world after reversible fallback proof'
}
if ($failed) {exit 1}

