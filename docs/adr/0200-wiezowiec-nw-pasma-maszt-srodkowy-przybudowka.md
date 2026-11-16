# ADR 0200 — wieżowiec Andersa 38: ściana NW w pasmach (6 grup okien na kondygnację), maszt środkowy i maszty końca NE, anteny zamiast „kul”, parterowa przybudówka SE

Status: przyjęty (scalony do main 2026-11-14, `6031883c7`; status zaktualizowany 2026-11-16); pierwotnie: PROPOSED (s20, 2026-11-14; do recenzji visual-critic). Gałąź `tower3-0200` (od main a08f9935d).
Źródła zadania: `docs/reports/REVIEW-2026-11-14-s20-mistral-m57.md` §6 („Poprawki dla gry”; recenzent sam obejrzał
kadry — opisy Mistrala M57 mają werdykt FIX i nie były używane), `docs/reports/REVIEW-2026-11-14-s20-0190.md`
(P2-A, P2-B, P2-G). Kontynuacja ADR 0180 / 0190.

## 1. Kontekst (obejrzane i zmierzone w tym zadaniu)

Budynek `bdot:2BE4B431-CA0F-1BF0-E053-CC2BA8C0D140` (11 kondygnacji, 41,81 m). Zdjęcia tylko jako referencja
(`research/_incoming/mistral-p14-office-tower-files/`, poza gitem): Commons `20210328_115626` i `20210328_105711`
(Rakoon, CC0), `20200711_073045` (Rakoon, CC BY 3.0), KartaView 1326673613 (2021-06-23, CC BY-SA, tylko referencja),
kafelek WMS ortofoto GUGiK 80 m (0,1 m / px). Wycinki 3–8× obejrzane przed zmianą.

- **NW** (115626 niemal frontalnie, 073045 skośnie): poziome pasma — na każdej kondygnacji 6 grup po ok. 5–6
  skrzydeł w białych ramach, między grupami filary w kolorze ściany; tynk piaskowy jak szczyt. Ułamki długości od
  końca NE z recenzji M57 (±0,02) zgadzają się z wycinkiem. Gra (ADR 0180 / 0190): haszowana siatka ok. 10 kolumn
  antracytowych okien punktowych — odczyt „siatka” pochodził ze skróconego rzutu ortofoto (korekta w ADR 0180 §2.5).
- Obrys po `footprint_open_m`: ściana NW to **dwie krawędzie** 9,73 + 27,36 m odchylone o 1,5° (wierzchołek 0,25 m
  od cięciwy; `simplify(0.15)` go zostawia) — reguła z `min_len_m: 30` nie trafiłaby w żadną.
- **Dach, ortofoto** (ramy podstaw masztów w kształcie X; pomiar w pikselach względem krawędzi dachu, ±1 m):
  maszt W — 3,3 m wzdłuż szczytu SW od narożnika W, 2,1 m w głąb; maszt środkowy — 0,48 długości krawędzi SE od S,
  2,7 m w głąb; narożnik N — 2,0 m / 3,9 m od krawędzi; narożnik E — 2,7 m / 3,0 m. Bez ramy przy narożniku S.
  Brak nadbudówki (korytka kablowe, niebieskie wentylatory). Przy środku ściany SE niski szary dach z krótkim cieniem.
- **Maszt W, triangulacja**: Mapillary z S — 0,3 szerokości szczytu od narożnika W; 073045 z SW — 0,18. Dla
  azymutów kamer 180° / ok. 220° daje to u ≈ 0,21, odsunięcie ≈ 2,6 m — zgodne z ortofoto. W grze (u 0,30, odsunięcie
  4,5 m) maszt wypadał z południa w 0,45 (recenzja 0190 P2-B). 115626 (0,89 długości NW = ok. 4 m w głąb) się z tym
  nie zgadza — nierozstrzygnięte.
- **Maszt środkowy**: 115626 — w 0,48 długości od NE, wysokość jak maszt W (ok. 2,8 podziałki kondygnacji nad attyką,
  stopa zasłonięta) → 10–12 m (ESTIMATED). Na Mapillary 2020-08-15 z południa w tym miejscu widać tylko krótki maszt
  — konflikt (data / pozycja), UNVERIFIED.
