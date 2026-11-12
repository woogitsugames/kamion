param([Parameter(Mandatory)][int]$GisExitCode)
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
if ((git branch --show-current).Trim() -ne 'gpt-light-r2') { throw 'Expected gpt-light-r2' }
if ($GisExitCode -ne 0) { throw 'Cannot close a failed final GIS run' }
if (Get-Process -Id 93072 -ErrorAction SilentlyContinue) { throw 'Final GIS process is still alive' }
$gisLog = "$PSScriptRoot/heavy-GisFinal-20261112-014702.log"
$summary = [regex]::Match((Get-Content $gisLog -Raw), '(?m)^(\d+) passed, (\d+) xfailed in ([\d.]+)s')
if (-not $summary.Success) { throw 'Missing complete passing pytest summary' }
$passed = [int]$summary.Groups[1].Value
$xfailed = [int]$summary.Groups[2].Value
$seconds = $summary.Groups[3].Value
$xml = [xml](Get-Content "$PSScriptRoot/tests/editmode-final.xml" -Raw)
if ($xml.'test-run'.passed -ne '276' -or $xml.'test-run'.failed -ne '0') { throw 'Final EditMode276 required' }
$budget = Get-Content "$PSScriptRoot/final-route-v2-budget.json" -Raw | ConvertFrom-Json
if ($budget.entries.Count -ne 134 -or @($budget.entries | Where-Object { $_.totalDrawDelta -gt 0 -or $_.totalTriangleDeltaPercent -gt 2 }).Count) { throw 'Incomplete or regressed camera budget' }
$generated = @(
    'Data/Regions/bialystok-industrial-c/generated/far_field_qa.json',
    'Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json',
    'Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_putry_underdeck.spec.json',
    'Data/Regions/bialystok-industrial-c/generated/roads_qa.json',
    'Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json',
    'Data/Regions/bialystok-industrial-c/generated/world_manifest.json',
    'Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json',
    'art-source/world/props/props_meta.json'
)
$unexpected = @(git diff --name-only | Where-Object { $_ -notin $generated })
if ($unexpected.Count) { throw "Unexpected unstaged changes: $unexpected" }
git diff --binary --output=artifacts/light-r2/generated-baseline-rebuild.patch -- @generated
if ($LASTEXITCODE) { throw 'Could not archive own regenerated effects' }
git restore -- @generated
if ($LASTEXITCODE) { throw 'Could not restore own generated effects' }
@{owner='gpt-light-r2';pool='heavy';command='uv run --project tools/worldgen python -m pytest tests/gis -q';exit_code=$GisExitCode;passed=$passed;xfailed=$xfailed;pytest_elapsed_seconds=$seconds;log=[IO.Path]::GetFileName($gisLog);editmode='tests/editmode-final.xml';source_sha=(git rev-parse HEAD).Trim()} | ConvertTo-Json | Set-Content "$PSScriptRoot/gis-final-result.json" -Encoding utf8
Add-Content docs/adr/0108-light-sky-exposure-post.md "`r`nZamknięcie r2: końcowy pełny GIS $passed passed / $xfailed xfailed, $seconds s według pytest, kod0. Run wykonał się pod heavy po analizie; oczekiwanie i zawieszenie przez nadzorcę są opisane oddzielnie, nie uznane za awarię testów. Własne efekty regeneracji poza light zachowano w artifacts/light-r2/generated-baseline-rebuild.patch i przywrócono do bazy. Odtwarzanie wymaga generatora/fidelity/importu w slotach. Następna runda r3 dotyczy mokrej nawierzchni; lokalna referencja cm92458760 ma klasęC i nie służy kalibrowanej fotometrii."
Add-Content "$PSScriptRoot/STATUS.md" "Zamknięcie walidacji r2: pełny GIS $passed passed / $xfailed xfailed w $seconds s, kod0; EditMode276/276. Własny generated patch zapisany, osiem efektów regeneracji przywrócone. Następny krok: REPORT i kompletna dostawa do main, następnie gpt-light-r3."
git add docs/adr/0108-light-sky-exposure-post.md
git add -f artifacts/light-r2/STATUS.md artifacts/light-r2/gis-final-result.json artifacts/light-r2/generated-baseline-rebuild.patch
git commit -m 'WIP light r2: record completed final validation and archive generator effects'
if ($LASTEXITCODE) { throw 'Validation commit failed' }
$source = (git rev-parse HEAD).Trim()
$report = @(
"Runda 2, gałąź gpt-light-r2, SHA wyniku $source; baza main ba0520cf. Poprawiono wygląd nocy, bez deklaracji pełnej nocnej widoczności lub PASS bramki.",
'Osobny LP_Night: słońce −8°, ekspozycja −3 EV, sky gain 0,125 i desaturacja 0,85. To przybliżenie wyglądu przy granicy istniejącego modelu zmierzchu, nie model astronomiczny. LP_Dusk pozostaje bez zmiany.',
'Ablacja 60 PNG wykluczyła −4/−5 EV przez utratę czytelności Low; 24 PNG oddzielnego grade wybrały ciemne neutralne niebo. Rodzic i niezależny krytyk obejrzeli wszystkie warianty.',
'Baseline Dusk 24 PNG potwierdza działanie pul: p95 stosunku jasności gruntu off/on przy kierowcy Low 1,519 / High 1,472, przy bloku 1,720 / 1,699, przy dokach 1,092 / 1,084. To metryki obrazu, nie luksy.',
'Usunięto pomarańczowy zachód odbijany w ekranie Putry i szkle domu przy czarnym niebie. Night mapuje także odbite niebo i horyzont; analityczne SH, grunt cubemapy i ekspozycja modelu pozostają bez zmiany. Test i 20 dodatkowych ujęć potwierdzają poprawkę.',
'Końcowy zestaw: 268 PNG Dusk/Night dla 67 kamer i obu tierów; po poprawce odbić powtórzono wszystkie 134 nocne obrazy. Wszystkie obejrzane, High przez niezależnego krytyka. Galeria: [index.html](index.html).',
'Trzy pary foto|render 956 px w [reference-pairs](reference-pairs/night-appearance-1.jpg): lokalne zdjęcia Rakoon, CC0, inne miejsca/czasy i zimowe dekoracje. Porównują hierarchię światła, nie geometrię ani skalibrowaną fotometrię.',
'Budżet wszystkich 134 wpisów: draws +0 i tris +0%, instancje osobno w [final-route-v2-budget.json](final-route-v2-budget.json). Estymaty CPU przed batchingiem, nie pomiar GPU A16. Bez nowego przebiegu, pełnoekranowego efektu Low i zmiany skali.',
'Eksperymentalne reflektory pozostają opt-in i domyślnie off we wszystkich presetach. Rzeczywiste anchory pojazdu i istniejący stan świateł, bez kamery jako źródła; 8 testów lifecycle i 32 ujęcia off/on. Brak occlusion, kalibracji kształtu/20 kcd, pomiaru zasięgu i kosztu A16.',
'Poprawiono błąd dodatkowej kamery QA po Camera.CopyFrom; cztery nowe ujęcia i actual-eye.json potwierdzają poziomy widok. Wcześniejsze pochylone dowody zachowano i opisano, nie uznano ich za poprawny eye.',
"Testy końcowe: [EditMode 276/276](tests/editmode-final.xml); pełny GIS $passed passed / $xfailed xfailed w $seconds s, kod0. GIS tylko na końcu rundy; własne zadania Python szeregowo przez heavy, Unity przez osobny slot.",
'Generator 438 s bez fallback=True, fidelity i import pięciu presetów zakończone kodem 0; build_all 459 s pod heavy. Raport pamięci importera Low 117,0 / High 259,1 MiB nie jest PSS telefonu.',
'W początkowej ablacji sky średnia zmiana RGB stałych ROI gruntu/instrumentów wynosiła 0,026–0,073 na Low i 0,090–0,260 na High, maksimum 2/11 poziomów 8-bitowego RGB. Nie deklarujemy identyczności pikseli ani braku bandingu.',
'Pozostają ciemne przejścia g3a-eye-s0262/stretch-03 i odcinki edge-west/fence2/office1/docks bez skutecznych reflektorów. Nie ogłaszamy pełnej nocnej przejezdności, kalibracji lamp, occlusion, GPU ani oceny telefonu.',
'Własne raporty/generated z regeneracji zachowano w generated-baseline-rebuild.patch i przywrócono; nie są produkcyjną zmianą light. Do odtworzenia wymagane generator, fidelity i import w slotach.',
'Przewidywane styki: LightingPreset/LookDevAssets/EnvironmentLighting/WorldAtmosphere/SkyModel/Sky.shader/RenderOverrides, addytywny include KamionLampPools. Nie zmieniono WorldPBR, WorldSurface, TruckLights, Cab, geometrii ani QualityProfile.',
'Integruje wyłącznie lider; bez pushowania, merge do main i telefonów w tej sesji. Decyzje i ograniczenia: ADR 0108, niezależne opinie: review. Następna runda: gpt-light-r3, merge main, mokra nawierzchnia po deszczu.'
)
if ($report.Count -gt 20) { throw 'REPORT too long' }
$report | Set-Content "$PSScriptRoot/REPORT.md" -Encoding utf8
git add -f artifacts/light-r2/REPORT.md
git commit -m 'docs(light): report round2 night lighting and remaining limits'
if ($LASTEXITCODE) { throw 'REPORT commit failed' }
$mainArtifacts = 'C:/Users/matma/Documents/Claude/kamion/artifacts/light-r2'
& robocopy $PSScriptRoot $mainArtifacts /E /R:1 /W:1 /NFL /NDL /NP /NJH /NJS
$copyCode = $LASTEXITCODE
if ($copyCode -gt 7) { throw "Robocopy failed $copyCode" }
$files = @(Get-ChildItem $PSScriptRoot -Recurse -File)
foreach ($file in $files) {
    $relative = $file.FullName.Substring($PSScriptRoot.Length+1)
    $target = Join-Path $mainArtifacts $relative
    if (-not (Test-Path -LiteralPath $target) -or (Get-Item -LiteralPath $target).Length -ne $file.Length) { throw "Incomplete copy: $relative" }
}
if ((Get-FileHash "$PSScriptRoot/REPORT.md").Hash -ne (Get-FileHash "$mainArtifacts/REPORT.md").Hash) { throw 'REPORT hash mismatch' }
Add-Content "$PSScriptRoot/STATUS.md" "Dostawa r2 zakończona: robocopy kod$copyCode, $($files.Count) plików, wszystkie rozmiary i hash REPORT zgodne. Bez merge/push do main. Następny krok: gałąź gpt-light-r3 i merge main."
git add -f artifacts/light-r2/STATUS.md
git commit -m 'WIP light r2: verify complete artifact delivery'
& robocopy $PSScriptRoot $mainArtifacts STATUS.md /R:1 /W:1 /NFL /NDL /NP /NJH /NJS
if ($LASTEXITCODE -gt 7) { throw 'Final STATUS copy failed' }
git switch -c gpt-light-r3
if ($LASTEXITCODE) { throw 'Could not start round3 branch' }
git merge main
if ($LASTEXITCODE) { throw 'Resolve round3 main merge explicitly; do not overwrite other owners' }
exit 0

