# ADR 0107: Zabudowa r6 + działki domów — spody balkonów, ślady spod parapetów, MultiRoof bez daszków i szczelin, ogrodzone działki z instancji

Status: propozycja (world-builder, gałąź `buildings-r6`, z main `ff400569`), 2026-11-11. Kontynuacja ADR 0097; odpowiedź
na `docs/reports/visual/REVIEW-2026-11-11-s10-0097.md` (P1-e..h, P2-h..n). Zrzut z A16 (pkt 8 recenzji) robi lider.

## Kontekst
Recenzja 0097 (PASS warunkowy): spody i boki płyt balkonowych prawie czarne (P1-e), zaciek = jedna centralna kropla
(P1-f), MultiRoof ze schodkiem w połaci i szczeliną przy szczycie (P1-g), domy na gołej łące (P1-h) oraz drobne P2.

Rozpoznanie:
- `balcony_slab` = beton 0,30 z ambientem spodu przyciętym o połowę (`sky_occ` 0,5 z ADR 0060) → 38–40 sRGB.
- Tryb „pod parapetem” shadera (ADR 0092) próbkuje teksturę zacieków po metrach ściany: pod oknem 1,5 m wypada
  zwykle jedna smuga w przypadkowym miejscu. Wzoru „od końców parapetu” nie da się uzyskać bez danych lokalnych okna.
- Schodek w połaci (r13_house2_az110): pole małej przybudówki sięgało 1,2 m (`MULTI_REACH`) w prostokąt bryły głównej
  i tam wygrywało z połacią (obwiednia max). Szczelina (az200): uskok pola na styku dwóch części nie miał żadnej ściany.
  Przybudówki przy szczycie dostawały własny dach dwuspadowy z kalenicą równoległą do ściany szczytowej (połać
  spływająca na ścianę — w rzeczywistości nie występuje).
- Dane działek: brak EGiB w pipeline, BDOT10k w kaflu nie ma ogrodzeń posesji, OSM `barrier=*` (99 odcinków) to głównie
  place przemysłowe. Działki trzeba więc wyznaczyć regułą; prawdziwe ogrodzenia z OSM/BDOT są respektowane.
- `game/Assets/_Generated` skopiowane do worktree było importem sprzed r5 — baza została zaimportowana na nowo ze
  snapshotu danych main (`artifacts/buildings-r14/_snap/base`).

## Decyzja
1. **Spody balkonów (P1-e)** — `balcony_slab`: albedo 0,30 → 0,52 (płyta otynkowana i malowana z elewacją, zdjęcia CC0
   Putry), `sky_occ` [0, 0] jak `soffit_boards` (ADR 0094). Krawędź płyty w wierszach `facade_far` 0,30 → 0,50.
   Blok addytywny na końcu `materials.py`.
2. **Ślady spod parapetów (P1-f)** — nowy, addytywny tryb `_RUNOFF` w `WorldPBR.shader`: TEXCOORD_1.v ≥ 112 = dane
   lokalne parapetu: u = metry (ze znakiem) od bliższego końca parapetu, v = 128 + 8·rnd + 1 + głębokość / skala
   (rnd 0–7 na okno). Shader rysuje dwa wąsy od końców (różnej długości, z rnd) i słaby szeroki pas pod całą
   krawędzią kapinosu; start na parapecie (głębokość 0). Bez dodatkowej próbki tekstury (ta sama próbka `_RunoffMap`
   daje strukturę pasa). Generator (`buildings_mesh.sill_marks`): kolumna pod oknem dzielona w osi parapetu (+2
   trójkąty na okno ze śladem), 40 % okien bez śladu, skala długości rośnie ku dołowi budynku (×1,3 parter … ×0,7 góra).
   Tryby ADR 0071/0092 bez zmian.
3. **MultiRoof (P1-g)** — `roofs.py`:
   - domena części = jej prostokąt + zasięg 1,2 m, ale **nie wewnątrz prostokąta innej części** (koniec schodków);
   - część dostaje własny dach dwuspadowy tylko jako prawdziwe skrzydło: oba boki ≥ 2,0 m i — przy szczycie — głębiej
     niż 4,5 m; mniejsze części to **jedna połać**: po stronie okapu przedłużenie połaci głównej (łagodniej, gdy spadek
     przekroczyłby 0,5 m), przy szczycie dach pulpitowy od ściany szczytowej (4–20°, okap ≤ 0,35 m pod okapem głównym);
   - `step_walls`: uskoki pola między częściami zamyka ściana w materiale elewacji (LOD0) / dachu (LOD1);
   - obróbka kosza 1,2 → 3 cm nad pokryciem; uskoki nie są już brane za kosze.
