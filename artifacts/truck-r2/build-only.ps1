$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
# Existing ignored build inputs only; no audio generator and no changes to audio source code.
if (!(Test-Path art-source/audio/generated/manifest.json)) {
    robocopy 'C:/Users/matma/Documents/Claude/kamion/art-source/audio/generated' 'art-source/audio/generated' /E /XJ /R:1 /W:1 /NFL /NDL /NJH /NJS
    if ($LASTEXITCODE -gt 7 -or !(Test-Path art-source/audio/generated/manifest.json)) { throw 'Brak gotowych wejść audio z main.' }
}
pwsh $slotScript -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 5
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
$start = Get-Date
try {
    # No -Install, -Run or device arguments: build-android exits before resolving devices.
    pwsh scripts/build-android.ps1 -WorldHigh
    if ($LASTEXITCODE -ne 0) { throw 'Nieudana kompilacja Android.' }
    $apk = Get-ChildItem artifacts/apk -Filter '*-high.apk' | Where-Object LastWriteTime -ge $start | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $log = Get-ChildItem artifacts/logs -Filter 'build-*.log' | Where-Object LastWriteTime -ge $start | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (!$apk -or !$log) { throw 'Brak świeżego APK lub logu.' }
    New-Item -ItemType Directory -Force artifacts/truck-r2/build | Out-Null
    Copy-Item -LiteralPath $apk.FullName,($apk.FullName + '.sha256') -Destination artifacts/truck-r2/build
    Copy-Item -LiteralPath $log.FullName -Destination artifacts/truck-r2/build/unity.log
    $buildSha = [regex]::Match($apk.Name, '-(?<sha>[0-9a-f]{10})(?:-dirty)?-high\.apk$').Groups['sha'].Value
    if (!$buildSha) { throw 'Nie odczytano SHA wejściowego z nazwy APK.' }
    [ordered]@{ result='Succeeded'; apk=$apk.Name; bytes=$apk.Length; sha256=(Get-FileHash -LiteralPath $apk.FullName -Algorithm SHA256).Hash; install=$false; run=$false; world_high=$true; source_commit=(git rev-parse $buildSha); evidence_commit_at_finish=(git rev-parse HEAD) } | ConvertTo-Json | Set-Content -Encoding utf8 artifacts/truck-r2/build/result.json
}
finally {
    pwsh $slotScript -Release -Owner gpt-truck
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Add-Content -Encoding utf8 artifacts/truck-r2/STATUS.md 'Build Android z Low i High zakończony poprawnie. APK, SHA i log w build/. Bez instalowania, uruchamiania i pomiarów telefonu. Następny krok: dokończyć REPORT i skopiować artefakty do main.'
git add -f artifacts/truck-r2/STATUS.md artifacts/truck-r2/build/result.json
git commit --only artifacts/truck-r2/STATUS.md artifacts/truck-r2/build/result.json -m 'wip(truck): Android APK bez uzywania telefonu'
