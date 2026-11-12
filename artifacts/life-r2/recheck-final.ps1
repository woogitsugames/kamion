$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
& pwsh -NoProfile -File artifacts/life-r2/heavy.ps1 -Task TestFile -Tag pytest-yard-wear-final -TestPath tests/gis/test_yard_wear.py
if($LASTEXITCODE -ne 0){throw 'Single-file yard test failed'}
Add-Content artifacts/life-r2/STATUS.md ("`nKontrola po historycznym limicie ({0}): test_yard_wear.py zakończony 0 pod heavy; liczby w pytest-yard-wear-final.log. Produkcja C bez zmian. Następny krok: pełny GIS z osobnym tagiem pytest-gis-final-rerun; nie nadpisywać dowodu pierwszej porażki." -f (Get-Date -Format o))
git add -f -- artifacts/life-r2/STATUS.md artifacts/life-r2/pytest-yard-wear-final.log artifacts/life-r2/pytest-yard-wear-final-result.json
git commit -m 'wip(life): potwierdź spójny limit w pojedynczym teście naczep'
if($LASTEXITCODE -ne 0){throw 'Could not checkpoint single-file test'}
& pwsh -NoProfile -File artifacts/life-r2/final-gis.ps1 -Tag pytest-gis-final-rerun
if($LASTEXITCODE -ne 0){throw 'Full GIS rerun failed'}
