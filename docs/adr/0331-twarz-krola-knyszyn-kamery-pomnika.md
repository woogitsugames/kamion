# ADR 0331 — twarz króla w Knyszynie (rzeźba głowy) i kamery kontrolne pomnika z ulicy

Status: Proposed (agent monument2-s24, 2026-11-24). Rozwija ADR 0325 §1 i §5 („twarz geometryczna, maska z bliska”).
Powiązane: ADR 0325 (figura), ADR 0320, `artifacts/critic-s24-build5/CRITIC.md` (pomnik bez klatek w przejeździe),
D43 (referencje tylko z otwartych źródeł), docs/06 §2 (anti-slop: „topiące się” bryły, maska, idealna symetria).

## Kontekst

Głowa z ADR 0325 była lofem 15 × 11 z osobnymi klinami (nos, brwi-belki, powieki, płaskie uszy). Z 4–6 m czytała się
jako maska, korona była wyższa niż twarz (0,185 m vs oczy–broda 0,135 m), kreza za nisko (widoczna szyja), fleurony
jak odłamki blachy. Render „przed”: `artifacts/monument2-s24/lookdev/before-face.jpg`.

## Pomiar referencji (Commons, CC BY-SA; poza gitem w `Data/raw/refs/knyszyn-king-commons`)

Zbliżenia `cs20127375` (H. Borawski, CC BY-SA 3.0) i `cs7518515` (Athantor, CC BY-SA 4.0), w jednostkach
E = oczy → broda (podbródek):

| Wielkość | Wartość | Status |
|---|---|---|
| dolna krawędź opaski korony nad oczami | 0,38 E | zmierzone na zdjęciu (perspektywa z dołu, ±15 %) |
| szczyty fleuronów nad oczami | 1,27 E (opaska ≈ 0,3 E, liście ≈ 2 × opaska) | j.w. |
| koniec brody pod podbródkiem | 0,7 E, broda w szpic, lekko w bok | j.w. |
| szerokość twarzy z włosami | ≈ 1,35 E; uszy odstające na wysokości oczu–nosa | j.w. |
| korona–koniec brody / wysokość figury | 0,18 (`cs7518515`, frontalne) | j.w. |

E = 0,165 m rysunkowo, potem cała głowa + kreza + korona skalowane × 1,12 wokół szyi (z 0,18 wysokości figury),
czyli E ≈ 0,185 m (figura ~1,6 × naturalnej wielkości). Wszystko `WORKING_VALUE`.

## Decyzja

1. **Głowa = jedna gładka siatka** (θ × z, 32 kolumny zagęszczone z przodu × 39 rzędów zagęszczonych na oczach i ustach)
   z promieniem = superelipsa czaszki + przemieszczenia (gaussy): czoło, łuk brwiowy, gładzizna, oczodoły, gałki
   z bruzdą nad powieką i rytą tęczówką, dolne powieki, skronie, kości policzkowe i zapadnięcia pod nimi, nos (grzbiet
   rosnący do czubka, skrzydełka, kulka), usta (warga górna, szpara, dolna), wąsy opadające na końcach, podbródek.
   Broda: grubość nad żuchwą od linii pod wargą przez kąciki ust do baków + płat w szpic pod podbródkiem, łączona
   gładkim maksimum (~5 mm) z twarzą; pasma i loki włosów jako falowane bruzdy kilku mm. Wspólne wierzchołki → gładkie
   normalne (bez klinów `flat`). Asymetria odlewu: przechył 1,6°, jedno oko 1,5 mm wyżej, koniec brody 6 mm w bok.
2. **Uszy**: muszle z rolowanym brzegiem i misą, tylna krawędź ~1,5 cm od głowy.
3. **Kreza** podniesiona do żuchwy, 48 wierzchołków na obwód z zaokrąglonymi płatami (4 na płat), z przodu podwinięta
   pod brodę, dół zapuszczony w szyję płaszcza (bez szczeliny widocznej z dołu).
4. **Korona** niższa (0,048 m opaski + 0,07 m liścia + kula), owal wokół włosów rozszerzający się 9 mm ku górze;
   4 liście z kamieniem w środku i kulą na szczycie (wysoki z przodu, jak na zdjęciach) + 4 perły na trzonkach;
   kamienie na wałku opaski. Liście jako bryły grubości 9 mm (`flat`), nie płaskie płytki.
5. **UV głowy** cylindryczne w skali twarzy (r = 0,10 m wokół osi głowy) — zacieki zestawu `bronze_cast_tint` mają
   na twarzy tę samą skalę co na płaszczu (wcześniej ×4 ściśnięte w pionowe prążki).
6. **Kamery**: nowe `king_street_driver_0331` (oko kierowcy 2,5 m na prawym pasie DW671 Grodzieńskiej w kierunku
   południowym, 40 m na wschód od pomnika, ortofoto 0,25 m ±1 m, obrót na pomnik, 40°) i `king_street_tele_0331` (ta
   sama poza, 12°: czy twarz i korona czytają się z ulicy). Kamery ADR 0325 (`king_front/34/head/side/square_0325`)
   zostają; `king_head_0325` jest parą dla zbliżenia `cs20127375`.

