# ADR 0162 clean A/B: (A) origin/main code + data -> build_world -> import -> baseline renders; (B) furn-0162 HEAD ->
# build_world -> import -> after renders. Nothing is committed while the tree holds main's files.
$ErrorActionPreference = 'Continue'
$W = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\furn-0162'
Set-Location $W
$A = "$W\artifacts\furn-0162"
$L = "$A\logs"
$paths = @('tools', 'Data/Regions', 'art-source', 'game/Assets/_Project/World/Import', 'game/Assets/_Project/UI/Resources/CabDisplay')
$probeIds = ((Get-Content "$A\probes.json" -Raw | ConvertFrom-Json).cameras | ForEach-Object id) -join ','
$sbsIds = ((Get-Content "$A\sbs_subset.json" -Raw | ConvertFrom-Json).cameras | ForEach-Object id) -join ','
function Build($tag) {
    pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner furn-0162 2>&1 | Select-Object -Last 1
    uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$L\build_$tag.log"
    "build $tag exit=$LASTEXITCODE $(Get-Date -f HH:mm)"
    pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner furn-0162 2>&1 | Select-Object -Last 1
}
function Unity([scriptblock]$body) {
    pwsh scripts/unity-slot.ps1 -Acquire -Owner furn-0162 2>&1 | Select-Object -Last 1
    try { & $body } finally {
        pwsh scripts/unity-slot.ps1 -Release -Owner furn-0162 2>&1 | Select-Object -Last 1
        git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>&1 | Out-Null
    }
}
"== A: main $(Get-Date -f HH:mm)"
git checkout origin/main -- @paths
Build 'main'
Unity {
    pwsh scripts/import-region.ps1 -Region bialystok-industrial-c 2>&1 | Select-Object -Last 2
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -OutputDir "$A\base-Low-clear" 2>&1 | Select-Object -Last 1
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Gate3 "$A\probes.json" -Cameras $probeIds -OutputDir "$A\base-probes-Low" 2>&1 | Select-Object -Last 1
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -Gate3 "$A\sbs_subset.json" -Cameras $sbsIds -OutputDir "$A\base-sbs-Low-clear" 2>&1 | Select-Object -Last 1
}
"== B: furn-0162 $(Get-Date -f HH:mm)"
git checkout HEAD -- @paths
git status --short | Select-Object -First 5
Build 'furn'
Unity {
    pwsh scripts/import-region.ps1 -Region bialystok-industrial-c 2>&1 | Select-Object -Last 2
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -OutputDir "$A\after-Low-clear" 2>&1 | Select-Object -Last 1
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting clear -OutputDir "$A\after-High-clear" 2>&1 | Select-Object -Last 1
    foreach ($t in 'Low', 'High') {
        pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting overcast -Gate3 "$A\probes.json" -Cameras $probeIds -OutputDir "$A\after-probes-$t" 2>&1 | Select-Object -Last 1
        pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting clear -Gate3 "$A\sbs_subset.json" -Cameras $sbsIds -OutputDir "$A\after-sbs-$t-clear" 2>&1 | Select-Object -Last 1
    }
}
git status --short | Select-Object -First 8
"== done $(Get-Date -f HH:mm)"
