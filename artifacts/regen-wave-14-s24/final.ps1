. "$PSScriptRoot/common.ps1"
Initialize-WaveRuntime
$lock = Enter-WaveLock 'final'
try {
    $missing = @($queue.tile | Where-Object { -not (Test-Path -LiteralPath "$stateDir/tiles/$_.done") })
    if ($missing.Count) { throw "Brakuje gotowych kafli: $($missing -join ', ')." }
    if (Test-Path -LiteralPath "$stateDir/final.checked") { Remove-Item -LiteralPath "$stateDir/final.checked" }
    & "$waveDir/autocommit.ps1"
    $tiles = $queue.tile -join ','
    $log = "$evidenceDir/logs/final.log"
    $failed = @(Invoke-WithHeavySlot "$waveName-final" $log {
        $checks = [ordered]@{
            route_links = @('tools/worldgen/streaming/route_links.py')
            tile_graph = @('tools/worldgen/streaming/tile_graph.py')
            catalog = @('scripts/export-region-catalog.py')
            catalog_check = @('scripts/export-region-catalog.py', '--check')
            seams = @('-m', 'tools.worldgen.qa.seams', '--tiles', $tiles,
                '--json', "$evidenceDir/seams_after.json", '--md', "$evidenceDir/seams_after.md")
            route_obstacles = @('tools/worldgen/qa/route_obstacles.py', '--tiles', $tiles,
                '--out', "$evidenceDir/route_obstacles.json")
            hv_wires_audit = @('tools/worldgen/qa/hv_wires_audit.py', '--json', "$evidenceDir/hv_wires_after.json", '--regions') + $queue.tile
            budgets = @('-m', 'pytest', '-q', '-p', 'no:cacheprovider',
                'tests/gis/test_budget_0221.py', 'tests/gis/test_typology_0238.py',
                'tests/gis/test_world_v31.py', 'tests/gis/test_hero_bridge.py')
            pytest_gis = @('-m', 'pytest', 'tests/gis', '-q', '-p', 'no:cacheprovider')
        }
        foreach ($name in $checks.Keys) {
            try { Invoke-WaveStep $name $python $checks[$name] "$evidenceDir/logs/$name.log" }
            catch { Write-Warning $_.Exception.Message; $name }
        }
    })
    & "$waveDir/vqa.ps1" -Phase after
    if ($failed.Count) { throw "Kontrole z błędem: $($failed -join ', ')." }
    Set-Content -LiteralPath "$stateDir/final.checked" -Value (Get-Date -Format o)
    & "$waveDir/commit.ps1" -Final
    Write-Host "Przejrzyj pary PNG oraz raporty szwów, trasy i WN w $evidenceDir."
}
finally { $lock.Dispose() }
