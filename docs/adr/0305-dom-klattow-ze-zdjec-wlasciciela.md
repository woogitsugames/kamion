# ADR 0305 — Dom Klattów ze zdjęć właściciela: dom z bali bielony, stara dachówka, ganek, płot (klattow-s24)

Status: Proposed, 2026-11-19 (agent klattow-s24; numer wskazany przez lidera).
Powiązane: ADR 0287 (nadpisania punktów orientacyjnych Knyszyna, deski `wood_siding`), 0295 (dom drewniany z reguły),
0298 (kolory desek), 0227 (autorskie budynki Knyszyna: kościół, urząd), D51 (rozpoznawalność).
Referencje: zdjęcia kolegi właściciela `Data/raw/refs/owner-knyszyn-klattow-2026-11-19/klattow-01…05` (zgoda właściciela
19.11.2026: tylko oglądanie i pomiar; **żaden piksel nie trafia do gry ani do gita**).

## Kontekst

Dom Klattów (ul. Kościelna, BDOT `2002917F-2F22…`, OSM way 294345657 `material=wood`) był od ADR 0287 domem drewnianym
z reguły: surowe brązowe deski poziome, dach z czerwonej dachówki z losowania, 3–4 okna z zestawu fasad, ganek jako
występ bryły. Wpis nadpisania sam mówił „ESTIMATED: plank colour (dark brown)” i prosił o zdjęcie. Zdjęcia właściciela
pokazują co innego: dom z bali **bielony wapnem**, szczyty z pionowych białych desek, stara dachówka esówka, ganek
z kratką, ciemnobrązowe okna ze szprosami, płot sztachetowy przy chodniku. Reguła `dom_drewniany` tego nie odda —
potrzebny autorski obiekt, tak jak kościół i urząd (ADR 0227).

## Decyzja

### 1. Autorski generator budynku (`tools/worldgen/streetscape/knyszyn_dom_klattow_0305.py`)
Ten sam mechanizm co `knyszyn_townhall_0227`: `hero_targets()` wyłącza fasadę z reguły (zostaje pryzma kolizyjna obrysu
i maski terenu), `build()` dokłada siatkę do warstw `buildings` (LOD0, treść High / PC) i `buildings_low` (LOD1).
Obiekt powstaje wyłącznie z danych i stałych w kodzie — przeżywa każdy reimport; gdy obrys w danych przestanie być
„długim domem z jednym gankiem”, generator się wyłącza i wraca dom z reguły (nadpisanie `look-dom-klattow-wooden`,
teraz białe deski `wood_planks_white` zamiast brązowych).

Korekta P2 (`klattow-fix-cli`): autorski układ wymaga korpusu 20,0–22,2 × 7,0–8,7 m i ganku
2,4–2,8 × 1,7–2,3 m. Każdy otwór wraz z obramowaniem i parapetem musi mieć ≥ 0,30 m zapasu
do narożnika; okna uliczne ≥ 0,10 m do dachu ganku. Sprawdzane są również drzwi, osadzenie ganku
z okapem oraz okno strychowe z daszkiem pod skosem szczytu. Niespełnienie warunków wyłącza
`hero_targets()` i pozostawia dom z reguły; `build()` również odrzuca taki obrys przed emisją siatki.
Korekta P3: `FENCE_PAST` ma osobne wartości W/E **2,6 / 4,5 m**, zgodnie z tabelą poniżej.
Testy obejmują graniczne wymiary, niezgodne obrysy i zapas reguły oraz długości obu odcinków płotu.
W tej korekcie nie przebudowywano świata ani nie wykonywano oceny wizualnej kolizji z płotem działki;
wcześniejsze pomiary i rendery poniżej dotyczą stanu sprzed korekty.

