# ADR 0324 — Narew jako rzeka, trzcina w kępach, pobocza i rowy z życiem, słupki U-1a, skraj lasu

Status: Proposed (agent banks-verges-s24, gałąź `banks-verges-s24`), 2026-11-21. Do scalenia przez lidera.
Powiązane: krytyk `artifacts/critic-s24-wave6/CRITIC.md` (top-5 pkt 2 i 4; wiersze 1.1, 2.5, 3.1, 3.2, 3.3, 3.5, 4.3),
ADR 0210 / 0213 / 0318 / 0321 (woda, szuwary, rowy), 0110 (pasy trawy w siatce terenu), 0272 (pobocza), 0187 / 0015
(płaszcz lasu, HLOD), 0308 (drzewa), 0279 (obszar zabudowany), 0268 (U-1a przy przejazdach).

## Kontekst
Krytyk fali 6 (FAIL): woda „płaska, ciemnoszara, granica trawa–woda jak od linijki”, szuwary „rozsypane brązowe
krzyżyki”, pobocze „jasnobetonowy pas stałej szerokości”, rów „ciemnozielony pas jednej tekstury”, brak słupków
U-1a, las „płaska kurtyna z ostrymi krawędziami”. Stan przed (r0, kod main `3fba5b3b7`) potwierdza: trzcina High to
jedna para skrzyżowanych kart na próbkę 2 m (z brzegu prostokątne „pudła” o płaskim wierzchu), rów to osobny
materiał `verge_grass` (inny shader niż łąka za nim), komórki HLOD lasu z powietrza i z drogi to pudełka.

## Decyzja

### 1. Woda (`Kamion/World Water`, `streetscape/water.py`, nadpisanie regionu)
- **Płycizna:** dno (mokry piasek / muł, `_BedColor` 0,36/0,33/0,26 — wartość właściwości Color, czyli kodowana sRGB jak `_BaseColor`; liniowo ≈ 0,11/0,09/0,06) prześwituje przez pierwsze decymetry
  wody — Beer-Lambert (`_Extinction` 1,6 1/m) po głębokości wynikającej z odległości od brzegu (profil koryta ADR 0210:
  0,12 m + 0,35 m/m). Oba tiery, bez tekstur, tafla nadal nieprzezroczysta.
- **Podmuchy (High):** szum 30–60 m dryfujący z wiatrem skaluje nachylenie zmarszczek (pasy gładkiej wody × 0,3,
  zmarszczone × 1,5) + trzecia, drobna oktawa do 45 m od kamery. Fresnel i sonda nieba bez zmian (były od ADR 0210).
- **Linia brzegu:** gładki szum (σ 3 m, deterministyczny, wygaszony 8 m od krawędzi kafla) przesuwa teren w pasie
  1 m po obu stronach zarysu BDOT przez poziom wody: zatoki (węzeł lądu do −0,10 m) i łachy (węzeł dna do +0,07 m).
  Każdy węzeł zatoki dostaje łatę tafli 2,6 × 2,6 m (reguła ADR 0210 „krawędź tafli zawsze pod brzegiem” zachowana —
  test). Za linią wody pas mułu / piasku 0,6–2,6 m (maska terenu A), łamany tym samym szumem.
- **Tykocin:** `water.material` + `bank_horizon` 0,04, `reflect` 0,92 — Narew ma ~48 m między niskimi brzegami;
  domyślny horyzont brzegu 0,10 (wąska, zadrzewiona Supraśl) zamieniał większość widocznej tafli w ciemny odcień
  brzegu zamiast odbicia nieba (Commons „Tykocin Most drogowy 03 / 05”).

### 2. Trzcina (`streetscape/reeds.py`, High)
Pas to gęsty łan **kęp**: 2 kępy na próbkę 2 m w każdym z 4 rzędów, kępa = gwiazda 3 kart (rzędy 0–1) lub 2 kart
(rzędy 2–3) szerokości 1,5–2,3 m (szerzej niż rozstaw — sąsiednie kępy się zazębiają), każda karta pochylona do 11°
(z góry widać płaszczyznę karty, nie kreskę). Wysokość nominalna rzędów 0–1 w zakresie **1,5–2,5 m** (trzcina
pospolita latem), rzędy tylne 0,9–1,9 m (turzyce, ziołorośla). Tekstura `water_reeds` w palecie lipca: zielone
liście, ~10 % zeszłorocznych słomek, wiechy na ~40 % wysokich źdźbeł. Low / Medium bez zmian (wstęga, budżet).
Wiatr: nie zrobiony (shader PlotKit bez animacji wierzchołków) — otwarte.

