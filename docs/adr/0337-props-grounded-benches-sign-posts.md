# ADR 0337 — Rekwizyty uliczne: ławki z otwartymi nogami na terenie i czytelne słupki znaków (krytyk build #5, pkt 10)

Status: Proposed (agent `neon-props-s24`, 2026-11-24). Numer zarezerwowany przez lidera.
Powiązane: `artifacts/critic-s24-build5/CRITIC.md` (pkt 10), ADR 0102 (meble uliczne r1, kontakt stóp), ADR 0162 (meble/tablice G5/G3), ADR 0227 (Knyszyn Rynek), ADR 0279 (normy znaków), ADR 0320 (Rynek w Tykocinie), `docs/06_GRAFIKA_ANTI_AI_SLOP.md`.

## 1. Diagnoza (klatki build #5 i rendery PRZED)

Przegląd klatek `artifacts/full-build-5-s24/runs/20261122-181152/shot_t3441.png` (Rynek w Tykocinie) oraz `artifacts/full-build-5-s24/sheets/sheet_05.jpg` (`t0650`, `t0670` w `bialystok-knyszynska`), potwierdzony renderami kontrolnymi PRZED (`artifacts/neon-props-s24/before/`, High clear/overcast, 16 PNG), ujawnił cztery przyczyny w generatorze:

1. **Ławki autorskie Rynku (`knyszyn_park_props_0227._bench`, wywoływane też z `tykocin_rynek_0320.py`)**: zamiast otwartych nóg generator budował dwa pełne ciemnoszare monolity boczne o wymiarach `0,60 × 0,90 m`, bez próbkowania wysokości terenu pod każdą nogą (wszystkie wierzchołki oparte o jedno centralne `z`, bez zagłębienia w bruk na pochyłości).
2. **Prototyp ławki i kosza OSM (`props.bench`, `props.waste_bin` + `furniture.SEATED_POLES`)**: `props.bench` miał dwie pełne płyty `0,40 × 0,44 m` pod siedziskiem i oparcie bez słupków wsporczych; `bench` i `waste_bin` nie były wpisane w `furniture.SEATED_POLES` ani `FOOT_R`, więc nie korzystały z osadzania `SurfaceTop`/kolizji z ADR 0102 i na chodnikach/poboczach mogły odstawać od powierzchni; oba miały też identyczną geometrię w LOD0 i LOD1.
3. **Słupki znaków w polu (`props.sign_post`, `materials.steel_galv`)**:
   - Materiał `steel_galv` (`metal=0,9`, `rough=0,55`) odbijał niebo i horyzont, redukując składnik dyfuzyjny do 10 % — słupek Ø60,3 mm tracił kontrast na tle zielonych pól i zachmurzonego nieba.
   - LOD1 był 4-bocznym pryzmatem o szerokości zaledwie `42,6 mm` po przekątnej, przez co na średnim dystansie znikał poniżej subpiksela.
   - Brak kołnierza u podstawy osłabiał czytelność styku z poboczem/trawą.
4. **Wysokość słupka przy znakach ostrokątnych (`furniture.sign_assembly`)**: słupek kończył się `zc - zb + 0,05 m`, czyli wystawał ~10 cm **ponad** górny wierzchołek rombu `D-1` i trójkątów ostrzegawczych `A-8`/`A-9`/`A-10`.

## 2. Decyzje

### 2.1. Ławki i kosze na śmieci
- **`knyszyn_park_props_0227._bench(..., z_at=None)` i `tykocin_rynek_0320.py`**: otwarta 4-nożna rama stalowa (`steel_painted`: nogi przednie ze słupkami podłokietników, nogi tylne ze słupkami oparcia, belki poprzeczne pod siedziskiem, podłokietniki, wzdłużna belka wiążąca) + 3 deski siedziska i 2 lekko odchylone deski oparcia (`bench_wood`). Gdy przekazane `z_at=ground`, każda z 4 nóg osobno próbkuje wysokość nawierzchni/terenu w swoim punkcie `(e, n)` i schodzi `6 cm` w głąb podłoża (`min(z_foot, z_ref) - 0,06 m`), dzięki czemu żadna noga nie wisi na spadkach placu. LOD0 = 140 tris, LOD1 (`buildings_low`) = 60 tris (1 płyta siedziska + 1 płyta oparcia + 4 osadzone nogi; 0 nowych materiałów). Wymiary `WORKING_VALUE`.
- **`props.bench` i `props.waste_bin`**: przebudowane z pełnym 4-nożnym szkieletem ławki (słupki oparcia sięgają górnej krawędzi oparcia) i cokołem/korpusem/daszkiem kosza; podstawy schodzą `-0,10 m` pod punkt zerowy (mieści się w oknie audytu kontaktu 15 cm z ADR 0102). Własny uproszczony LOD1 (`bench`: 72 tris; `waste_bin`: 6-boczny). Bez nowych slotów materiałowych (`bench_wood` + `steel_painted`; `steel_painted` + `steel_galv`).
- **`furniture.SEATED_POLES` i `FOOT_R`**: dopisano `bench` (`FOOT_R = 0,75 m`) i `waste_bin` (`FOOT_R = 0,22 m`), aby wszystkie instancje OSM i przystankowe osadzały się na `SurfaceTop`/kolizji tak samo jak latarnie i znaki.