- **Maszt narożnika S 6,5 m** (ADR 0190, z Mapillary 2020): 073045 pokazuje tam tylko anteny na ścianie do linii
  attyki, ortofoto — brak ramy. Konflikt źródeł; zostaje bez zmian.
- Grubość masztu W z antenami w 073045: ok. 1,05 m przy szczycie 16,09 m; sama krata 0,6–0,7 m (ESTIMATED).

## 2. Decyzja

1. **Reguła NW** w override `g3a-office-tower-colour`: `{facing: NW, min_len_m: 30, windows: ribbon, glazing: light,
   sill_m: 1.0, head_m: 2.3, light_m: 0.96, light_sashes: 1, light_mix: [10, 20, 70], far_kind: office, spans:
   [[0.01,0.14],[0.17,0.30],[0.33,0.47],[0.51,0.64],[0.67,0.81],[0.84,0.99]]}` — ułamki WORKING_VALUE (±0,02),
   parapet / nadproże jak SE (WORKING_VALUE), bez linii nadproża (na NW niewidoczna), ściana w kolorze budynku.
   Wynik: 6 grup po 5 / 5 / 5 / 5 / 5 / 6 skrzydeł na każdej z 11 kondygnacji, na obu LOD-ach.
2. **Nowe pola (wszystkie opcjonalne, domyślnie stare zachowanie; walidowane — błąd autora, nie cichy fallback):**
   - `footprint_simplify_m` (budynek; domyślnie 0,15): tolerancja uproszczenia po `footprint_open_m`. Wieżowiec: 0,3
     → NW = jedna krawędź 37,09 m (obrys 4 krawędzie).
   - `light_m` (reguła pasma `glazing: light`): szerokość jednego światła (domyślnie 1,5 m).
   - `light_sashes: 1`: światło = jedno skrzydło okna dwuskrzydłowego (połowa komórki atlasu, lewa / prawa na
     przemian); światła 2k i 2k+1 to jedno haszowane okno — LOD1 rysuje parę jednym quadem.
   - `light_mix: [żaluzja, żaluzja 2/3, szkło]` (suma 100): udziały świateł zamiast `BAND_LIGHTS` (SE: 62 / 28 / 10;
     NW na zdjęciach to głównie szkło w białych ramach — 10 / 20 / 70, WORKING_VALUE).
   - `far_kind`: grupa materiału dalekiej elewacji ściany LOD1 (NW: `plaster_beige__far_office` — materiał szczytów,
     bez nowego draw; `plaster_beige__far_ribbon` byłby nowym materiałem chunku).
   - `door` (reguła): `true` — ta ściana niesie wejście, `false` — nigdy; brak = jak dotąd (krawędź najbliżej drogi).
   - `machine_rooms: false` (budynek): bez haszowanej maszynowni dźwigu na dachu.
   - `roof_masts`: `panel_h_m` (0,8–2,7 m), `dish_m` (0,3–1,2 m).
3. **Maszty** (`roof_masts`, 10 struktur; było 8): maszt W `u 0.20, inset 2.3` (było 0,30 / 4,5), **nowy maszt
   środkowy** kratowy 11 m (`SE, u 0.49, inset 2.7`), maszt S 6,5 m bez zmian (adnotacja konfliktu w override),
   **kratowe 5,0 m i 4,6 m przy narożnikach N i E** (zastępują pręt 2,6 m przy E), 4 krótkie maszty krawędzi SE o
   różnych wysokościach 2,1–3,4 m: dwa z panelami, dwa z bębnami (jeden 0,3 m), maszt panelowy przy narożniku W
   (3 panele 1,4 m). Dwa wysokie maszty: bok kraty 0,7 m (było 0,5).
4. **Anteny (P2-A, P2-G):** bęben radiolinii w materiale masztu (`downpipe`, ocynk) zamiast białego, zawieszony
   poniżej wierzchołka (pręt biegnie ponad nim; `ROOF_DISH_DROP`), panele masztów prętowych odsunięte na wysięgnikach
   0,32 m (LOD0: dwa ramiona na panel). LOD1 kraty: tylko zewnętrzne lica nóg i przekątnych (−248 trójkątów).
