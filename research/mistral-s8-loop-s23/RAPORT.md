# RAPORT — pakiet badawczy pętli S8 ↔ DW671 ↔ Tykocin (D82), sesja s23

Gałąź: `research/mistral-s8-loop-s23`. Wszystko w `research/mistral-s8-loop-s23/` + jedna sekcja w `docs/LICENSES.md`. Tylko dane tekstowe, bez zdjęć/kadrów, bez marek. Źródła: OSM API 0.6 (ODbL), GUGiK WMS ortofoto + BDOT10k 2002 (open data), Dz.U./ELI, gov.pl (e-TOLL), Panoramax (pokrycie). Bez Google/Bing/Apple/Yandex. Brak tokena Mapillary → weryfikacja zdjęciowa znaków UNVERIFIED.

## Co zrobione (sekcje A–G)

- **A `tiles.json`**: 15 kafli siatki ADR 0203: `s8-01..12` (S8 od dk65-01 do Jeżewa) + `dw671-jezewo-01..03` (DW671 do Tykocina), bbox EPSG:2180/WGS84, kolejność jazdy, styki: s8-01↔`dk65-01` (krawędź 2048 m), dw671-jezewo-03↔`tykocin` (pierścień 0231, PR #115 — wg MAP-DECISIONS (b)). S8 w pętli: 71 way, 43,1 km jezdni (oś ~21,2 km — zgodne z planem 0278).
- **B `xsec/`**: 289 stacji pomiaru metodą ADR 0272 (WMS GUGiK, 0,05 m/px; narzędzie `xsec/measure_loop_xsec.py`, dane wejściowe `raw/osm/loop_roads.json`). Mediany: S8 2-pasowa asfalt 10,35 m (jezdnia ~7,0–7,5 + pobocze utwardzone ~2,5), 3-pasowa 11,3 m; oś–oś jezdni 12,27 m → pas dzielący ~4,8 m ze stalową barierą (potwierdzone na wycinku); DW671/DK64 ~7,0–7,4 m + pobocze żwirowe ~1 m; łącznice 1-pasowe ~7,5–8,7 m. Zgodne z Dz.U. 2022 poz. 1518 (§15/§16/§17: pas 3,50 m, pas awaryjny 2,50 m, bariera w medianie).
- **C `junctions.json` + `mop.json`**: 5 węzłów S8 (Białystok Zachód, Choroszcz, Tykocin, Rzędziany, Jeżewo) — łącznice 81–231 m (geometria OSM), `maxspeed` na łącznicach 60/40; S8: `maxspeed=120`, `maxspeed:hgv=80`, `toll:hgv=yes` (e-TOLL). 2 MOP (Radule: ~12 miejsc TIR / ~50 osobowych; Złotoria: ~8 / ~12 — ESTIMATED z ortofoto), 7 stacji paliw w promieniu 2 km (funkcja, bez marek).
- **D `signs.json` + `SIGNS.md`**: 6 węzłów `traffic_sign` w kaflach (A-2, B-18+10 t przy Żółtkach, maxspeed 40/50/60, zakaz wyprzedzania), 6 way tertiary `maxweight=10` przy Choroszczy, `maxaxleload` 11,5/10; porównanie z Dz.U. 2019 poz. 2310/2311 (znaki), 2024 poz. 1251 (PoRD art. 20: 80 km/h >3,5 t na S8), 2022 poz. 1518 (węzły WA, pasy włączania/wyłączania §63–64), e-TOLL (rozp. RM 8.01.2026, S8 na liście).
- **E `destinations.json`**: 68 celów w kaflach pętli + 83 w pierścieniu ±2 km (151 razem ≤2,5 km): tereny przemysłowe (s8-01: strefa przy dk65-01 ~47 ha wg planu; hale/magazyny/zakłady), 1 żwirownia, 1 silos, 4–7 stacji paliw, sklepy; brama z topologii OSM gdzie jest (reszta UNVERIFIED). 348 podwórzy gospodarstw (266,8 ha).
- **F `settlements.md`**: 19 miejscowości; BDOT10k 2002 (14 616 budynków w bbox+2 km): przewaga 1-kondygnacyjnych domów jednorodzinnych + gospodarczych (~72% 1 kond.), największe skupiska Nowosiółki/Żółtki-Kolonia (przy dk65-01), Jeżewo Stare/Nowe przy węźle. Typy dachów: UNVERIFIED (LoD2 poza zakresem).
- **G**: ten raport, `README.md` (schematy), sekcja w `docs/LICENSES.md`, `raw/osm/manifest.json` (112 komórek: URL/UTC/SHA256; surowe poza gitem).

## Czego nie udało się ustalić (UNVERIFIED)

1. Weryfikacja zdjęciowa znaków (B-33 wartości, D-42/D-43, A-7, E-*, tablice e-TOLL) — brak tokena Mapillary; Panoramax ma pojedyncze zdjęcia.
2. Dokładne rozbicie łącznic na pas zwalniania/klina/przyspieszania wg §63–64 Dz.U. 2022 poz. 1518 — są długości całkowite z OSM.
3. Przyczyna `maxweight=10` na drogach tertiary przy Choroszczy (prawdopodobnie most) — do sprawdzenia na ortofoto przy budowie.
4. 4 way S8 bez `toll:hgv` (luka OSM; przepisowo płatne), miejsca postojowe MOP (zliczenie z orto, ESTIMATED), typy dachów (LoD2 nie pobrane), rozdzielczość/data arkuszy WMS przy 0,05 m/px (usługa nie podaje).

## Ryzyka

- Pokrycie znaków w OSM rzadkie — gra musi stawiać znaki wg przepisu + układu dróg (D63), nie tylko wg tagów OSM.
- `tykocin`/`monki` (pierścień 0231) są w PR #115, nie w main — styk pętli z nimi wg MAP-DECISIONS (b); przy scalaniu #115 dopasować szwy.
- Ort'f WMS StandardResolution przy 0,05 m/px to przepróbkowanie arkuszy — błąd odczytu ±0,2–0,3 m mieści się w tolerancji, ale detale (typ bariery, szerokość opaski) ESTIMATED.

## Jak odtworzyć

OSM: per komórka siatki `GET api.openstreetmap.org/api/0.6/map.json?bbox=…` (UA `osm-research-client/1.0`, 1,5 s; 400 → 4 ćwiartki) — `raw/osm/manifest.json`. Przekroje: `uv run --project tools/worldgen python research/mistral-s8-loop-s23/xsec/measure_loop_xsec.py`. BDOT: `2002_GPKG.zip` (opendata.geoportal.gov.pl), warstwa `OT_BUBD_A`. Prawo: ELI (api.sejm.gov.pl / eli.gov.pl) — wydania w `SIGNS.md`.
