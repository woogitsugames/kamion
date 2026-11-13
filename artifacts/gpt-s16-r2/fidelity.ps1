$ErrorActionPreference='Stop'
$root='C:\Users\matma\Documents\Claude\kamion';$slot=Join-Path $root 'scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Pool heavy -MaxSlots 3 -Owner gpt-s16
try {
 & uv run --project tools/worldgen python -u tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art artifacts/gpt-s16-r2/fidelity *> artifacts/gpt-s16-r2/fidelity.log
 if($LASTEXITCODE -ne 0){throw 'Fidelity failed'}
} finally { & pwsh $slot -Release -Pool heavy -Owner gpt-s16 }
Add-Content artifacts/gpt-s16-r2/STATUS.md "`nFidelity odświeżone dla końcowego generatora r2; pełny GIS może sprawdzić świeży raport."
git add Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json
git add -f artifacts/gpt-s16-r2/STATUS.md artifacts/gpt-s16-r2/fidelity.ps1
git commit -q -m 'wip(s16): refresh final garden fidelity evidence'
