$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion'
$slot = Join-Path $root 'scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Pool heavy -MaxSlots 3 -Owner gpt-s16
$timer = [Diagnostics.Stopwatch]::StartNew()
try {
    & uv run --project tools/worldgen python -m pytest tests/gis -q *> artifacts/gpt-s16-r3/final-gis.log
    $result = $LASTEXITCODE
} finally { & pwsh $slot -Release -Pool heavy -Owner gpt-s16 }
$timer.Stop()
@("# GIS — gpt-s16 r2", (Get-Date -Format o), "Exit: $result; wall time: $($timer.Elapsed.TotalSeconds) s",
  (Get-Content artifacts/gpt-s16-r3/final-gis.log -Tail 3),
  'NASTĘPNY KROK: Get-Content artifacts/gpt-s16-r3/final-gis.log -Tail 30') | Set-Content artifacts/gpt-s16-r3/GIS-STATUS.md
Add-Content artifacts/gpt-s16-r3/STATUS.md "`nPełny GIS zakończony: exit $result; szczegóły GIS-STATUS.md oraz final-gis.log."
git add -f artifacts/gpt-s16-r3/STATUS.md artifacts/gpt-s16-r3/GIS-STATUS.md artifacts/gpt-s16-r3/test-gis.ps1
git commit -m "wip(s16): record full GIS result exit $result"
Copy-Item artifacts/gpt-s16-r3/STATUS.md "$root/artifacts/gpt-s16/PRZEKAZANIE.md"
Add-Content "$root/artifacts/gpt-s16/PRZEKAZANIE.md" "SHA: $(git rev-parse HEAD)"
exit $result

