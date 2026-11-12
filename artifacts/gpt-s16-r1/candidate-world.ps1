$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion'
$slot = Join-Path $root 'scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Pool heavy -MaxSlots 3 -Owner gpt-s16
try {
    & uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> artifacts/gpt-s16-r1/after-world.log
    if ($LASTEXITCODE -ne 0) { throw 'Candidate generator failed' }
} finally { & pwsh $slot -Release -Pool heavy -Owner gpt-s16 }
& uv run --project tools/worldgen python artifacts/gpt-s16-r1/audit_glb.py artifacts/gpt-s16-r1/baseline-street_props.glb art-source/world/props/street_props.glb artifacts/gpt-s16-r1/glb-audit.json
if ($LASTEXITCODE -ne 0) { throw 'Candidate GLB audit failed' }
@("# STATUS — gpt-s16 r1", (Get-Date -Format o), "Gałąź: $(git branch --show-current)",
  'Kandydat wygenerowany; audyt GLB zakończony poprawnie. Import after dopiero po ukończeniu kamer before.',
  'NASTĘPNY KROK: pwsh artifacts/gpt-s16-r1/import-render.ps1 -Stage after', 'Gotowe do recenzji: NIE') |
    Set-Content artifacts/gpt-s16-r1/STATUS.md
git add -f artifacts/gpt-s16-r1/STATUS.md artifacts/gpt-s16-r1/candidate-world.ps1 artifacts/gpt-s16-r1/glb-audit.json
git commit -m 'wip(s16): regenerate atlas candidate and verify protected GLB buffers'
Copy-Item artifacts/gpt-s16-r1/STATUS.md "$root/artifacts/gpt-s16/PRZEKAZANIE.md"
Add-Content "$root/artifacts/gpt-s16/PRZEKAZANIE.md" "SHA: $(git rev-parse HEAD)"
