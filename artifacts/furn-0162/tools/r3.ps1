# ADR 0162 review s17 fixes: build + import + probes lamp-door / tys-vms / shelter_black (Low+High)
$ErrorActionPreference = 'Continue'
$W = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\furn-0162'; Set-Location $W
$A = "$W\artifacts\furn-0162"; $L = "$A\logs"
"== R3 $(Get-Date -f HH:mm)"
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner furn-0162 2>&1 | Select-Object -Last 1
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$L\build_r3.log"
"build r3 exit=$LASTEXITCODE $(Get-Date -f HH:mm)"
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner furn-0162 2>&1 | Select-Object -Last 1
pwsh scripts/unity-slot.ps1 -Acquire -Owner furn-0162 2>&1 | Select-Object -Last 1
try {
    pwsh scripts/import-region.ps1 -Region bialystok-industrial-c 2>&1 | Select-Object -Last 2
    $ids = 'f162-lamp-door,f162-tys-vms-g3p010,f162-shelter-bus_shelter_black'
    foreach ($t in 'Low', 'High') {
        pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting overcast -Gate3 "$A\probes.json" -Cameras $ids -OutputDir "$A\r3-probes-$t" 2>&1 | Select-Object -Last 1
    }
} finally {
    pwsh scripts/unity-slot.ps1 -Release -Owner furn-0162 2>&1 | Select-Object -Last 1
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>&1 | Out-Null
}
"== done r3 $(Get-Date -f HH:mm)"