| Element | Źródło | Wartość |
|---|---|---|
| Bryła, ganek | BDOT10k (SOURCED) | korpus 21,10 × 7,84 m; ganek 2,7 × 2,0 m, środek 10,35 m od zachodniego narożnika ściany od ulicy |
| Okap, kalenica | GUGiK LoD2 2017 (SOURCED) | okap 2,22 m → górny bal 2,25 m; kalenica 6,06 m → 6,05 m; spadek 39,7° |
| Okna od ulicy (6) | zdjęcie 01, skala 0,0213 m/px z długości ściany, względem ganku (ESTIMATED ±0,3 m) | −8,65 / −4,98 / −3,19 / +2,34 / +4,45 / +8,12 m; 0,95 × 0,97 m, nadproże pod okapem |
| Ściana od podwórza: 3 okna, drzwi, 3 okna | zdjęcie 05 (dopasowanie rzutowe), zdjęcie 03 potwierdza kolejność (ESTIMATED ±0,4 m) | od wschodniego narożnika 3,26 / 6,87 / 9,18, drzwi 12,06, 14,69 / 16,30 / 18,85 m |
| Szczyt wschodni | zdjęcia 03–05 | 2 okna parteru ±1,98 m od osi, okno strychu z daszkiem, daszek okapowy 0,55 m z blachy, pionowe białe deski, białe wiatrownice |
| Szczyt zachodni | brak zdjęcia | lustrzane odbicie wschodniego (ESTIMATED) |
| Kominy (2) | zdjęcie 01 + ortofoto 2025 (ESTIMATED ±0,5 m) | −2,35 / +0,55 m od osi ganku, na kalenicy |
| Ganek | zdjęcia 01, 04 | słupki 10 cm, dół z desek, kratka ukośna (158 listew jako geometria), dach dwuspadowy z dachówki, białe wiatrownice, drzwi czerwonobrązowe |
| Płot | zdjęcie 01 | sztachety 9 cm co 14 cm, 1,05 m, dwie łaty, słupki co ≤ 2,4 m, na linii czoła ganku; 2,6 m za narożnik zachodni, 4,5 m za wschodni |
| Podmurówka | zdjęcie 05 | kamień polny 0,30 m |

Wymiary elementów (deski, listwy, przekroje) to `WORKING_VALUE` odczytane ze zdjęć. Bez tabliczek, numerów, napisów.
**Płot a chodnik z generatora.** Na zdjęciach sztachety stoją w linii czoła ganku, przy tylnej krawędzi chodnika.
W świecie gry tylna krawędź chodnika Kościelnej leży ~1 m od ściany (ganek ma 2 m), więc reguła „płot poza obrysem
drogi” dała w rundzie 1 płot 0,83 m od ściany i ganek wystający przez płot na chodnik. Decyzja: gdy linia czoła ganku
wypada na modelowanym chodniku, płot i tak tam staje, o ile do jezdni zostaje ≥ 1,4 m chodnika (`WALKWAY_MIN_M`,
`WORKING_VALUE`; zmierzone w raporcie `streetscape_qa.json`: `fence.walkway_left_m`); podstawy sztachet biorą wysokość
z wierzchu siatki chodnika (`furniture.SurfaceTop`), a między podmurówką a płotem leży pas trawy 5 cm nad chodnikiem
z betonowym obrzeżem. Gdy chodnika zostałoby mniej — linia cofa się poza obrys drogi (0,15 m zapasu) co 0,1 m,
a poniżej 0,8 m od ściany płotu nie ma. **Wynik w Knyszynie (runda 2): chodnika zostałoby < 1,4 m, więc płot
stoi 0,83 m od ściany, a ganek nadal wystaje przez płot na chodnik** — odstępstwo od zdjęcia. Właściwa poprawka (szerokość i odsunięcie chodnika Kościelnej z danych) należy
do warstwy dróg — otwarte.

**Płot działki** (`plot_fence`, nowe pole nadpisania budynku czytane przez `streetscape.plots.plan`): styl płotu
frontowego / bocznego działki z nadpisania zamiast losowania z wieku zabudowy. Dom Klattów: sztachety (`picket`)
zamiast ceglanych słupków ze sztachetami. Działki bez pola — bez zmian.

