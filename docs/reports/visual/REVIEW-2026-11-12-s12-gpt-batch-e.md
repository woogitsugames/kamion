# Recenzja niezależna — pakiet E rund GPT (light r5, life r4, edge r5) — s12

Data: 2026-11-12 · Recenzent: visual-critic (Opus), niezależny od autorów i ich self-review. Tylko odczyt (jedyny zapisany plik: ten).
Pytanie: czy każdą gałąź można **scalić do main** (`29f5cf85`, po 0130/0131 i truck r3). Kryteria jak w batch A–D: (a) brak regresji rozpoznawalności trasy (D51), (b) Low draws nie rośnie, tris ≤ +2 % na trasie, (c) docs/06 — poprawa albo brak pogorszenia, (d) licencje/marki. Wszystko to render edytora; koszt GPU A16 **UNVERIFIED** dla wszystkich trzech.

Metoda: `git merge-tree --write-tree [--name-only] main <gałąź>` (bez refów), `git log --no-merges --name-only main..<gałąź>` (własne pliki rundy), `git log -p` własnych zmian shaderów. Obrazy: edge `hall-review/{High-clear,Low-overcast}-pair.jpg`, `hall-review/full-High-clear.jpg`, `native-review/High-clear-sbs-g3-a-303305…-pair.jpg`; life `refs/sbs-wheel-detail-a2.jpg`, `refs/sbs-yard-rim-a2.jpg`, `a2-preview/High-clear-details.jpg`; light `reference-night/night-1-High.jpg`, `night-2-Low.jpg`. Kontrola main po 0131: `artifacts/integration-s12/vqa-f/Low-clear/edge-south.png`, `vqa-f/High-dusk/stretch-02.png`.

## Podsumowanie

| Runda | Werdykt | Jakość | (a) D51 | (b) Low draws / tris | (c) anti-slop | (d) licencje | Uwagi feedbacku wykonane? |
|---|---|---|---|---|---|---|---|
| **edge r5** (hala ≥ 22 m, fasada przemysłowa) | **SCAL** (merge-tree czysty; generaty i tak regenerować) | PARTIAL, realny plus | bez zmian (tło) | 0 / 0 (236 par Low: draws, instancje, cienie, trisK = 0) | usunięte pomarańczowo-brązowe „pudło EC”; teraz szara okładzina + pas szkła na High | OK (zdjęcia B z atrybucją, tylko artefakty) | P1 hala — TAK. Apron NW — NIE (jawnie w backlogu) |
| **light r5** (natywna LUT High→Low, referencja HDR QA) | **SCAL warunkowo** — bez martwego eksperymentu w shaderach runtime (patrz §2) | diagnostyka; obraz domyślny niezmieniony | bez zmian | 0 / 0 (327 Low) | **brak zmiany obrazu**; Night nadal FAIL | OK (Rakoon CC0 tylko referencja) | Smog — NIE ruszony. Plamy pod latarniami — NIE (tylko `night-pool-state-analysis.json`) |
| **life r4** (felgi placowe LOD0) | **SCAL warunkowo** (`LICENSES.md` → main; generaty/GLB → `--ours` + regeneracja) | PARTIAL, mały plus | bez zmian | 0 draws; trasa Low maks. +0,37 % tris; **wszystkie kamery Low +3,50 %** (zbliżenia placu) | miska felgi lepsza od płaskiego wachlarza; **opona to 10-kąt** — slop | OK w grze; artefakty z logo Wielton (P2) | Z listy r4 (czarne auto, szum lakieru, cień-prostokąt, brud tyłu, naczepy) — **0 z 5**. Felgi z batch B — częściowo |

**Kolejność scalania:** 1) edge r5 (czysty) → 2) light r5 (czysty w merge-tree, ale z ręczną poprawką §2) → 3) life r4 (konflikty) → **jedna** regeneracja świata na końcu (`build_region` → `build_world` → `import-region`), bo edge i life zmieniają `world_manifest.json`, a life — `street_props.glb`.

