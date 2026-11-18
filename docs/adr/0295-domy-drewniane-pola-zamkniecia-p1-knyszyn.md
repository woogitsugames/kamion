# ADR 0295 — P1 z recenzji Knyszyna: dom drewniany Podlasia, przebiegi desek, mozaika pól, cofnięcie zamknięć (knyszyn-p1-s24)

Status: Proposed, 2026-11-18 (agent knyszyn-p1-s24; numer wskazany przez lidera dla zmiany globalnej).
Powiązane: ADR 0287 (zabudowa Knyszyna z danych, deski `wood_siding`), 0289 „Recenzja s24” (kafel desek 6 × 2,6 m),
0082 / 0169 (zamknięcia krawędzi świata), 0273 §10–11 (streaming, „Koniec mapy”), 0109 (maska suchości trawy).
Recenzja: `docs/reports/REVIEW-2026-11-18-s24-knyszyn.md` (FAIL anti-slop, P1-1…P1-4).

## Kontekst

1. **P1-1** Dom drewniany był „teksturą drewna na pudełku”: te same poziome deski na ścianie i w szczycie, żadnych desek
   narożnych, opasek, listwy cokołowej.
2. **P1-2** Deski (`wood_planks*`, kafel UV 6,0 × 2,6 m) powtarzały się co kafel: najdłuższa ściana Domu Klattów
   21,10 m = 3,52 kafla wzdłuż, UV ciągłe dookoła budynku (ta sama faza na każdym domu).
3. **P1-3** Biało-czerwona zapora w poprzek DK65 za rondem to **zamknięcie krawędzi świata** (`WorldEdgeBuilder`, ADR 0082 /
   0169): rząd barier z tablicą U-20 i koliderem na każdej drodze przeciętej przez bbox kafla, 60 m przed krawędzią albo
   w 80 % długości krótszego odcinka drogi. DK65 wychodzi z kafla `knyszyn` krawędzią W (n = −533,3) 61,7 m za rondem
   DK65 / DW671, więc zamknięcie stało 49,4 m przed krawędzią = ~12 m za rondem. Przy streamingu (`stream=1`, ADR 0273)
   z gotowym sąsiadem `knyszyn-w` streamer to zamknięcie otwiera; w scenie pojedynczego kafla (edytor, visual-qa,
   `-Scene knyszyn` bez streamingu) stoi.
4. **P1-4** Maska suchości trawy (COLOR_0.b terenu, ADR 0109) poza pasem 4 m od dróg była wszędzie tym samym szumem łat
   8 m / 2,5 m (`0,25 + 0,75 × dry`), a shader mnoży nią jasność trawy 0,70…1,30 — stąd jednakowe plamy od ronda po horyzont.
   Zdjęcie właściciela nr 11 i ortofoto GUGiK 2025 pokazują gładkie pola pasowe, każde w jednym tonie, z miedzami.

## Decyzja

### 1. Dom drewniany (`streetscape/buildings_mesh.py`, `wood_wall`) — każdy `dom_drewniany`, wszystkie regiony
Na LOD0 (LOD1 bez zmian — pryzma z tym samym materiałem):
- **deski narożne** 0,14 m na każdym licu wypukłego narożnika obrysu, 3 cm przed deskowaniem, od cokołu do okapu;
- **lisice** (pionowe listwy ściągające, 0,12 m) co ~4,6 m na ścianach dłuższych niż 5,6 m, poza otworami i ich opaskami;
- **listwa cokołowa** (okapnik 0,11 m, 4,5 cm przed ścianą) nad cokołem, przerwana pod drzwiami;
- **szczyt**: deska 0,14 m na linii okapu, nad nią **deskowanie pionowe** (to samo UV zamienione osiami — ten sam
  materiał, zero nowych draw calli), okienko strychowe w swojej kolumnie; okno, które przecinałoby linię okapu, odpada;
- **opaski** okien i drzwi 0,10 m z podokiennikiem i **nadokiennikiem** (deska 0,16 m + daszek 3 cm) w nowym materiale
  `wood_trim_white` (stara biała farba olejna, liniowo 0,40 / 0,39 / 0,35 — poniżej `soffit_boards` 0,55, które recenzja
  nazwała „plastikiem”);