**Cień domu jako „korony”** (`kind: plot_canopy_exclude`, `polygons_en`): `plot_canopy.json` (korony z ortofoto,
ADR 0132 / 0298) miał osiem „koron” o promieniu 1,0–1,25 m co 2,5 m, metr na północ od ściany podwórza — to cień
budynku na trawniku. W rundzie 1 wyrosły z nich krzewy zasłaniające bieloną ścianę. Wpis nadpisania wycina pas
0,2–2,7 m od tej ściany; prawdziwe drzewa w głębi podwórza zostają. **Uwaga ogólna dla lidera:** ten sam fałszywy
odczyt (ciemna zieleń w cieniu po północnej stronie budynku) może dotyczyć innych domów we wszystkich kaflach
z `plot_canopy.json` — do sprawdzenia przy źródle (`streetscape/plot_canopy.py`), poza zakresem tej decyzji.

### 2. Materiały (bez pobrań — pięć zestawów proceduralnych, licencja: własne, kod w repo)
- **`log_whitewash`** (zestaw modulacyjny, `sets_facade.log_whitewash`, kafel 4,0 × 2,2 m = cała wysokość ściany):
  dziesięć wieńców bali 0,20–0,24 m, falujące fugi z pakułami, pęknięcia wzdłuż włókien, chmury pędzla, zabrudzony
  i łuszczący się dół. Materiał `log_wall_white` (liniowo 0,60 / 0,595 / 0,565; po rundzie 1 z 0,66 — ściana w słońcu
  przepalała się do bieli i gubiła fugi).
- **`boards_painted`** (kafel 6,0 × 2,6 m, 19 rzędów **na fugach `wood_siding`** — `buildings_mesh.WOOD_JOINT_V`, więc
  każda reguła UV desek `wood_planks*` działa bez zmian): deski pod kryjącą farbą, cienkie fugi, włosowate spękania.
  Materiał `wood_planks_white` (szczyty, wiatrownice, deski czołowe, narożniki). Runda 1: skan `wood_siding` pod białą
  barwą czytał się jak szare, zwietrzałe deski.
- **`roof_tiles_old`** (kafel 2,8 × 2,8 m, fala 0,20 m, rząd 0,35 m jak `roof_tiles`): każda dachówka ma własny ton
  (pomarańcz → ciemny brąz, kilka jasnych wymienionych), nierówne linie rzędów, mech w korytach i na zakładach, porosty —
  barwa mchu jest w mapie modulacji. Materiał `roof_tiles_old` (liniowo 0,145 / 0,047 / 0,021). Runda 1: `roof_tiles`
  z silnym dryfem makro dawał równą, bladopomarańczową kratę (w słońcu sRGB ~185 / 125 / 85; zdjęcie ~175 / 92 / 58).
- **`fieldstone`** (kafel 2,4 × 0,6 m): otoczaki 0,15–0,30 m w zaprawie, wilgotny dół. Materiał `fieldstone_plinth`.
- **`wood_shingles`** (kafel 1,5 × 1,5 m): gont, rzędy 0,15 m, szerokości 7–12 cm, srebrnoszary. Materiał
  `roof_shingles_grey` (lamus, pkt 4); `log_wall_raw` = `log_whitewash` pod barwą surowego drewna, kafel 4,6 × 2,55 m.
- **`wood_planks_stain`** — istniejący skan CC0 `wood_siding` (Poly Haven `raw_plank_wall`, wpis w `docs/LICENSES.md`
  od ADR 0287) pod czerwonobrązową bejcą (ganek, płot; liniowo 0,125 / 0,055 / 0,026).
- **`wood_trim_brown`** — płaski ciemny brąz stolarki (elementy 2–9 cm); pas trawy za płotem: istniejący `plot_lawn`.
- `log_wall_`, `fieldstone_`, `roof_shingles_` dopisane do `_TINT_LINEAR` (kolor liniowy, jak tynki i dachy).
Poly Haven / ambientCG nie mają skanu bielonej ściany z bali ani starej esówki o znanych wymiarach; zestawy proceduralne
dają kontrolę nad wysokością wieńców, rozstawem dachówek i zabrudzeniem. Wszystkie kolory `WORKING_VALUE` do oceny
właściciela.

