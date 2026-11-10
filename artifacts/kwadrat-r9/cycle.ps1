# Full cycle: build_world (rebuilds the hero asset when stale) -> pytest hero -> Unity import -> control renders.
# pwsh artifacts/kwadrat-r9/cycle.ps1 -Phase after2 [-WaitFor artifacts/kwadrat-r9/logs/qa_after1.log]
param([string]$Phase = 'after2', [string]$WaitFor = '')
$root = Resolve-Path "$PSScriptRoot/../.."
Set-Location $root
if ($WaitFor) { while (-not (Select-String -Path $WaitFor -Pattern 'QA RUNS DONE' -Quiet)) { Start-Sleep 15 } }
$env:KAMION_BLENDER = 'C:\Users\matma\AppData\Local\Programs\Blender4.2\blender-4.2.9-windows-x64\blender.exe'
$env:PYTHONUNBUFFERED = '1'
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "artifacts/kwadrat-r9/logs/build_world_$Phase.log"
"BUILD EXIT $LASTEXITCODE"
if ($LASTEXITCODE -ne 0) { exit 1 }
uv run --project tools/worldgen pytest tests/gis -q -k "hero_depot or prototypes" *> "artifacts/kwadrat-r9/logs/pytest_$Phase.log"
"PYTEST EXIT $LASTEXITCODE"
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> "artifacts/kwadrat-r9/logs/import_$Phase.log"
"IMPORT EXIT $LASTEXITCODE"
if ($LASTEXITCODE -ne 0) { exit 1 }
pwsh artifacts/kwadrat-r9/qa_runs.ps1 -Phase $Phase
"CYCLE DONE"