- **wiatrownica / deska czołowa** dachu domu drewnianego w materiale ściany (było jasne `soffit_boards`).
Deski, lisice i listwy w materiale ściany biorą **jeden rząd desek** zestawu (tabela `WOOD_JOINT_V` — 19 fug zmierzonych na
`wood_siding/High`, test porównuje ją z teksturą), słoje wzdłuż dłuższego boku. Wszystkie wymiary `WORKING_VALUE`
(recenzja: narożniki 0,12–0,15 m, opaski 0,10 m); zdjęć domów drewnianych Knyszyna w repo nie ma.
Reguła wyboru domu drewnianego bez zmian (nadpisanie `typology: dom_drewniany` / ściana `wood_planks*`, albo reguła
obrysu). OSM `building:material` nie trafia do `buildings.geojson` — otwarte (build_region).

### 2. Powtarzalność desek (P1-2)
- Ściana dzielona lisicami na **przebiegi krótsze niż kafel** (6,0 m); każdy przebieg i szczyt ma własną fazę UV
  (`wood_phase`: dowolne przesunięcie wzdłuż desek, całe rzędy desek w poprzek — rzędy sąsiednich przebiegów zostają na
  jednym poziomie), więc ani dwa przebiegi, ani dwa domy nie pokazują tych samych desek.
- Zestaw `wood_siding`: wyrównanie tonu desek `k` 1,0 → 0,85 (wraca 15 % zróżnicowania desek skanu). CV tonu desek
  (`materials_spec.json`): 0,0157 → 0,0324 (skan 0,124). Pierwsza próba `k` 0,7 (CV 0,0502) na renderze
  `look_dom_klattow` dała znów łaciatą ścianę w słońcu (pojedyncze deski o 1/3 jaśniejsze) — odrzucona.

### 3. Zamknięcia krawędzi (P1-3): autorskie cofnięcie na kafel
`Data/Regions/<id>/world_edge.authored.json` (`closures: [{id, near_en, radius_m, setback_m, reason}]`), czytane przez
`WorldEdgeBuilder.ReadExits` przy imporcie (przeżywa każdą regenerację): zamknięcie drogi, która przecina krawędź w promieniu
`radius_m` od `near_en`, staje `setback_m` (8…60 m) przed krawędzią zamiast domyślnych 60 m (albo 80 % długości krótszego
odcinka drogi). Knyszyn: DK65 na krawędzi W — odcinek do ronda ma 61,7 m, więc zamknięcie stało 49,4 m przed krawędzią,
~12 m za rondem; teraz 12 m przed krawędzią. DW671 (Tykocka) wpisu nie potrzebuje: jej odcinek ma 12,6 m, zamknięcie
stoi 10 m przed krawędzią z reguły 80 %. Zamknięcie zostaje (bariery + kolider + tablica), prostokąt `WorldBoundary` i ostrzeżenie „Koniec mapy” bez zmian;
kafel bez pliku — bez zmian. Odrzucone: usunięcie zamknięcia na szwie z istniejącym sąsiadem (scena pojedynczego kafla
kończyłaby się wtedy bez fizycznej granicy), reguła automatyczna dla wszystkich kafli (przesuwa zamknięcia w ~60 kaflach
bez przeglądu).

### 4. Pola (P1-4): mozaika zamiast szumu (`streetscape/vegetation.py`, `field_mosaic`) — wszystkie regiony
W BDOT10k `OT_PTTR_A` (roślinność trawiasta / uprawa na gruntach ornych), dalej niż 4 m od dróg, poza trawnikami i lasem:
jedno pole = jeden poziom suchości (paleta wg RODZAJ), dryf ±3 % w skali 40 m, miedza 2 m o suchości 0,78 między polami.
**Układ pól jest ESTIMATED**: w repo nie ma działek ewidencyjnych (EGiB), więc bloki równoległych pasów (bloki ~300 m,
pasy 22–46 m — odczytane z ortofoto Knyszyna, `WORKING_VALUE`) są funkcją wyłącznie położenia w EPSG:2180: ten sam wzór
po obu stronach szwu kafli. Blok ma jeden użytek (pasy różnią się o ±0,05), 20 % pasów ma własny. Kanały R / G / A maski
i pas przydrożny bez zmian. Ortofoto służy tylko do pomiaru szerokości pasów — żaden piksel nie trafia do gry.

