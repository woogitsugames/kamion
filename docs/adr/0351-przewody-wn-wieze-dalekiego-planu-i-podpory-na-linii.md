# ADR 0351 — Przewody WN: wieże dalekiego planu tylko na liniach WN i zawsze z przewodami; zmapowane wieże jako podpory w kaflu

Status: Proposed, 2026-11-26 (agent hv-wires-s24). Numer do potwierdzenia przez lidera.
Powiązane: ADR 0022 (warstwa `wires`, Kamion/World Wire), 0085 (daleki plan), 0127 (zawieszenie 6 faz + odgromowy pod
ramionami `props.pylon`), 0162 (słup SN), 0318 / drive-review-s24 #15 (ażurowa kratownica dalekiego planu),
farfield-low-s24 (≤ 2 submesze na sektor). Zgłoszenie: `artifacts/critic-s24-wave11/CRITIC.md` pkt 1 (P0), zrzut
`artifacts/regen-wave-11-s24/vqa/dk65-07/High-clear/owner02-seam-n-cab.png` (6 kratownic bez przewodów, śnieżnobiałe).

## Kontekst — przyczyna
1. **Zrzut dk65-07 to daleki plan, nie kafel.** Kamera `owner02_seam_n_cab` stoi w (533, 1080) — 56 m za północnym szwem;
   dk65-08 nie jest wczytany, widać `FarField_far_north` kafla dk65-07. W kaflu dk65-07 nie ma żadnej linii WN (BDOT10k
   OT_SULN_L: 13 linii SN, 0 WN; brak OSM power=tower).
2. **`far_field.py` stawiał kratownicę 27 m co 210 m wzdłuż KAŻDEJ linii pierścienia** (BDOT10k OT_SULN_L dowolnego napięcia
   + OSM power=line / minor_line, bez rozróżnienia) i rysował każdy BDOT10k „słup energetyczny” (w większości betonowe
   słupy SN) jako kratownicę 26 m — **bez żadnego przewodu** (generator dalekiego planu nie miał przewodów w ogóle). Linia na
   zrzucie to linia SN z dk65-08. dk65-07: 307 kratownic, 1 linia WN w pierścieniu (2,7 km na wschód). Wszystkie 54 kafle
   z danymi: **17 110 kratownic bez przewodów** w dalekim planie.
3. **Kolor**: `COL_PYLON_STEEL` (0,27; 0,285; 0,30) liniowo × `plaster_white` materiału `far_field_buildings` — ponad
   2× jaśniej niż `pylon_steel` kafla (0,115–0,12); w słońcu biel.
4. **W kaflu (pokrewny błąd)**: `furniture.power_supports` brał za podpory tylko wierzchołki BDOT i równe podziały
   odcinków (≤ 350 m), przyciągając je do zmapowanej wieży w promieniu 15 m. Wieża OSM między wierzchołkami (nie przy
   punkcie podziału) zostawała obok przewodu, a reguła stawiała drugą wieżę kilkadziesiąt metrów dalej: **31 z 298**
   zmapowanych wież w 54 kaflach bez przęsła (kleeberga 5, monki-07 5, monki-05 4, maczka 4, …). Do tego BDOT
   „słup energetyczny” stojący NA linii WN (wieża) był słupem SN (bojary, monki-05 ×2).

## Decyzja
**Kafel (`streetscape/furniture.py`)**
- `power_supports`: każda zmapowana podpora klasy linii (WN → `pylon`, SN → `power_pole`) w promieniu `SUPPORT_SNAP_M`
  od linii jest podporą w miejscu swojego rzutu; wierzchołki/końce jak dotąd (przyciąganie do zmapowanej, inaczej reguła);
  dzielone są tylko luki między kolejnymi podporami > `SPAN_MAX_M`. Wynik po kolei wzdłuż linii; raport `mapped_supports`.
- `points()`: BDOT „słup energetyczny” w promieniu 15 m od linii BDOT WN → `pylon`.
- Szew bez zmian (spójny przy obu wczytanych kaflach): koniec linii przyciętej do bbox ma podporę na krawędzi w obu kaflach.

**Daleki plan (`streetscape/far_field.py`, cache GIS `far-field-gis-cache/14`)**
- Linie z klasą napięcia: BDOT `rodzaj … wysokiego napięcia`; OSM `voltage ≥ 60 kV` (minor_line = nie WN; power=line bez
  `voltage` = WN tylko, gdy stoją na niej ≥ 2 zmapowane wieże). Linia OSM pokrywająca się z linią BDOT WN (≥ 70 % próbek
  w 25 m) jest pomijana. Linie WN przycinane do samej krawędzi kafla (nie do marginesu 8 m).
