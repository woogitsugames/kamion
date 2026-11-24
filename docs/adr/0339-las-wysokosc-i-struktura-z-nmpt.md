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
Ustalenie przy okazji (przekroje `artifacts/forest-height-s24/hlod_profile_*.png`): reguła klasowa skaluje quad ściany
medianą wysokości WSZYSTKICH roślin wypieczonego obrazu (`h_median_m` 10,9–13,9 m razem z podszytem), więc linia koron
ściany lasu liściastego stoi ok. 1,5× wyżej niż jego drzewa (drzewa 5–19 m, ściana do 30–40 m) — stąd „ciemne pudła”
w dali i skok wysokości przy przełączeniu instancje → HLOD. Kafle z modelem koron tego błędu nie mają.
- **Czasza:** wierzchołki siatki 12 m na 0,80 × wysokości górującej z modelu; bez sztucznego opadu skraju z 0324 i bez
  trójkątów bardziej stromych niż ~32° (gładka czasza o jednej normalnej, widziana z drogi pod kątem ślizgowym, lśni
  niebem — jasne odłamki nad ścianą; runda r2).
- **Ściany zewnętrzne i druga ściana:** quad tak wysoki, żeby wierzchołki koron obrazu (p90 najwyższego
  nieprzezroczystego teksela w kolumnie: 0,888 iglasty / 0,833 mieszany / 0,766 liściasty — zmierzone, test) stały na
  zmierzonej wysokości górującej w punkcie ściany; druga ściana (6 m w głąb) z pomiaru na własnej linii; szum wierzchu
  0,94–1,05 + ± 6 % na punkt; obraz skalowany tak samo wzdłuż ściany (wyższy drzewostan = większe drzewa, młodnik =
  małe; bez rozciągania pni w tyczki).
- **Żebra (nowe):** ściany alfa tego samego obrazu co 16 m w obu kierunkach (linie siatki metrów kafla, meandrujące
  ± 4,5 m, ciągłe między komórkami), wierzch z pomiaru. Każdy uskok wysokości drzewostanu ma poszarpaną linię koron —
  bez nich wyższa część drzewostanu wystawała nad niższą jako gładkie zielone wzgórze (runda r1). Ten sam prymityw i
  materiał co ściany (0 dodatkowych draw calli).
- Gdzie model nie ma koron (< 3 m: dziura, komórka poza maską) — drzewa wygenerowane wokół punktu w tej samej skali,
  a gdy żadnego w 15 m: niska ściana (reguła klasowa brała tam medianę całego kafla = 40 m szpilka w luce).
- `KAMION_FOREST_CHM=0` — przełącznik ablacji (reguła klasowa na kaflu z modelem; tylko do porównań).

## Zmierzone (prototyp: `dk65-04`, `dk65-05` — Puszcza Knyszyńska, `dw671-tykocin-03`)

Pełne tabele: `artifacts/forest-height-s24/numbers.txt` (generuje `tools/summary.py`); runda końcowa r5.

| Kafel | wierzch koron modelu p10 / p50 / p90 / p99 [m] | luki [m²] | drzewa okapu: w lukach / przerzedzone / młode / dojrzałe | wysokość drzew okapu p10 / p50 / p90 / max [m] |
|---|---|---|---|---|
| `dk65-04` | 6,8 / 14,5 / 26,5 / 28,8 | 2 390 | 71 / 326 / 145 / 4 279 | 10,0 / 19,1 / 26,1 / 29,6 |
| `dk65-05` | 10,2 / 22,2 / 27,5 / 30,8 | 41 857 | 1 471 / 2 817 / 1 864 / 52 238 | 13,2 / 21,8 / 26,8 / 35,1 |
| `dw671-tykocin-03` | 8,0 / 18,5 / 24,0 / 27,2 | 300 | 17 / 332 / 81 / 4 741 | 13,0 / 19,2 / 23,5 / 33,2 |

