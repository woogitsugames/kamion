$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Push-Location $taskRoot
try {
    $probeFile=Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c/sbs_pose_probes.json'
    $mapping=(Get-Content artifacts/sbs-r1/pose-probes.json -Raw | ConvertFrom-Json).probes
    foreach($group in ($mapping | Group-Object { "$($_.width)x$($_.height)" })) {
        $renderDir='artifacts/sbs-r1/pose-renders'
        $first=$group.Group[0]; $height=[int](1280*$first.height/$first.width)
        $ids=$group.Group.probe -join ','
        pwsh -NoProfile -File C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1 -Acquire -Owner gpt-sbs -PollSeconds 7 -StaleHours 87600
        if($LASTEXITCODE -ne 0){throw 'Brak slotu Unity'}
        try {
            pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Width 1280 -Height $height -Gate3 $probeFile -Cameras $ids -OutputDir $renderDir
            if($LASTEXITCODE -ne 0){throw 'Nieudany render prób pozy'}
            Copy-Item -LiteralPath (Join-Path $renderDir 'stats.txt') -Destination (Join-Path $renderDir "stats-$($group.Name).txt")
            [ordered]@{git_sha=(& git rev-parse HEAD).Trim();cameras_sha256=(Get-FileHash $probeFile -Algorithm SHA256).Hash;probes=@($group.Group.probe);tier='Low';lighting='overcast';captured_at_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $renderDir "capture-$($group.Name).json")
        } finally {
            git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
            pwsh -NoProfile -File C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1 -Release -Owner gpt-sbs
        }
    }
    uv run --project tools/refs python artifacts/sbs-r1/compose_pose_probes.py
    if($LASTEXITCODE -ne 0){throw 'Nieudane galerie prób pozy'}
} finally {Pop-Location}