- `power_plan()`: podpory jak w kaflu (zmapowane wieże na linii, wierzchołki, luki ≤ 350 m); wierzchołek reguły < 60 m od
  zmapowanej sąsiedniej wieży łączy się z nią (`RULE_MERGE_M`); koniec na krawędzi kafla = **podpora szwu** (wieża kafla,
  bez siatki w dalekim planie, przewody od jej ramion). Wieże poza liniami WN (słupy SN) nie są rysowane; maszty
  telekomunikacyjne / wieże ciśnień rysowane bez trawers. Raport `power_plan` w `far_field_qa.json`.
- Wieża = układ `props.pylon` (3 poziomy trawers 20/24/28 m z 32, ramię 4,3 m), skrócona perspektywą jak dotąd.
- **Przewody**: przęsło między podporami, krzywa łańcuchowa `furniture.catenary_span` (zwis 1,5 % rozpiętości), pod
  końcami ramion obu wież (6 faz + odgromowy na High, dolna para na Low), jako nieprzezroczyste wstęgi w submeszu 0
  (`far_field_buildings`) — **0 nowych draw calli, kontrakt ≤ 2 submesze/sektor zachowany, bez zmian w C#**. Szerokość:
  0,6 px widoku 1080 px / 60° w odległości (od krawędzi kafla + 60 m), nie mniej niż 2× `WIRE_HALF_W`; kolor 0,05
  (0,11 jak materiał `wire` dawał w słońcu jasnoszare wstęgi na tle nieba, VQA r1) (WORKING_VALUE).
- **Linie SN** (BDOT `… średniego napięcia`, OSM power=line 1–60 kV) do `MV_FAR_MAX_M` = 600 m od kafla, tylko High:
  betonowe słupy `props.power_pole` (12 m, trawersa ocynk), podpory jak w kaflu (zmapowane BDOT „słup energetyczny”
  w 10 m, przęsła ≤ 80 m, łączenie z regułą < 25 m), 3 przewody na H − 0,3 m (−0,8/0/+0,8 m), szew = słup kafla.
  Kolor betonu 0,16 (0,36 renderował się biało, VQA r1). Dalej niż 600 m słup 12 m ma < 1 px.
- **Kolor**: ocynk `COL_PYLON_GALV` (0,150; 0,155; 0,160) z rozrzutem na wieżę ±12 % jasności i ±3 % ciepły/zimny (kolor
  wierzchołków, bez materiału i draw calla). WORKING_VALUE, oceniane na klatkach visual-QA.

## Liczby (audyt `tools/worldgen/qa/hv_wires_audit.py`, 54 kafle)
| | przed | po |
|---|---|---|
| zmapowane wieże w kaflu bez przęsła | 31 / 298 | 0 / 308 (10 słupów BDOT na liniach WN to teraz wieże) |
| słupy SN w kaflu bez przęsła | 34 / 60 | 24 / 50 (pozostałe: brak linii w BDOT; bez danych) |
| kratownice dalekiego planu bez przewodów | 17 110 / 17 110 | 0 (po przebudowie dalekiego planu kafla) |
| dk65-07 daleki plan | 307 kratownic, 0 przęseł; High 146 898 / Low 15 816 tri | 30 wież WN + 5 masztów, 29 przęseł WN; 101 słupów SN, 99 przęseł SN, 7 szwów SN; High 99 214 / Low 10 852 tri |
| knyszyn-w daleki plan | 328 kratownic, 0 przęseł; High 104 569 / Low 11 830 tri | 44 wieże + 4 maszty, 44 przęsła, 2 szwy WN (= podpory kafla E 737,9 / 792,2); 246 słupów SN, 245 przęseł; High 63 921 / Low 6 934 tri |

## Konsekwencje
- Przebudowa: `far_field.py --region <id>` (bez build_world; ~3 min/kafel — ekstrakcja GIS od nowa przez schemat 13) dla
  wszystkich kafli; zmiana w kaflu (podpory) wymaga `build_world.py` kafli z liniami WN: bialystok-bojary, -industrial-c,
  -kleeberga, -maczka, -porosly, dk65-11, dk65-monki-03/-05/-07, knyszyn, monki-e, s8-03/-04/-05 (wieże nie były
  podporami) oraz kafle z wieżami w liczbie zmienionej (lista w `artifacts/hv-wires-s24/audit_after_tile.json`).