Kontrola main (vqa-f) dla uwag z poprzednich rund: `Low-clear/edge-south` — dół nieba jasny, bladoszary, bez twardego beżowego pasa; w tym kadrze smog akceptowalny (P2), reszta kątów nadal niezweryfikowana. `High-dusk/stretch-02` — głowica latarni to biały prostokąt, **na jezdni pod latarniami nie ma żadnej plamy światła**; zmierzch to pochmurny dzień z różowym horyzontem. Na main nadal widać pomarańczowe pudło hali (edge r5 to naprawia) oraz biało-czerwone zapory końca mapy na osi kadru (B-edge, otwarte).

## 1. edge r5 — SCAL

**Zmiany:** `far_field.py` (usunięta reguła „wysokość ≥ 22 m ⇒ EC”, wygląd energetyczny tylko z jawnej funkcji), `WorldSurface.shader` (+20 linii: gałąź za istniejącym `_FAR_FACADE`, aktywowana tylko znacznikami alfa 0,25/0,65; bez nowego keywordu, tekstury, przebiegu ani varyingu), `test_far_field_industrial_facade.py` (red 18+2 oczekiwane → green 20/20), ADR 0121, manifesty.

**Obraz:** przed — brązowo-pomarańczowa skrzynia z pomarańczową czapą: główny element slopu na panoramie południowej. Po (High-clear) — szara okładzina panelowa z jaśniejszym pasem świetlików w górnej krawędzi; z odległości czyta się jako hala magazynowa. Low-overcast — tylko spokojniejszy kolor, podziałów praktycznie nie widać (zgodnie z deklaracją). Nadal pudło bez cokołu, bram, rynien i brudu; na tle kadru to już tło, nie przyciąga oka. W porównaniu z G3-A 303305 zmiana jest poza kadrem — bez wpływu na rozpoznawalność.

**Liczby:** far-field 24 500 tris Low / 118 524 High bez zmian, bufory 1 411 032 B / 6 852 634 B bez zmian, 472 pary kamer z deltą 0. Testy: EditMode 340/340, GIS 710 passed / 1 xfailed / 0 failed.

**Uwagi (P2):** hash `frac(sin(dot(...))*43758.5453)` w `WorldSurface.shader` — na Mali przy dużych UV precyzja `sin` się sypie, a wariacja paneli może migotać; tłumienie `panelFW` łagodzi problem, ale na A16 trzeba to sprawdzić (lepszy byłby hash całkowitoliczbowy albo z tabeli). Dodatkowy koszt ALU tej gałęzi na telefonie UNVERIFIED.

**Następna runda (r6):** P1 apron NW („podłoga sceny”) i styk kurtyn; P1 biało-czerwone zapory końca mapy na osiach widokowych (widać na `edge-south` i w hall-review) — zamienić na kontynuację drogi lub las/ekran, zgodnie z uwagą s11; B9 bloki na horyzoncie. Po `git merge main` (baza r5 nie zawiera poprawki nieba light r3).

## 2. light r5 — SCAL warunkowo

**Co jest wartościowe:** (1) **znalezisko w QA**: High mimo `HDR=true` zapisuje kolor R8 sRGB przed post, więc wszystkie dotychczasowe kamery kontrolne High pokazują obcięty/zbandowany obraz przed tonemapem. Jest to istotne dla wszystkich dziedzin. `LightHdrQaReference` daje referencję R16. Lider powinien sprawdzić format bufora na telefonie (UNVERIFIED). (2) Narzędzia lab LUT (`LightGradeLutLab*`, `LightNativeGradeLutCapture`, `LightGradeLutWorldProbe`) — tylko Editor. (3) Refaktor `KamionDimColour` — neutralny.

**Czego nie robi:** obraz w grze jest bajtowo taki sam jak na main (LUT domyślnie OFF). Pary nocne (`night-1-High`, `night-2-Low`): render to szary dzień-za-noc. Latarnie nie świecą, pod nimi nie ma plam, okna są martwe, brak halo i ciepłej barwy sodowej/LED. Zdjęcie (Rynek Kościuszki, Rakoon CC0) ma kontrast plam światła rzędu kilku EV. Pod względem nocy runda dalej daje **FAIL**, tak samo jak batch D. Uwaga P1 o smogu (batch C/D) nie była nawet testowana na innych wysokościach słońca.