### 3. Reguła ogólna „dom z bali bielony” — NIE wprowadzona (brak danych)
Sprawdzone na danych Knyszyna: w OSM (`podlaskie-261108.osm.pbf`) znacznik `material` / `building:material` ma **jeden**
budynek miasta — Dom Klattów; BDOT10k nie niesie materiału ścian; `buildings.geojson` nie przenosi znaczników materiału
z OSM (otwarte w ADR 0295). Masowa zmiana bez danych byłaby zgadywaniem. Zamiast tego:
- `wood_planks_white` jest dozwoloną ścianą nadpisania (`HOUSE_WALL_OVERRIDES`) — każdy dom drewniany, który właściciel
  lub zdjęcie z otwartej licencji pokaże jako biały, dostaje wpis w `overrides.yaml` (deski, nie bale);
- `log_wall_white` zostaje materiałem obiektów autorskich (kafel = wysokość ściany parterowej; reguła `wood_wall`
  zakłada kafel desek 6,0 × 2,6 m); natomiast `roof_tiles_old` został w ADR 0316 przepisany na pełny kafel 4,2 × 4,2 m
  i w ADR 0336 dopuszczony w `BM.ROOF_OVERRIDES` (dopisek `neon-testfix-s24`, test `test_materials_and_sets`);
- droga do reguły: przeniesienie `building:material` / `building:colour` z OSM do `buildings.geojson` + uzupełnienie
  znaczników w OSM dla Knyszyna i Tykocina (praca terenowa właściciela lub Mapillary) — osobne zadanie geo-worldgen.

### 4. Lamus przy plebanii (zdjęcie 02) — drugi obiekt autorski (`streetscape/knyszyn_lamus_0305.py`)
Budynek zidentyfikowany na ortofoto (BDOT `40f8044a…6fe1`, „budynek gospodarczy”, 12,05 × 6,67 m, bez wysokości LoD,
jedyny ciemnoszary dach czterospadowy między frontem kościoła a Kościelną; czerwony dach plebanii między nim a kościołem
jak na zdjęciu). W OSM nie ma znaczników. Reguła budowała płaską szarą szopę 4,5 m.
- SOURCED: obrys. ESTIMATED ze zdjęcia: okap 2,7 m, kalenica 6,5 m (dach ~1,5 × ściana), okap 0,55 m, podcień 1,7 m
  głęboki na 0,72 długości z pięcioma słupami 20 cm i mieczami, pomieszczenie zrębowe na pełną głębokość przy końcu
  zachodnim, podłoga z desek, podmurówka z kamienia.
- **Strona podcienia jest ESTIMATED**: na zdjęciu kościół stoi za dalszym końcem podcienia, a budynek po prawej stronie
  osi widzenia; kościół leży na przedłużeniu osi budynku ku ESE, więc podcień patrzy na NNE. Do potwierdzenia przez
  właściciela (jedno słowo: „od plebanii” / „od ulicy”).
- Materiały: `log_wall_raw` (zestaw `log_whitewash` pod barwą surowego, spatynowanego drewna, kafel 4,6 × 2,55 m),
  `roof_shingles_grey` (nowy zestaw proceduralny `wood_shingles`: gont, rzędy 0,15 m, szerokości 7–12 cm), `wood_planks`
  (słupy, miecze, oczep, podłoga, drzwi), `fieldstone_plinth`.
- Nadpisanie `look-lamus-plebanski` zostaje jako zapas reguły (dom drewniany, dach czterospadowy 6,4 m), gdyby obiekt
  autorski się wyłączył (zmiana obrysu).
- Pominięte: wole oko w połaci, załamanie połaci przy okapie, wrota i detale zrębu (ostatki).

### 5. Kamery kontrolne
`look_dom_klattow_street` (z drugiej strony Kościelnej, 18,4 m od ściany, 1,6 m, kadr zdjęcia 01) obok istniejącej
`look_dom_klattow`; `look_lamus_plebanski` (kadr zdjęcia 02, pozycja ESTIMATED).

## Budżet i walidacja
Wszystko zmierzone w tej gałęzi; rendery = edytor, High clear, 1920 × 1080, scena `World_knyszyn_High` (nie build
Windows). „Przed” dla kamery `look_dom_klattow` = `artifacts/knyszyn-p2-s24/stats-after5.txt` (stan main, ten sam
generator); pozostałe kamery są nowe i nie mają pomiaru „przed” na treści High.

