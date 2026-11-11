$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal'
foreach ($job in @(
    @{id='materials';args=@('run','--project','tools/worldgen','python','art-source/world/materials/_src/build_all.py')},
    @{id='world';args=@('run','--project','tools/worldgen','tools/worldgen/roads/build_world.py','--region','bialystok-industrial-c')}
)) {
    pwsh $slotScript -Acquire -Pool heavy -Owner gpt-truck-r2 -StaleHours 100000 -PollSeconds 1
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu heavy.' }
    try {
        $arguments = $job.args
        uv @arguments *> "artifacts/truck-r2/baseline-$($job.id).log"
        if ($LASTEXITCODE -ne 0) { throw "Nieudany generator $($job.id)." }
        if (Select-String -LiteralPath "artifacts/truck-r2/baseline-$($job.id).log" -SimpleMatch 'fallback=True' -Quiet) { throw 'Fallback Megascans; nie wolno użyć takiej bazy.' }
    }
    finally { pwsh $slotScript -Release -Pool heavy -Owner gpt-truck-r2 }
    Add-Content -Encoding utf8 artifacts/truck-r2/STATUS.md "Generator $($job.id) zakończony pod heavy, bez fallback=True. Następny krok: pozostałe wejścia, import i baseline r2."
    git add -f artifacts/truck-r2/STATUS.md
    git commit --only artifacts/truck-r2/STATUS.md -m "wip(truck): wejscia r2 $($job.id)"
}
# Guard import-region's automatic Python fallbacks before occupying Unity.
$spec = Get-Content art-source/world/materials/materials_spec.json -Raw | ConvertFrom-Json
$sourceTime = (Get-ChildItem art-source/world/materials/_src -Filter *.py | Measure-Object LastWriteTimeUtc -Maximum).Maximum
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
Add-Content -Encoding utf8 artifacts/truck-r2/STATUS.md 'Import bieżącej bazy zakończony. Zmiany generated innych dziedzin zachować jako dowód i cofnąć przed kodem r2. Następny krok: render-phase.ps1 -Stage before -Lighting overcast,clear oraz all-cameras.ps1 -Stage before-all.'
git add -f artifacts/truck-r2/STATUS.md
git commit --only artifacts/truck-r2/STATUS.md -m 'wip(truck): import aktualnej bazy r2'
