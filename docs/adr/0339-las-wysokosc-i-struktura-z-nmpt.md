# ADR 0339 — Las: wysokość, luki, młodniki i linia koron z modelu pokrycia terenu (NMPT GUGiK)

Status: Proposed (agent world-builder, gałąź `forest-height-s24`), 2026-11-24. Do scalenia przez lidera.
Powiązane: ADR 0015 / 0023 (HLOD lasu), 0170 (`forest_stand`), 0187 (ściana lasu, płaszcz, dane BDL + NMPT dla Dojlid),
0242 (NMPT przez WCS dla brył budynków), 0308 (korony), 0324 (skraj lasu, szum wierzchu ściany), 0330 (dal lasu),
0327 (budżet trójkątów C). Decyzja właściciela D68 (lato). Krytyk: `artifacts/critic-s24-build5/CRITIC.md` pkt 7.

## Kontekst
Krytyk buildu #5 (pkt 7, P1): „lasy: ściana koron jednej wysokości i ciemna kurtyna nad horyzontem” (`t2931`, `t3271`,
`t0440`). Przyczyna w generatorze: wysokość każdego drzewa lasu losowana niezależnie z jednego zakresu na gatunek
(`HEIGHT`: sosna 14–24 m, świerk 14–25, brzoza 9–19), ta sama w każdym drzewostanie każdego kafla; `zagajnik` × 0,7.
Maksimum z kilkudziesięciu losowań w oknie HLOD jest wszędzie takie samo (~23 m), więc czasza i ściana HLOD są równe
jak stół, a szum wierzchu z ADR 0324 (0,82–1,14) tylko faluje tę jedną wysokość. Nie ma wieku drzewostanu, zrębów,
upraw, młodników, przestojów; gatunki są wymieszane „sól z pieprzem”.

W `Data/raw` nie ma NMPT ani chmur LiDAR (opcje `ingest.py --with nmpt|lidar` nigdy nie były uruchomione: ~600 MB i
~5 GB na kafel). GUGiK udostępnia NMPT 0,5 m także przez WCS (użyte w ADR 0242 i w pomiarach M68 dla ADR 0187); usługa
obsługuje `SCALEFACTOR`, więc kafel 2048 × 2048 m w siatce 1 m to 4 zapytania (~86 MB tekstu, ~3 min).

## Decyzja

### 1. Produkt danych: model wysokości koron kafla (`tools/worldgen/streetscape/forest_chm.py`)
`uv run --project tools/worldgen python tools/worldgen/streetscape/forest_chm.py --region <id> [...]`
- NMPT (WCS `PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel`, `DSM_PL-EVRF2007-NH`, siatka 1 m) minus NMT kafla
  (`heightmap_2049.r16`, ten sam układ wysokości PL-EVRF2007-NH; grunt w środku komórki = średnia 4 węzłów).
- Redukcja do siatki 4 m: `L` = najwyższa próbka komórki (wierzch koron, krok 0,25 m), `A` = udział próbek ≥ 5 m nad
  gruntem (pokrycie). Próbki > 60 m (maszt, dźwig, ptak) i braki danych = 0. Zerowane poza lasami BDOT10k
  `OT_PTLZ_A` + 40 m (nie przechowujemy budynków ani pól).
- `Data/Regions/<id>/forest_chm.png` (PNG 2-kanałowy, 512 × 512, **w gicie, poza LFS** — wpis w `.gitattributes`;
  21–133 kB na kafel) + `forest_chm.json` (georeferencja, usługa, data pobrania, sha256 odpowiedzi i PNG, statystyki).
  Budowa świata nie potrzebuje sieci i jest odtwarzalna. Surowy model: `Data/raw/gugik/gugik-nmpt-wcs-<id>/dsm_1m.npz`.
- **Opt-in danymi:** kafel bez `forest_chm.png` generuje się bajt w bajt jak dotąd (test `test_no_model_no_change`).
- Data nalotu komórek: usługa jej nie podaje — `UNVERIFIED` (jak w 0242). Model pokrycia zaniża wierzchołki
  (impuls nie trafia w pęd szczytowy; 0242 odnotował 7,1–8,3 m wobec 10,5 m dla pojedynczej lipy) — bez korekty,
  `WORKING_VALUE`.

