param([switch]$SkipGenerators)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$other = @(Get-CimInstance Win32_Process -Filter "Name='pwsh.exe'" | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -match 'truck-r3[/\\]prepare-baseline\.ps1' })
if ($other.Count) { throw 'Poprzednia procedura nadal działa; nie wolno współdzielić jej Owner heavy.' }
if ($SkipGenerators -and (!(Select-String -LiteralPath artifacts/truck-r3/STATUS.md -SimpleMatch 'Generator materials zakończony pod heavy' -Quiet) -or !(Select-String -LiteralPath artifacts/truck-r3/STATUS.md -SimpleMatch 'Generator world zakończony pod heavy' -Quiet))) { throw 'Brak potwierdzenia ukończenia obu generatorów przed wznowieniem.' }
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal'
foreach ($job in @(
    @{id='materials';args=@('run','--project','tools/worldgen','python','art-source/world/materials/_src/build_all.py')},
    @{id='world';args=@('run','--project','tools/worldgen','tools/worldgen/roads/build_world.py','--region','bialystok-industrial-c')}
)) {
    if ($SkipGenerators) { continue }
    pwsh $slotScript -Acquire -Pool heavy -Owner gpt-truck-r3 -StaleHours 100000 -PollSeconds 1
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu heavy.' }
    try {
        $arguments = $job.args
        uv @arguments *> "artifacts/truck-r3/baseline-$($job.id).log"
        if ($LASTEXITCODE -ne 0) { throw "Nieudany generator $($job.id)." }
        if (Select-String -LiteralPath "artifacts/truck-r3/baseline-$($job.id).log" -SimpleMatch 'fallback=True' -Quiet) { throw 'Fallback Megascans; nie wolno użyć takiej bazy.' }
    }
    finally { pwsh $slotScript -Release -Pool heavy -Owner gpt-truck-r3 }
    Add-Content -Encoding utf8 artifacts/truck-r3/STATUS.md "Generator $($job.id) zakończony pod heavy, bez fallback=True. Następny krok: pozostałe wejścia, import i baseline r3."
    git add -f artifacts/truck-r3/STATUS.md
    git commit --only artifacts/truck-r3/STATUS.md -m "wip(truck): wejscia r3 $($job.id)"
}
# Guard import-region's automatic Python fallbacks before occupying Unity.
$spec = Get-Content art-source/world/materials/materials_spec.json -Raw | ConvertFrom-Json
$sourceTime = (Get-ChildItem art-source/world/materials/_src -Filter *.py | Measure-Object LastWriteTimeUtc -Maximum).Maximum
$photoNeedsBuild = $false
foreach ($tier in $spec.sets.asphalt_detail_photo.files.PSObject.Properties) {
    foreach ($name in $tier.Value.files) {
        $file = Get-Item -LiteralPath (Join-Path 'art-source/world/materials' "$($tier.Value.dir)/$name") -ErrorAction SilentlyContinue
        if (!$file -or $file.LastWriteTimeUtc -lt $sourceTime) { $photoNeedsBuild = $true }
    }
}
if ($photoNeedsBuild) {
    if (!(Test-Path Data/photos/nowe/Worn_cracked_asphalt_pavement.jpg)) { throw 'Brak lokalnej kopii dostarczonego zdjęcia detalu asfaltu.' }
    pwsh $slotScript -Acquire -Pool heavy -Owner gpt-truck-r3 -StaleHours 100000 -PollSeconds 1
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu heavy dla brakującej warstwy.' }
    try {
        uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only asphalt_detail_photo *> artifacts/truck-r3/baseline-photo-layer.log
        if ($LASTEXITCODE -ne 0) { throw 'Nie wygenerowano brakującej warstwy zdjęciowej.' }
    }
    finally { pwsh $slotScript -Release -Pool heavy -Owner gpt-truck-r3 }
    Add-Content -Encoding utf8 artifacts/truck-r3/STATUS.md 'Uzupełniono wyłącznie pominiętą warstwę asfalt_detail_photo pod heavy. Zdjęcie wejściowe skopiowano z main z identycznym SHA. Bez zmiany źródeł asfaltu. Następny krok: import aktualnej bazy.'
    git add -f artifacts/truck-r3/STATUS.md
    git commit --only artifacts/truck-r3/STATUS.md -m 'wip(truck): komplet brakujacego wejscia importu r3'
    $spec = Get-Content art-source/world/materials/materials_spec.json -Raw | ConvertFrom-Json
}
foreach ($set in $spec.sets.PSObject.Properties) {
    $tier = $set.Value.files.Medium
    foreach ($name in $tier.files) {
        $file = Get-Item -LiteralPath (Join-Path 'art-source/world/materials' "$($tier.dir)/$name")
        if ($file.LastWriteTimeUtc -lt $sourceTime) { throw 'Import uruchomiłby ponownie build_all; sprawdź wejścia.' }
    }
}
if (!(Test-Path Data/raw/derived/bialystok-industrial-c/world/chunk_0_0.glb) -or !(Test-Path Data/Regions/bialystok-industrial-c/route_start.json)) { throw 'Brak wejść; import uruchomiłby dodatkowego Pythona.' }
pwsh $slotScript -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 1
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
try {
    pwsh scripts/import-region.ps1 -Region bialystok-industrial-c
    if ($LASTEXITCODE -ne 0) { throw 'Nieudany import nowej bazy.' }
}
finally {
    pwsh $slotScript -Release -Owner gpt-truck
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Add-Content -Encoding utf8 artifacts/truck-r3/STATUS.md 'Import bieżącej bazy zakończony. Zmiany generated innych dziedzin zachować jako dowód i cofnąć przed kodem r3. Następny krok: render-phase.ps1 -Stage before -Lighting overcast,clear oraz all-cameras.ps1 -Stage before-all.'
git add -f artifacts/truck-r3/STATUS.md
git commit --only artifacts/truck-r3/STATUS.md -m 'wip(truck): import aktualnej bazy r3'