5. **Przybudówka SE**: `kind: building_part` `g3a-office-tower-se-annex` (ADR 0179) — pierścień = 4 wierzchołki
   występu BDOT10k 6,39 × 1,8 m (dwa od strony ściany cofnięte 0,3 m w głąb wieży), 1 kondygnacja, 3,9 m (ESTIMATED),
   gładki tynk w kolorze budynku (wygląd ścian: UNVERIFIED). Haszowane wejście wieży leżało w środku ściany SE, czyli
   w połowie za przybudówką — drzwi przeniesione na lico SE przybudówki (`door: true`; ortofoto: dojście z parkingu
   kończy się przy przybudówce; WORKING_VALUE), ściana SE wieży `door: false`.
6. **Bez zmian:** kolor i pasma SE (`plaster_white` — źródła sprzeczne, decyzja po sesji zdjęciowej), szczyty,
   nadproża SE.

Odrzucone: dwie reguły NW per krawędź BDOT (granica krawędzi wypada w środku 2. grupy okien); `plaster_beige__far_ribbon`
(+1 materiał LOD1 w chunku 6_6); ciemne rzędy `ribbon` na LOD1 NW (jeden quad na grupę, ale antracytowa stolarka
przy białej na LOD0 — skok wyglądu); odciągi masztu W i drabiny kablowe (P3).

## 3. Budżet (A/B, tier Low)

A = `base2`: świat przebudowany ze źródeł bazowych (a08f9935d; manifest **bit w bit = HEAD**, 64 chunki), B = r2
(ta zmiana), ten sam łańcuch (`artifacts/tower3-0200/tools/full.ps1`): import → vqa Low clear, 52 kamery.

| Wielkość | Wynik (zmierzony) |
|---|---|
| draws, tier Low, 52 kamery, base2 → r2 | **−2 … 0** (żadna kamera w górę; −1 / −2 = materiał `balcony_slab` maszynowni znika z chunku 6_6) |
| trójkąty w kamerach | min +0,00 %, maks. **+0,34 %** (`cab-materials` 218 708 → 219 443); `stretch-02` +0,12 % |
| chunk 6_6 (manifest) | `buildings` 20 698 → 21 105 (+407), `buildings_lod1` 3804 → 4539 (+735), `road_collision` +7 (przybudówka) |
| wieżowiec (test, bez przybudówki) | LOD0 5307 → 5896, LOD1 1179 → 1886 (ściany 1238, maszty 648); przybudówka LOD0 142 / LOD1 28 |
| nowe materiały / tekstury | 0; materiały dalekie wieżowca bez zmian (`plaster_beige__far_office`, `plaster_white__far_ribbon`) |
| manifest poza 6_6 | zmienione także 4_5, 6_5, 7_5 (powtarzalnie w r1 i r2). Porównanie prymitywów glb z kopią bazową (main): **tylko warstwa `paved`** — 4_5: `yard_asphalt` 1578 → 1579 trójkątów (+ ta sama zmiana w `road_collision/collision_asphalt`), 17 wierzchołków w polu ok. 19 × 17 m; 6_5 i 7_5: `curb_concrete`, ten sam zbiór pozycji wierzchołków i liczba trójkątów (inna kolejność / atrybuty). Budynki, instancje, znaki, pozostały JSON chunków: bez różnic. To inna triangulacja nawierzchni placu po dodaniu obrysu przybudówki; mechanizmu w kodzie nawierzchni nie śledziłem |

`artifacts/tower3-0200/r2/budget-vs-base.txt`. Telefon: niezmierzony.

## 4. Walidacja

Łańcuch (sloty heavy / unity): base (import HEAD) → r1 → base2 (build ze źródeł bazowych) → r2: `build_world`
exit 0, import exit 0, vqa Low-clear exit 0, kamery wieżowca (`tower_cameras.json`, 15: 4 ściany z 60 / 200 m, z
południa, dach × 3, kierunki zdjęć 115626 / 073045 / KV 2021) Low clear + overcast i High clear, SBS Low **42 + 42
pary**. Dowody: `artifacts/tower3-0200/` (r2, sbs-r2, logs, tools).