### 2. Drzewa drzewostanu (`vegetation.place(chm=)`)
Pozycje i strumień losowy bez zmian (ADR 0173); zmiany tylko skrótem pozycji, po losowaniu:
- **Wysokość** = wysokość górująca w miejscu drzewa (`Chm.dom`: najwyższa korona w oknie 3 × 3 komórki = 12 m; M68
  mierzył drzewostany jako „h30_max”) × pozycja biosocjalna: 50 % drzew 0,90–1,00 (górujące), 32 % 0,76–0,90
  (współpanujące), 18 % 0,50–0,74 (opanowane; sosna, brzoza, olsza jako światłożądne zostają w klasie
  współpanującej). Najwyższe drzewa modelu sięgają zmierzonych wierzchołków, przestoje stoją tam, gdzie ma je pomiar.
- **Luki:** brak korony ≥ 3 m w oknie → drzewo usunięte (zrąb, halizna, linia oddziałowa); luki ≥ 300 m² są
  wycinane z poligonu drzewostanu — bez czaszy / ścian HLOD i bez maski dna lasu.
- **Uprawy i młodniki** (górująca < 9 m): prototypy młode (`tree_pineyoung`, `tree_birchyoung`, świerk w formie z
  gałęziami do ziemi) na zmierzonej wysokości, nie przeskalowane drzewa dojrzałe (ADR 0187).
- **Zwarcie:** pokrycie < 0,72 → drzewo zostaje z prawdopodobieństwem pokrycie / 0,72 (min. 0,25).
- **Płaszcz skraju** nie wyrasta ponad drzewostan za nim (0,45 / 0,65 / 0,85 wysokości drzewostanu w oknie 28 m).
- **Gatunki w kępach** (szum gładki na siatce metrów kafla): w płatach świerka / brzozy część sosen staje się
  świerkiem / brzozą, poza płatami świerk / brzoza ustępują sośnie — udziały klasy BDOT zostają w przybliżeniu,
  znika równomierne wymieszanie. **Olsza w obniżeniach:** grunt ≥ 1,5 m poniżej średniej z otoczenia 120 m (NMT) →
  70 % olszy. Kategoria (iglasty / mieszany / liściasty) nadal z BDOT10k — innego źródła gatunków w `Data/raw` nie ma
  (BDL: patrz „Otwarte”).
- Autorskie `forest_stand` (ADR 0170 / 0187) mają pierwszeństwo przed modelem.
- Raport: `streetscape_qa.json` → `vegetation.forest_chm` (drzewostany, luki, przerzedzenia, młode, percentyle wysokości).

### 3. HLOD lasu (`forest_hlod.build(chm=)`)
- Czasza: wierzchołki siatki 12 m na 0,93 × wysokości górującej z modelu (zamiast maksimum z wygenerowanych drzew).
- Ściany: linia koron obrazu ściany (0,78 wysokości obrazu) na zmierzonym wierzchu w punkcie ściany; szum wierzchu z
  0324 zmniejszony do 0,94–1,05 (zmienność niesie pomiar). Ściany powstają też wokół wyciętych luk.
- Gdzie model nie ma koron (< 3 m: komórka poza maską, mała dziura) zostaje dotychczasowa reguła z drzew.

## Zmierzone (prototyp: `dk65-04`, `dk65-05` — Puszcza Knyszyńska, `dw671-tykocin-03`)

WYNIKI_TABELA

## Otwarte / WORKING_VALUE
- Progi (3 m, 9 m, 300 m², 0,72), klasy biosocjalne, udziały płatów, próg obniżenia — `WORKING_VALUE`.
- Gatunek panujący i wiek z Banku Danych o Lasach (jak dla Dojlid w 0187) — nieużyte: licencja BDL ma
  `LEGAL_REVIEW_REQUIRED` (cz. V lit. b regulaminu); kategoria BDOT bywa sprzeczna z BDL (M68: „liściasty” = 7SO).
- Tło dali (`far_field`, pierścień do 4,2 km poza kaflem) nadal z reguły 0330 (wysokość klasy × 0,86–1,12 na
  drzewostan): model koron jest tylko dla bbox kafla. Rozszerzenie: zgrubny CHM pierścienia (WCS 10 m + NMT WCS).
- Tekstura ściany HLOD jest wypiekana z drzew reguły klasowej (korony sosny w obrazie są brązowawe, wierzch obrazu
  równy ± 9 %); ponowny wypiek z większą zmiennością wysokości i poprawionym kolorem igliwia — osobne zadanie.
- `tree_stand` (ogrody działkowe) i drzewa poza `OT_PTLZ_A` nie korzystają z modelu (maska).
- Data nalotu NMPT `UNVERIFIED`; zręby młodsze niż nalot będą w grze lasem (i odwrotnie).
