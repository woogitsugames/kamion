$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$target = 'C:/Users/matma/Documents/Claude/kamion/artifacts/truck-r2'
if (!(Test-Path artifacts/truck-r2/gis-result.json)) { throw 'Brak końcowej oceny GIS.' }
if ((git status --porcelain | Measure-Object).Count -ne 0) { throw 'Przed przekazaniem wymagany czysty worktree.' }
$sourceCount = @(Get-ChildItem artifacts/truck-r2 -Recurse -File).Count
$sourceBytes = (Get-ChildItem artifacts/truck-r2 -Recurse -File | Measure-Object Length -Sum).Sum
robocopy artifacts/truck-r2 $target /E /XJ /R:1 /W:1 /NFL /NDL /LOG:artifacts/truck-r2-delivery.log
$copyExit = $LASTEXITCODE
if ($copyExit -gt 7) { throw "Nieudane przekazanie robocopy: $copyExit" }
$hash = (Get-FileHash artifacts/truck-r2/REPORT.md -Algorithm SHA256).Hash
if ((Get-FileHash "$target/REPORT.md" -Algorithm SHA256).Hash -ne $hash) { throw 'Różne REPORT po kopiowaniu.' }
[ordered]@{source_branch=(git branch --show-current);source_commit=(git rev-parse HEAD);files=$sourceCount;bytes=$sourceBytes;robocopy_exit=$copyExit;report_sha256=$hash;destination=$target;copied_at=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -Encoding utf8 artifacts/truck-r2/delivery-result.json
Copy-Item artifacts/truck-r2-delivery.log artifacts/truck-r2/delivery.log
Add-Content -Encoding utf8 artifacts/truck-r2/STATUS.md "Przekazano rundę 2 robocopy do main/artifacts/truck-r2: $sourceCount plików, $sourceBytes bajtów, exit $copyExit, REPORT SHA256 zgodne. Następny krok: git switch -c gpt-truck-r3; git merge --no-stat --no-edit main, następnie aktualizacja wejść i baseline kół. Bez merge do main i bez push."
git add -f artifacts/truck-r2/STATUS.md artifacts/truck-r2/delivery-result.json
git commit --only artifacts/truck-r2/STATUS.md artifacts/truck-r2/delivery-result.json -m 'wip(truck): potwierdzenie przekazania rundy 2'
if ($LASTEXITCODE -ne 0) { throw 'Nie zapisano przekazania w git.' }
robocopy artifacts/truck-r2 $target /E /XJ /R:1 /W:1 /NFL /NDL /LOG:artifacts/truck-r2-delivery-refresh.log
if ($LASTEXITCODE -gt 7) { throw 'Nie przekazano uaktualnionego STATUS.' }
if ((Get-FileHash "$target/REPORT.md" -Algorithm SHA256).Hash -ne $hash) { throw 'REPORT niezgodne po odświeżeniu.' }
exit 0