## Budżet

| Pozycja | ADR 0325 | ADR 0331 | Uwagi |
|---|---|---|---|
| figura LOD0 | 2 214 | 5 478 | głowa 2 462, uszy 2 × 82, kreza 480, korona ~700 |
| figura LOD1 | 288 | 372 | głowa 7 × 10, kreza 8, korona: opaska + 8 trójkątów |
| pomnik z cokołem i zegarem LOD0 / LOD1 | 2 380 / 326 | 5 558 / 422 | test: LOD0 ≤ 6 000, LOD1 ≤ 480 |

Uzasadnienie: obiekt charakterystyczny rynku, LOD0 tylko z bliska (warstwa `buildings`), +3,1 k trójkątów to < 0,1 %
budżetu klatki knyszyn-w (3,17 M p95, ADR 0327). Materiały bez zmian (3 brązy, 0 nowych tekstur).

## Wyniki

Pętla: look-dev Blender (Cycles) r1–r7 (`artifacts/monument2-s24/lookdev/`, przed: `before-face.jpg`), potem Unity
High / clear, Win64, kafel knyszyn przebudowany w kopii derived worktree (`build_world` exit 0, 1 047–1 068 s), dwie rundy:

- przed: `vqa-before/` (derived z main), po r1: `vqa-after/`, po r2: `vqa-after2/`; arkusze ref-vs-game
  `sbs/before-ref-vs-game.jpg`, `sbs/after2-ref-vs-game.jpg`, zbliżenie `sbs/head-crop-ref-before-after2.jpg`
  (zdjęcie Commons | przed | po).
- r1 w Unity: twarz czyta się z 4,5 m (nos, oczodoły, broda w szpic leżąca na krezie, uszy, niższa korona z liśćmi
  i perłami); wada: usta z wąsami dawały grymas, szeroka żuchwa → r2: poziome usta, węższa żuchwa, dłuższy szpic brody.
- Kadr `king_head_0325`: trisExact 429 862 → 431 797 (szacunek edytora przed batchingiem SRP). FPS w playerze nie mierzony.
- Kamery ulicy: render „przed” zrobiony w pozie −616,5 / −187,5 (skraj wjazdu na parking), „po” w docelowej
  −612,5 / −187,5. Z 40 m przez szybę kierowcy figura jest widoczna między lipami i za zaparkowanymi autami;
  w 12° widać koronę i sylwetkę, twarzy w cieniu lip nie (ADR 0325 §5).
- pytest: `tests/gis/test_knyszyn_park_props_0227.py`, `test_region_knyszyn_0204.py`, `test_truss_bridge_0320.py` —
  32 passed (`artifacts/monument2-s24/logs/pytest-targeted.log`). C# bez zmian (EditMode nie puszczane).

## Otwarte

- Pomnik stoi w cieniu lip frontem na NE; w `clear` twarz jest ciemna (bez zmian względem ADR 0325 §5).
- Brak napisu na płaszczu i tekstury patyny we wnękach twarzy (jeden materiał na głowie).
- Pozycja `KING` (ESTIMATED z ADR 0227) nie była przez to zadanie weryfikowana.

## Brąz i patyna (neon-bronze-s24, 2026-11-24)

Zamyka punkt otwarty wyżej („jednolita czerń figury w cieniu lip, brak patyny we wnękach”).

### Problem
Po ADR 0325 / 0331 baza trzech materiałów brązu (`monument_bronze` liniowe `[0.160, 0.145, 0.125]`, `metal 0.45`) dawała
w cieniu lip niemal jednolitą ciemną szarość/czerń bez ciepłego koloru brązu, bez jaśniejszych wytarć na wypukłościach
i bez zielonkawej patyny we wnękach i zaciekach pod krezą.

### Rozwiązanie (0 dodatkowych draw calli, 0 nowych tekstur, budżet trójkątów bez zmian)
1. **Wypiekanie masek do `COLOR_0` w Pythonie** (`tools/worldgen/streetscape/knyszyn_king_0325.py::_curvature_and_ao`,
   przekazanie `COL` w `buildings_mesh.Acc` oraz dla tablicy cokołu w `knyszyn_park_props_0227.py`):
   - `R` — patyna (wklęsła krzywizna laplasjanowa, lokalna okluzja między częściami, spody, bruzda szwu płaszcza,
     wilgoć u podstawy i pionowe zacieki spod krezy na klatce/płaszczu);
   - `G` — wytarcia wypukłości (grzbiet nosa, czoło, łuki brwiowe, kości policzkowe, czubek brody, krawędzie korony,
     grzbiety fałd płaszcza, ogniwa łańcuchów);
   - `B` — lokalne AO z półsferycznej bliskości całej bryły figury;
   - `A = 1.0` — znacznik aktywacji (pozostałe prymitywy chunka bez `COLOR_0` mają `A = 0` i pozostają nietknięte).