4. **Działki domów (P1-h)** — nowy moduł `streetscape/plots.py` (nie zmienia `furniture.py`):
   - plan: domy bliżej niż 2,5 m = jedna działka (dom + garaż, bliźniak, szeregowiec); prostokąt w układzie domu,
     front = kierunek z najbliższą drogą, linia ogrodzenia 1 m od śladu drogi (2–9 m przed domem), boki 3–6 m,
     tył 7–15 m; kurczony co 1 m, aż ominie drogi, duże budynki, place, wcześniejsze działki i **istniejące ogrodzenia
     OSM/BDOT** (te stają się granicą; przęsło równoległe do istniejącego płotu w odległości < 2,5 m (±25°) nie powstaje);
   - typologia (WORKING_VALUE, do sprawdzenia ze zdjęciami właściciela): front — panel na podmurówce (antracyt /
     zielony), sztachety drewniane, siatka (zielona / ocynk), płyty betonowe; boki i tył — głównie siatka; jeden typ
     frontu i jeden boków na działkę;
   - brama 3,5 m + furtka 1,0 m obok siebie od strony drogi, podjazd 3 m (kostka 60 % / żwir 40 %) od śladu drogi obok
     domu; szeregowce: furtka przed każdym domem, bez bramy;
   - zieleń: rząd tuj wzdłuż jednego płotu (35 % działek), 2–4 krzewy (`tree_shrub`), 1–2 małe drzewa liściaste za
     domem (`tree_maple` w skali 3,2–4,8 m — brak prototypu drzewa owocowego), trawnik = kanał „niekoszone” maski
     terenu obniżony w obrysie działki;
   - **wszystko jako instancje** 26 prototypów w `street_props.glb` (przęsła 2,5 / 1,25 m, bramy, furtki, płyty
     podjazdu, tuja) z istniejących materiałów — zero siatek w chunkach, zero nowych materiałów chunków;
   - seed = sha1(id budynku): odtwarzalne, bez stanu.
5. **P2** — pranie na suszarce pod poręczą, bez czerwieni (P2-h); wyjątki balustrad bez maty trzcinowej (P2-i);
   próg w szarej blasze zamiast bieli parapetu (P2-j, częściowo); fugi wysokiego cokołu: pas 0,5 m + fugi pionowe co
   2,4 m paskami 1,5 cm w materiale kapinosu (P2-k); kamery `r13_*` na wysokości NMT z omijaniem drzew (P2-m);
   dryf tonu dachówki 7 m / 0,16 (P2-n).
6. Pliki wspólne: `materials.py` — blok dopisany na końcu; `WorldPBR.shader` — wstawka w bloku `_RUNOFF`;
   `props.py` (+2 linie w `build_all`), `stage.py` (import + 3 wstawki). `WorldPbrMaterials.cs`, `WorldSurface.shader`,
   `furniture.py` — bez zmian. Kontrakt `_Tint` (ADR 0086/0101) nietknięty.

WORKING_VALUE: albedo płyty 0,52; kształt i siła wąsów / pasa; 40 % czystych parapetów; progi 2,0 m / 4,5 m części
dachu, spadki pulpitów; wszystkie wymiary i udziały działek (marginesy, typy ogrodzeń, 35 % tuj, 60/40 kostka/żwir);
fugi co 2,4 m; dryf dachówki.

## Liczby (edytor; nic z telefonu)
Rundy: base (świeży import danych main `ff400569`) → r1 → r2 → r3 (= stan końcowy). Dowody `artifacts/buildings-r14/<runda>/`.

| miara | base | r3 |
|---|---|---|
| region High: submeshe / mln tris (`chunk_mats.py`) | 4028 / 14,03 | 4028 / 14,05 (+0,2 %) |
| region Low: submeshe / mln tris | 3009 / 4,497 | 3009 / 4,499 (+0,04 %) |
| budżet Low, 57 kamer: draws (szac. przed SRP, `budget.py`) | 16695 | 16695 (+0,0 %) |
| budżet Low, 57 kamer: suma tris | 15256 k | 15297 k (+0,3 %; maks. kamera r10_block_2 +1,6 %) |
| kamery > 400 draws | 10 | 10 |
| spód balkonu / ściana, `r10_block_4`, ten sam prostokąt (`underside.py`) High overcast | 42 / 112 sRGB = 0,38 | 71 / 112 = 0,63 |
| to samo, Low overcast | 0,36 | 0,61 |
| domy MultiRoof: części dodatkowe dwuspadowe / pulpitowe | 98 domów: wszystkie dwuspadowe | 98 domów: 21 / 125 (89 domów z pulpitem); 0 dziur pokrycia (`roof_scan.py`) |
| działki | 0 | 97 z 104 grup domów (270 domów), mediana 532 m² |
| instancje działek | 0 | 4737: 3887 przęseł (siatka 5482 m, panel 2285 m, beton 1041 m, sztachety 555 m), 59 bram, 139 furtek, 275 płyt podjazdu, 165 tuj, 187 krzewów, 25 drzewek |

- Instancje działek **nie wchodzą do `drawsEst`** (liczy tylko MeshRenderery; instancje rysuje `WorldInstances`). Górne
  oszacowanie kosztu przy domach (`plot_instances.py`, wszystkie prototypy w promieniu 120 m, bez frustum): r1 21
  prototypów / 38 submeshy → r3 14 prototypów / 17 submeshy na jeden LOD; ~3,4–5,9 tys. trójkątów. Zasięg wg domyślnej
  reguły importera: LOD0 30 m, cull 120 m × lodBias. Realny koszt rozstrzygnie telefon.
