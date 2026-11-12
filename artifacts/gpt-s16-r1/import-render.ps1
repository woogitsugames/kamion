param([string]$Stage = 'before')
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion'
$slot = Join-Path $root 'scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Owner gpt-s16
try {
    if (Test-Path "$root/artifacts/locks/PHONE_RUN") { throw 'PHONE_RUN appeared after acquisition' }
    & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> "artifacts/gpt-s16-r1/$Stage-import.log"
    if ($LASTEXITCODE -ne 0) { throw "$Stage import failed" }
} finally {
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner gpt-s16
}
@("# STATUS — gpt-s16 r1", (Get-Date -Format o), "Gałąź: $(git branch --show-current)",
  "Import $Stage zakończony; log $Stage-import.log. Następnie cztery serie kamer.",
  "NASTĘPNY KROK: pwsh artifacts/gpt-s16-r1/render.ps1 -Stage $Stage", 'Gotowe do recenzji: NIE') |
    Set-Content artifacts/gpt-s16-r1/STATUS.md
git add -f artifacts/gpt-s16-r1/STATUS.md artifacts/gpt-s16-r1/import-render.ps1
git commit -m "wip(s16): imported $Stage world"
Copy-Item artifacts/gpt-s16-r1/STATUS.md "$root/artifacts/gpt-s16/PRZEKAZANIE.md"
Add-Content "$root/artifacts/gpt-s16/PRZEKAZANIE.md" "SHA: $(git rev-parse HEAD)"
& pwsh artifacts/gpt-s16-r1/render.ps1 -Stage $Stage
if ($LASTEXITCODE -ne 0) { throw "$Stage render failed" }
