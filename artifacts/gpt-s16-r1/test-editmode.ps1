$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion'
$slot = Join-Path $root 'scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Owner gpt-s16
try {
    if (Test-Path "$root/artifacts/locks/PHONE_RUN") { throw 'PHONE_RUN appeared after acquisition' }
    & pwsh scripts/test.ps1 -Platform EditMode *> artifacts/gpt-s16-r1/final-editmode.log
    $result = $LASTEXITCODE
} finally {
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner gpt-s16
}
$xml = Get-ChildItem artifacts/tests -Filter 'editmode-*.xml' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $xml) { throw 'No EditMode result XML' }
Copy-Item $xml.FullName artifacts/gpt-s16-r1/final-editmode.xml
@("# EditMode — gpt-s16 r1", (Get-Date -Format o), "Exit: $result",
  (Get-Content artifacts/gpt-s16-r1/final-editmode.log -Tail 3),
  'NASTĘPNY KROK: Get-Content artifacts/gpt-s16-r1/final-editmode.xml -TotalCount 2') | Set-Content artifacts/gpt-s16-r1/EDITMODE-STATUS.md
Add-Content artifacts/gpt-s16-r1/STATUS.md "`nEditMode zakończony: exit $result; szczegóły EDITMODE-STATUS.md i final-editmode.xml."
git add -f artifacts/gpt-s16-r1/STATUS.md artifacts/gpt-s16-r1/EDITMODE-STATUS.md artifacts/gpt-s16-r1/test-editmode.ps1 artifacts/gpt-s16-r1/final-editmode.xml
git commit -m "wip(s16): record full EditMode result exit $result"
Copy-Item artifacts/gpt-s16-r1/STATUS.md "$root/artifacts/gpt-s16/PRZEKAZANIE.md"
Add-Content "$root/artifacts/gpt-s16/PRZEKAZANIE.md" "SHA: $(git rev-parse HEAD)"
exit $result
