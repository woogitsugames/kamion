# Rynek P1 (D41, ADR 0227 dopisek) — dane pomiarowe

Tylko liczby. Żadnych obrazów ortofotomapy ani zdjęć właściciela w gicie.

## `market_canopies_ortho.json` — wiaty targowicy (a)

- **Źródło:** GUGiK ORTO WMS StandardResolution, warstwa `Raster`, EPSG:2180, 0,1 m/px. To ten sam arkusz 2025 co w ADR 0227.
  Dane otwarte. Narzędzie: `tools/worldgen/qa/market_canopy_ortho.py`, metoda opisana w docstringu.
- **Komenda:** `uv run --project tools/worldgen python tools/worldgen/qa/market_canopy_ortho.py measure docs/reports/rynek-p1/market_canopies_ortho.json`
- **Metoda:** dla każdej wiaty dwa profile.
  - Wzdłuż kalenicy, w pasie ±1,2 m od osi obrysu, z klasyfikacją dach / cień / grunt. Grafit od strony cienia jest niebiesko-szary.
    Połać w słońcu rozpoznajemy po prążkach rąbka. Koniec okapu to pierwszy odcinek bez dachu dłuższy niż 0,3 m.
  - W poprzek, 0,3 m wewnątrz początku naroży. Tam połać ma pełną szerokość i nie ma paneli PV.
  - Linijkę sprawdza test na syntetycznym rastrze: `tests/gis/test_rynek_p1_0227.py::test_ortho_ruler_reads_gaps_and_lengths_on_a_synthetic_raster`.
- **Wynik (SOURCED, pomiar):**

  | wiata | długość okapu | szerokość okapu |
  |---|---|---|
  | north-separated | 27,10 m | 7,25 m |
  | north-group | 27,15 m | 7,23 m |
  | middle-group | 27,10 m | 7,28 m |
  | south-solar (PV) | 27,10 m | 7,20 m |

  Prześwity między okapami:

  | między wiatami | prześwit |
  |---|---|
  | north-group / middle-group | **1,15 m** |
  | middle-group / south-solar | **1,17 m** |
  | north-separated / north-group | 14,2 m |

  Prześwity są wypełnione cieniem rzucanym na grunt, bo słońce świeci od południa. Układ 3+1 i przerwy zgadzają się z opisem zdjęcia 12 właściciela.
- **Dokładność:** ±0,1 m na krawędź, ±0,2 m na prześwit. Położenie bezwzględne ±0,5 m (przesunięcie radialne dachów na wysokości ok. 4 m).
  Środka rzutu WMS nie publikuje, dlatego to UNVERIFIED. Przesunięcie jest jednakowe dla sąsiednich wiat, więc nie zmienia prześwitów.
- **Przyczyna błędu w grze:** ręczne obrysy z R24 nachodziły na siebie o ok. 1 m. Generator odejmował po 0,25 m z każdej strony.
  W efekcie okapy stały 0,3 m od siebie na wysokości 3,2 m, czyli z poziomu oczu stykały się.
- **Poprawka:** wpis `knyszyn-market-canopy-eaves-d41` (`kind: market_canopy_geometry_d41`) na końcu `Data/Regions/knyszyn/overrides.yaml`.
  Podmienia obrysy po `id` na zmierzone prostokąty `rectangles_epsg2180` bez wcięcia. Wpis R24 zostaje bez zmian.

## Pozostałe punkty D41

- **(b) Pawilon:** dach namiotowy, ściany żółte. Dane w override `knyszyn-market-pavilion-d41`, opis w ADR 0227, dopisek D41.
- **(c) Korony lip:** proporcja wysokość/szerokość jako dane. Opis w ADR 0227, dopisek D41.
- **(d) Średnica ronda DK65 × Tykocka:** `outer_diameter_m: 26.0` WORKING_VALUE (`knyszyn-roundabout-outer-diameter-d41`).
- **(e) Uskok krawędzi jezdni od południa** zmierzony na odtworzeniu modułu dróg z NMT GUGiK. Użyto WCS `DTM_PL-KRON86-NH_TIFF` 1 m,
  z przesunięciem +0,17 m do EVRF2007, zmierzonym na 3 węzłach grafu (różnice 0,13–0,19 m). Plik NMT został poza gitem.
  - Za krawężnikiem narożnika S→E teren spadał o 0,51–0,74 m w odległości 1,5 m, na odcinku 2–24 m od węzła rozdziału.
  - Po poprawce: ≤ 0,28 m, tyle co profil wiejski samego ramienia DK65.
  - Przyczyna i poprawka: ADR 0227, dopisek D41 (e).
