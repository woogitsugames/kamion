# ADR 0324 — Narew jako rzeka, trzcina w kępach, pobocza i rowy z życiem, słupki U-1a, skraj lasu

Status: Proposed (agent banks-verges-s24, gałąź `banks-verges-s24`), 2026-11-22. Do scalenia przez lidera.
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
### Bez przebudowy kafli (zmierzone 2026-11-21)
- pytest: `tests/gis/test_banks_verges_0324.py` 7/7; `test_water_0210.py` + `test_water_0213.py` 14/14 (reguły brzegu
  dopasowane do ADR 0324; przy okazji poprawiony nieaktualny od ADR 0321 napis w `test_stage_hooks_guarded`);
  `test_forest_0187`, `test_ditch_floor_0321`, `test_rural_xsec_0272` zielone.
- EditMode Win64 (kod gałęzi, sceny r0): 1525 testów, 1416 zaliczonych, 0 błędów, 109 pominiętych
  (`artifacts/tests/editmode-20261121-213618.xml`).
- Próba na sucho na prawdziwych sieciach (`roads.pipeline.build`, płaski NMT, bez `build_world`): knyszyn-w —
  23 strony bezkrawężnikowe, 12 201 kart trawy = 24 402 trójkąty (krawędź 4 030, skarpy 2 393, dno 5 778), 69 części
  rowu do terenu, 16 słupków U-1a (8 par; 18 stacji w obszarze zabudowanym pominiętych); dk65-07 — 16 stron,
  8 516 trójkątów, 6 słupków. Trzcina Tykocin (`water_banks.json`, bez wykluczeń): ≤ 145 218 trójkątów High
  (ADR 0321: 116 752), Low 8 532.
- Podgląd shadera wody na scenie sprzed przebudowy: `artifacts/banks-verges-s24/r0s/`, `r0s2/`.

### Po przebudowie tykocin / dk65-07 / knyszyn-w (prywatna kopia derived, import Win64, edytor)
Rundy: r0 = stan przed (kod main `3fba5b3b7`), r1 → r2 → r3 (maks. 3). Każda: `build_world` × 3, import Low + High,
visual-qa 1920 × 1080 High clear + High overcast + Low clear, kamery z kabiny (driver eye 2,5 m) i z boku
(`artifacts/banks-verges-s24/cams-<kafel>.json` przez `-Gate3`). Arkusze przed | po i referencja | gra:
`artifacts/banks-verges-s24/sbs/r{1,2,3}/` (referencje: Commons „Tykocin Most drogowy 03 / 05 / 06”, Zala, CC BY-SA 4.0).
- r1 → r2: karty trzciny prostokątne pokazywały pionowe cięcie boku → wachlarz (stopa 0,35–0,7 szerokości);
  maska mułu rysowała trójkątne „schodki” → wygładzona, A 0,85 → 0,70; karty trawy czytały się jako prostokąty
  i „jodełka” → atlas 4 osobnych kęp w rzędzie, karta = 1–2 całe kępy (boki karty w przezroczystych tekselach);
  dno rowu za ciemne → maska wilgoci G ≤ 0,38, wygładzona.
- r2 → r3: zatoki tylko w sąsiadach osiowych dawały schodki terenu 1 m na skośnym brzegu → także sąsiedzi po
  przekątnej (d ≤ 1,5 m), próg `LIP_M` 1,5 → 2,5 m; ciemny pas za koroną rowu = fartuch skarpy tylnej, został w
  `verge_grass` → też do terenu.
- Generator (r3): tykocin — trzcina High 139 486 trójkątów (ADR 0321: 116 752; +19 %), Low 8 414; tafla 47 433
  trójkąty (było 32 175: łaty zatok); U-1a 0 (cały odcinek w obszarze zabudowanym), trawa 0 (brak stron z poboczem
  gruntowym). dk65-07 — trawa 8 112 trójkątów (16 stron), 64 części rowu do terenu, U-1a 5 (1 pominięty przy
  barierze), HLOD lasu 110 768 trójkątów w kaflu (na kamerach +40–48 %, np. 11,7 → 16,2 tys.). knyszyn-w — trawa
  23 002 trójkąty (23 strony), 91 części rowu do terenu, U-1a 16 (8 par).