- Zrzut krytyka (dk65-07 `owner02_seam_n_cab`) pokazuje teraz linię SN dk65-08 jako słupy betonowe z przewodami.
- Draw calle: 0 nowych (wszystko w submeszu 0 sektora); trójkąty dalekiego planu spadają (mniej kratownic).
- Test `test_far_field.py` (`fc["pylons"] >= 150` dla bialystok-industrial-c) zmieni znaczenie po przebudowie C (tylko WN +
  maszty) — do przeliczenia przy przebudowie.
- Wstęgi przewodów nie mają zanikania `_KamionWireFade` ani pikselowej podłogi shadera Wire; przy obu wczytanych kaflach
  sektor jest ukryty i przewody kafla przejmują rolę.

## Dopisek fala 12 (regen-wave-12-s24): próg pylonów i budżet Low C
- `fc["pylons"]` liczy po zmianie tylko wieże WN i maszty. bialystok-industrial-c: 406 (wieża co 210 m na każdej linii) -> 329.
  Próg w `tests/gis/test_far_field.py` podniesiony ze 150 do 250 (dolna granica poczytalności, zmierzone 329). Pozostałe kafle
  mają od 0 (tykocin, wieś bez WN) do 384 (dk8-wasilkow-01).
- Pierwsza przebudowa C dała Low 32 351 tri (> 30 000, test budżetu; przed 0351: 29 139). Przyczyna: ramiona wieży (3 poziomy x 3
  wstęgi) i przęsła Low. Poprawka generatora (limit nie podniesiony), tylko poziom Low: ramiona tylko na poziomie niosącym parę
  przewodów (bez zmiany High), 2 panele kratownicy zamiast 3, przęsła Low `ceil(L/90)` w zakresie 3..4 segmentów (było `L/40`, 3..8).
  C Low = 29 295 tri (zapas 2,3 %). High bez zmian.
- Wszystkie 54 kafle przebudowane `far_field.py` po tej zmianie. Low > 30 000 poza C (test 30k dotyczy tylko C) mają
  bojary 38 502 (było 35 752 przed 0351), mickiewicza 33 843 (32 299), krywlany 31 755 (33 257), maczka 30 530 (29 996),
  wygoda — patrz raport fali 12. WORKING_VALUE, bez pomiaru na urządzeniu.

