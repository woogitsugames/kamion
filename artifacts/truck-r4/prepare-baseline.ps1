param([switch]$SkipGenerators,[switch]$SkipMaterials)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$snapshot = @(Get-CimInstance Win32_Process)
$ancestors = [System.Collections.Generic.HashSet[int]]::new()
$cursor = [int]$PID
while ($cursor -gt 0 -and $ancestors.Add($cursor)) {
    $parent = $snapshot | Where-Object ProcessId -eq $cursor | Select-Object -First 1
    if (!$parent) { break }
    $cursor = [int]$parent.ParentProcessId
}
$other = @($snapshot | Where-Object { $_.Name -eq 'pwsh.exe' -and !$ancestors.Contains([int]$_.ProcessId) -and $_.CommandLine -match 'truck-r4[/\\]prepare-baseline\.ps1' })
if ($other.Count) { throw 'Poprzednia procedura nadal działa; nie wolno współdzielić jej Owner heavy.' }
if ($SkipMaterials) {
    $materialLog=Get-Item artifacts/truck-r4/baseline-materials.log
    $lastSource=(Get-ChildItem art-source/world/materials/_src -Filter '*.py' | Measure-Object LastWriteTimeUtc -Maximum).Maximum
    if ($materialLog.LastWriteTimeUtc -lt $lastSource -or !(Select-String -LiteralPath artifacts/truck-r4/STATUS.md -SimpleMatch 'Generator materials zakończony pod heavy' -Quiet)) { throw 'Brak potwierdzonej świeżej regeneracji materiałów.' }
}
if ($SkipGenerators -and (!(Select-String -LiteralPath artifacts/truck-r4/STATUS.md -SimpleMatch 'Generator materials zakończony pod heavy' -Quiet) -or !(Select-String -LiteralPath artifacts/truck-r4/STATUS.md -SimpleMatch 'Generator world zakończony pod heavy' -Quiet))) { throw 'Brak potwierdzenia ukończenia obu generatorów przed wznowieniem.' }
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
    if ($SkipMaterials -and $job.id -eq 'materials') { continue }
    pwsh $slotScript -Acquire -Pool heavy -Owner gpt-truck-r4 -StaleHours 100000 -PollSeconds 5
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu heavy.' }
    try {
        $arguments = $job.args
        uv @arguments *> "artifacts/truck-r4/baseline-$($job.id).log"
        if ($LASTEXITCODE -ne 0) { throw "Nieudany generator $($job.id)." }
        if (Select-String -LiteralPath "artifacts/truck-r4/baseline-$($job.id).log" -SimpleMatch 'fallback=True' -Quiet) { throw 'Fallback Megascans; nie wolno użyć takiej bazy.' }
    }
    finally { pwsh $slotScript -Release -Pool heavy -Owner gpt-truck-r4 }
    Add-Content -Encoding utf8 artifacts/truck-r4/STATUS.md "Generator $($job.id) zakończony pod heavy, bez fallback=True. Następny krok: pozostałe wejścia, import i baseline r4."
    git add -f artifacts/truck-r4/STATUS.md
    git commit --only artifacts/truck-r4/STATUS.md -m "wip(truck): wejscia r4 $($job.id)"
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
    pwsh $slotScript -Acquire -Pool heavy -Owner gpt-truck-r4 -StaleHours 100000 -PollSeconds 5
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu heavy dla brakującej warstwy.' }
    try {
        uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only asphalt_detail_photo *> artifacts/truck-r4/baseline-photo-layer.log
        if ($LASTEXITCODE -ne 0) { throw 'Nie wygenerowano brakującej warstwy zdjęciowej.' }
    }
    finally { pwsh $slotScript -Release -Pool heavy -Owner gpt-truck-r4 }
    Add-Content -Encoding utf8 artifacts/truck-r4/STATUS.md 'Uzupełniono wyłącznie pominiętą warstwę asfalt_detail_photo pod heavy. Zdjęcie wejściowe skopiowano z main z identycznym SHA. Bez zmiany źródeł asfaltu. Następny krok: import aktualnej bazy.'
    git add -f artifacts/truck-r4/STATUS.md
    git commit --only artifacts/truck-r4/STATUS.md -m 'wip(truck): komplet brakujacego wejscia importu r3'
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
pwsh $slotScript -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 5
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
try {
    pwsh scripts/import-region.ps1 -Region bialystok-industrial-c
    if ($LASTEXITCODE -ne 0) { throw 'Nieudany import nowej bazy.' }
}
finally {
    pwsh $slotScript -Release -Owner gpt-truck
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Add-Content -Encoding utf8 artifacts/truck-r4/STATUS.md 'Import bieżącej bazy zakończony. Zachować patch wygenerowanych danych, lecz nie przywracać starego world_manifest przed końcowym GIS: test deterministyczności musi porównać świeżą regenerację z tą samą wersją źródeł. Plików innych dziedzin nie commitować; przywrócić je dopiero po konsumentach i testach. Następny krok: baseline-captures.ps1.'
git add -f artifacts/truck-r4/STATUS.md
git commit --only artifacts/truck-r4/STATUS.md -m 'wip(truck): import aktualnej bazy r4'