- Testy: `pytest tests/gis` 421 passed, 1 xfailed, 1 failed — `test_road_fidelity::test_report_not_stale` (raport
  fidelity nieaktualny względem plików dróg z main; nie dotykane w tym zadaniu). Nowe `test_buildings_r6.py` 13 testów.
  EditMode 241: 234 passed, 7 failed — `WorldPbrTintTests.LinearTint_ActualWorldShaderGpuReceivesLinear` × 7: kopia
  shadera testu w `_Generated/TintGammaProbe` nie znajduje `../../Rendering/Shaders/VegetationGround.hlsl` (include
  względny z ADR 0088 — nie z tej gałęzi; nie sprawdzałem na main).

## Samokrytyka (docs/06)
- **Bez `visual-critic` i bez telefonu** (zakaz subagentów; A16 robi lider). Oceny wyłącznie moje.
- **Działki są regułą, nie danymi**: obrysy, typy ogrodzeń, położenie bramy i podjazdu nie pochodzą z EGiB ani ze zdjęć.
  Z lotu ptaka widać to po prostokątach ustawionych wg domu, nie wg ulicy; 7 grup domów nie dostało działki (ciasno).
- **Ogrodzenia bez kolizji** — ciężarówka przejedzie przez płot posesji.
- **Podjazd to płyty-instancje**: na spadku schodkuje (krawędź 4 cm + fartuch), kończy się na śladzie drogi (nie
  przecina chodnika ani pobocza jako zjazd), nie ma dojścia od furtki do drzwi.
- **Brak siatki plecionej**: „siatka” używa tekstury panelu zgrzewanego (jedyna tekstura ogrodzeń); zieleń
  `fence_green` jest jaskrawsza niż RAL 6005 (materiał wspólny, nie zmieniany). Płot betonowy z daleka czyta się
  prawie biało.
- **Znikanie**: ogrodzenia giną na 120 m × lodBias (Low: 60 m) — reguła domyślna importera.
- **Ślady spod parapetów są subtelne** (siła materiału × 0,6 dla tynków bez zmian): z 15 m dwa miękkie wąsy i słaby
  pas; wąs leży po wewnętrznej stronie krawędzi okna (geometria kolumny pod oknem), nie na osi końca parapetu.
- **MultiRoof**: przybudówki przy szczycie mają pulpit 4–20° w materiale dachu głównego (dachówka na 5° jest
  nierealna — powinna być blacha/papa); okap główny nad przybudówką jest przycięty (pole jednowarstwowe).
- **P2-j częściowo**: zmieniony tylko kolor progu; wysokości stopnia nie ruszałem. **P2-l otwarte**: żółta linia w
  trawie (`r13_block3_close`) nadal jest; źródła nie znalazłem (nie pochodzi z zabudowy).
- **P2-n**: dryf tonu dachówki dodany, nie zmierzony liczbą.

## Otwarte / do decyzji lidera
- visual-critic + zrzut z A16 (`r10_block_2`, `r10_block_5`, `r10_house_2`); realny koszt instancji działek na Low.
- EGiB (działki ewidencyjne, otwarte dane GUGiK) jako źródło obrysów zamiast reguły — wymaga pobrania.
- Kolizja ogrodzeń, zjazd przez chodnik, dojście do drzwi, tekstura siatki plecionej, materiał blachy dla pulpitów.
- Reguła LOD/cull dla `plot_*` w `InstanceImporter.Policy` (+ lustro `build_world.instance_ends`).
- P2-l (żółta linia), P2-j (stopień), EditMode `WorldPbrTintTests` (include względny).
- Po scaleniu: `build_all.py --only facade_far` → `build_world` → `import-region`.

## Przewidywane konflikty
- `gpt-furniture-r1` (`streetscape/furniture.py`, meble i ogrodzenia uliczne): `plots.py` nie importuje ani nie zmienia
  `furniture.py`. Możliwe konflikty tekstowe: `streetscape/stage.py` (moje wstawki: import `plots`, blok „house plots”
  przed „# vegetation”, `lawn_mask` po `ground_masks`) i `streetscape/props.py` (`build_all`: 2 linie na końcu).
  Konflikt merytoryczny: jeśli GPT zbuduje ogrodzenia uliczne wzdłuż posesji, `plots.build` powinien dostać ich linie
  jako `barriers` (dziś czyta tylko OSM/BDOT) — wtedy przęsła równoległe znikną same (reguła 2,5 m).
- `tools/worldgen/streetscape/materials.py`: blok na końcu pliku (po bloku 0097) — konflikt, gdy inna gałąź też dopisze
  na końcu albo zmieni `balcony_slab` / `roof_tiles_*`.
- `WorldPBR.shader`: wstawka między `float2 ur = …` a `half k = _RunoffStrength…` w bloku `_RUNOFF`.
- `InstanceImporter.Policy` (nie zmieniany): prototypy `plot_*` biorą domyślne 30 / 120 m × lodBias — do decyzji, czy
  ogrodzenia mają własną regułę.
- `tests/gis/test_buildings_r5.py` (ślady parapetów, próg), nowy `tests/gis/test_buildings_r6.py`.
