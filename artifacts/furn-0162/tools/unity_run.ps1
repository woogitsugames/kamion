# ADR 0162: baseline Low render (main world), import of the furn-0162 world, after renders + probes + sbs subset.
param([switch]$SkipBaseline, [switch]$SkipImport)
$ErrorActionPreference = 'Continue'
$W = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\furn-0162'
Set-Location $W
$A = "$W\artifacts\furn-0162"
$probeIds = ((Get-Content "$A\probes.json" -Raw | ConvertFrom-Json).cameras | ForEach-Object id) -join ','
$sbsIds = ((Get-Content "$A\sbs_subset.json" -Raw | ConvertFrom-Json).cameras | ForEach-Object id) -join ','
pwsh scripts/unity-slot.ps1 -Acquire -Owner furn-0162 2>&1 | Select-Object -Last 1
try {
    if (-not $SkipBaseline) {
        "== baseline Low clear $(Get-Date -f HH:mm)"
        pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -OutputDir "$A\base-Low-clear" 2>&1 | Select-Object -Last 2
        pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Gate3 "$A\probes.json" -Cameras $probeIds -OutputDir "$A\base-probes-Low" 2>&1 | Select-Object -Last 2
        pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -Gate3 "$A\sbs_subset.json" -Cameras $sbsIds -OutputDir "$A\base-sbs-Low-clear" 2>&1 | Select-Object -Last 2
    }
    if (-not $SkipImport) {
        "== import $(Get-Date -f HH:mm)"
        pwsh scripts/import-region.ps1 -Region bialystok-industrial-c 2>&1 | Select-Object -Last 3
    }
    "== after renders $(Get-Date -f HH:mm)"
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -OutputDir "$A\after-Low-clear" 2>&1 | Select-Object -Last 2
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting clear -OutputDir "$A\after-High-clear" 2>&1 | Select-Object -Last 2
    foreach ($t in 'Low', 'High') {
        pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting overcast -Gate3 "$A\probes.json" -Cameras $probeIds -OutputDir "$A\after-probes-$t" 2>&1 | Select-Object -Last 2
        pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting clear -Gate3 "$A\sbs_subset.json" -Cameras $sbsIds -OutputDir "$A\after-sbs-$t-clear" 2>&1 | Select-Object -Last 2
    }
} finally {
    pwsh scripts/unity-slot.ps1 -Release -Owner furn-0162 2>&1 | Select-Object -Last 1
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>&1 | Out-Null
    "== done $(Get-Date -f HH:mm)"
}
