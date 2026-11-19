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
  zakłada kafel desek 6,0 × 2,6 m);
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

## Otwarte
- Ocena właściciela i `visual-critic` (kolory bielenia, dachówki, bejcy; rozmieszczenie okien).
- Krzew i pnącze przy ganku, tabliczka z numerem, słup energetyczny przy narożniku.
- Podmurówka `fieldstone_plinth` w silniku: ciemne kamienie / jasna zaprawa (tekstura ma odwrotnie) — do diagnozy.
- Chodnik Kościelnej: w grze szerszy i bliżej ściany niż na zdjęciach (płot stoi na modelowanym chodniku).
- Płot działki z atlasu `plot_kit` ma inny (czerwony) odcień niż sztachety obiektu — atlas nie ma barwienia per działka.
- Zachodni szczyt (brak zdjęcia), wnętrze ganku.
- Płot w LOD1 (treść Low / Medium) — pominięty; atlas `plot_kit` ma sztachety, ale w innym kolorze.
- Lamus: potwierdzenie strony podcienia, wole oko, załamanie połaci, ostatki zrębu.
- Reguła ogólna dla bielonych domów — po danych (pkt 3).
