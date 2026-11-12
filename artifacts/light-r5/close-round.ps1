param([Parameter(Mandatory)][int]$GisExitCode,[Parameter(Mandatory)][string]$GisLog)
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
if((git branch --show-current).Trim() -ne 'gpt-light-r5'){throw 'Require round5'}
git diff --cached --quiet HEAD
if($LASTEXITCODE){throw 'Unexpected staged work'}
if($GisExitCode -ne 0){throw 'GIS not terminated0'}
$summary=[regex]::Match((Get-Content -LiteralPath $GisLog -Raw),'(?m)^(\d+) passed, (\d+) xfailed in ([\d.]+)s')
if(-not $summary.Success){throw 'Missing passing GIS summary'}
$passed=$summary.Groups[1].Value;$xfailed=$summary.Groups[2].Value;$seconds=$summary.Groups[3].Value
$xml=[xml](Get-Content "$PSScriptRoot/tests/editmode-final.xml" -Raw)
if($xml.'test-run'.result -ne 'Passed' -or $xml.'test-run'.passed -ne '341' -or $xml.'test-run'.failed -ne '0'){throw 'Require341/341EditMode'}
& pwsh "$PSScriptRoot/compare-final-budget.ps1"
if($LASTEXITCODE){throw 'Budget/proof failed'}
foreach($preset in 'clear','overcast','night'){foreach($tier in 'Low','High'){
    if(@(Get-ChildItem "$PSScriptRoot/final-native-v2/$tier-$preset" -Filter '*.png').Count -ne 109){throw 'Require109PNG'}
}}
foreach($name in 'FINAL-HDR-REVIEW.md','FINAL-LOW-PARENT.md'){
    if((Get-Content "$PSScriptRoot/review/$name" -Raw).Length -lt 300){throw 'Missing full visual review'}
}
foreach($series in 'reference-day','reference-night'){
    $inventory=Get-Content "$PSScriptRoot/$series/sources.json" -Raw|ConvertFrom-Json
    foreach($item in $inventory){
        if($item.width -gt 960 -or (Get-FileHash -LiteralPath $item.photo).Hash -ne $item.photo_sha256 -or (Get-FileHash -LiteralPath $item.render).Hash -ne $item.render_sha256 -or (Get-FileHash -LiteralPath $item.pair).Hash -ne $item.pair_sha256){throw 'Photo evidence changed'}
    }
}
$generated=@('Data/Regions/bialystok-industrial-c/generated/far_field_qa.json','Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json','Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_putry_underdeck.spec.json','Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json','Data/Regions/bialystok-industrial-c/generated/world_manifest.json','Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json','art-source/world/props/props_meta.json','art-source/world/props/street_props.glb')
$dirty=@(git diff --name-only HEAD)
if(@($dirty|Where-Object {$_ -notin $generated}).Count){throw 'Unexpected changes outside own generated effects; inspect manually'}
git diff --binary -- @generated | Set-Content "$PSScriptRoot/generated-rebuild.patch" -Encoding utf8
$glb='art-source/world/props/street_props.glb'
Copy-Item -LiteralPath $glb -Destination "$PSScriptRoot/generated-street_props.glb"
if((Get-FileHash -LiteralPath $glb).Hash -ne (Get-FileHash "$PSScriptRoot/generated-street_props.glb").Hash){throw 'GLB archive differs'}
@{source=$glb;sha256=(Get-FileHash -LiteralPath $glb).Hash;bytes=(Get-Item -LiteralPath $glb).Length}|ConvertTo-Json|Set-Content "$PSScriptRoot/generated-archive.json" -Encoding utf8
git restore -- @generated
if($LASTEXITCODE){throw 'Generated restore failed'}
$sha=(git rev-parse HEAD).Trim()
Add-Content docs/adr/0108-light-sky-exposure-post.md "Zamknięcie r5: czysty bakev6 (65PNG, pięć presetów), finalv2 (654PNG,109kamer), oględziny wszystkich327Low i327High oraz10par956px. Budżet327Low draws/tris0, instancing osobno. EditMode341/341, pełnyGIS $passed passed/$xfailed xfailed w $seconds s, kod0 podheavy. Własne8 efektówgeneratora zarchiwizowano i przywrócono. Natywna LUT pozostaje eksperymentem Editor OFF, kosztGPU/runtime i całejklatki niezatwierdzone; regresje Overcastkabiny oraz nocneźródła nadalotwarte."
@(
"Gałąź gpt-light-r5; stan dowodów $sha, baza main 889201d5 (merge 8a76b69b).",
'Runda diagnostyczna spójności tonów Low/High: natywna kostka High URP32³ w RGBAHalf, domena LogC, bez runtime bindera i domyślnego włączenia.',
'Wykryto ograniczenie dotychczasowego QA: High mimo HDR=true zapisuje kolor R8 sRGB już przed post. Jawna referencja HDR zachowuje R16 half-float przed post przy końcowym ARGB32; telefonu nie badano.',
'Czysty bake v6:65PNG, pięć presetów; holdout192/preset max1 RGB, rampy12288/preset max3/2/3/3/3. Pięć kostek po256KiB, physical-capture bypass max0.',
'Pierwsza racjonalna LUT miała błąd zieleni max14/15; natywna usuwa duże odchylenie. Białe chmury odrzuconej v3 naprawiono przez zachowanie tego samego sky cap co High.',
'Nieudany shader_feature v6 oraz observer v4/v5 z wyjątkiem inicjalizacji pozostają odrzuconą diagnostyką. Końcowy native v6 jest czysty,65/65PNG identyczne z wcześniej obejrzanymi.',
'Final-native-v2:654PNG,109kamer x3presety x2tiery, wszystkie obejrzane przez rodzica i krytyka. Pierwszy final402PNG odrzucono; poprawiony spec wymaga109kamer/job.',
'Budżet wszystkich327Low: draws/tris+0, instancing osobno. W36parach statycznych kostek ablation mip0 RGBmean/max0; nie rozszerzamy tego na niezmierzone capture całej trasy.',
'W12kamerowej ablation błąd całych klatek wobec HDR maleje w34/36; Overcast cab-dash4,731→5,648 i cab-driver6,694→9,245 pozostają regresjami. To różne tiery/geometria/skala/alpha, bez fotometrycznego gate.',
'Pary foto|render: reference-day (4) i reference-night (6), po956px, hasze i licencje w sources.json. Inne warunki/miejsca/pory, bez zaliczenia pozy lub fotometrii.',
"Pełny EditMode341/341; końcowy GIS $passed passed/$xfailed xfailed w $seconds s, kod0. Ciężki Python tylko przez heavy, pełnyGIS wyłącznie na końcu rundy.",
'Pozostają: gładkie chmury Overcast Low, szkło i instrumenty, płaski detal białych aut, nierówny Night, ciemne doki/okna i brak halo. Brak GPU/A16, runtime i pełnego Night/wholeframe PASS.',
'Konflikty możliwe w KamionAtmosphere.hlsl, Sky.shader, EnvironmentLighting, LightQaBatch i ADR0108. Cab/Truck/Vegetation/WorldPBR/WorldSurface oraz Claude bez edycji w tej rundzie.',
'Własne efekty generatora zachowano w patch i GLB, następnie przywrócono. Odtworzenie wymaga generatora/fidelity/importu w slotach; artefakty dostarczone do main bez merge/push.',
'Następna runda: kandydat native grade runtime domyślnie OFF, według NEXT-ROUND-CANDIDATE.md; najpierw nowa gałąź z poprzedniej i merge aktualnego main.'
)|Set-Content "$PSScriptRoot/REPORT.md" -Encoding utf8
Add-Content "$PSScriptRoot/STATUS.md" "Krok końcowy: EditMode341/341,GIS $passed/$xfailed xfailed/$seconds s. REPORT, ADR i własnegeneratedarchive/restore gotowe. Następny krok: dostawa/verify, r6 i merge aktualnego main. Cel24h aktywny do21:30:47Warszawa."
git add docs/adr/0108-light-sky-exposure-post.md
git add -f artifacts/light-r5/REPORT.md artifacts/light-r5/STATUS.md
git commit -m 'wip(light): close round5 with bounded HDR and native grading evidence'
$destination='C:/Users/matma/Documents/Claude/kamion/artifacts/light-r5'
& robocopy $PSScriptRoot $destination /E /R:1 /W:1 /NFL /NDL /NP /NJH /NJS
if($LASTEXITCODE -ge 8){throw 'Delivery failed'}
foreach($file in Get-ChildItem -LiteralPath $PSScriptRoot -Recurse -File){
    $relative=[IO.Path]::GetRelativePath($PSScriptRoot,$file.FullName)
    $target=Join-Path $destination $relative
    if(-not(Test-Path -LiteralPath $target) -or (Get-Item -LiteralPath $target).Length -ne $file.Length){throw "Delivery missing/different size: $relative"}
}
if((Get-FileHash "$PSScriptRoot/REPORT.md").Hash -ne (Get-FileHash "$destination/REPORT.md").Hash){throw 'Delivered REPORT differs'}
Add-Content "$PSScriptRoot/STATUS.md" 'Dostawa rundy5 do main przez robocopy zakończona; wszystkie rozmiary plików i SHA256 REPORT zweryfikowane. Bez merge/push. Następny krok: r6 i merge aktualnego main.'
git add -f artifacts/light-r5/STATUS.md
git commit -m 'wip(light): record verified round5 artifact delivery'
& robocopy $PSScriptRoot $destination /E /R:1 /W:1 /NFL /NDL /NP /NJH /NJS
if($LASTEXITCODE -ge 8){throw 'Final metadata delivery failed'}
if((Get-FileHash "$PSScriptRoot/STATUS.md").Hash -ne (Get-FileHash "$destination/STATUS.md").Hash){throw 'Delivered STATUS differs'}
Write-Output "ROUND5_DELIVERY: verified all file sizes and REPORT SHA256; no merge/push. Next: branch gpt-light-r6 from current round, merge latest main."