| Punkt | Wynik (obejrzany / zmierzony) |
|---|---|
| NW vs 115626 | `r2/photo115626-vs-r2.jpg`: 6 grup po 5–6 skrzydeł na 11 kondygnacjach, filary w kolorze ściany, szersza przerwa w środku; Low ≡ High (`r1/z/L-nw200c.jpg` / `H-nw200c.jpg`). W oświetleniu overcast jak na zdjęciu (`r2/photo115626-vs-r2-overcast.jpg`): układ zgodny, pary świateł z żaluzją to jasnoszare pola, nie białe plamy. Różni się: tynk w renderze jest bladobeżowy (wspólny `plaster_beige`), na zdjęciu nasycona ochra; w clear ściana jest w cieniu; brak klimatyzatorów, mniej drobnego sprzętu na dachu |
| maszty vs 115626 / 073045 | maszt środkowy w 0,51 długości (zdjęcie 0,48), W w 0,92 (0,89), krótsze przy końcu NE; z SW (`r2/photo073045-vs-r2.jpg`) maszt W za lewą częścią szczytu; z południa W w ok. 0,3 szerokości szczytu (`r1/z/H-s150c.jpg`) |
| anteny (P2-A, P2-G) | `r1/z/H-roof_s_c.jpg`: panele na wysięgnikach, szare bębny poniżej wierzchołków, różne wysokości; białych kul brak |
| przybudówka SE | `r2/z/H-annex.jpg`: parterowa bryła z drzwiami i daszkiem na środku ściany SE, bez z-fightingu i szczeliny |
| SE / SW bez zmian | `t190_se_200` Low: średni kolor ściany (134, 136, 132) → (133, 135, 131); piksele różne (fuzz 10 %) 0,02 % (SE), 0,01 % (SW) — maszty |
| trasa | para `sbs-r2/pairs/Low-overcast/sbs-g3-a-178689077481862.jpg`: budynek rozpoznawalny jak przed zmianą |
| testy | `tests/gis/test_tower_0200.py` 8 nowych; zaktualizowane liczby w `test_tower_0190`, `test_buildings_0180`, `test_buildings_0167` oraz strażnicy „region C bez building_part” w `test_dojbld_0185` / `test_dojlidy_0179` (dopuszczona dokładnie ta jedna część). Pełny `pytest tests/gis` (po `fidelity/run.py`, exit 0): **1157 passed, 3 failed, 2 xfailed** — 2 to ci strażnicy (po poprawce oba pliki + 0200: 21 passed), 1 to `test_fence_mesh_mips_do_not_preserve_coverage`, czerwony także na main (cofnięcie 0185 w e668a9588), niezwiązany. Pełnego przebiegu po poprawce strażników nie powtarzałem. EditMode: **581 total, 580 passed, 0 failed, 1 skipped** |

Recenzji visual-critic nie było (agent nie tworzy subagentów) — do wykonania przez lidera na `r2/` i `sbs-r2/pairs`.

## 5. Otwarte

- Recenzja visual-critic; zrzuty z telefonu (APK Low na A16) — telefon niezmierzony (bez adb w tym zadaniu).
- Kolor ściany SE (biała / piaskowa) — test A/B na kamerze `t200_kv2021` po sesji zdjęciowej właściciela (pkt 6).
- Konflikty masztów: środkowy (brak na Mapillary 2020), S 6,5 m (brak na 073045 i ortofoto), odsunięcie masztu W
  (115626: ok. 4 m) — sesja zdjęciowa albo oryginał 073045 w 4608 px.
- NW: udziały żaluzji / szkła, parapet i nadproże pasm, klimatyzatory pod oknami (widoczne na 115626 i 073045),
  ciemny pionowy pas (kabel?) pod masztem środkowym; filary między grupami na 115626 wyglądają miejscami na jasnoszare.
- Przybudówka SE: wygląd ścian i wysokość (confidence low); parter szczytu SW (pas szklenia przy narożniku S, P3).
- Odciągi masztu W, drabiny kablowe, wentylatory dachowe (P3). P2-C / P2-D / P2-E recenzji 0190 (komórka atlasu
  „jasne okno”, serie ciemnych świateł SE) — poza zakresem.
- Ton tynku: `plaster_beige` jest wyraźnie bledszy niż ochra na 115626 / 073045 (materiał wspólny wielu budynków — wariant dla wieżowca to osobna decyzja; ADR 0190 mierzył zgodność tylko z Mapillary 2020).
- Triangulacja `paved` zmienia się w 3 chunkach po dodaniu jednego obrysu budynku (§3) — do wyjaśnienia w generatorze nawierzchni.
- NE: nadal bez zdjęcia (kopia reguły SW, confidence low).
