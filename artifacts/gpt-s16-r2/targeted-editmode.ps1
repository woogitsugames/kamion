$ErrorActionPreference='Stop'
$root='C:\Users\matma\Documents\Claude\kamion';$slot=Join-Path $root 'scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Owner gpt-s16
try {
 if(Test-Path "$root/artifacts/locks/PHONE_RUN"){throw 'PHONE_RUN appeared'}
 & pwsh scripts/test.ps1 -Platform EditMode -Filter Game.Tests.GardenCanopyWidthTests *> artifacts/gpt-s16-r2/targeted-editmode.log
 $result=$LASTEXITCODE
} finally {
 git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
 & pwsh $slot -Release -Owner gpt-s16
}
$xml=Get-ChildItem artifacts/tests -Filter 'editmode-*.xml' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Copy-Item $xml.FullName artifacts/gpt-s16-r2/targeted-editmode.xml
Add-Content artifacts/gpt-s16-r2/STATUS.md "`nCelowany EditMode GardenCanopyWidthTests: exit$result; szczegóły targeted-editmode.xml/log."
git add -f artifacts/gpt-s16-r2/STATUS.md artifacts/gpt-s16-r2/targeted-editmode.xml artifacts/gpt-s16-r2/targeted-editmode.ps1
git commit -q -m "wip(s16): record targeted canopy matrix tests exit $result"
exit $result