| | przed | po (runda 2) | źródło |
|---|---|---|---|
| Dom Klattów, LOD0 / LOD1 | dom z reguły | 3 854 / 99 tris | `streetscape_qa.json` |
| Lamus, LOD0 / LOD1 | szopa z reguły | 232 / 70 tris | jw. |
| Kafel `knyszyn`: budynki LOD0 | 669 021 | 671 857 (+2 836) | `world_manifest.json` (`artifacts/klattow-s24/budget-r2.json`) |
| Kafel `knyszyn`: budynki LOD1 | 110 008 | 110 049 (+41) | jw. |
| Kafel `knyszyn`: działki (`plots`) | 432 339 | 432 095 (−244; krzewy z cienia, płot działki) | jw. |
| Chunk 0_4: materiały | 52 | 62 (+10; każdy = draw call, gdy widoczny) | jw. |
| Tabela materiałów manifestu | 345 | 353 | jw. |
| `look-dom-klattow`: draws / tris | 615 / 1 481 809 | 626 / 1 484 401 (+11 / +2 592) | `stats.txt` (szacunek edytora przed SRP batchingiem) |
| `look-dom-klattow-street` (nowa) | — | 547 / 1 466 323 | `artifacts/klattow-s24/r2/stats.txt` |
| `look-dom-klattow-gable-e` (nowa) | — | 234 / 955 389 | jw. |
| `look-dom-klattow-yard` (nowa) | — | 98 / 375 046 | jw. |
| `look-lamus-plebanski` (nowa) | — | 458 / 1 119 089 | jw. |
| Tekstury nowych zestawów (szacunek ASTC z mipami) | 0 | Medium 2,21 MB, High 11,26 MB (5 zestawów) | `materials_spec.json` |

Wszystkie kadry poniżej 2 mln trójkątów; draw calle +11 na kadrze z domem (limit roboczy 850 z D-s24).
Treść Low (scena `World_knyszyn`, LOD1) zmierzona przed / po rundzie 1: `look-dom-klattow` 600 → 604 draws,
865 370 → 866 030 tris (`artifacts/klattow-s24/before2-low`, `r1-low`).

Rundy wizualne (2 z 3): `artifacts/klattow-s24/sbs/*-r1.jpg`, `*-r2.jpg` (render nad zdjęciem właściciela).
Ocena własna agenta (nie `visual-critic`): bryła, biel ścian z wieńcami, szczyt z pionowych desek z okienkiem
i daszkiem, daszek okapowy, łaciata stara dachówka, dwa kominy, ganek z kratką, rytm okien i płot — rozpoznawalne
wobec zdjęć 01 / 04 / 05. Odstępstwa: płot 0,83 m od ściany zamiast w linii ganku (chodnik z generatora), podmurówka
czyta się jako ciemne kamienie w jasnej zaprawie (odwrotnie niż tekstura — przyczyna nieustalona), brak krzewu,
pnącza i słupa, płot działki z atlasu jest czerwony. Lamus: bryła, podcień ze słupami i mieczami, dach czterospadowy
z gontu — zgodne z kierunkiem zdjęcia 02; kadr z wysokości 3,2 m.

Testy: `tests/gis/test_dom_klattow_0305.py` (8). Pełny `pytest tests/gis` i EditMode Win64 — wyniki w raporcie agenta
i `docs/status/klattow-s24-STATUS.md`.

**Do lidera:** (1) agent `road-widen-s24` budował `knyszyn` równolegle do wspólnego `Data/raw/derived` — po scaleniu obu
gałęzi kafel trzeba przebudować raz jeszcze; ten worktree ma prywatną kopię `Data/raw/derived/knyszyn` (reszta to
junctiony — odpinać `cmd /c rmdir`, nigdy `-Recurse`). (2) Nowe materiały trafiają do tabeli manifestu każdego kafla
przy jego najbliższej przebudowie (GLB bez zmian).

## Runda 3 (klattow-r3-s24, 2026-11-20) — poprawki po przeglądzie lidera

Stan wyjściowy: main z korektami P2 / P3 (`klattow-fix-cli`). Wszystkie wymiary poniżej `WORKING_VALUE` / ESTIMATED ze zdjęć,
o ile nie napisano inaczej.

