param([ValidateSet('baseline','after')][string]$Stage='baseline')
$ErrorActionPreference='Stop'
$root='C:\Users\matma\Documents\Claude\kamion'
$slot=Join-Path $root 'scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Pool heavy -MaxSlots 3 -Owner gpt-s16
$timer=[Diagnostics.Stopwatch]::StartNew()
try {
 & uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "artifacts/gpt-s16-r3/$Stage-world.log"
 if ($LASTEXITCODE -ne 0) { throw "World generation failed: $Stage" }
 if (Select-String -LiteralPath "artifacts/gpt-s16-r3/$Stage-world.log" -SimpleMatch 'fallback=True' -Quiet) { throw 'Material fallback detected' }
} finally { & pwsh $slot -Release -Pool heavy -Owner gpt-s16 }
$timer.Stop()
Copy-Item Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json "artifacts/gpt-s16-r3/$Stage-streetscape-qa.json"
Copy-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json "artifacts/gpt-s16-r3/$Stage-world-manifest.json"
Add-Content artifacts/gpt-s16-r3/STATUS.md "`nŚwiat $Stage wygenerowany: $($timer.Elapsed.TotalSeconds) s, bez fallback=True. NASTĘPNY KROK: import i kamery $Stage."
git add -f artifacts/gpt-s16-r3/STATUS.md artifacts/gpt-s16-r3/baseline-world.ps1 "artifacts/gpt-s16-r3/$Stage-streetscape-qa.json" "artifacts/gpt-s16-r3/$Stage-world-manifest.json"
git commit -q -m "wip(s16): generate $Stage world for Putry shadow round"
  & pwsh artifacts/gpt-s16-r3/handoff.ps1 -Step "baseline-world.ps1 completed step"