Reguła klasowa dawała na każdym kaflu p10 / p50 / p90 ≈ 11 / 17 / 23 m (max 25), a w Tykocinie 9 / 13 / 17 m (`zagajnik`
× 0,7) wobec zmierzonych 13 / 19 / 23,5 m. Pozostałe 21 kafli trasy: mediana wierzchu koron 12–23,5 m, p99 27–33 m.

**Budżet — czysta ablacja `dk65-05`** (ten sam kod, `KAMION_FOREST_CHM=0` → model koron; szacunek klatki generatora):

| | reguła klasowa | model koron | Δ |
|---|---|---|---|
| instancje drzew / krzewów / runa | 104 776 | 101 899 | −2 877 (−2,7 %) |
| HLOD lasu, trójkąty w kaflu | 63 085 | 82 757 | +19 672 (+31,2 %) |
| najgorsza klatka High (`route_s0472`) | 1 562 135 | 1 525 548 | −36 587 |
| Δ High po 22 kamerach: min / max / suma | | | −236 172 / +22 482 / −636 464 |
| najgorsza klatka Low | 472 434 | 467 417 | −5 017 |
| Δ Low po 22 kamerach: min / max / suma | | | −58 928 / +8 639 / −78 238 |

Kamery lasu w edytorze (High, 12 kamer × 2 światła, `stats.txt`): trójkąty −0,2 … −1,6 %, draws ± 1 — ale „przed” to
starszy build main (różnice także spoza tego ADR). Region C (2 M na `stretch_04`): **nie przebudowany**; przebieg na
sucho bez dróg i budynków (`dry_run_bialystok-industrial-c.json`, wersja sprzed żeber): mediana koron 14,6 → 22,9 m,
drzew −5,4 %, HLOD +9 % (z żebrami spodziewane ok. +30–40 % z 92 tys. trójkątów w kaflu) — margines C do sprawdzenia
`build_world.py` przed włączeniem (produkt czeka w `artifacts/forest-height-s24/candidate-c/`).

## Ocena wizualna
Rundy: r0 = przed (derived = kopia main), r1 = wysokości z modelu (dk65-04: wyższa część drzewostanu jako gładkie
wzgórze czaszy), r2 = żebra (dk65-05: jasne odłamki stromej czaszy, pnie rozciągnięte w tyczki), r3 = bez stromych
trójkątów, obraz w proporcji, jitter wierzchu (tykocin-03: ostrza czaszy na obrysie), r5 = czasza odsunięta od obrysu.
Pary przed | po: `artifacts/forest-height-s24/pairs-r5-after/` (24), przekroje HLOD `hlod_profile_*.png`, mapy modelu
i kamer `cams/*_map.png`.
`visual-critic` (r5, dk65-05 + tykocin-03, 16 par): **PASS dla samej zmiany** („po” lepsze w 5 z 8 par z lasem, gorszej
brak, bez P0), las jako całość nadal poniżej `docs/06`. Sylweta i zróżnicowanie wysokości 3 → 5 / 10. Wskazane wady:
- nowe P1: z lotu ptaka jasnozielone skupiska brzozy / młodych liściastych w borze (`dk65-05 fh_air`) — płaty brzozy i
  prototyp `birchyoung` za jasne i za liczne; miejscami linia koron HLOD płaska na długim odcinku (okno 3 × 3 komórki
  wygładza); rozmyte korony drzew przeskalowanych do 28–30 m (`fh_cab_approach`) — do potwierdzenia w powiększeniu;
- nowe P2: skraj boru przy drodze bardziej ażurowy (wyższe pnie, podszyt bez zmian);
- istniejące, nietknięte: pionowo ucięte boki bloków lasu, ciemna równa wstęga lasu na horyzoncie z kabiny (tło dali),
  płaskie turkusowe karty świerka, las w pochmurny dzień jako płaska plama.