- Budżet kamer r0 → r3 (`artifacts/banks-verges-s24/budget-r3.md`; stats.txt edytora, szacunek przed SRP batching;
  30 kamer, w tym 4 przestawione między rundami): High — suma draws 7 800 → 7 716 (−84), trójkąty 21,11 → 21,00 M
  (−0,5 %); kamery z kabiny: most Narew +0 draws / +0,4…+1,4 % trójkątów, dk65-07 `drive-wood` +0 / +0,6 %,
  knyszyn-w +0…−3 draws / −0,4…+0,7 %. Low — draws 5 012 → 4 940 (−72), trójkąty 4,12 → 4,14 M (+0,4 %); most
  +0,8…+2,6 %, drogi zamiejskie −3,8…−9,2 % (rów w terenie tylko do LOD1). Czas klatki, pamięć i `WORLD_MEMORY`:
  **nie mierzone** (pomiar tylko w buildzie na bezczynnej maszynie — `pc-metrics.ps1`, lider).
- EditMode Win64 na scenach r2: 1525 / 1416 zaliczonych / 0 błędów / 109 pominiętych
  (`artifacts/tests/editmode-20261122-015956.xml`). pytest: `test_banks_verges_0324.py` 8/8 (w tym test na prawdziwej
  sieci dk65-07), `test_water_0210/0213` 14/14, podzbiór roślinność / przejazdy / plamy / tunel / drzewa 63/63.
  Pełny `pytest tests/gis` nie uruchamiany (pula heavy zajęta przez regenerację fali 6).
- Ocena własna (nie zastępuje `visual-critic`): trzcina to zwarta zielona ściana z wiechami, z góry ciągły pas zamiast
  krzyżyków; linia wody nieregularna z płatami mułu; z pomostu mostu tafla jasna, niebieskoszara, z pasami gładkiej i
  zmarszczonej wody; rów ma ruń łąki obok, kępy trawy przy krawędzi pobocza i w dnie; słupki U-1a widoczne z kabiny;
  bloki lasu w dali mają nierówny wierzch i zejście na skraju, ale nadal czytają się jako ciemne bryły (poprawa
  umiarkowana). Z góry tafla pozostaje ciemna (~48/53/54 sRGB) — zgodnie ze strojeniem ADR 0213 na ortofoto.

## Otwarte
- **Schodkowa krawędź skarpy przy brzegu** (kamera `bv_bank_n`, pierwszy plan): teren przycięty do profilu brzegu
  ADR 0210 schodzi po węzłach 1 m wzdłuż skośnego brzegu; poprawka r3 (zatoki po przekątnej) tego nie usunęła —
  przyczyna jest w `carve` (cap brzegu), nie w szumie. Do osobnej poprawki (wygładzenie pasa brzegu).
- Kępy trawy na stromych skarpach stoją pochylone razem ze skarpą (stopy karty idą po przekroju) — z boku część
  wygląda na przewrócone; karty na skarpach powinny mieć stopę poziomą.
- Bloki lasu (HLOD) w dali nadal ciemne i zwarte; poprawa sylwetki umiarkowana.
- `water_reeds.png` kafla wspólnej biblioteki (C nie ma wody) i `verge_tufts.png` (zacommitowany w
  `art-source/world/textures/`) — po przebudowie C sprawdzić, czy plik się nie zmienił.
- Przebudowa trzech kafli czekała łącznie ok. 2,5 h na pulę `heavy` (regeneracja fali 6) — patrz STATUS.md.
- Dz.U. 2019 poz. 2311 zał. 4 nieprzeczytany: rozstaw U-1a na łukach, odsunięcie od krawędzi korony i wymiary słupka
  to `WORKING_VALUE`; brak pikietażu (km / hm) na słupku i słupków U-1b na barierach.
- Wiatr trzciny / trawy, pałka i kałuże w rowach, wilgotność łąk z NMT i wierzby (krytyk 3.4), tło dali lasu
  (`far_field.py`, krytyk 3.6) — nie zrobione.
- `shoulder_gravel` i albedo dna to `WORKING_VALUE` bez pomiaru ze zdjęcia; `_BaseColor` / `_BedColor` wody są
  wartościami właściwości Color (kodowanie sRGB), nie liniowym albedo, jak sugerują komentarze ADR 0210 / 0213.
- Po scaleniu: przebudować wszystkie kafle z drogami zamiejskimi (trawa, U-1a, rów w terenie, płaszcz lasu) i z wodą;
  `visual-critic` do zlecenia przez lidera (agent nie tworzy subagentów).
