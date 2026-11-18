# ADR 0293 — ekrany akustyczne: styl z danych (przezroczyste w mieście); pas P-21 zamiast krawężnika przy jezdni A/S

Status: Proposed (agent screens-s24, gałąź `screens-s24`), 2026-11-18. Numer nadany przez lidera.
Powiązane: ADR 0069 (ekrany wg Mapillary, style `solid` / `glazed`), 0125 / 0127 / 0139 (szkło ekranów, słupki),
0077 / 0093 (szczeliny między jezdniami, P-21 tylko z obrysów), 0100 (P-21 jako kwadraty), 0146 (ekrany na wiaduktach),
0288 (pętla S8, `dk65-01`), D43 (referencje tylko z otwartych źródeł).

## Kontekst
**A.** Rendery s24 (DK19 Bojary / Mickiewicza, `artifacts/dk19-tiles-s24/vqa/*`) pokazują ekrany jako ciemne,
pełne ściany. Na otwartych zdjęciach miasta ekrany są w większości przezroczyste w jasnych ramach: rondo Meyera /
Nowowarszawska DK19 (Commons cm106568383, cm106790713 CC0), Ciołkowskiego DW678 (cm94000570 CC0), Nowowarszawska
2024 (Mapillary 1032387041872194), Sulika DK65 (Mapillary 1035629900575719, szare kasety na dole + szkło). Generator
miał styl domyślny `solid`, a `glazed` tylko w strefach autorskich `industrial-c` (Andersa / Putry / Tysiąclecia).
Dane nie mówią, z czego są panele: 184 drogi OSM `barrier=wall` + `wall=noise_barrier` w Białymstoku nie mają
żadnego tagu poza tymi dwoma (sprawdzone 2026-11-18 na `podlaskie-261108.osm.pbf`), BDOT10k OT_OIKM_L ma tylko `RODZAJ`.
Wariant przezroczysty istniał już w kodzie (materiał `noise_glass`, shader Kamion/World Car Glass, Transparent,
ZWrite Off, Cull Off, `Blend One OneMinusSrcAlpha`, na obu tierach).

**B.** `dk65-01`, kamera `s8_corner_eye` (`artifacts/s8-loop-s24/vqa-r10/dk65-01/small/s8-corner-eye.jpg`): między jezdnią
S8 a pasem wyłączania stoi podniesiony krawężnik. Przyczyna (sonda na sieci dk65-01): OSM rysuje pasy wyłączania /
włączania węzła jako osobne `motorway_link` (i jeden `service`) 1,4–3,1 m od krawędzi S8 na ~200 m. Profil każdej z
tych dróg z NMT 2024 (sprzed budowy węzła) leżał 0,3–1,1 m pod krawędzią S8, więc (1) szczelina „merge” była odrzucana
jako „jezdnie na różnych wysokościach” (stopnie 0,22–0,56 m), (2) była dłuższa niż `GORE_MERGE_MAX_LEN_M` 90 m,
(3) `network._tight_side` stawiał na obu krawędziach krawężnik 0,13 m (reguła z Ronda Bieżeństwa, ADR 0076).
Na drodze klasy A/S krawężnika tam nie ma: pas wyłączania przylega do jezdni, a klin przed noskiem to P-21
(powierzchnia wyłączona z ruchu, zał. 2 do rozporządzenia o znakach, t.j. Dz.U. 2019 poz. 2311).

## Decyzja
### A — styl ekranu z danych (`streetscape/furniture.py`)
Kolejność (pierwsza pasująca):
1. tag OSM `material=*` drogi ekranu (`glass`, `acrylic_glass`, `plexiglass`, `pmma`, `plastic`, `polycarbonate`,
   `acrylic` → `clear`; `concrete`, `metal`, `steel`, `aluminium`, `wood`, `brick`, `stone`, … → `solid`); fragment
   BDOT10k bierze tag drogi OSM leżącej ≤ 4 m od niego;
2. strefa autorska `kind: noise_barrier_style` (bez zmian); region, który ma takie strefy, zostawia poza nimi `solid`
   (te ekrany sprawdzono na zdjęciach, ADR 0069) — dziś tylko `bialystok-industrial-c`, więc tam nic się nie zmienia;
3. reguła drogowa (WORKING_VALUE): jezdnie w promieniu 30 m od ekranu (3 próbki na 25/50/75 % długości) —
   autostrada / droga ekspresowa (klasa A lub S, numer S/A, albo ≥ 100 km/h) → `solid`; arteria miejska GP / G / Z
   ≤ 70 km/h → `clear`; inaczej `solid`.
Nowy styl **`clear`**: jasny cokół 0,6 m, szkło od cokołu do góry (bez pasa kaset), jasne ramy (rama dolna na cokole,
rygle co ~1,0 m, rygiel górny) i słupki co 4 m z materiału `noise_post_light` (liniowo 0,42/0,43/0,43, metal 0,35,
WORKING_VALUE z kolorów na zdjęciach). Tagi `material` przypięte do zmiany OSM wejdą same przy następnym ingeście.
Raport: `streetscape_qa.json` → `furniture.noise_barriers.style_rule_m` (metry wg przyczyny wyboru).
Przełącznik A/B (do renderów „przed”): `WORLDGEN_NOISE_RULE_OFF=1` = zachowanie sprzed ADR.