**Lamus (`knyszyn_lamus_0305.py`, zdjęcie 02).**
- **Gont jako geometria.** Każdy rząd to osobny pas siatki, którego dolna krawędź (czoło) stoi 5 cm nad rzędem niżej (3,5 cm w przebiegach 1–2 — za płytko wg `visual-critic`)
  (`SHINGLE_STEP`); rząd 0,214 m (`SHINGLE_COURSE` = 1,5 m / 7 — na zdjęciu ~29 rzędów na ~6,2 m połaci), 29 rzędów na
  każdej z czterech połaci, w jednej linii na narożach. Zestaw `wood_shingles` ma ten sam rząd (7 na kafel, było 10 po
  0,15 m), gonty 9–15 cm, cień pod następnym rzędem — linia czoła tekstury leży na stopniu geometrii. LOD1: dwie płaskie
  połacie na stronę; te same płaskie połacie leżą w LOD0 2 cm pod rzędami jako zamknięta bryła rzucająca cień
  (przebieg 2: przesunięcie wierzchołków w przebiegu cieni otwierało szczeliny między rzędem a czołem — jasne kropki
  w cieniu dachu, P0 krytyka). Wariant „normal / parallax w materiale” odrzucony: shader świata nie ma parallaksy, a sama mapa
  normalnych była już w rundzie 2 (płaska szara płyta z 20 m).
- **Proporcje dachu:** krawędź okapu 2,27 m, kalenica 6,8 m (było 2,7 / 6,5), okap 0,9 m (0,55), **załamanie połaci**:
  dolne 1,15 m rzutu pod kątem 32° (27° w przebiegach 1–2: okap na szczycie czytał się jak odklejona półka), wyżej ~51°. Dach ≈ 1,6 × ściana jak na zdjęciu. Brak wysokości LoD — ESTIMATED.
- **Wole oko** na połaci od podcienia tuż nad załamaniem: brew o profilu cos² (1,9 × 0,60 m) z gontu, czoło z brązowej deski
  (`wood_planks`) z ciemnym półokrągłym otworem 0,72 m.
- **Podcień:** głębokość 2,1 m (1,7), sześć słupów 20 cm (5), miecze 0,65 m po obu stronach każdego słupa, oczep 22 cm,
  nad nim końce belek stropowych co ~0,87 m wysunięte 0,28 m, płatew, strop z desek; **podest deskowy** na podwalinie
  wysunięty 0,25 m przed słupy, czoło z drewna do poziomu terenu (kamień tylko tam, gdzie teren opada), jeden stopień. Izba zrębowa: mały kwadratowy otwór zamiast okiennicy.
- Materiały: `log_wall_raw` 0,235 / 0,172 / 0,118 (przebieg 2: 0,185 / 0,160 / 0,135 — zimna szarość, P1 krytyka) (miodowy z rundy 2 wychodził pomarańczowo; zdjęcie: zrąb zszarzały),
  nowy `wood_planks_weathered` (skan `wood_siding`, 0,215 / 0,168 / 0,125) na słupy, miecze, belki, podest zamiast brązowego
  `wood_planks`; `roof_shingles_grey` 0,195 / 0,196 / 0,192.

**Dom.**
- **Podmurówka (`fieldstone`).** Przyczyna „odwrotnego” odczytu: (a) kopuła kamienia `sqrt(e)` miała pionową ścianę przy
  fudze — mapa normalnych rysowała w słońcu cienką czarną kreskę wokół każdego kamienia („płytki łamane”); (b) w albedo
  brzegi kamieni i wilgotny dół były ciemniejsze od zaprawy — w cieniu wychodziły ciemne kamienie w jasnej siatce.
  Nowy zestaw: gładka kopuła bez ostrza, fugi 2–4 cm tylko lekko cofnięte, zaprawa piaskowa ciemniejsza od średniego
  kamienia i jaśniejsza od ciemnych, ton kamieni 0,53–1,03 × z kilkoma ciemnymi głazami, AO 0,5 (było 0,9).
  Barwa `fieldstone_plinth` 0,215 / 0,200 / 0,172.
