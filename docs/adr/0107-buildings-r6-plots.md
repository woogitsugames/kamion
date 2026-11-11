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
LICZBY_TBD

## Samokrytyka (docs/06)
SAMOKRYTYKA_TBD

## Otwarte / do decyzji lidera
OTWARTE_TBD

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
