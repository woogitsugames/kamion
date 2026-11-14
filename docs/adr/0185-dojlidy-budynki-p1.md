# ADR 0185 — Dojlidy: budynki po recenzji 0179 (hala zakładu przy Kuronia, blok Kuronia 3, ogrodzenie, poziom LoD1)
Status: Proposed (agent world-builder, s20, gałąź `dojbld-0185`), 2026-11-13. Do scalenia przez lidera.
Poprzednik: ADR 0179, recenzja `docs/reports/REVIEW-2026-11-13-s19-0179.md` (P1 P11-094, P1 P11-001, P2 tło).

## Kontekst
Recenzja 0179: (1) hala północna zakładu przy Kuronia ~12 % za wysoka w kadrze P11-094 i bez niższego segmentu na
prawym końcu, (2) białe ogrodzenie panelowe u podstawy daje morę na Low, (3) okładzina czyta się jak siatka bloczków
i ma rząd małych okienek, których nie ma na zdjęciu, (4) blok Kuronia 3 wygląda jak tynkowany biurowiec z PRL
z czarnymi pasami okien, P2: dodatkowe białe bloki w tle za blokiem — sprawdzić wysokości LoD1.
Zakres: tylko region `bialystok-dojlidy`; chunki regionu C bajt w bajt (manifest C dostaje 4 nowe wpisy materiałów). Bramy segmentowe / Bravilor / kamera pasa: ADR 0196;
zieleń: ADR 0186.

## Ustalenia z danych (zmierzone)
- **Poziom odniesienia LoD1.** `measuredHeight` LoD1 2024 to wysokość bryły nad jej dolną ścianą
  (`ground_z_evrf2007`); dla 329 budynków kafla z LoD1 najniższy teren obrysu (NMT 2025) leży medianowo 0,06 m poniżej
  tej podstawy (`artifacts/dojbld-0185/datum_stats.py`). Generator stawiał budynek na **medianie** terenu obrysu, więc na skarpie dach był za wysoko: mediana
  +0,22 m, p95 +1,42 m, max +3,52 m. Hala zakładu `bdot:2BE4B431-BC59…` +1,83 m (przy narożniku NE ściana 20,5 m
  zamiast 18,7 m = −9 %), budynek badawczy `bdot:2BE4B431-C1A0…` za blokiem Kuronia 3 (18,09 m) +2,69 m, hala
  Kuronia 2 +1,96 m. Same wysokości LoD1 są dobre — to odpowiedź na P2 „tło” i większość „12 %”.
- **Hala zakładu, P11-094.** 16 pasów paneli na ścianie (moduł nieznany: 1,0 m → 16,5 m z cokołem, 1,15 m → 18,9 m
  = LoD1). Pomiar w kadrze (`measure.py`, kolumna tuż za narożnikiem NE: zdjęcie x 230, rendery x 240 z 960 px):
  okładzina od krawędzi dachu do cokołu — zdjęcie 281 px, 0179 320 px (+14 %), dach na rzędnej LoD1 z niskim cokołem
  (r4) 319 px (+14 %), r5 285 px (+1 %). Krawędź dachu → grunt odczytane z profilu (±5 px): zdjęcie 294, 0179 363,
  r4 330, r5 296 → z r4: 18,7 m / 1,12 = 16,7 m nad gruntem 152,3 (liczby w `overrides.yaml` to te odczyty). Linia dachu ściany północnej schodzi w dół na zachodnim końcu (x 793/960; koniec ściany
  x 870/960) do niższego segmentu w tej samej płaszczyźnie: wysokość 180 px wobec 255 px (0,71). Ortofoto 2024: wysoka
  hala kończy się na prostej równoległej do ściany wschodniej, 11,8 m od narożnika NW + ~2 m przesunięcia radialnego
  krawędzi dachu = 13,8 m (z namiaru w kadrze 15–19 m). Rzędu małych okienek na zdjęciu nie ma (lampy).
- **Ogrodzenie istnieje**: OSM way 702465389 (`barrier=fence`, 819 m wokół zakładu, 8,5 m od ściany północnej) i widać
  je na P11-094 jako cienką siatkę ze słupkami u podnóża skarpy. Mora: tekstura `fence_mesh` miała mipy zachowujące
  pokrycie alfa (`mipMapsPreserveCoverage`) — ~15 % tekseli kryjących na każdej odległości, czyli biała krata tam, gdzie
  piksel jest szerszy niż rozstaw drutów (50 mm).