- **Płot działki** (`plot_fence.tint`): atlas `plot_kit` maluje sztachety rdzawoczerwono; nowe pole `tint: [r, g, b]`
  (mnożnik liniowy 0–2 barw atlasu = `Kit.tint` tej działki zamiast barwy starzenia klasy wieku). Dom Klattów:
  `[0.90, 1.40, 1.10]` → ok. 112 / 58 / 40 sRGB (przebieg 1 z `[0.80, 2.0, 1.30]`: szare, „złuszczone” sztachety
  atlasu — 16 % — wychodziły zielone; mnożnik nie zrobi z rdzawej i szarej deski tego samego brązu). Inne działki bez zmian.
- **Ganek a płot i chodnik — warstwa dróg, nadpisanie lokalne.** Zmierzone w danych: oś OSM Kościelnej 4,06 m od czoła
  ganku (BDOT), jezdnia 5,5 m (BDOT) → krawężnik 1,31 m przed gankiem. Reguła `implied_sidewalks` kładzie chodnik
  standardowy 2,0 m, więc jego tylna krawędź wchodziła 0,7 m w głąb ganku. Zdjęcie 01 i ortofoto 0,25 m pokazują
  wąski chodnik (~1,1–1,2 m) między krawężnikiem a płotem. Nowy klucz nadpisania krawędzi `sidewalk_w_left` /
  `sidewalk_w_right` (m, 0,6–6,0; `roads/network.py`: szerokość chodnika tej strony zamiast `SIDEWALK_W`, tylko tam,
  gdzie strona ma chodnik) i wpis `look-dom-klattow-koscielna-footway` po stronie północnej krawędzi
  `w98072526:1134839334-1134842485` (303 m; szerokość z dala od domu ESTIMATED z ortofoto). Przebieg 1 z 1,10 m:
  płot 1,53 m od ściany (oś OSM nie jest równoległa do ściany: 1,2°, ~0,4 m na długości płotu). Ostatecznie
  **0,70 m** + zapas płotu od obrysu drogi `ROAD_CLEAR_M` 0,15 → 0,05 m (sztachety stoją przy samej krawędzi chodnika,
  jak na zdjęciu). Chodnik wychodzi o 0,1–0,3 m węższy niż na zdjęciu — właściwa poprawka to oś / szerokość jezdni
  Kościelnej (warstwa dróg, otwarte).
- **Zieleń przy ścianie (zdjęcie 01):** krzew (r 1,2 m, 2,2 m) między pierwszym a drugim oknem na zachód od ganku,
  młode drzewko (2,8 m) między dwoma ostatnimi na wschód, pnącze jako girlanda na wschodniej połowie szczytu ganku z wąskim zwisem przy narożnym słupku (przebieg 2: karta
  na całą wysokość czytała się jak tuja) — siatki atlasu
  `plot_kit` (`plots.bush`, `fruit_tree`, `card`), tylko treść High, tylko gdy pas między ścianą a płotem ma ≥ 1,5 m.
- **Słup energetyczny:** w danych go nie ma (BDOT10k `OT_BUWT_P`: najbliższy obiekt 476 m; `OT_SULN_L`: tylko linie SN
  183 m dalej; OSM: brak `power=*` w kaflu przy Kościelnej) — nie dodany, zostaje otwarty.

**Budżet rundy 3** (edytor, High clear, 1920 × 1080, scena `World_knyszyn_High`; „przed” dla kafla = manifest z gita
8ad119ad9, „przed” dla kamer = runda 2 z tabeli wyżej — render stanu main w tej gałęzi nie był możliwy, patrz niżej):