**Ogrody** (`OT_PTZB_A` o RODZAJ jednorodzinna / wielorodzinna / zagrodowa, dalej niż 4 m od dróg, poza trawnikami):
suchość 0,12 + 0,30 × (łaty 18 m z domieszką 2,5 m) zamiast 0,25 + 0,75 × (łaty 8 m) — między domami jest utrzymana ruń,
nie nieużytek. Inne klasy zabudowy (przemysłowo-składowa, handlowo-usługowa, pozostała) i grunt bez klasy — bez zmian.

**Shader** (`Environment/Shaders/WorldPBR.shader`, wszystkie kafle od razu, bez przebudowy): „spokojna ruń” —
`swardCalm = _GroundTint × smoothstep(0,5; 0,9; R) × (1 − smoothstep(0,30; 0,60; B)) × (1 − G) × (1 − A)`; gdzie teren jest
dalej niż ~10–18 m od drogi / placu i ma niską suchość (trawniki, ogrody, pola mozaiki), znikają plamy słomy (×0,1) i
gleby (×0), kępy słabną o połowę, chmury tonu 8–64 m o połowę. Sucha, niekoszona ziemia (B wysokie) i pas przy drodze
zachowują wszystkie plamy. Zero nowych próbek tekstur i słów kluczowych. Na nieprzebudowanych kaflach maska B poza
drogami ma 0,25–1,0, więc efekt jest tam częściowy (ok. 1/3 powierzchni otwartego terenu) — **kafel C i pozostałe
zatwierdzone kadry wymagają ponownego renderu kamer kontrolnych przez lidera** (w tej gałęzi renderowany tylko Knyszyn).

## Skutki dla innych kafli
Zmiany 1, 2 i 4 działają w generatorze dla wszystkich regionów, ale pokażą się dopiero po `build_world` danego kafla:
- domy drewniane: każdy kafel z zabudową jednorodzinną (reguła obrysu 12 % domów parterowych < 120 m²);
- pola: każdy kafel z `OT_PTTR_A` (wszystkie pozamiejskie: dk65-*, dw671-*, s8-*, knyszyn-s, monki*, tykocin);
  do czasu przebudowy sąsiada szew pokazuje mozaikę po jednej i szum po drugiej stronie;
- nowy materiał `wood_trim_white` dochodzi do tabeli materiałów manifestu każdego przebudowanego kafla.
- **kafel C (`bialystok-industrial-c`) trzeba przebudować przed scaleniem albo zaraz po nim**: `tests/gis/test_world_roads.py::
  test_export_is_deterministic` buduje C w procesie i porównuje z zapisanym manifestem — po zmianie generatora różni się
  już chunk 0_0 (maska pól w COLOR_0 terenu, 3 domy drewniane). To jedyny test GIS, który ta zmiana czerwieni
  (pełny przebieg: 2486 passed, 2 failed; drugi — `test_ec_chimneys…one_authored_instance_per_chimney` — pada także na
  main: `read_text()` bez kodowania na `streetscape_qa.json` kafla C).
Przebudowane w tej gałęzi: `knyszyn`, `knyszyn-w`. Do przebudowy przez właścicieli kafli: `knyszyn-s` (szew S Knyszyna)
i pozostałe przy najbliższej okazji.

## Pomiary (przed → po)
Wszystko zmierzone w tej gałęzi; rendery = edytor, High clear, 1920 × 1080 (nie build Windows).