- **Okładzina**: set `sandwich_ribbed` ma tylko fugi poziome, ale 10 % pionowych zacieków wpieczonych w albedo i był
  próbkowany w domyślnym kaflu 4 m (pasy 0,67 m) — stąd „bloczki”.
- **Blok Kuronia 3, P11-001**: panele pionowe w jasnym srebrnoszarym kolorze; trzy wysokie kondygnacje — parapety pasm
  okien ściany południowej na 0,19 / 0,51 / 0,82 wysokości = 2,7 / 7,2 / 11,5 m z 14 m, pasma ~1,4 m, od ~12 %
  długości; na szczycie zachodnim pionowy pas przeszklenia klatki przy narożniku południowym i małe okna (nie rysowane).

## Decyzja
1. **Generator (opt-in; region bez takich wpisów nie zmienia wyniku)** — `streetscape/buildings_mesh.py`:
   - `kind: building_rules` / `lod1_base_datum: true` — dach na poziomie podstawa LoD1 + wysokość (`roof_height`; nie
     mniej niż 60 % wysokości LoD1 — 5 budynków na limicie; tylko `height_source` LoD1 / authored z `ground_z_evrf2007`).
   - `target_sets`: kilka wpisów `target: {building}` na ten sam budynek = suma `set` w kolejności pliku (było: ostatni
     wpis zastępował poprzednie w całości). Region C nie ma budynku z dwoma wpisami (test). `override:<id>` celuje
     w `building_part`.
   - klucze `set`: `storeys`, `hall_windows: false` (bez losowanego rzędu okienek hali), `hall_sign: false` (bez tablicy
     reguły — w r1 ciemna pusta płyta w miejscu prawdziwego szyldu), `hall_plinth_z` (rzędna wierzchu cokołu hali na
     skarpie; reguła dawała 0,6 m nad MEDIANĄ terenu = 2,2 m ciemnej ściany przy narożniku NE); `ground_z_evrf2007`
     w `building_part`.
2. **Materiały** (`streetscape/materials.py`, blok addytywny) i sety (`art-source/world/materials/_src/sets_facade.py`):
   - `sandwich_smooth` (kafel 3,45 m = 3 pasy 1,15 m, gładkie lico, fugi cieniowe, bez wpieczonych zacieków) →
     `hall_wall_smooth` z `panel_m: [6.0, 1.15]` (styk pionowy co 6 m i ton na panel — shader ADR 0092), kolor
     `hall_wall_white`. Moduł 1,15 m i raster 6 m: WORKING_VALUE.
   - `cladding_vertical` (panele pionowe 1,0 m) → `cladding_vertical_grey` 0,33 (+ `__far_office` / `__far_ribbon`).
     Ton zmierzony: ściana długa bloku / biała hala naprzeciwko = 129 / 140 sRGB na zdjęciu (liniowo 0,85), w renderze
     107 / 113 (0,89); r1 z 0,47 był jaśniejszy od hali.
   - Oba sety generowane w 1024 px (High 1024, Medium 512, Low 256): ¼ pamięci zwykłego setu przy tej samej gęstości
     tekseli co `sandwich_ribbed` (kafel 3–3,45 m zamiast 6 m).
3. **Ogrodzenie** (`World/Import/InstanceImporter.cs`) — **jedyna zmiana nie-opt-in, dotyczy też regionu C**: tekstury
   `fence_*` bez `mipMapsPreserveCoverage` — druty cienieją z odległością i znikają; słupki i cokół zostają (na
   P11-094 siatki z 45 m też prawie nie widać). Próg alfa 0,25 (r2), który trzymał poziome druty dłużej, rozpadał je
   w kropki przy 40 m — odrzucony.