## Kafle do przebudowy po scaleniu
Model koron jest w gicie dla 24 kafli trasy Białystok – Knyszyn – Tykocin; każdy z nich zmienia się przy następnej
przebudowie (`build_world.py` → `import-region.ps1`): `dk65-01` … `dk65-11`, `knyszyn`, `knyszyn-s`, `knyszyn-w`,
`dw671-tykocin-01` … `dw671-tykocin-09`, `tykocin`. Prototypy (`dk65-04`, `dk65-05`, `dw671-tykocin-03`) są zbudowane w
kopii `derived` worktree (r5) — do skopiowania albo przebudowy w main. Bez modelu (bez zmian): kafle `bialystok-*`,
`dk65-monki-*`, `monki*`, `dk8-*`, `s8-*`, `dw671-jasionowka-01`, `dw671-jezewo-*` — dociągnięcie:
`forest_chm.py --region <id>` (~2–3 min / kafel), C dopiero po sprawdzeniu marginesu.

## Otwarte / WORKING_VALUE
- Następna runda wg krytyka: (1) udział i kolor brzozy / `birchyoung` w borze (płaty, młodniki sosnowe ciemne),
  (2) linia koron HLOD z pojedynczej komórki modelu zamiast okna 3 × 3 + zachowane lokalne maksima, (3) okrajek z
  gradientu wysokości modelu przy obrysie (pionowe boki bloków), (4) wariant prototypu zamiast skali > ~1,3,
  (5) rytm koron i perspektywa powietrzna pasa lasu na horyzoncie.
- Progi (3 m, 9 m, 300 m², 0,72), klasy biosocjalne, udziały płatów, próg obniżenia — `WORKING_VALUE`.
- Gatunek panujący i wiek z Banku Danych o Lasach (jak dla Dojlid w 0187) — nieużyte: licencja BDL ma
  `LEGAL_REVIEW_REQUIRED` (cz. V lit. b regulaminu); kategoria BDOT bywa sprzeczna z BDL (M68: „liściasty” = 7SO).
- Tło dali (`far_field`, pierścień do 4,2 km poza kaflem) nadal z reguły 0330 (wysokość klasy × 0,86–1,12 na
  drzewostan): model koron jest tylko dla bbox kafla. Rozszerzenie: zgrubny CHM pierścienia (WCS 10 m + NMT WCS).
- Tekstura ściany HLOD jest wypiekana z drzew reguły klasowej (korony sosny w obrazie są brązowawe, wierzch obrazu
  równy ± 9 %); ponowny wypiek z większą zmiennością wysokości i poprawionym kolorem igliwia — osobne zadanie.
- `tree_stand` (ogrody działkowe) i drzewa poza `OT_PTLZ_A` nie korzystają z modelu (maska).
- Data nalotu NMPT `UNVERIFIED`; zręby młodsze niż nalot będą w grze lasem (i odwrotnie).

---

## Dopisek — runda 2 wg krytyka r5 (agent world-builder, gałąź `forest2-s24`, 2026-11-24)

Zakres: cztery uwagi P1 z „Oceny wizualnej” powyżej. Wszystko nadal tylko na kaflach z modelem koron; kafel bez
`forest_chm.png` generuje się bajt w bajt jak dotąd (`test_no_model_no_change`). Stałe — `WORKING_VALUE`.
`KAMION_FOREST_CHM_R2=0` — przełącznik ablacji (runda 1 na tym samym kodzie; tylko do porównań i budżetu).

### Ustalenie (pomiar, `artifacts/forest2-s24/base_dk65-05.json`)
„Jasna brzoza w borze” i „rozmyte korony” to jedna przyczyna. Prototypy liściaste mają 12–15 m (`trees_meta.json`
`href_m`: brzoza 13,4–15,0, olsza 12,5–14,0, lipa 12,6–14,4, klon 11,8–12,9; sosna 17,9–20,4, świerk 21,0–21,9), a runda 1
stawiała je na zmierzonej wysokości górującej: w borze `dk65-05` 67 % brzóz, 82 % olsz i 76 % klonów okapu miało skalę
> 1,45 (mediana 1,57–1,76, max 2,5–2,7). Korona w skali 2 zajmuje 4 × większą powierzchnię i ma karty liści 2 × większe —
19 % drzew liściastych okapu boru (reguła klasowa: 10 % brzozy + 6 % olszy / klonu / lipy, do tego 45 % sosen w płatach
brzozy) przykrywało z lotu ptaka dużą część koron sosen. Tekstura liścia brzozy jest przy tym 1,45 × jaśniejsza od
lipy i 1,85 × od igieł sosny (zieleń liniowo 0,120 / 0,083 / 0,065, średnia pokrytych tekseli).

