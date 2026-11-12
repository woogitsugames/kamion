$ErrorActionPreference='Stop'
. ./artifacts/vegetation-r4/checkpoint.ps1
Add-Content artifacts/vegetation-r4/STATUS.md 'Autor obejrzał wszystkie 40 arkuszy before (368 ujęć). SELF-REVIEW-before opisuje bryłowy berberys, otwarte drzewa B8 i zakres próby. RED: 1 failed, 4 passed, 0,66 s. Następny krok: materiał liści istniejącej warstwy wewnętrznej, bez nowych trójkątów.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 przegląd wszystkich ujęć przed kandydatem' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/SELF-REVIEW-before.md')
$baseline=Get-Content artifacts/vegetation-r4/snapshot-baseline/sha256.json -Raw | ConvertFrom-Json
if ((Get-FileHash tools/worldgen/streetscape/plantings.py).Hash.ToLowerInvariant() -ne $baseline.source_files.'tools/worldgen/streetscape/plantings.py') { throw 'Source drift' }
git apply --check artifacts/vegetation-r3/next-round-proposal/leaf-core-proposal.patch
if ($LASTEXITCODE -ne 0) { throw 'Patch mismatch' }
git apply artifacts/vegetation-r3/next-round-proposal/leaf-core-proposal.patch
if ($LASTEXITCODE -ne 0) { throw 'Patch failed' }
