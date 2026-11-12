param([string]$NightRoot = 'final-route-v2', [string]$Output = 'final-route-v2-budget.json')
$ErrorActionPreference = 'Stop'
function Read-Stats([string]$Path) {
    $cameras = [ordered]@{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line -match '^(.+?): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)') {
            $id = $Matches[1]
            if ($cameras.Contains($id)) { throw "Duplicate camera $id" }
            $cameras[$id] = [ordered]@{objects=[int]$Matches[2];draws=[int]$Matches[3];shadowDraws=[int]$Matches[4];trianglesK=[int]$Matches[5]}
        }
        elseif ($line -match '^\s+(.+?) instanced \(props\+trees\): draws (\d+), instances (\d+), triangles (\d+)k') {
            $cameras[$Matches[1]].instancedDraws=[int]$Matches[2]
            $cameras[$Matches[1]].instances=[int]$Matches[3]
            $cameras[$Matches[1]].instancedTrianglesK=[int]$Matches[4]
        }
    }
    if ($cameras.Count -ne 67) { throw "Expected all67 cameras, got $($cameras.Count)" }
    foreach ($value in $cameras.Values) { if (-not $value.Contains('instancedDraws')) { throw 'Missing separate instancing counts' } }
    return $cameras
}
$result = foreach ($tier in @('Low','High')) {
    $before = Read-Stats "$PSScriptRoot/final-route/$tier-dusk/stats.txt"
    $after = Read-Stats "$PSScriptRoot/$NightRoot/$tier-night/stats.txt"
    foreach ($id in $before.Keys) {
        if (-not $after.Contains($id)) { throw "Missing $id" }
        $a=$before[$id]; $b=$after[$id]
        $drawDelta=$b.draws+$b.instancedDraws-$a.draws-$a.instancedDraws
        $trisDelta=100.0*($b.trianglesK+$b.instancedTrianglesK-$a.trianglesK-$a.instancedTrianglesK)/[Math]::Max(1,$a.trianglesK+$a.instancedTrianglesK)
        if ($drawDelta -gt 0 -or $trisDelta -gt 2) { throw "Budget regression $tier/$id" }
        [ordered]@{tier=$tier;camera=$id;beforeDusk=$a;afterNight=$b;totalDrawDelta=$drawDelta;totalTriangleDeltaPercent=$trisDelta}
    }
}
@{method='All67 identical cameras per tier. CPU SceneStats estimates before SRP batching, rounded trianglesK; instancing separate. Dusk vs Night on same regenerated geometry, projection off. No GPU or phone timing claim.';nightSource=$NightRoot;entries=@($result)} | ConvertTo-Json -Depth 8 | Set-Content "$PSScriptRoot/$Output" -Encoding utf8
Get-Content "$PSScriptRoot/$Output" -Raw | ConvertFrom-Json | ForEach-Object entries | Group-Object tier,totalDrawDelta,totalTriangleDeltaPercent | Select-Object Count,Name