**P1 — warunek scalenia (ręczna zmiana lidera po merge):** gałąź wprowadza do **wszystkich shaderów runtime** martwy eksperyment. W `game/Assets/_Project/Rendering/Shaders/KamionAtmosphere.hlsl` są: `TEXTURE3D(_KamionOpaqueGradeLut)` + sampler, trzy uniformy `_KamionOpaqueGrade*`, `#include ".../Color.hlsl"`, a `KamionOpaqueTone()` ma `UNITY_BRANCH` na uniformie i ścieżkę LogC. `KamionMixFog()` woła to dla każdego opaque piksela świata i ciężarówki, a `Sky.shader:219` zmienia `KamionTone(c)` → `KamionOpaqueTone(c)`. Wersja z `shader_feature` (v6) jest przez autora odrzucona jako nieudana, czyli zostaje uniform branch + dodatkowe wiązanie tekstury 3D w player buildzie (limit samplerów GLES, rejestry Mali). Nikt tego nie zmierzył na A16, a efektu w grze nie ma. Co zrobić:
- `KamionAtmosphere.hlsl`: **zachować** `KamionDimColour()` i nowe `KamionTone()`. **Usunąć z runtime** blok `TEXTURE3D(_KamionOpaqueGradeLut)…KamionOpaqueTone(){…}` oraz include `Color.hlsl`; `KamionMixFog` ma zwracać `KamionTone(c)` (jak na main).
- `Sky.shader:219`: zostawić wersję main `c = KamionTone(c);`.
- Przenieść `KamionOpaqueTone` + deklaracje LUT do include'a tylko dla labu (np. `Rendering/Editor/LightGradeLutLab.hlsl`) dołączanego przez `LightGradeLutLab.shader`. Bez tego shader labu się nie skompiluje. `LightGradeLutWorldProbe` (świat z LUT) wtedy nie zadziała, dopóki autor nie zrobi wariantu, który da się wyciąć z buildu. To koszt po stronie GPT, nie runtime.
- Alternatywa: scalić bez zmian **dopiero po** pomiarze A16 (`device-metrics.ps1`, p50/p95 przed/po) z deltą ≤ szumu.

`LP_Night.asset` — tylko przestawione pole `dimColourDesaturation` (bez zmiany wartości). Bez znaczenia, przyjąć.

**Liczby:** 654 PNG (109 kamer × 3 presety × 2 tiery); Low draws/tris +0. EditMode 341/341, GIS 690 passed / 1 xfailed. Ablacja: 34/36 klatek bliżej HDR, Overcast `cab-dash` 4,73→5,65 i `cab-driver` 6,69→9,24 to regresje (tylko lab).

**Licencje:** referencje nocne Rakoon CC0, dzienne grobin CC BY-SA 4.0 — w `sources.json` są hasze i atrybucje, tylko artefakty. OK.

**Następna runda (r6) — kolejność:** P0 dla Night: plamy światła pod latarniami Putry/Andersa (`KamionLampPools` już jest — dlaczego `night-pool-state-analysis` pokazuje zero na jezdni?), emisja głowic, ciepła barwa, 10–20 % okien zapalonych. P1 smog: kamery yaw 0–135/180–225/270–315 i słońce 10°/25°/42°. Natywną LUT runtime wprowadzić dopiero jako wariant wycinany z buildu + pomiar A16. Diagnozę Overcast (szyba) robić równolegle, nie zamiast.

## 3. life r4 — SCAL warunkowo

**Zmiany:** `life_props.py` (miska, piasta, otwory felg LOD0), `test_yard_wheel_recess.py` (9/9), oczekiwania w `test_streetscape.py`/`test_world_v31.py`, ADR 0122, generaty + `street_props.glb` (LFS) + `props_meta.json`.

