$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r4'){throw 'Wrong branch'}
if(Test-Path artifacts/life-r4/mirror-diagnosis.json){throw 'Diagnosis already exists'}
if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/gpt-life-r4.slot'){throw 'Own heavy already held'}
& pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner gpt-life-r4 -StaleHours 1000000 -PollSeconds 1
if($LASTEXITCODE){throw 'Acquire failed'}
try {
 & uv run --project tools/worldgen python artifacts/life-r4/diagnose-wheel-mirror.py *> artifacts/life-r4/mirror-diagnosis.log
 if($LASTEXITCODE){throw 'Diagnosis failed'}
 Add-Content artifacts/life-r4/STATUS.md "`nDiagnoza odbicia zakończona: mirror-diagnosis.json zawiera osobno baseline/candidate rim/tyre i nowe wnętrza. Odczytać rzeczywiste różnice przed decyzją o zakresie testu; nie deklarować PASS na podstawie hipotezy."
 git add -f artifacts/life-r4/STATUS.md artifacts/life-r4/mirror-diagnosis.json artifacts/life-r4/mirror-diagnosis.log
 git commit -m 'wip(life): zmierz odbicie starego i nowego koła'
 if($LASTEXITCODE){throw 'WIP failed'}
} finally {
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner gpt-life-r4
}