### 3. Pobocza i rowy (`streetscape/verge_flora.py`, `roads/build_world.py`)
- `shoulder_gravel` 0,20/0,19/0,17 → **0,135/0,120/0,095** (kruszywo z gruntem, ciemniejsze i cieplejsze niż beton
  krawężnika 0,24; `WORKING_VALUE`).
- **Rów w siatce terenu:** części `verge_grass` skarp i dna rowu stron bezkrawężnikowych dostają sufiks źródła `:vg`
  i są scalane z prymitywami terenu (mechanizm ADR 0110): rów rysuje shader trawy terenu z maskami węzłów — ta sama
  ruń co łąka obok, miękkie przejście, brak skoku materiału na koronie rowu (otwarte ADR 0321).
- **Maski dna:** wzdłuż osi dna rowu głębszego niż 0,22 m: plamy wilgotnej, ciemnej ściółki (G 0,25–0,70), miejscami
  goła mokra gleba (A 0,42), bujna niekoszona trawa na skarpach (B ≤ 0,5); łamane szumem 14 m / 5 m wzdłuż drogi.
- **Trawa 3D:** karty alpha-clip (materiał `verge_tufts`, Kamion/World PlotKit, warstwa `banks` = tylko High,
  LOD0 / LOD1 kafla, bez cienia): niskie kępki 0,14–0,38 m na krawędzi pobocza (do 0,42 m w głąb kruszywa — krawędź
  przestaje być linią, szerokość pasa się zmienia), średnie 0,22–0,50 m na skarpach, wysoka trawa / turzyca
  0,45–0,90 m w dnie. Większość kart stoi **w poprzek** drogi (kierowca patrzy wzdłuż). Tylko tam, gdzie pas pobocza
  jest rysowany (stacje wycięte pod płytami skrzyżowań pominięte).
- Pałka i kałuże w rowie: nie zrobione (otwarte).

### 4. Słupki prowadzące U-1a (`streetscape/guide_posts.py`)
Podstawa: Dz.U. 2019 poz. 2311 zał. 4 (słupki prowadzące U-1a / U-1b) — **treść załącznika nie została przeczytana**
(PDF większy niż limit narzędzi), więc wymiary i tabela rozstawu na łukach to `WORKING_VALUE`.
Zacytowane: GDDKiA „ABC oznakowania dróg — słupki prowadzące” (gov.pl/web/gddkia-wroclaw, odczyt 2026-11-21):
„słupki ustawiane są standardowo co 100 m, a w przypadku łuków poziomych odpowiednio częściej”; odblask czerwony po
prawej, biały po lewej. Wygląd: Commons „PL urządzenie U-1a (prawy / lewy).svg” (domena publiczna) — biały słupek,
czerwony pas wznoszący się ku jezdni, na nim odblask.
Reguła: tylko drogi klasy trunk / primary / secondary (+ łącznice), poza obszarem zabudowanym (`built_up.Zone.at`),
strona bezkrawężnikowa z poboczem, nie na obiekcie mostowym ani rondzie, 20 m od końców łańcucha; pary po obu stronach
co **100 m** (prosta), na łukach R < 1250 / 400 / 150 m co 50 / 33 / 20 m (`WORKING_VALUE`); słupek 0,15 m od
zewnętrznej krawędzi pobocza gruntowego; bez słupka 2,5 m od bariery i 1,5 m od innego słupa. Wysokość 1,0 m,
przekrój 0,12 × 0,05 m (`WORKING_VALUE`). **Bez kolizji** (prawdziwy U-1a to pusty słupek z tworzywa; sztywny
kolider 0,2 m za poboczem zaczepiałby naczepę).

### 5. Skraj lasu (`streetscape/forest_hlod.py`, `streetscape/vegetation.py`)
- HLOD: górna krawędź ściany × 0,82–1,14 gładkim szumem 16 m; **druga ściana** 6 m za każdą zewnętrzną, wyższa
  × 1,04–1,22 z innym wycinkiem tekstury (prześwity pierwszej pokazują drugą, paralaksa przy przejeździe); korony
  (powierzchnia) **opadają** w pasie 5 m od prawdziwego skraju do 0,62–0,86 wysokości; narożnik drzewostanu schodzi do
  0,62 (było 0,80) na dwóch segmentach; fartuch krzewów na 45 % krawędzi (było 18 %) o zmiennej wysokości × 0,55–1,25.
- Drzewa: `MANTLE_BAND_KEEP` 0,18 / 0,58 → **0,40 / 0,75** (pas krzewów na ~40 %, pas młodych drzew na ~75 % obrysu).
- Tło dali (`far_field.py`) bez zmian (ma własną falę koron i zwężanie końców) — otwarte.

## Wyniki
(uzupełniane po rundach — patrz sekcja na końcu)

## Otwarte
(uzupełniane po rundach)
