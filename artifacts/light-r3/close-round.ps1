param([Parameter(Mandatory)][int]$GisExitCode,[Parameter(Mandatory)][string]$GisLog)
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
if((git branch --show-current).Trim() -ne 'gpt-light-r3'){throw 'Expected round3'}
if($GisExitCode -ne 0){throw 'Final GIS did not pass'}
$summary=[regex]::Match((Get-Content -LiteralPath $GisLog -Raw),'(?m)^(\d+) passed, (\d+) xfailed in ([\d.]+)s')
if(-not $summary.Success){throw 'No complete GIS summary'}
$passed=[int]$summary.Groups[1].Value;$xfailed=[int]$summary.Groups[2].Value;$seconds=$summary.Groups[3].Value
$xml=[xml](Get-Content "$PSScriptRoot/tests/editmode-final.xml" -Raw)
if($xml.'test-run'.result -ne 'Passed' -or [int]$xml.'test-run'.failed -ne 0 -or [int]$xml.'test-run'.passed -lt 276){throw 'Incomplete full EditMode'}
$editPassed=[int]$xml.'test-run'.passed
$budget=Get-Content "$PSScriptRoot/clear-budget-all.json" -Raw|ConvertFrom-Json
if($budget.entries.Count -ne 122 -or @($budget.entries|Where-Object {$_.totalDrawDelta -ne 0 -or $_.totalTriangleDeltaPercent -ne 0}).Count){throw 'All122 budgets must be unchanged'}
$generated=@('Data/Regions/bialystok-industrial-c/generated/far_field_qa.json','Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json',
'Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_putry_underdeck.spec.json','Data/Regions/bialystok-industrial-c/generated/roads_qa.json',
'Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json','Data/Regions/bialystok-industrial-c/generated/world_manifest.json',
'Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json','art-source/world/props/props_meta.json')
$unexpected=@(git diff --name-only|Where-Object {$_ -notin $generated})
if($unexpected.Count){throw "Unexpected dirty source: $unexpected"}
git diff --binary --output=artifacts/light-r3/generated-baseline-rebuild.patch -- @generated
if($LASTEXITCODE){throw 'Patch archive failed'}
git restore -- @generated
if($LASTEXITCODE){throw 'Own generated restore failed'}
@{owner='gpt-light-r3';pool='heavy';command='uv run --project tools/worldgen python -m pytest tests/gis -q';exit_code=$GisExitCode;passed=$passed;xfailed=$xfailed;pytest_elapsed_seconds=$seconds;log=[IO.Path]::GetFileName($GisLog);editmode_passed=$editPassed;source_sha=(git rev-parse HEAD).Trim()}|ConvertTo-Json|Set-Content "$PSScriptRoot/gis-final-result.json" -Encoding utf8
Add-Content docs/adr/0108-light-sky-exposure-post.md "Zamknięcie walidacji r3: pełne EditMode$editPassed/$editPassed, GIS$passed passed/$xfailed xfailed w$seconds s, kod0 pod heavy. Estymaty122kamer draws/tris bez zmiany, instancing osobno; GPU niezmierzony. Własne efekty regeneracji zarchiwizowano i przywrócono. P1 nieba naprawione, mokra droga nadalFAIL, bez nieprzyjętego presetu lub mechanizmu odbić. R4: spójność tonów Low/High po merge main."
Add-Content "$PSScriptRoot/STATUS.md" "Końcowa walidacja r3: EditMode$editPassed/$editPassed, GIS$passed/$xfailed xfailed w$seconds s. Archiwum własnych generated i restore zakończone. Następny krok: REPORT, robocopy i r4."
git add docs/adr/0108-light-sky-exposure-post.md
git add -f artifacts/light-r3/STATUS.md artifacts/light-r3/gis-final-result.json artifacts/light-r3/generated-baseline-rebuild.patch
git commit -m 'WIP light r3: archive completed validation and own regenerated effects'
if($LASTEXITCODE){throw 'Validation commit failed'}
$sha=(git rev-parse HEAD).Trim()
$report=@(
"Runda3, gałąź gpt-light-r3, SHA wyniku$sha; baza main522361aa, merge b36e36b2. Naprawiono P1 nieba; mokra nawierzchnia nie została zaakceptowana.",
'Szary klin nad halami2948595898752384/303305168125936 pochodził z obróconej twardej granicy dolnej półsfery mapy chmur. Maski FarField/Apron go nie barwiły, a izolacja samego nieba zachowała go przy0 aktywnych rendererów i instancerów.',
'Clear ogranicza teraz źródłową elewację mapy do0,5 stopnia po obrocie. Ablacja0/0,5/1 na12PNG wybrała najmniejszy sprawdzony margines; inne presety domyślnie0 zachowują starą ścieżkę. Hasz tekstury niezmieniony, bez nowej próbki lub przebiegu.',
'Końcowy Clear122/122,61kamer na obu tierach, obejrzany przez rodzica i niezależnego krytyka. Dodatkowo48 poprawnych kierunków kamery przy słońcu42 stopnie i8 statycznych kostek64/128 bez powrotu ostrego klina. Pierwszy błędny sweep look_at odrzucony, dowód tylko sky-direction-v2.',
'Pozostaje miękki szary pas dolnego nieba; inne kąty słońca, ruch, GPU i ekran telefonu niezweryfikowane. Nie deklarujemy zaliczenia bramki lub kalibracji wszystkich zdjęć.',
'Mokry baseline36PNG przy wet0/0,5/1 pokazuje globalnie jasne wygładzenie bez wiarygodnej lokalnej treści odbić. Zdjęciecm92458760: Rakoon2020-07-11, CC BY3.0, zgodny SHA; pozaC błędna, tylko odniesienie jakościowe, bez fotometrii.',
'Eksperyment istniejącej kostki pojazdu:16PNG z oka/daleka i32 bliskiePNG z32dumpami. Dał ciemny owal8–12m, nie przekonujące odbicie. Usunięto cały binder, shader, flagę i styki wspólnych shaderów; patch i opinie zachowano.',
'Ablacja filmu72PNG: połysk0,52/0,35/0,2 oraz udział kałuż0,3/0,08. Krytyk i rodzic odrzucili wszystkie warianty: mniejszy połysk redukuje plastik, lecz nie daje mokrego odczytu z odbiciem. Usunięto nieprzyjęty parametr, presety nadal bez nowego mokra.',
'Scena diagnostyczna v2:16PNG i2kostki. Surowa kostka/sfera20m deformują położenie znanych pasów ściany; znana rzeczywista płaszczyzna pozwala dopasować odbicie. To ograniczenie paralaksy, nie rozwiązanie geometrii/okluzji całego świata. Scena nie jest zapisana ani częścią produktu.',
'Cztery odległe porównania off/on mokrego eksperymentu miały zerową różnicę pikseli. Suche oko miało śladowe różnice średnie poniżej0,00004 RGB; nie deklarujemy identyczności całego kadru.',
'Budżet122/122 porównany na tych samych kamerach: estymowane draws+0 i tris+0, instancing osobno. To estymatyCPU przed grupowaniemSRP, nie pomiarGPU/A16. Brak nowych kamer lub przebiegów produktu.',
"Pełne końcowe EditMode$editPassed/$editPassed; GIS$passed passed/$xfailed xfailed w$seconds s, kod0. W trakcie rundy tylko ukierunkowane testy13/13 i wcześniejsze7/7; pełnyGIS wyłącznie przy zamknięciu.",
'Generator428s bezfallback, fidelity0, build_all446s, importLow/High0. Import raportuje117,5/259,6MiB, nie PSS telefonu. Własny Python pojedynczo w heavy z limitem wątków1, Unity osobnym slotem.',
'Własne efekty regeneracji zapisano w generated-baseline-rebuild.patch i przywrócono do bazy. Nie są zmianą produkcyjną light; odtworzenie wymaga generatora/fidelity/importu przez sloty.',
'Styki końcowe: LightingPreset, WorldAtmosphere, Sky.shader, Clear asset i metadane źródła; własne narzędzia QA. WorldPBR, WorldSurface i mokry KamionAtmosphere przywrócone po odrzuceniu eksperymentów, bez zmian cudzej geometrii/asfaltowego albedo.',
'Wynik: P1 nieba poprawione, mokra droga nadalFAIL. Raporty niezależne w review, szczegóły i ograniczenia w ADR0108. Integruje lider; bez push, merge do main i telefonów. Następna runda gpt-light-r4: spójność tonówLow/High po merge main.'
)
if($report.Count -gt 20){throw 'REPORT exceeds20lines'}
$report|Set-Content "$PSScriptRoot/REPORT.md" -Encoding utf8
git add -f artifacts/light-r3/REPORT.md
git commit -m 'docs(light): report round3 sky fix and rejected wet-road experiments'
if($LASTEXITCODE){throw 'Report commit failed'}
$destination='C:/Users/matma/Documents/Claude/kamion/artifacts/light-r3'
& robocopy $PSScriptRoot $destination /E /R:1 /W:1 /NFL /NDL /NP /NJH /NJS
$copyCode=$LASTEXITCODE
if($copyCode -gt 7){throw "Copy failed$copyCode"}
$files=@(Get-ChildItem $PSScriptRoot -Recurse -File)
foreach($file in $files){$relative=$file.FullName.Substring($PSScriptRoot.Length+1);$target=Join-Path $destination $relative;if(-not(Test-Path -LiteralPath $target) -or (Get-Item -LiteralPath $target).Length -ne $file.Length){throw "Incomplete artifact$relative"}}
if((Get-FileHash "$PSScriptRoot/REPORT.md").Hash -ne (Get-FileHash "$destination/REPORT.md").Hash){throw 'Report hash mismatch'}
Add-Content "$PSScriptRoot/STATUS.md" "Dostawa r3: robocopy$copyCode,$($files.Count) plików, rozmiary i hashREPORT zgodne. Następny krok: gpt-light-r4 i merge main; bez merge/push do main."
git add -f artifacts/light-r3/STATUS.md
git commit -m 'WIP light r3: verify complete artifact delivery'
& robocopy $PSScriptRoot $destination STATUS.md /R:1 /W:1 /NFL /NDL /NP /NJH /NJS
if($LASTEXITCODE -gt 7){throw 'Final status copy failed'}
git switch -c gpt-light-r4
if($LASTEXITCODE){throw 'Round4 branch failed'}
git merge main
if($LASTEXITCODE){throw 'Resolve round4 merge explicitly'}