### B — pas P-21 przy jezdni A/S (`roads/profile.py`, `roads/gores.py`, `roads/markings.py`)
1. **Wiązanie profilu (1d):** jednokierunkowa jezdnia biegnąca obok jezdni zasadniczej A/S w tym samym kierunku,
   z krawędzią ≤ `EXPRESS_PARALLEL_GAP_M` 4,0 m od niej (≥ 10 m takich stacji) dostaje cele wysokości z powierzchni
   tej jezdni (istniejący `adjacent_targets`, waga `ADJ_WEIGHT`); węzły między kolejnymi drogami OSM tego pasa (nie
   leżące na jezdni zasadniczej) biorą wysokość celu, końce przesunięte z węzła (1c) zachowują swój offset.
2. **Gore `express`:** szczelina między takimi jezdniami (zamknięcie 2,0 m = `GORE_MIN_NOSE_W`/2) jest asfaltem bez
   krawężnika przy dowolnej długości; sprawdzana i budowana w kawałkach po 12 m (`EXPRESS_CHUNK_M`), więc kawałek z
   niezgodną wysokością (koniec pasa przy węźle z wysokością z NMT) zostaje z krawężnikiem, a reszta pasa jest malowana.
3. **Malowanie:** zbudowane kawałki jednego pasa łączone w jedną strefę `painted_zone` (`gores.p21_zones`), bez ramki
   (ramką są linie krawędziowe P-7a obu jezdni), ukośne pasy P-21 jak w ADR 0100 (`p21_hatch`, 0,5 / 1,0 m, 45°);
   raport `roads_qa.json` → `summary.markings.gore_p21`. Reguła miejska ADR 0093 (brak farby z reguły) bez zmian —
   dotyczy tylko jezdni, które nie są A/S.

## Liczby (zmierzone 2026-11-18, `artifacts/screens-s24/`, statystyki VisualQA = estymata przed SRP batching)
| | przed | po |
|---|---|---|
| `bialystok-maczka` ekrany (BDOT 753 m): styl | solid 753 m | clear 753 m (`rule: city arterial`) |
| `dk65-01` ekrany (OSM 222 m) | solid | solid (`rule: motorway / expressway`) |
| `dk65-01` gore `express` (asfalt + P-21) | 0 (2 „merge” odrzucone, krawężnik ~200 m) | 78 kawałków, 2444 m²; 1 kawałek 28,6 m² odrzucony (−465, −1016) |
| maczka High `screen_wb_eye` draws / tris | 987 / 1 593 924 | 987 / 1 600 227 (+0,4 %) |
| maczka High `screen_eb_eye` | 794 / 1 729 579 | 794 / 1 735 882 |
| maczka Low `screen_wb_eye` | 467 / 309 792 | 467 / 311 277 (+0,5 %) |
| maczka Low `screen_eb_eye` | 404 / 301 774 | 404 / 304 029 |
| dk65-01 High `s8_corner_eye` | 115 / 485 216 | 116 / 495 764 (+2,2 %) |
| dk65-01 Low `s8_corner_eye` | 87 / 147 151 | 88 / 153 546 (+4,3 %) |
Szkło nie dodaje wywołań w kadrach maczka (materiał `noise_glass` zamiast `noise_panel_dark` w tym samym chunku);
koszt to overdraw jednej przezroczystej płaszczyzny ~3,3 m × długość ekranu — nie zmierzony na GPU (estymator nie
liczy fill-rate), do pomiaru `pc-metrics.ps1` na trasie przez Maczka. `build_world` maczka 2840 s (bez zmian
kodu ścieżki krytycznej), dk65-01 ~760 s.
Obejrzane (High i Low): maczka `screen_wb_eye` (szkło w jasnych ramach, dom i płot widoczne przez ekran, brak
artefaktów sortowania, brudny pas u dołu), `screen_eb_eye`; dk65-01 `s8_corner_eye` (krawężnik zniknął, pas P-21
między S8 a pasem wyłączania), `s8_corner_top` (pasy P-21 wzdłuż 4 pasów węzła). `screen_close_0293` nie trafia
w ekran (kamera do poprawy, nie zmienia wniosku).

## Konsekwencje
- Kafle do przebudowy po scaleniu: z ekranami bez stref autorskich (A) — `bialystok-kleeberga`, `bialystok-knyszynska`,
  `bialystok-maczka`, `bialystok-bojary`, `bialystok-mickiewicza`, `bialystok-wygoda`, `bialystok-dojlidy` (jeśli ma
  ekrany), `dk8-s8-jeroniki`, `dk65-01`, `dk65-02`, `s8-01`…`s8-04`; z jezdnią A/S i pasami obok (B) — `dk65-01`,
  `s8-01`…`s8-05`, `dk8-s8-jeroniki`. `bialystok-industrial-c` bez zmian (strefy autorskie).
- Reguła A to WORKING_VALUE: konkretny ekran inny niż reguła → strefa `noise_barrier_style` (`style: solid|glazed|clear`)
  albo tag `material` w OSM. Ekrany wzdłuż S8 zostają `solid` bez zdjęć potwierdzających.
- Szkło jest przezroczyste (Transparent) na Low i High; koszt patrz „Liczby”.
- Otwarte: łącznice A (`motorway_link` 60 km/h) dalej mają krawężniki poza pasem P-21 (`xsec_rules.yaml open_road:
  min_speed_kmh 70`) — na S8 to błąd przekroju, osobne zadanie; ortofoto 2024 nie pokazuje jeszcze węzła S8 ×
  Szosa Knyszyńska (budowa), więc długości klina nie da się zmierzyć.
