param([Parameter(Mandatory)][int]$GisExitCode,[Parameter(Mandatory)][string]$GisLog)
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
if((git branch --show-current).Trim() -ne 'gpt-light-r4'){throw 'Expected round4'}
git diff --cached --quiet HEAD
if($LASTEXITCODE){throw 'Resolve staged changes explicitly before close'}
if($GisExitCode -ne 0){throw 'GIS did not terminate0'}
$summary=[regex]::Match((Get-Content -LiteralPath $GisLog -Raw),'(?m)^(\d+) passed, (\d+) xfailed in ([\d.]+)s')
if(-not $summary.Success){throw 'Missing complete passing GIS summary'}
$passed=[int]$summary.Groups[1].Value;$xfailed=[int]$summary.Groups[2].Value;$seconds=$summary.Groups[3].Value
$xml=[xml](Get-Content "$PSScriptRoot/tests/editmode-final.xml" -Raw)
if($xml.'test-run'.result -ne 'Passed' -or $xml.'test-run'.passed -ne '332' -or $xml.'test-run'.failed -ne '0'){throw 'Require final332/332'}
$budget=Get-Content "$PSScriptRoot/final-budget-all.json" -Raw|ConvertFrom-Json
if($budget.entries.Count -ne 654 -or @($budget.entries|Where-Object {$_.totalDrawDelta -gt 0 -or $_.totalTriangleDeltaPercent -gt 2}).Count){throw 'Budget incomplete/regressed'}
$pixels=(Get-Content "$PSScriptRoot/day-pixel-deltas.json" -Raw|ConvertFrom-Json).entries
if($pixels.Count -ne 436){throw 'Missing all day comparisons'}
$meanMax=($pixels|Measure-Object meanAbsoluteRgb -Maximum).Maximum;$pixelMax=($pixels|Measure-Object maximumRgb -Maximum).Maximum
$review=Get-Content "$PSScriptRoot/review/FINAL-NIGHT-V2-REVIEW.md" -Raw
if($review.Length -lt 300){throw 'Missing independent final review'}
$pairs=Get-Content "$PSScriptRoot/reference-pairs/sources.json" -Raw|ConvertFrom-Json
if($pairs.Count -ne 6){throw 'Missing qualified photo-render pairs'}
foreach($pair in $pairs){if((Get-FileHash -LiteralPath $pair.pair).Hash -ne $pair.pair_sha256){throw 'Reference pair changed'}}
foreach($tier in @('Low','High')){
    $probes=(Get-Content "$PSScriptRoot/final-v2/$tier-night/lamp-probes.json" -Raw|ConvertFrom-Json).cameras
    if($probes.Count -ne 109 -or @($probes|Where-Object {[Math]::Abs($_.actualDimColourDesaturation-.65) -gt .0001 -or [Math]::Abs($_.presetDimColourDesaturation-.65) -gt .0001}).Count){throw 'Actual final Night grade not proved'}
}
$generated=@('Data/Regions/bialystok-industrial-c/generated/far_field_qa.json','Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json',
'Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_putry_underdeck.spec.json','Data/Regions/bialystok-industrial-c/generated/roads_qa.json',
'Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json','Data/Regions/bialystok-industrial-c/generated/world_manifest.json',
'Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json','art-source/world/props/props_meta.json','art-source/world/props/street_props.glb')
$unexpected=@(git diff --name-only|Where-Object {$_ -notin $generated})
if($unexpected.Count){throw "Unexpected source changes$unexpected"}
Copy-Item -LiteralPath art-source/world/props/street_props.glb -Destination "$PSScriptRoot/generated-street-props.glb"
$glbHash=(Get-FileHash "$PSScriptRoot/generated-street-props.glb").Hash
git diff --binary --output=artifacts/light-r4/generated-baseline-rebuild.patch -- @generated
if($LASTEXITCODE){throw 'Own generated archive failed'}
git restore -- @generated
if($LASTEXITCODE){throw 'Own generated restore failed'}
@{owner='gpt-light-r4';pool='heavy';exit_code=$GisExitCode;passed=$passed;xfailed=$xfailed;elapsed_seconds=$seconds;log=[IO.Path]::GetFileName($GisLog);editmode_passed=332;source_sha=(git rev-parse HEAD).Trim();generated_glb_sha256=$glbHash;day_max_mean_rgb=$meanMax;day_max_rgb=$pixelMax}|ConvertTo-Json|Set-Content "$PSScriptRoot/final-validation.json" -Encoding utf8
Add-Content docs/adr/0108-light-sky-exposure-post.md "Zamknięcie r4: EditMode332/332, GIS$passed passed/$xfailed xfailed w$seconds s, kod0 podheavy. Budżet654kamer i436porównańdziennegoobrazu, maxśredniejbezwzględnejRGB=$meanMax, maxkanałuRGB=$pixelMax (poziomy0–255). Własneefektygeneratorazarchiwizowano i przywrócono, surowyGLB w artifacts zhaszem. R5 kontynuuje otwarte dopasowanie jasnychtonówLow/High oraz wygląd źródełNight; brakfullNight/GPU/telefonPASS."
Add-Content "$PSScriptRoot/STATUS.md" "Końcowechecki:332/332EditMode,GIS$passed/$xfailed xfailed/$seconds s;654budżety,436daydelta(meanMax=$meanMax,max=$pixelMax). Własnygeneratedpatch+GLBzapisaneiprzywrócone. Następnykrok:REPORT,dostawa,r5."
git add docs/adr/0108-light-sky-exposure-post.md
git add -f artifacts/light-r4/STATUS.md artifacts/light-r4/final-validation.json artifacts/light-r4/generated-baseline-rebuild.patch
git commit -m 'WIP light r4: preserve completed validation and own generator artifacts'
if($LASTEXITCODE){throw 'Validation commit failed'}
$sha=(git rev-parse HEAD).Trim()
$report=@(
"Runda 4, gałąź gpt-light-r4, SHA wyniku $sha; baza main 67f6702c, merge 2e82dc46. Ograniczono nasycenie ciemnych powierzchni Night; spójność jasnych tonów Low/High pozostaje otwarta.",
'Night używa dimColourDesaturation 0,65 w istniejącym KamionTone. Modulacja zanika pomiędzy liniową luminancją 0,02 i 0,25; zachowuje luminancję przed istniejącym toe/post. To przybliżenie wyglądu, nie model widzenia nocnego lub fotometria zdjęcia.',
'Ablacja 64 poprawnych PNG: siła 0/0,35/0,65/1 na ośmiu kamerach i obu poziomach jakości. Rodzic i krytyk wybrali 0,65: mniej zielonożółtej trawy, bez pełnej popielatości siły 1 i bez utraty kolorów instrumentów.',
'Nie zmieniono słońca, SH, ekspozycji, albedo, geometrii, rozmiaru lub harmonogramu capture ani liczby świateł. Fizyczne kostki pomijają desaturację; sześć statycznych porównań kostek ma średnią/maksymalną różnicę RGB 0/0. Ruch i szkło na urządzeniu niezweryfikowane.',
'Świeży baseline: 654 PNG, 109 kamer × trzy presety × dwa poziomy jakości, wszystkie obejrzane. Końcowy zestaw: 436 Clear/Overcast z final-v1 oraz 218 Night z final-v2; wszystkie sondy Night potwierdzają preset i global 0,65. Końcowe Night obejrzane przez rodzica i niezależnego krytyka.',
'Pierwsze final-v1 Night odrzucono: Unity czytało dim 0 z pola dopisanego po pustych liniach YAML. Pole przeniesiono do ciągłego bloku; dodano test rzeczywistego assetu względem fabryki i twardy guard sond po renderze. Pierwsza seria dim miała błąd shadera i również została odrzucona.',
'Poprawiona plansza tonów v2 ma osiem obrazów i 192 próbek, z kontrolą aktywnego gradingu. Overcast przy wejściu 0,5 daje Low 182, High 204–205; Night przy 0,7 daje Low 218 i High około 247. Różnice dotyczą także kompresji świateł i nasycenia, nie tylko ekspozycji.',
'Pierwsza plansza używała SingleCameraRequest bez odświeżenia VolumeStack, więc jej identyczne High nie są dowodem spójności. Poprawiona metoda korzysta z istniejącego Camera.Render świata i porównuje rzeczywisty master, saturację, post i shaderowy toe.',
'Plamy światła na Putry istnieją, choć szeroki jasny pierwszy plan i ciemny dystans nadal wyglądają słabo. Sonda znalazła trzy punkty gruntu w kadrze Low i cztery High, bez dowodu okluzji. Emisja zarejestrowanych klonów głowic jest niezerowa, Cull 0; nie podnoszono natężenia na podstawie błędnych odczytów assetów.',
'Pozostają ciemne doki, czarne okna, słabe wizualnie głowice i brak halo; nie dodano nowych okien ani miejskiej łuny. Nie deklarujemy pełnego Night PASS, bramki, zgodności tonów Low/High lub kalibracji lamp.',
"Budżet 654/654 kamer porównany przed/po, instancing osobno, bez naruszenia draws +0 i tris ≤+2%. To zaokrąglone estymaty CPU przed SRP, nie pomiar GPU/A16. Wszystkie 436 dzienne porównania PNG: maksymalna średnia różnica RGB $meanMax, maksymalna różnica kanału $pixelMax w skali 0–255.",
'Bez nowych przebiegów, tekstur lub fullscreen na Low i bez obniżenia skali. Dodatkowy ALU oraz gałąź uniformu desaturacji wymagają pomiaru GPU przez lidera; kosztu nie uznano za zerowy.',
"Pełne końcowe EditMode 332/332, w tym test serializacji Night i kontrakt niezmienności modelu; GIS $passed passed / $xfailed xfailed w $seconds s, kod 0. Pełny GIS wyłącznie przy końcu rundy, własny Python pojedynczo przez heavy z limitem wątków 1.",
'Generator 563,6 s bez fallback, fidelity i import z kodem 0, build_all 507 s. Importer raportuje Low 117,7 / High 259,8 MB, bez pomiaru PSS telefonu. Własne efekty regeneracji zapisano w patchu i kopii GLB, następnie przywrócono do bazy.',
'Sześć par zdjęcie|render po 956 px w reference-pairs: Rakoon CC0, inne miejsca, czasy i zimowy sezon, tylko hierarchia światła. Źródła i hasze zachowane; bez dopasowania pozy lub fotometrii.',
'Styki: LightingPreset, Night asset, WorldAtmosphere, EnvironmentLighting i wspólny KamionAtmosphere; Sky dzieli jedną deklarację istniejącego capture bypass. Bez zmian WorldPBR, WorldSurface, shaderów kabiny/pojazdu, geometrii lub QualityProfile. Własne narzędzia QA i testy opisano w ADR 0108.',
'Integruje lider; bez push, merge do main i telefonów. Następna runda gpt-light-r5: aktualny main, kontynuacja największych otwartych różnic tonów i źródeł nocnego światła. Mokra droga z r3 nadal FAIL.'
)
if($report.Count -gt 20){throw 'REPORT exceeds20lines'}
$report|Set-Content "$PSScriptRoot/REPORT.md" -Encoding utf8
git add -f artifacts/light-r4/REPORT.md
git commit -m 'docs(light): report round4 Night colour and remaining tone differences'
if($LASTEXITCODE){throw 'Report commit failed'}
$destination='C:/Users/matma/Documents/Claude/kamion/artifacts/light-r4'
& robocopy $PSScriptRoot $destination /E /R:1 /W:1 /NFL /NDL /NP /NJH /NJS
$copyCode=$LASTEXITCODE
if($copyCode -gt 7){throw 'Artifact copy failed'}
$files=@(Get-ChildItem $PSScriptRoot -Recurse -File)
foreach($file in $files){$relative=$file.FullName.Substring($PSScriptRoot.Length+1);$target=Join-Path $destination $relative;if(-not(Test-Path -LiteralPath $target) -or (Get-Item -LiteralPath $target).Length -ne $file.Length){throw "Missing artifact$relative"}}
if((Get-FileHash "$PSScriptRoot/REPORT.md").Hash -ne (Get-FileHash "$destination/REPORT.md").Hash){throw 'Report hash mismatch'}
Add-Content "$PSScriptRoot/STATUS.md" "Dostawa r4:robocopy$copyCode,$($files.Count)plików,wszystkierozmiaryihashREPORTzgodne. Następnykrok:r5imerge main."
git add -f artifacts/light-r4/STATUS.md
git commit -m 'WIP light r4: verify complete artifact delivery'
if($LASTEXITCODE){throw 'Delivery commit failed'}
& robocopy $PSScriptRoot $destination STATUS.md /R:1 /W:1 /NFL /NDL /NP /NJH /NJS
if($LASTEXITCODE -gt 7){throw 'Final status copy failed'}
git switch -c gpt-light-r5
if($LASTEXITCODE){throw 'Cannot start round5'}
git merge main --no-stat
if($LASTEXITCODE){throw 'Resolve round5 merge explicitly'}
