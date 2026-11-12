$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
# Main changed a material source. Refresh its complete cache under heavy so import cannot start an unslotted builder.
& pwsh artifacts/asphalt-r2/run-heavy.ps1 -Stage Materials -Label baseline
if ($LASTEXITCODE -ne 0) { throw 'Baseline material producer failed' }
& pwsh artifacts/asphalt-r2/run-heavy.ps1 -Stage World -Label baseline
if ($LASTEXITCODE -ne 0) { throw 'Baseline world producer failed' }
if ((Get-Content artifacts/asphalt-r2/baseline-World.log -Raw) -match 'fallback=True|Traceback') {
    throw 'World fallback or producer error; refuse baseline import.'
}
& uv run --project tools/worldgen python artifacts/asphalt-r2/audit_manifest.py
if ($LASTEXITCODE -ne 0) { throw 'World manifest audit failed' }
& git add -- Data/Regions/bialystok-industrial-c/generated art-source/world/materials/materials_spec.json art-source/world/props/props_meta.json
if ($LASTEXITCODE -ne 0) { throw 'Cannot stage generated metadata' }
Add-Content artifacts/asphalt-r2/STATUS.md "$(Get-Date -Format o): Świat i materiały baseline po merge main gotowe, brak Megascans fallback, audyt odwołań bez rozbieżności. Następny krok: import i cztery serie baseline."
git add -f artifacts/asphalt-r2/STATUS.md
git commit -q -m 'wip(asphalt): checkpoint r2 canonical baseline producers'
& pwsh artifacts/asphalt-r2/run-unity-stage.ps1 -Stage Import -Label baseline
if ($LASTEXITCODE -ne 0) { throw 'Baseline import failed' }
& pwsh artifacts/asphalt-r2/run-unity-stage.ps1 -Stage Capture -Label baseline
if ($LASTEXITCODE -ne 0) { throw 'Baseline capture failed' }
Set-Content artifacts/asphalt-r2/BASELINE-COMPLETE.txt (Get-Date -Format o)
Add-Content artifacts/asphalt-r2/STATUS.md "$(Get-Date -Format o): Pełny baseline r2 zakończony. Obejrzeć nowe zbliżenia krawężnika/kostki i referencje przed zmianą materiału."
git add -f artifacts/asphalt-r2/STATUS.md artifacts/asphalt-r2/BASELINE-COMPLETE.txt
git commit -q -m 'wip(asphalt): checkpoint complete second-round baseline'