4. **Dane Dojlid** (`overrides.yaml`, 4 nowe bloki, stare nietknięte):
   - `dojlidy-lod1-base-datum`.
   - `rosti-west-wing` (`building_part`, 3234 m², granica 13,8 m ±2 m od narożnika NW, 12,2 m nad podstawą LoD1
     152,06 = 0,71 × ściany głównej, WORKING_VALUE ±1 m).
   - `rosti-hall-cladding`: `hall_wall_smooth`, `hall_windows: false`, `hall_sign: false`, `hall_plinth_z: 152.9`,
     **`height_m: 16.9`** (nad podstawą LoD1; LoD1 mówi 18,92) — z pomiaru w kadrze 16,7 m nad gruntem, zgodnie
     z recenzją (16,5–17 m); WORKING_VALUE ±1,2 m, **niżej niż pomiar GUGiK** — do rozstrzygnięcia zdjęciem z miarą.
     Wysokość dotyczy całego obrysu BDOT (także części południowej zakładu).
   - `kuronia3-office-block-facades`: `storeys: 3`, `cladding_vertical_grey`, `facades`: długie ściany — pasma
     2,3–3,6 m nad posadzką kondygnacji od 12 % długości, pozostałe (w tym szczyt W) — ślepe (r3 z kolumną okien
     klatki dawał okna biurowe z klimatyzatorem; polecenie: szczyt bez okien).
   Hala główna zachowuje id BDOT (`bdot:2BE4B431-BC59…`); jej ściana północna ma teraz 69,6 m od narożnika NE.

## Wyniki
- **Iteracje:** r1 → r2 (bez tablicy hali, blok ciemniejszy, próg alfa siatki 0,25) → r3 (próg odrzucony) → scalenie
  `origin/main` → r4 (szczyt K3 ślepy, cokół hali) → r5 (wysokość hali z kadru). Każda: build_world → import → 5 kadrów
  foto Low overcast → oględziny par.
- **Wizualnie** (`artifacts/dojbld-0185/sbs-r5/`; przed: `artifacts/dojlidy-vis-0179/sbs/`; przed/po bez zdjęcia: `cmp/`):
  | Para | Jest | Rozbieżne |
  |---|---|---|
  | `sbs-P11-094.jpg` | schodek dachu i niższy segment na prawym końcu; długie poziome panele ze stykami co 6 m; brak okienek i tablicy; niski cokół; ogrodzenie = słupki bez białej kraty; okładzina przy narożniku NE 285 px wobec 281 px na zdjęciu (+1 %; 0179: 320 px, +14 %) | zacieki pod attyką mocniejsze niż na zdjęciu (nowy budynek); brak bram (ADR 0196); D-6 blisko kamery |
  | `sbs-P11-001.jpg` | blok srebrnoszary z pionowymi panelami, trzy wąskie pasma okien na ścianie długiej, szczyt ślepy, budynek badawczy w tle niższy (rzędna LoD1) | szczyt na zdjęciu ma ciemny pas przeszklenia i dwa krótkie pasma okien; brak doku z wiatą; brama/DDR/płot (0188/0189) |
  | 063, 056, 129b | obejrzane pary r5 (`sbs-r5/`) i przed/po r3 (`cmp/before-after-*.jpg`): hala Kuronia 2 niższa (rzędna LoD1: −1,96 m wg `datum_stats.py`), bloki szpitala nieco niższe (UNVERIFIED ile), biała krata płotów w tle zniknęła; nic nie zepsute | bez zmian względem recenzji 0179 (zakres 0186/0189/0196) |
- **Kondygnacje po regule poziomu LoD1** (`storey_check.py`; domy/biura/bloki z liczbą kondygnacji BDOT, 246): zgodność generatora z BDOT
  168 → 195; pogorszenie w 2 biurach (BDOT 2 → 1 i 3 → 2 kondygnacje przy 5,3 m i 8,65 m).
- **Budżet statyczny A/B** (`budget_ab.py`, klin 120°, 13 kamer; `budget_ab.txt`): względem `origin/main` materiały w kadrze +0…+3 (max 118 → 121), trójkąty Low −0,03…+0,24 % (max 700 869), High −0,79…+0,08 % (max 1 714 298). Nowe materiały tylko w chunkach 5_1, 5_2 (blok) i 5_3, 6_2, 6_3 (hala).
- **Unity, kadry foto Low** (`*/stats.txt`, szacunek edytora przed batchingiem; przed = 0179 build #4, między nimi
  scalono też 0170/0172/0184…): drawsEst 001 335 → 336, 056 125 → 124, 063 317 → 323, 094 195 → 198, 129b 320 → 318; trójkąty 462 860 → 455 744, 158 580 → 158 524, 333 897 → 331 161, 288 046 → 289 153, 426 238 → 422 945.