2. **Parametry materiałów** (`tools/worldgen/streetscape/materials.py`, wszystkie `WORKING_VALUE` skalibrowane wizualnie
   do zdjęć Wikimedia Commons `cs20127375` i `cs7518515`, bez użycia pikseli zdjęć):
   - `monument_bronze`: liniowe albedo `[0.26, 0.21, 0.140]`, `metal 0.72`, `set_smooth 0.88`, `bronze_patina`
     (`patina_color [0.065, 0.125, 0.090]`, `rubbed_color [0.44, 0.34, 0.205]`, `patina_smooth 0.18`,
     `rubbed_smooth 0.56`, `rubbed_metal 0.85`, `ao_strength 0.46`);
   - `monument_bronze_patina` (kreza, futrzane wyłogi, rama tablicy): `[0.195, 0.172, 0.122]`, `metal 0.46`,
     mocniejsza matowa patyna (`patina_strength 0.90`, `patina_smooth 0.16`);
   - `monument_bronze_rubbed` (korona, łańcuchy, klejnot): `[0.28, 0.225, 0.150]`, `metal 0.78`, wyraźniejsze wytarcia.
3. **Shader i importer Unity** (`WorldPBR.shader`, `RegionImporter.cs`, `WorldPbrMaterials.cs`):
   - opt-in keyword `#pragma shader_feature_local _BRONZE_PATINA` sterowany blokiem `bronze_patina` z manifestu
     (i flagą `colors = true` w `WorldPbrMaterials.MeshUsage`);
   - spokojna modulacja bazy wokół `_Tint` z mikro-ziarnem `bronze_cast_tint` (bez plam „moro” na płaskich płaszczyznach
     płaszcza), progowe `smoothstep` dla wytarć (ciepły połyskliwy brąz, wysoki metal) i patyny (ciemna matowa
     zielonkawa warstwa węglanów/siarczanów miedzi, `metal → 0.14`) oraz przemnożenie AO przez `COLOR_0.b`.

### Pętla wizualna i wyniki (High, Win64, `clear` + `overcast`)
- 3 rundy kalibracji (`r1` → `r2` → `r3`) + pełna odtwarzalna przebudowa kafla `knyszyn`
  (`build_world.py --region knyszyn --context`, 1 258,6 s, exit 0, `terrain walls > 0.15 m: 0`, `on route {}`),
  reimport `knyszyn` (`Win64`, `High`) oraz finalny VQA `clear` i `overcast` (8 kamer).
- r1: płaszcz zbyt żółto-mosiężny i plamy „moro” z kontrastu mapy `bronze_cast_tint`; r2: uspokojona modulacja bazy
  wokół `_Tint`, progi `smoothstep`, stonowany stary brąz; r3: szlif czytelności ciepłego brązu i patyny pod krezą
  w cieniu (`clear`) oraz uspokojony połysk łańcuchów w `overcast`.
- Dowody: `artifacts/neon-bronze-s24/vqa-final/`, `vqa-final-overcast/`, `sbs-final/`, `sbs-final-overcast/`
  (zestawienia `ref | przed (ADR 0331) | po` dla `king_head_0325`, `king_front_0325`, `king_34_0325`,
  `king_street_driver_0331`, `king_street_tele_0331`).

### Liczby przed / po (zmierzone)

| Pozycja | Przed (ADR 0331) | Po (r3 final) | Uwagi |
|---|---|---|---|
| figura LOD0 / pomnik z cokołem i zegarem | 5 478 / 5 558 tris | 5 478 / 5 558 tris | bez zmian (test: LOD0 ≤ 6 000, LOD1 ≤ 480) |
| brąz w `chunk_1_4.glb` | 3 materiały, bez `COLOR_0` | 3 materiały (`3 552 + 602 + 1 344 = 5 498` tris), wszystkie z `COLOR_0` | figura + tablica na cokole |
| `king_head_0325` (`drawsEst` / `trisExact`, High) | `111` / `431 797` | `111` / `431 797` | +0 draw calli, +0 tris (szacunek edytora przed SRP) |
| `king_front_0325` (`drawsEst`, High) | `484` | `484` | +0 draw calli |
| `king_street_driver_0331` (`drawsEst`, High) | `556` | `556` | +0 draw calli |
| testy Python (`knyszyn/king/0325/0331`) | — | 303 passed, 2 skipped, 1 xfailed | w tym nowy `test_king_bronze_patina_and_wear_vertex_colors` |
| testy budżetowe (`0221`, `0238`, `v31`, `hero_bridge`) | — | 62 passed | `artifacts/neon-bronze-s24/logs/pytest-budget.log` |
| Unity EditMode Win64 | — | 1 429 passed, 0 failed, 111 skipped | `artifacts/neon-bronze-s24/logs/editmode-win64.log` |

### Otwarte po dopisku
- Pomiar FPS w zbudowanym playerze Windows nie był wykonywany w tym zadaniu (do weryfikacji przy buildzie lidera).
- Napis na płaszczu nadal celowo pominięty (ADR 0325).
- Kafel `Data/raw/derived/knyszyn` przebudowany w prywatnej kopii derived worktree — do skopiowania do main przed
  usunięciem worktree.
