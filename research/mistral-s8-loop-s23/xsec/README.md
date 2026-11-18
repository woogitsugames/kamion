# Przekroje z ortofoto GUGiK — pętla S8 ↔ DW671 ↔ Tykocin (wyniki pomiaru)

Narzędzie: `measure_loop_xsec.py` w tym katalogu — metoda jak `tools/worldgen/qa/ortho_xsec.py` (ADR 0272): stacje na osi way (OSM, `../raw/osm/loop_roads.json`), co 500 m na S8 / 250 m na DW671 i DK64 / 150 m na łącznicach / 200 m na drogach przy węzłach, wycinek GetMap 36×36 m przy 0,05 m/px, WMS `mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution`, warstwa `Raster`, EPSG:2180 (serwer przepróbkuje arkusze — rozdzielczość natywna i data arkuszy przy tej skali: UNVERIFIED). W repo tylko liczby (289 stacji), żaden piksel nie jest zapisywany.

Pola wiersza: `asphalt_L/R/w` (ciągły przebieg asfaltu przez oś, dokładność krawędzi ±0,3 m), `paved_L/R/w` (luźniejszy próg = asfalt + pobocze utwardzone), `lines` (piki jasności — linie malarskie, ±0,2 m), `grass_L/R` (pierwsza zieleń za asfaltem).

## Mediana per grupa (`summary.json` = pełne statystyki per way)

| grupa | stacje | asfalt mediana [m] | paved mediana [m] | uwagi |
|---|---|---|---|---|
| `s8.json` (jezdnie S8, co 500 m) | 122 | 10.45 | 11.2 | 2 pasy: ~10,3 m (7,0–7,5 jezdnia + ~2,5 pobocze awaryjne); 3 pasy: ~11,3 m |
| `s8_links.json` (łącznice, co 150 m) | 77 | 9.9 | 11.82 | 1 pas: ~7,5–8,7 m; część stacji przy wlotach (szersze) |
| `dw671.json` (DW671, co 250 m) | 52 | 7.4 | 8.3 | jezdnia ~7,0–7,4 m, linie krawędziowe ±3,5 i środkowa; pobocze żwirowe ~0,9–1,5 m |
| `dk64.json` (DK64 przy Jeżewie, co 250 m) | 29 | 7.2 | 7.85 | jak DW671 (~6,9–7,2 m) |
| `junction_roads.json` (drogi przy węzłach, co 200 m) | 9 | 11.55 | 12.65 | wloty/wyloty — część stacji przy skrzyżowaniach (szerzej) |

## Pas dzielący i bariera na S8

- Odległość oś–oś przeciwnych jezdni S8 (z geometrii OSM, stacje z sąsiednią jezdnią w zasięgu 40 m): **mediana 12.27 m** (zakres [10.83, 15.17]), stacji: 122.
- Pas dzielący = oś–oś minus połowy jezdni: przy jezdni 7,0 m → **~5.27 m** (ESTIMATED, wyprowadzone z pomiaru).
- Bariera stalowa w pasie dzielącym: potwierdzona wzrokowo na wycinku ortofoto (stacja way 100133887, 40×40 m) — zgodna z Dz.U. 2022 poz. 1518 § 16 ust. 2 (bariera przy prędkości > 50 km/h).

## Zgodność z przepisem (Dz.U. 2022 poz. 1518 — rozp. MI z 24.06.2022, tekst via ELI)

| parametr | przepis | pomiar ortofoto |
|---|---|---|
| przekrój klasy S | § 15: 2/2, 2/3, 2/4 | 2/2 i 2/3 występują (OSM lanes 2/3) |
| pas ruchu klasy S | § 17 ust. 1 pkt 2: 3,50 m | jezdnia 2-pasowa ~7,0–7,5 m ✓ |
| pas awaryjny (pobocze twarde) klasy S | standardowo 2,50 m | paved − asphalt ≈ 0,9–2,9 m; wizualnie ~2–2,5 m ✓ (ESTIMATED) |
| pas dzielący + bariera | § 16 ust. 2 | ~4–4,8 m ze stalową barierą ✓ |
| DW671/DK64 (klasa G/Z) | pas 3,00–3,50 m, pobocze | ~7,0 m jezdnia + ~1 m pobocze żwirowe (wizualnie, bez krawężnika) ✓ |

## Typ krawędzi (z ortofoto, klasyfikacja wzrokowa na wycinkach 40×40 m)

- S8: krawędź jezdni z linią ciągłą + pobocze utwardzone (asfalt/podbudowa) przechodzące w opaskę/grunt; bariera w medianie; **brak krawężnika** na poboczu.
- DW671/DK64: linie krawędziowe + środkowa przerywana; pobocze **żwirowe/gruntowe ~1–1,5 m**, bez krawężnika (ADR 0272: pobocze gruntowe jako dane).
- Łącznice: asfalt ~6,5–8,7 m, pobocze trawiaste ~2,5 m (wizualnie na wycinku przy Jeżewie).

## Odtworzenie

`uv run --project tools/worldgen python research/mistral-s8-loop-s23/xsec/measure_loop_xsec.py` (we: `../raw/osm/loop_roads.json`; WMS GUGiK; UA `osm-research-client/1.0`).