- **Pamięć tekstur** (`materials_spec.json`, ASTC z mipami, oba sety razem): High 4,98 MB, Medium 0,97 MB, Low 0,17 MB.
- **Region C:** po pełnym pytest (build C kodem tej gałęzi) `world_manifest.json` C różni się od main tylko 4 nowymi
  wpisami w tabeli `materials`; sha wszystkich chunków bez zmian. Pliki C cofnięte, nie są w commicie.
- **Testy** (po scaleniu `origin/main` b4daac9df, kod = stan końcowy poza danymi r5):
  - `pytest tests/gis`: 1110 passed, 2 failed, 2 xfailed (913 s). Porażki nie z 0185:
    `test_world_v31::test_forest_trees_reference_their_cell` (komórka `25_16`; pada też w `bollards-0183` po scaleniu
    main), `test_p1_0161::test_ring_mast_survives_the_carriageway_clearing` (czyta `Data/raw/derived/<C>/world` —
    w worktree kopia sprzed regeneracji C, `signal_mast` zamiast `signal_mast_9m`).
  - `tests/gis/test_dojbld_0185.py` (7) + `test_dojlidy_0179.py` (7) po r5: 16 passed (z `test_photo_cameras_0174.py`).
  - EditMode: 581 total, 580 passed, 0 failed, 1 skipped.
- Brak zrzutu z telefonu (zakaz adb w tej sesji) — docs/06 §5 pkt 2 do wykonania przy bramce.

## Otwarte
- **Warunek scalenia — płot w regionie C:** zmiana importera nie była renderowana w C (bramka 3 zaliczona na starej
  siatce). Przy regeneracji lider renderuje kadr C z ogrodzeniem panelowym; jeśli „słupki bez wypełnienia” od ~10 m
  (odległość UNVERIFIED, widać w `cmp/fence-near-P11-001-0179-vs-r3.jpg`) nie przejdą — cofnąć jedną linię
  `mipMapsPreserveCoverage` (wraca mora) albo zlecić daleki LOD siatki jako półprzezroczystą „mgiełkę” (rendering).
- Wysokość hali zakładu 16,9 m (kadr) wobec LoD1 18,92 m; skrzydło 12,2 m i granica 13,8 m — WORKING_VALUE; przybudówka
  za skrzydłem dostała tę samą wysokość; południowa część zakładu dzieli wysokość hali (jeden obrys BDOT).
- Drzwi osobowe na ścianie północnej hali stoją ~1,2–1,7 m nad gruntem (próg reguły = mediana terenu + 0,15 m,
  UNVERIFIED z kadru r5) — po obniżeniu cokołu widać to z ulicy; potrzebny próg wg terenu pod ścianą albo schody.
- Zacieki pod attyką na `hall_wall_smooth` (siła liczona z jasności, wspólna dla hal) — za mocne dla nowej hali (P2).
- Blok Kuronia 3: szczyt z pasem przeszklenia i krótkimi pasmami, dok z wiatą, ściany N/E nieznane (zdjęcie właściciela).
- Reguła `lod1_base_datum` jest włączona tylko w Dojlidach; w regionie C ten sam błąd poziomu istnieje (decyzja lidera,
  zmienia bajty C). Dwa biura z gorszą liczbą kondygnacji — do poprawy `storey_plan` (zakres 2,8–4,6 m/kondygnację).
- `set` hali głównej: ADR 0196 (bramy) celuje w ten sam budynek — po scaleniu sety się sumują (`target_sets`).

## Odtworzenie
```
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy
pwsh scripts/import-region.ps1 -Region bialystok-dojlidy
pwsh scripts/visual-qa.ps1 -Scene World_bialystok-dojlidy -Tier Low -Lighting overcast -Width 1920 -Height 1080 `
  -Cameras 'photo_P11-001,photo_P11-063,photo_P11-056,photo_P11-094,photo_P11-129b' -OutputDir artifacts/dojbld-0185/r5-Low-overcast-photo
bash artifacts/dojbld-0185/sbs.sh artifacts/dojbld-0185/r5-Low-overcast-photo artifacts/dojbld-0185/sbs-r5
uv run --project tools/worldgen python artifacts/dojbld-0185/measure.py artifacts/dojbld-0185/r5-Low-overcast-photo
```