### 1. Brzoza w borze (`vegetation.chm_species`, podszyt, płaszcz)
- **Wnętrze drzewostanu „iglasty”** (dalej niż `CHM_EDGE_ZONE_M` = 30 m od obrysu lasu i od drogi / placu / budynku):
  poza płatem brzozy zostaje 12 % brzóz reguły klasowej, olsza / klon / lipa → sosna (olsza zostaje w obniżeniach
  terenu); w płacie brzozy 20 % sosen staje się brzozą (było 45 %). W strefie skraju brzoza jak w rundzie 1 (kępy),
  klon / lipa 30 %. Przebieg na sucho `dk65-05` (bez dróg): wnętrze — brzoza 4,4 %, olsza 3,0 %, klon / lipa 0;
  strefa skraju — brzoza 10,8 %, olsza 2,9 %, klon + lipa 1,1 %.
- **Podszyt wnętrza boru:** 70 % siewek brzozy → odnowienie świerka / leszczyna (te same pozycje, skrót pozycji).
- **Płaszcz boru:** brzoza i brzoza młoda tylko tam, gdzie szum (okres 60 m) > 0,5 — kępy zamiast równej jasnej lamówki;
  poza nimi sosna młoda / sosna.
- Drzewostany „mieszany” i „liściasty” — bez zmian składu. Uprawy i młodniki boru są przez to prawie w całości
  `pineyoung` (ciemne).
- **Kolor:** `trees_meta.json` → `foliage_tint` (`make_trees.py` `FOLIAGE_TINT`): mnożnik liniowy albedo liści i
  impostorów gatunku, stosowany przez `InstanceImporter.FoliageTint` przy imporcie (bez ponownego wypieku). Brzoza i
  brzoza młoda (0,74; 0,80; 0,85): zieleń 0,120 → 0,096 (lipa 0,083), mniej żółta. Dotyczy każdej brzozy w grze (także
  miejskich) po następnym imporcie kafla. Tekstury ściany HLOD i czaszy (wypiek) — bez zmian.

### 2. Skala prototypu (`vegetation.chm_fit`, `chm_cap_m`)
- Żadne drzewo okapu nie jest rysowane w skali > `CHM_MAX_SCALE` = 1,45 × `href_m` swojego wariantu. Drzewo, którego
  wylosowany wariant by ją przekroczył, bierze wariant, który się mieści (skrót pozycji; świerk: formy drzewostanowe
  0 / 1 i forma otwarta 2 osobno); gdy żaden — najwyższy wariant na granicy. Granice: brzoza 21,8 m, olsza 20,2,
  lipa 20,9, klon 18,7, sosna 29,6, świerk 30,9 (31,7 forma otwarta).
- Drzewostan wyższy, niż gatunek da się narysować (wysokość drzewostanu `Chm.stand` > granica): wysokości × (granica /
  wysokość drzewostanu) — zostaje struktura (górujące / współpanujące / opanowane), nie linijka koron uciętych na
  granicy. W borze brzoza i olsza stoją więc pod okapem sosny jako piętro współpanujące (zgodnie z naturą);
  **las liściasty wyższy niż ~22 m jest niższy niż w pomiarze** (`dw671-tykocin-03`: p50 19,2 → 17,2 m, p90 23,5 →
  20,0 m, max 33,2 → 21,8 m) — do czasu wysokich wariantów leśnych w bibliotece (otwarte).