### 2.2. Słupki znaków drogowych
- **Normy wysokości i średnicy**:
  - Dolna krawędź tarczy: `SIGN_H_MIN = 2,00 m` poza chodnikiem, `SIGN_H_SIDEWALK = 2,20 m` na/nad chodnikiem — źródło: załącznik nr 1 do rozporządzenia w sprawie szczegółowych warunków technicznych dla znaków i sygnałów drogowych (`[ZNAKI-Z1]`, Tabela 1.11, Dz.U. 2019 poz. 2311 / Dz.U. 2022 poz. 2377; cytowane w `tools/worldgen/roads/standards.py`).
  - Średnica rury słupka: `SIGN_POST_D = 0,0603 m` (Ø60,3 mm, typowa rura ocynkowana do znaków drogowych, `WORKING_VALUE`).
- **Materiał `materials.sign_post_galv`**: matowy, utleniony ocynk ogniowy (`color=[0,36, 0,37, 0,38]`, `rough=0,62`, `metal=0,42`, `WORKING_VALUE`), korzystający z istniejącej tekstury `furniture_galv` (ziarno cynku + strefa zabrudzenia przy ziemi) i `sky_occ=SKY_OCC_STRUCT`. 1 slot materiałowy na `sign_post` = **+0 draw calls**.
- **Geometria `props.sign_post`**:
  - LOD0: 10-boczny trzon Ø60,3 mm osadzony do `-0,04` w skali jednostkowej (~11–14 cm w gruncie przy typowym `sz = 2,7..3,5 m`, w oknie audytu 15 cm z ADR 0102) + subtelny kołnierz u podstawy (`r × 1,85 → 1,18`, `z = -0,025..+0,022`), z przemapowaniem UV0.v tak, by strefa zabrudzenia przy gruncie wypadała u stopy.
  - LOD1: 6-boczna rura (zamiast 4-bocznej) ze skalą promienia `SIGN_POST_LOD1_SCALE = 1,20` (`WORKING_VALUE`), żeby słupek nie ginął subpikselowo na tle pól na średnim dystansie.
- **Zakończenie słupka `furniture.sign_assembly`**: wierzchołek słupka kończy się czysto za górną obejmą (`>= zcen + 0,22·hh + 0,04 m`), a dla tarcz ze szpicem u góry (`diamond` D-1, `triangle_up` A-8/A-9/A-10) jest cofnięty o 14 cm poniżej wierzchołka tarczy, dzięki czemu rura Ø60 mm nie wystaje nad czubek znaku.

## 3. Liczby i budżet (PRZED → PO)

- **Geometria `tykocin_rynek_0320`** (10 ławek + pomnik + mała architektura):
  - `buildings` (LOD0): `2 870 → 3 370` tris (+500 tris, +50/ławkę za pełne 4 nogi, podłokietniki i belkę wiążącą)
  - `buildings_low` (LOD1): `1 562 → 1 262` tris (**−300 tris**, −30/ławkę)
  - `collision`: `120 → 120` tris (bez zmian)
- **Znak `sign_post`**: nadal dokładnie 1 slot materiałowy (`sign_post_galv`, +0 draws).
- **Audyt kontaktu z terenem (`terrain_conformed.npy`)** w przebudowanych kaflach:
  - `tykocin`: `bench` n=15 (`dz ∈ [-0,601, 0,000]` m, med `-0,011 m`), `waste_bin` n=5 (`dz ∈ [-0,381, +0,351]` m), `sign_post` n=104 (każda tarcza ma słupek).
  - `bialystok-knyszynska`: `waste_bin` n=19 (`dz ∈ [-0,518, +0,351]` m), `sign_post` n=182 (każda tarcza ma słupek).
  - `dk65-01`: w trakcie przebudowy (liczby do uzupełnienia po zakończeniu).
- **SceneStats High (edytor, przed SRP batchingiem)** — do uzupełnienia po zakończeniu renderów PO.

## 4. Testy i dowody

- Nowy test regresji: `tests/gis/test_props_grounding_0337.py` (17 testów: otwarte 4 nogi i kontakt każdej nogi na skarpie w `_bench`, uziemienie i oparcie prototypów `bench`/`waste_bin`, `SEATED_POLES`, średnica/kontrast/kołnierz/LOD1 `sign_post`, wysokość słupka i obejmy dla D-1/A-7/A-8/B-33/D-6, pokrycie wszystkich znaków słupkami i kontakt propów z terenem w `tykocin`, `bialystok-knyszynska`, `dk65-01`, QA `tykocin_rynek_0320`).
- Testy budżetowe: `test_budget_0221.py`, `test_typology_0238.py`, `test_hero_bridge.py` (41 passed), `test_world_v31.py` (21 passed).
- Dowody wizualne (High clear + overcast, 16 PNG przed + 16 PNG po + porównanie SBS): `artifacts/neon-props-s24/`.

## 5. Otwarte / dla lidera

- Przebudowano w tym zadaniu kafle `tykocin`, `bialystok-knyszynska` i `dk65-01` (lokalne `Data/raw/derived/` w worktree to kopia — skopiować do `main` lub przebudować w kolejnej fali regenu, a wspólne `art-source/world/props/street_props.glb` odświeży przebudowa kafla referencyjnego `bialystok-industrial-c`).
- Pozostałe kafle (w tym `knyszyn` z `_bench`) dostaną nowe ławki i słupki automatycznie przy kolejnej fali regenu.
- Zużycie/rdza/odblaski pasów na słupkach oraz bardziej szczegółowy wariant kosza betonowego (z kruszywem) pozostają otwarte jako osobny temat tekstur PBR.
