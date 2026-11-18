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
Przebudowane w tej gałęzi: `knyszyn`, `knyszyn-w`. Do przebudowy przez właścicieli kafli: `knyszyn-s` (szew S Knyszyna)
i pozostałe przy najbliższej okazji.

## Pomiary (przed → po)
TBD_MEASURE

## Otwarte
- Zdjęcia Domu Klattów (Kościelna) od właściciela: kolor desek i opasek, okiennice, ganek — wymiary desek do weryfikacji.
- P2 z recenzji nietknięte: płot sztachetowy (atlas `plot_kit`), wyspa ronda, drzewa-kępki, wariant overcast kamer.
- Fartuch poza kaflem (`WorldEdgeBuilder.ApronMask`) ma strefy lasu / gruntu wpisane dla Białegostoku i szum sinusowy —
  pola za krawędzią kafla nie dostają mozaiki.
- Działki ewidencyjne (EGiB / GUGiK KIEG) jako prawdziwy układ pól — osobne zadanie geo-worldgen.
- Render z buildu Windows (recenzja §5.2) — do lidera.