**Obraz:** `sbs-wheel-detail-a2` — felga ma teraz głębię, wypukłą piastę i 5 ciemnych otworów, czyli lepiej niż płaski wachlarz r3. Nadal jednak wygląda jak **zabawka**: 10-kątny obrys obręczy, 8-kątna piasta, trapezowe otwory, jednolity jasnoszary materiał bez nakrętek, pierścienia nakrętek, zabrudzenia hamulcowego i ciemnego wnętrza bębna. To dokładnie zarzut z truck r3. W `a2-preview/High-clear-details` **opona to wyraźny 10-kąt** (sylwetka kanciasta w każdym zbliżeniu). Autor podniósł LOD0 ciągnika 766→1550 i naczepy 1102→1942 tris, ale wydał je na otwory felgi, zostawiając wielokątną oponę. To złe rozłożenie budżetu: obrys opony jest pierwszą rzeczą, którą widzi oko. `sbs-yard-rim-a2` — z odległości 10–15 m felga jest czytelna, ale z boku naczepa wciąż jest pudłem z płaskimi czarnymi plandekami. Kadr `reefer_0_supports5`: szara płaszczyzna terenu przecina obraz (autor sam to oznaczył). To błąd świata, nie tej rundy, ale do zgłoszenia.

**Liczby:** draws +0 wszędzie. Trasa: Low maks. +0,37 %, High +0,59 % — w limicie. **Wszystkie kamery: Low +3,50 % (`yard_tractor_white_side8`), High +2,64 %** — powyżej +2 %, ale to zbliżenia placowe, nie trasa. Przyjmuję, z warunkiem P2 poniżej. Sufity LOD0 w teście: naczepy 1200→2200, ciągniki 1500→1700 — uzasadnić w ADR 0122 (podobnie jak 260→320 w r3). Testy: EditMode 340/340, GIS 709 passed / 1 xfailed.

**Konflikty (merge-tree):** `generated/{fidelity_qa,streetscape_qa,world_manifest}.json`, `street_props.glb` → `--ours` + **regeneracja** (`life_props.py` scala się automatycznie, więc GLB odtworzony z main po merge zawiera felgi r4; `props_meta.json` auto-merge, ale i tak go nadpisać regeneracją). `docs/LICENSES.md` → **w całości strona main (`--ours`)**. Strona gałęzi to tylko starsze duplikaty (Life r3 i „Kabina — skan skóry CC0”, który main już ma jako sekcję ADR 0112). Life r4 nie dodaje żadnego nowego wpisu licencji. Duże pliki: brak (artefakty w gicie 4,6 MB, największy `a2-all-camera-budget.json` 576 kB); `baseline-street_props.glb` jest tylko na dysku, nie w gicie.

**Licencje/marki (P2):** `artifacts/life-r4/refs/sbs-yard-rim-a2.jpg` i `yard-34-reference.jpg` zawierają duże logo i hasło WIELTON (zdjęcie Cekay CC0). Prawa autorskie są w porządku, ale zasada „bez cudzych marek” plus precedens z cab r4 (wykluczone zdjęcia z logo) mówią: `git rm` obu przy scaleniu albo zastąpić je kadrem z wyciętą/rozmytą plandeką. W grze logo nie ma.

**Uwagi z feedbacku r4 (s12 11:52):** czarne auto = szary metalik — NIE; szum płatków lakieru na High — NIE; twardy prostokątny cień pod autem (P1) — NIE; brud tyłu — NIE; naczepy z batch B (barierki boczne, tylny zderzak, fałdy plandeki) — autor twierdzi, że „osprzęt podwozia już istnieje”, ale tego nie pokazał na obrazie przed/po; przycięcie artefaktów — częściowo (3,5 GB na dysku main, 128 plików w gicie). **Wykonanie listy: 0/5.** Runda zrobiła tylko zaległy punkt z batch B.

**Następna runda (r5) — zamiast „zaległych palet”:** P1 obrys opony ≥ 20–24 segmentów na LOD0 (tris przenieść z otworów felgi), ciemne wnętrze felgi/bębna i pierścień nakrętek jako mapa, nie geometria. P1 cień-prostokąt pod osobówkami. P1 czarny lakier (albedo ~0,02–0,04, bez szarego metaliku) i szum płatków na High. P2 brud tyłu. Dopiero potem palety.

## Ryzyka wspólne
- Wszystkie trzy bazują na main sprzed 0130/0131 (`889201d5`/`8b74c2c5`). Po scaleniu i regeneracji puścić jedną serię `visual-qa` WorldC Low/High × clear/overcast/dusk i porównać z `vqa-f`.
- Każdy GPT zostawił na dysku main kilka GB artefaktów (`light-r5` 6,4 GB, `life-r4` 3,5 GB, `edge-r5` 2,6 GB). Do gita trafia mało, ale dysk trzeba posprzątać.