## Dopisek (2026-11-27, `neon-hvfar-s24`): sylwetki „A”/„Y” wież WN, LOD gęstości i zanikanie przewodów dalekiego planu
- **Kontekst (krytyk build #10, `artifacts/critic-s24-build10/CRITIC.md`, zrzut `t0180` + klatki `hv0351-*`)**: kratownice i
  7 nieprzezroczystych wstęg przewodów przy horyzoncie zlewały się w szare kratkowane pasmo („jak siatka, nie linia WN”).
  Pomiar w generatorze wykazał trzy przyczyny:
  1. Kompresja radialna (`foreshorten_dist`) zgniatała sąsiednie wieże na 2–3,6 km do **1,6–15 m** odstępu (`knyszyn-w`
     1,6 m przy d=3,5 km; `dk65-07` 10,2 m przy d=2,4 km), przy rozpiętości ramion 5,6 m (`scale = max(s_h, 0.65)`).
  2. Każda wieża High miała 222 trójkąty gęstych rurek 3-bocznych w tym 12 grubych pierścieni poziomych i płaską górę.
  3. 7 nieprzezroczystych wstęg przewodów (`FAR_WIRE_PX_FRAC = 0.6`, półszerokość do ~0,22 m = 44 cm na horyzoncie) bez
     zanikania z odległością + 245 przęseł SN do 600 m tworzyło ciemne poziome pasmo na niebie i nad koronami.
- **Decyzja (0 nowych draw calli, ≤ 2 podsiatki/sektor, bez nowych materiałów ani keywordów shadera; parametry `WORKING_VALUE`):**
  1. **LOD gęstości w przestrzeni skróconej** (`far_field._select_far_hv`, `_select_far_mv`): przejście po łańcuchach od
     podpór szwu na zewnątrz; minimalny odstęp w przestrzeni skróconej `_hv_min_eff_sep` 45→140 m (High, `HIGH_HV_MAX_D_M`
     3400 m) / 45→170 m (Low, 2000 m), łączący sąsiednie zachowane podpory w przęsła bez rozrywania linii. Słupy SN do
     `MV_FAR_MAX_M = 380 m` z odstępem ≥ 28 m. Raport `power_plan()` zachowuje pełną topologię GIS.
  2. **Czytelna pionowa sylweta „A”/„Y”** (`far_field._add_pylon`): usunięto pierścienie poziome, proporcjonalna skala
     `_pylon_scale = max(s_h, 0.38)`, stożkowy korpus „A” zbieżny do szpica (jak `props.pylon_half_width`). Do 800 m (High):
     otwarta rama 3D „A” (150 tri). Powyżej 800 m (High) i na Low: otwarta wstęgowa sylweta „A”/„Y” zwrócona ku kaflowi z
     wyraźnym prześwitem nieba wewnątrz „A” (2 poziomy ramion „Y” od 1500 m i na Low; **22–28 tri/wieża** zamiast 222).
  3. **Cieńsze przewody z LOD żył i zanikaniem w `WorldSurface.shader`**: `FAR_WIRE_PX_FRAC` 0,60→0,42 HV (limit półszerokości
     0,095 m) i 0,26 MV (limit 0,042 m), zwężanie z odległością; liczba żył High 7 (≤ 450 m — ciągłość szwu) → 3 główne
     (450–1050 m) → 0 (> 1050 m, gdzie przewód 24 mm ma < 0,03 px); Low do 900 m. W `TEXCOORD_1 = (fadeStart/100,
     -(100 + fadeEnd/100))` przy `COLOR_0.a == 0` (rozłączne z elewacjami i flagą skyline `-16`): `WorldSurface.shader`
     (`_FAR_FACADE`) płynnie wtapia kontrast przewodów w mgłę/perspektywę powietrzną (`KamionFogTauExtra`, 420–1350 m WN,
     200–480 m SN) jak `Kamion/World Wire`, a pod `_FAR_RING_CLIP` (ADR 0354, ForwardLit + DepthOnly) odrzuca piksele po
     całkowitym zaniku.
- **Liczby przed → po (prototyp `knyszyn-w` i `dk65-07`):**
  | Region / tier | Wieże WN rysowane (min. odstęp skrócony) | Trójkąty sieci WN+SN | Trójkąty całego dalekiego planu | Podsiatki/sektor |
  |---|---|---|---|---|
  | `knyszyn-w` High | 44 (1,6 m) → **27 (58,1 m)** | 25 592 → **8 964** (−65,0 %) | 63 921 → **46 753** (−26,9 %) | 2 → 2 (+0 DC) |
  | `knyszyn-w` Low | 44 (1,6 m) → **23 (58,1 m)** | 1 238 → **792** (−36,0 %) | 6 216 → **5 746** (−7,6 %) | 2 → 2 (+0 DC) |
  | `dk65-07` High | 30 (10,2 m) → **14 (101,2 m)** | 14 104 → **2 004** (−85,8 %) | 99 214 → **86 322** (−13,0 %) | 2 → 2 (+0 DC) |
  | `dk65-07` Low | 30 (10,2 m) → **4 (152,4 m)** | 320 → **96** (−70,0 %) | 10 648 → **10 392** (−2,4 %) | 2 → 2 (+0 DC) |
- **Dowody**: `artifacts/neon-hvfar-s24/` (High PC 1920×1080 clear + overcast, `-Neighbours auto` i `none`, cropy 1:1 `sbs/`;
  w `-Neighbours auto` dla `knyszyn-w` odświeżono też lokalnie krawędzie sąsiadów `knyszyn` i `dk65-monki-01`, aby widoczny
  za nimi horyzont używał nowego generatora). Pomiary `stats.txt` (High clear): `knyszyn-w` `hv0351-seam-n` (`none`)
  `drawsEst` 23 → 23 (+0 DC), `trisExact` 234 588 → **218 932**; `hv0351-seam-n` (`auto`) `drawsEst` 142 → 132,
  `trisExact` 671 282 → **585 041**; `dk65-07` `hv0351-far-e` (`auto`) `drawsEst` 131 → 131 (+0 DC), `trisExact`
  671 927 → **660 139**; `owner02-seam-n-cab` (`none`) `drawsEst` 5 → 5 (+0 DC), `trisExact` 50 731 → **41 981**.
  Testy: `test_hv_wires_0351`, `test_far_field*`, budżetowe (`0221`, `0238`, `v31`, `hero_bridge`) — **167 pass, 3 skip, 0 fail**.
  Przebudowa pozostałych kafli dla lidera: `far_field.py --region <id>` + `WorldEdgeBuilder.RebuildEdgeBatch` (Win64).