| | przed | po | źródło |
|---|---|---|---|
| Dom Klattów: najdłuższy przebieg desek / kafel 6 m | 21,10 m = 3,52 kafla | 4,65 m = 0,78 kafla | `BM.build`, `streetscape_qa.json` |
| Knyszyn: przebiegi desek > kafel | wszystkie ściany > 6 m | 0 z 256 (max 5,50 m) | `buildings.wooden_houses` |
| CV tonu desek `wood_siding` | 0,0157 | 0,0324 | `materials_spec.json` |
| Budynki LOD0, cały kafel `knyszyn` (25 domów drewnianych) | 656 343 tris | 669 021 (+12 678, +1,9 %) | `world_manifest.json` |
| Budynki LOD0, `knyszyn-w` (5 domów drewnianych) | 127 160 | 129 718 (+2 558) | `world_manifest.json` |
| Chunki z nowym materiałem `wood_trim_white` (LOD0) | 0 | 13 z 64 (`knyszyn`) | `world_manifest.json` |
| Draw calle, maks. z 83 kamer / średnio | 731 | 732 / +1,65 (najgorzej +6 `rynek-owner-04`) | `stats.txt` (szacunek edytora przed SRP batchingiem) |
| Trójkąty, maks. z 83 kamer | 2 333 091 | 2 339 271 (najgorzej +7 756) | jw.; kadry kabinowe (`cab-mirror-front`, `cab-mirrors-right`) były > 2 mln już przed zmianą |
| `look-dom-klattow`: draws / tris | 603 / 1 442 088 | 607 / 1 447 136 | jw. |
| DK65 W: zamknięcie przed krawędzią kafla (wzdłuż drogi) | 49,4 m (~12 m za rondem) | 12,0 m (~50 m za rondem) | `roads.graph.json` + reguła `ReadExits` |
| Maska suchości na polach (72 % kafla): średnia / odch. | 0,624 / 0,262 (szum 8 m) | 0,327 / 0,228 (różnice między polami) | `vegetation.farmland` |
| Maska suchości w ogrodach (22 ha): średnia / odch. | 0,628 / 0,264 | 0,269 / 0,050 | jw. |
| Plamistość pola na `rondo-owner-11` (odch. luminancji w paśmie 4–24 px, pole NE) | 0,0219 | 0,0165 (−25 %; w tym zamierzone pasy pól) | `artifacts/knyszyn-p1-s24/field_noise.py` |
| Średni kolor pola NE (sRGB) | 131 / 133 / 101 | 118 / 123 / 96 | jw. |

Baseline ADR 0238 kafla C (`tests/gis/data/typology_0238_baseline_bialystok-industrial-c.json`) przeliczony: 3 domy drewniane
kafla C dają +102…+106 trójkątów High na 4 kamerach; suma budynków 961 562 → 958 445 (inne zmiany od ostatniego
przeliczenia). Low (LOD1) bez zmian w tej decyzji.

Testy: `tests/gis/test_wood_house_p1_s24.py` (9), EditMode `WorldEdgeSetbackOverrideTests` (2). Pełny `pytest tests/gis`:
2486 passed, 2 failed (patrz „Skutki dla innych kafli”), 1 skipped, 2 xfailed. EditMode Win64: 1257 passed, 2 failed
(`ArtPrefabs_HavePinnedGuids`, `ImportedGlassSemanticIsRestrictedAndStillReceivesShadows` — środowisko świeżego worktree, te
same w przebiegach regen-c-s24 / knyszyn-r24), 90 skipped.
Dowody: `artifacts/knyszyn-p1-s24/{before,after2,sbs}/*.jpg`, `budget-before-after2.json`, `field-noise-before-after2.json`.

Obejrzane rendery (ocena własna agenta, nie `visual-critic`): `look-dom-klattow` — szczyt pionowo, deska na linii okapu,
narożniki, lisica, opaski z nadokiennikiem, wiatrownica w kolorze ściany; `look-wooden-house-brown` — to samo na domu
z reguły (ganek); `rondo-owner-11` — pasy pól z miedzami zamiast plam, ale ton pól wciąż oliwkowy (zdjęcie nr 11: soczysta
zieleń) i teren w pasie ~20 m od dróg bez zmian; `dk65-outlet-nw` — zapora ok. 50 m dalej niż przedtem (61,7 − 12 = 49,7 m za rondem), **nadal
widoczna** w scenie pojedynczego kafla; `rondo-dk65-above` — zamknięcie DW671 W zostaje 10 m przed krawędzią (kafel kończy
się 12,6 m za rondem). Zapory na obu ramionach znikają dopiero przy streamingu z `knyszyn-w`.

## Otwarte
- Zdjęcia Domu Klattów (Kościelna) od właściciela: kolor desek i opasek, okiennice, ganek — wymiary desek do weryfikacji.
- P2 z recenzji nietknięte: płot sztachetowy (atlas `plot_kit`), wyspa ronda, drzewa-kępki, wariant overcast kamer.
- Fartuch poza kaflem (`WorldEdgeBuilder.ApronMask`) ma strefy lasu / gruntu wpisane dla Białegostoku i szum sinusowy —
  pola za krawędzią kafla nie dostają mozaiki.
- Działki ewidencyjne (EGiB / GUGiK KIEG) jako prawdziwy układ pól — osobne zadanie geo-worldgen.
- Render z buildu Windows (recenzja §5.2) — do lidera.