- HLOD skaluje linię koron drzewostanu danej kategorii tak samo (ściany, żebra, czasza), więc przy przełączeniu
  instancje ↔ HLOD nie ma skoku.

### 3. Linia koron HLOD (`forest_hlod.build`, `Chm.cell_top`)
- Wierzch ścian i żeber: wierzch koron **pojedynczej komórki 4 m** pod punktem (lokalne maksima jak w pomiarze), nie
  niżej niż `CHM_LINE_FLOOR` = 0,70 × wysokość górująca (dołek między koronami, nie dziura do ziemi, która
  spłaszczyłaby obraz). Runda 1 brała maksimum z okna 12 m: każde wysokie drzewo dawało 12-metrowy płaskowyż.
- Czasza na 0,64 × wysokości górującej (było 0,80) — pod najniższymi koronami żeber.
- **Okrajek z gradientu modelu:** punkt ściany ZEWNĘTRZNEJ schodzi za koronami do `CHM_EDGE_FLOOR` = 0,45 × wysokości
  drzewostanu za nim; druga ściana 6 m w głąb trzyma 0,70. Gdzie pomiar ma niższe drzewa skraju, las kończy się
  stopniem; gdzie sosny stoją do samego obrysu — ścianą, jak w terenie.

### 4. Boki bloków i ton (`forest_hlod.build`)
- **Nieregularny obrys:** punkty ściany zewnętrznej przesunięte w głąb drzewostanu o 0–3,5 m (szum położenia, okres
  22 m; 0 na granicy komórki, żeby sąsiad kontynuował linię); wysokość mierzona tam, gdzie ściana stoi.
- **Narożniki:** zejście przez 3 punkty po każdej stronie (0,50 / 0,66 / 0,82 / 0,93; było 0,62 i 2 punkty).
- **Przejście tonalne:** normalna dolnego rzędu ściany prawie pozioma (z = 0,25), górnego odchylona ku niebu
  (z = 1,6 przy poziomej 1): korony biorą światło nieba i słońca, pnie zostają w cieniu drzewostanu. Było jedno
  odchylenie 27° na całej wysokości = jeden ciemny ton od pni po wierzchołki.
- **Poza zakresem tej rundy:** pas lasu w tle dali (`far_field`, pierścień 1–4 km poza kaflem, ADR 0330) — nie ma tam
  modelu koron; bez zmian. Ściana HLOD nadal korzysta z tego samego wypieku obrazu (ciemne, brązowawe korony sosny).

### Zmierzone (prototyp, runda r1 tej gałęzi; `artifacts/forest2-s24/numbers.txt`)
„Przed” = runda 1 jak scalona (QA i rendery r5 poprzednika z 2026-11-24, `artifacts/forest-height-s24/r5-after*`).

| Kafel | instancje roślin | brzoza + brzoza młoda | sosna + świerk + sosna młoda | HLOD lasu, trójkąty | cięcia skali | najgorsza klatka High (szac. generatora) | najgorsza klatka Low |
|---|---|---|---|---|---|---|---|
| `dk65-05` | 101 899 → 101 899 | 14 395 → 9 963 (−31 %) | 44 134 → 49 896 | 82 757 → 82 919 (+0,2 %) | 515 | 1 525 548 → 1 525 761 (+213) | 467 417 → 467 651 (+234) |
| `dk65-04` | 14 880 → 14 880 | 2 772 → 2 540 | 4 003 → 4 347 | 11 650 → 11 681 (+0,3 %) | 30 | 1 331 698 → 1 332 394 (+696) | 460 228 → 459 471 (−757) |
| `dw671-tykocin-03` | 13 201 → 13 201 | 3 885 → 3 885 | 705 → 706 | 11 272 → 11 272 | 114 | 1 319 129 → 1 318 800 (−329) | 398 470 → 398 357 (−113) |

Liczba instancji, komórek HLOD i draw calli bez zmian; trójkąty HLOD + 0–0,3 % (inne trójkąty czaszy odpadają na
teście nachylenia). Kamery lasu w edytorze: patrz `numbers.txt`.
