$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion'
$slot = Join-Path $root 'scripts/unity-slot.ps1'
$out = 'artifacts/gpt-s16-r1'
function Checkpoint($message, $next) {
    @("# STATUS — gpt-s16 r1", (Get-Date -Format o), "Gałąź: gpt-s16-r1; SHA przed zapisem: $(git rev-parse HEAD)", $message, "NASTĘPNY KROK: $next", 'Gotowe do recenzji: NIE') | Set-Content "$out/STATUS.md"
    git add -f "$out/STATUS.md" "$out/baseline.ps1" "$out/prepare.ps1"
    git commit -m "wip(s16): $message"
    Copy-Item "$out/STATUS.md" "$root/artifacts/gpt-s16/PRZEKAZANIE.md"
}
& pwsh $slot -Acquire -Pool heavy -MaxSlots 3 -Owner gpt-s16
try {
    & uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py *> "$out/baseline-materials.log"
    if ($LASTEXITCODE -ne 0) { throw 'baseline materials failed' }
    & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$out/baseline-world.log"
    if ($LASTEXITCODE -ne 0) { throw 'baseline generator failed' }
} finally { & pwsh $slot -Release -Pool heavy -Owner gpt-s16 }
Checkpoint 'Odtworzono bazowy świat i materiały; logi baseline-world.log oraz baseline-materials.log.' 'pwsh scripts/import-region.ps1 -Region bialystok-industrial-c'
Copy-Item art-source/world/props/street_props.glb "$out/baseline-street_props.glb"
Copy-Item art-source/world/props/props_meta.json "$out/baseline-props_meta.json"
& pwsh $slot -Acquire -Owner gpt-s16
try {
    if (Test-Path "$root/artifacts/locks/PHONE_RUN") { throw 'PHONE_RUN appeared after acquisition' }
    & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> "$out/baseline-import.log"
    if ($LASTEXITCODE -ne 0) { throw 'baseline import failed' }
} finally {
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner gpt-s16
}
Checkpoint 'Zaimportowano bazowy świat; baseline-import.log.' 'pwsh artifacts/gpt-s16-r1/render.ps1 -Stage before'
& pwsh "$out/render.ps1" -Stage before
if ($LASTEXITCODE -ne 0) { throw 'baseline render failed' }
Checkpoint 'Baseline Low/High clear/overcast zapisany; wymaga oględzin PNG.' 'Get-Content artifacts/gpt-s16-r1/before/Low-clear/stats.txt'