| | przed | po (przebieg 3) |
|---|---|---|
| Dom Klattów LOD0 / LOD1 (+ ogród w `plots`) | 4 404 / 99 (po korektach P2 / P3) | 4 404 / 99 (+ 78 tris zieleni) |
| Lamus LOD0 / LOD1 | 232 / 70 | 891 / 86 |
| Kafel `knyszyn`: budynki LOD0 / LOD1 | 671 857 / 110 049 | 673 066 / 110 065 (+1 209 / +16) |
| Kafel: `plots` / `plots_low` | 432 095 / 291 942 | 432 789 / 292 418 (+694 / +476: dłuższy płot działki przy węższym chodniku, zieleń) |
| Kafel: `road` | 258 116 | 258 214 (+98) |
| Tabela materiałów / chunk 0_4 | 353 / 62 | 355 / 63 (`wood_planks_weathered`, `plaster_peach__far_ribbon`) |
| `look-dom-klattow`: draws / tris | 626 / 1 484 401 | 627 / 1 487 203 |
| `look-dom-klattow-street` | 547 / 1 466 323 | 556 / 1 469 104 |
| `look-dom-klattow-gable-e` | 234 / 955 389 | 241 / 957 803 |
| `look-dom-klattow-yard` | 98 / 375 046 | 99 / 377 550 |
| `look-lamus-plebanski` | 458 / 1 119 089 | 459 / 1 121 790 |
| `look-lamus-plebanski-close` (nowa) | — | 473 / 936 456 |

Różnice kamer względem rundy 2 obejmują też zmiany main między rundami (m.in. `road-widen-s24`); wkład tej rundy w kaflu
to +1 209 trójkątów budynków i +2 materiały. Wszystkie kadry < 2 mln trójkątów i < 850 draw calli.

**Błąd importu z main (naprawiony przy okazji):** kafel `knyszyn` (chunk 1_4, LOD1) używa `plaster_peach__far_ribbon`,
którego nie było w tabeli materiałów (`_FAR_WALLS["ribbon"]` = lista biurowa bez `plaster_peach`) — import Unity kończył się
`[WORLD_MATERIAL] … missing material` zarówno na kopii derived z main, jak i po świeżym `build_world` na 8ad119ad9.
Dopisane do `materials.py`.

**Ocena.** `visual-critic` na przebiegu 2: dom PASS, lamus FAIL (P0 kropki słońca w cieniu dachu, wole oko niewidoczne,
kamień pod podestem, zrąb za szary, pnącze jak tuja). Przebieg 3 poprawia te punkty (ocena własna agenta, bez
ponownego krytyka — limit trzech przebiegów): cień dachu pełny, zrąb cieplejszy, brew z brązowej deski, pnącze jako
girlanda. Zostaje: pod podestem od strony niższego terenu widać kamień, wole oko jest małe z kadru zdjęcia.
SBS: `artifacts/klattow-r3-s24/sbs/*-r1.jpg`, `*-r2.jpg`, `*-r3.jpg`.

## Otwarte
- Runda 3: `visual-critic` na przebiegu 3 i ocena właściciela; płot działki z atlasu — mnożnik daje rdzawy brąz, pojedyncze
  szare sztachety oliwkowe (potrzebny brązowy rząd sztachet w atlasie `plot_kit`); chodnik Kościelnej 0,70 m (węższy
  niż na zdjęciu — oś / szerokość jezdni do pomiaru); dachówka domu nadal jako równa krata (P1 krytyka, poza zakresem
  rundy); słup energetyczny (brak w danych); ostatki zrębu i czerwonawe górne wieńce lamusa; kamień pod podestem lamusa;
  EditMode: `RegionSelectTests` — `routeLengthM` kafla `bialystok-industrial-c` nieaktualne (poza tą gałęzią).
- Ocena właściciela i `visual-critic` (kolory bielenia, dachówki, bejcy; rozmieszczenie okien).
- Krzew i pnącze przy ganku, tabliczka z numerem, słup energetyczny przy narożniku.
- Podmurówka `fieldstone_plinth` w silniku: ciemne kamienie / jasna zaprawa (tekstura ma odwrotnie) — do diagnozy.
- Chodnik Kościelnej: w grze szerszy i bliżej ściany niż na zdjęciach (płot stoi na modelowanym chodniku).
- Płot działki z atlasu `plot_kit` ma inny (czerwony) odcień niż sztachety obiektu — atlas nie ma barwienia per działka.
- Zachodni szczyt (brak zdjęcia), wnętrze ganku.
- Płot w LOD1 (treść Low / Medium) — pominięty; atlas `plot_kit` ma sztachety, ale w innym kolorze.
- Lamus: potwierdzenie strony podcienia, wole oko, załamanie połaci, ostatki zrębu.
- Reguła ogólna dla bielonych domów — po danych (pkt 3).
