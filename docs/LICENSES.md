# LICENSES — rejestr źródeł i zasobów

Każde pobrane źródło danych, zasób graficzny, dźwięk, czcionka i narzędzie, którego wynik trafia do repo lub buildu, ma tu wpis. Manifesty maszynowe (URL, data, SHA256, CRS) leżą w `Data/SourceManifests/*.json`; surowe pliki w `Data/raw/` (poza gitem). Zakaz źródeł Google: ADR 0002.

## Dane geograficzne

| ID | Źródło | URL (snapshot) | Pobrano (UTC) | SHA256 | Licencja | Atrybucja | W gicie? | Użycie |
|---|---|---|---|---|---|---|---|---|
| `osm-geofabrik-podlaskie` | OpenStreetMap, wycinek województwa podlaskiego (Geofabrik) | https://download.geofabrik.de/europe/poland/podlaskie-261108.osm.pbf | 2026-11-09T09:31:29Z | `0ff26cd42f175a5711c69b6d3087a9dcd3bb93367eda16809c75a11ce6c3869d` | ODbL 1.0 | „© OpenStreetMap contributors” | nie (manifest: `Data/SourceManifests/osm-geofabrik-podlaskie.json`) | analiza kandydatów D4 (`tools/worldgen/analyze_candidates.py`), mapy w `docs/reports/map/` |

### Uwagi ODbL (do przeglądu prawnego przed wydaniem w sklepie)
- **Wytworzone obrazy** (`docs/reports/map/*.png`) to w rozumieniu ODbL *Produced Work*: wymagana atrybucja „© OpenStreetMap contributors” (jest na każdej mapie); share-alike nie obejmuje samego obrazu.
- **Baza pochodna** (np. przyszły graf dróg, GeoJSON, paczka regionu z geometrią z OSM) to *Derivative Database*: jeśli będzie udostępniana publicznie (także jako część buildu gry, z której da się ją wyodrębnić), może podlegać share-alike (ODbL §4.4) — do udostępnienia na ODbL lub w formie pozwalającej odtworzyć zmiany. Status: `LEGAL_REVIEW_REQUIRED` przed sklepem.
- Atrybucja OSM musi być widoczna w grze (ekran „O grze”/napisy) — ADR 0002.
- Danych OSM nie łączymy z Mapillary (CC BY-SA) w jednej bazie (docs/05 §3).

## GUGiK (Główny Urząd Geodezji i Kartografii)
Zbiory pobrane 2026-11-09 przez `tools/worldgen/ingest.py --region bialystok-industrial-c`. Surowe pliki leżą w `Data/raw/gugik/` (poza gitem). Pełna lista plików z SHA256, datą pobrania, arkuszem i datą aktualności jest w manifestach. Tabela nie powtarza SHA256 plików, bo są ich dziesiątki: autorytatywne są manifesty JSON. Dostępność i źródła zasad licencyjnych: `docs/map-decisions.md` (sekcja „Dane GUGiK”).

| ID (manifest) | Zbiór | URL | Pliki / rozmiar | Licencja | Atrybucja | W gicie? | Użycie |
|---|---|---|---|---|---|---|---|
| `gugik-nmt-2025-bialystok-industrial-c` | NMT 1 m, PL-EVRF2007-NH, 2025-04-18 | `https://opendata.geoportal.gov.pl/NumDaneWys/NMT/83271/…` | 4 arkusze ASC, 149 MB | dane GUGiK udostępniane nieodpłatnie (PGiK art. 40a ust. 2 pkt 1, od 2020-07-31), `LEGAL_REVIEW_REQUIRED` | „Źródło danych: GUGiK (geoportal.gov.pl)” | nie | heightmapa `Data/raw/derived/…/heightmap_2049.r16` (pochodna, poza gitem), `z_terrain` w grafie |
| `gugik-orto-2024-rgb-0p25-bialystok-industrial-c` | Ortofotomapa RGB 0,25 m, 2024-05-27 | `https://opendata.geoportal.gov.pl/ortofotomapa/81427/…` | 4 GeoTIFF, 179 MB | j.w., `LEGAL_REVIEW_REQUIRED` | j.w. | nie | **tylko referencja i QA** (nie tekstura); wycinki w `docs/reports/map/bialystok-industrial-c_ortho_alignment.png` |
| `gugik-bdot10k-2061` | BDOT10k powiat 2061, GPKG, wersja 2024-09 | `https://opendata.geoportal.gov.pl/bdot10k/schemat2021/GPKG/20/2061_GPKG.zip` | 15,6 MB | j.w., `LEGAL_REVIEW_REQUIRED` | j.w. | nie | obrysy budynków, szerokość i nawierzchnia jezdni (fallback w grafie) |
| `gugik-lod2-2017-2061` | Modele 3D budynków LoD2 (stan 2017), CityGML 2.0 | `https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD2/2061_gml.zip` | 23,5 MB | **CC BY 4.0** (panel pobierania GUGiK) | „Źródło danych: GUGiK (geoportal.gov.pl), CC BY 4.0” | nie | wysokość kalenicy i okapu, typ dachu |
| `gugik-lod1-2024-2061` | Modele 3D budynków LoD1 2024, CityGML | `https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD1/2024/20/2061.zip` | 12,8 MB | **CC BY 4.0** | j.w. | nie | wysokość budynków (`measuredHeight`), tło horyzontu poza kaflem (`far_field`, ADR 0085) |
| `bialystok-industrial-c-far-field` | Pierścień tła horyzontu (poza bbox 2048 × 2048 m, do ±4200 m od kotwicy regionu): BDOT10k powiat 2061 (`OT_PTLZ_A`, `OT_BUBD_A`, `OT_BUWT_P`, `OT_SULN_L`) + LoD1 2024 (`2061_lod1_2024.zip`) + OSM (`podlaskie-261108.osm.pbf`, w tym powiat 2002 na N) | manifest zbiorczy: `Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json` | 6 plików źródłowych (SHA256 w manifeście) | dane GUGiK (PGiK art. 40a ust. 2 pkt 1) + CC BY 4.0 (LoD1) + ODbL 1.0 (OSM), `LEGAL_REVIEW_REQUIRED` | „Źródło danych: GUGiK (geoportal.gov.pl), CC BY 4.0; © OpenStreetMap contributors (ODbL)” | manifest tak; GLB pochodne (`far_field.glb`, `far_field.low.glb`) poza gitem | 4-sektorowe tło dalekiego planu (`tools/worldgen/streetscape/far_field.py` → `WorldEdgeBuilder`, ADR 0085): lasy, osiedla bloków, hale, kominy EC i słupy WN za zamknięciami dróg |

Sprawdzone, ale **niepobrane** (opcje `ingest.py --with nmpt|trees|lidar`): NMPT 0,5 m 2025, modele 3D drzew LoD1 2023 (CC BY 4.0, 1,07 GB), LiDAR LAZ 2025 (12 pkt/m², ~4,8 GB).

### Uwagi
- Pochodne produkty w `Data/Regions/bialystok-industrial-c/` (`roads.graph.json`, `buildings.geojson`) **łączą dane ODbL (OSM) z CC BY 4.0 / danymi GUGiK**. Graf dróg to baza pochodna OSM (share-alike ODbL §4.4), a pola z BDOT10k mają oznaczone pochodzenie (`src: bdot10k`). Przed udostępnieniem publicznym (build w sklepie) potrzebny jest przegląd prawny zgodności ODbL z CC BY 4.0: `LEGAL_REVIEW_REQUIRED`.
- Mapy w `docs/reports/map/bialystok-industrial-c_*.png` to *Produced Work* z atrybucją OSM i GUGiK na każdym obrazie. Wycinki ortofoto w raporcie są małe (6 × 90 m) i służą jako dowód QA.

## Narzędzia (biblioteki Pythona w `tools/worldgen`, wersje w `tools/worldgen/uv.lock`)
Używane tylko w pipeline, nie są dystrybuowane w buildzie: osmium (pyosmium, BSD-2), shapely (BSD-3), pyproj (MIT), geopandas (BSD-3), pyogrio (MIT), networkx (BSD-3), matplotlib (PSF-based/matplotlib licence), numpy (BSD-3), Pillow (MIT-CMU), requests (Apache-2.0), rasterio (BSD-3, z wbudowanym GDAL — MIT/X), PyYAML (MIT), pytest (MIT, tylko testy).

## Zasoby gry generowane kodem i wbudowane (Etap 1)

| Zasób | Pochodzenie | Licencja | Użycie |
|---|---|---|---|
| Tekstury placu `Environment/DrivingLab/Textures/T_*.png` (asfalt, beton, kostka, żwir, trawa), siatki, materiały | generowane proceduralnie przez `DrivingLabSceneBuilder.cs` (szum z hasha, bez zewnętrznych zdjęć) | własne (repo) | DrivingLab |
| Graybox ciągnika `Vehicle/Runtime/Prefabs/Tractor4x2_Graybox.prefab` | generowany z prymitywów Unity przez `GrayboxTractorBuilder.cs` | własne (repo) | DrivingLab, testy |
| Sprite kierownicy HUD | generowany w kodzie (`DrivingHud.WheelSprite`) | własne | HUD |
| Tekstury powierzchni świata `Rendering/Textures/World/T_World_*.png` (trawa, asfalt, beton, kostka, kostka kamienna, żwir, farba, szum makro) | generowane proceduralnie przez `WorldTextureGenerator.cs` (szum z hasha, Worley), bez zdjęć | własne (repo) | WorldC (shader `Kamion/World Surface`) |
| Shadery `Kamion/Sky`, `Kamion/World Surface`, model nieba `SkyModel.cs` | własny kod; wzory z publikacji: Preetham, Shirley, Smits 1999 (model nieba), CIE S 011/E:2003 (niebo zachmurzone), IESNA Lighting Handbook (natężenia), Kasten i Young 1989 (masa powietrza) — formuły, nie kod | własne (repo) | WorldC, docelowo każda scena świata |
| Czcionka `LegacyRuntime.ttf` | wbudowany zasób edytora Unity (`Resources.GetBuiltinResource`) | w ramach licencji Unity Editor/Runtime | HUD, tablice na placu (tymczasowo, do zastąpienia czcionką docelową) |

## Fotografie referencyjne świata (Wikimedia Commons, `Data/photos/nowe/`, poza gitem, nie trafiają do buildu)

Licencje sprawdzone przez lidera (`docs/REFERENCES.md` na `main`). W r2 kafla C (world-builder, 2026-11-09) użyte wyłącznie do porównań i ustaleń wyglądu; żadna tekstura nie została z nich wycięta.

| Plik (https://commons.wikimedia.org/wiki/File:…) | Autor | Licencja | Użycie |
|---|---|---|---|
| `20201102_152339_Rondo_Pamięci_Bieżeństwa_1915_roku_Białystok.jpg` | Rakoon | CC0 | wiadukt Andersa nad Rondem Bieżeństwa: czerwona krawędź pomostu, okrągłe filary (override `andersa-viaduct-biezenstwa-style`), porównanie z kamerą `biezenstwa_above` |
| `7204_May_2021_in_Białystok.jpg` | Rakoon | CC0 | wiadukt przy Rondzie Putry: zielona krawędź, żółte filary, przezroczyste ekrany (override `andersa-viaduct-putry-style`); treść tablic nad jezdnią (override `andersa-putry-approach-gantry`; lica tablic to nasz własny rysunek) |
| `7197_May_2021_in_Białystok.jpg`, `20240626_103137_June_2024_in_Białystok.jpg`, `6972_December_2019_…`, `20201223_141958_…`, `20201223_143208_…` (Al. Tysiąclecia) | Rakoon | CC0 | porównania kadrów, kolor i stan nawierzchni |
| `Worn_cracked_asphalt_pavement.jpg` | John Harvey | domena publiczna | referencja kształtu spękań (siatka wieloboczna, rysy); dopuszczalne jako źródło tekstury, w r2 nieużyte jako tekstura |
| `Krzysztof_Putra_Roundabout_in_Białystok.jpg`, `Andersa,_Maczka_streets_in_Białystok_1.jpg`, `…_2.jpg` | Henryk Borawski | CC BY-SA 3.0 / 4.0 | tylko referencja wizualna (kolory wiaduktu Putry, filary w parach) |
| `EC_Białystok.jpg` | Hiuppo | CC BY-SA 2.5 | tylko referencja wizualna (kominy EC jako dominanta; położenie i wysokość z OSM) |

Świat C v3 (world-builder, 2026-11-09): zdjęcia CC0 `20201102_152339…` i `7204_May_2021…` posłużyły do sprawdzenia skrajni pod obydwoma wiaduktami Andersa (pomost wyraźnie nad pierścieniem) i wysokości malowanego pasa krawędzi pomostu (ok. 0,55 m). Nic z nich nie wycięto. Nowe prototypy v3 to nasze własne proceduralne siatki z `tools/worldgen/streetscape`, bez tekstur zewnętrznych, marek i logo: ciągnik siodłowy 4×2, kontenery ISO 20/40 ft, druga rodzina latarni, lampa rampy i ślady opon.

Hala Kwadrat Park (ADR 0071): zdjęcia Rakoon `20210904_101250_September_2021_in_Białystok.jpg` i
`20241222_122132_December_2024_in_Białystok.jpg` (CC0, Wikimedia Commons) oraz ortofoto GUGiK 2024 posłużyły wyłącznie jako
referencja kształtu i kolorów; asset `art-source/world/landmarks/kwadrat_park/` jest wygenerowany naszym kodem
(`tools/blender/world/landmarks/make_depot.py`), nie zawiera pikseli zdjęć ani własnych tekstur (materiały świata po nazwie).

Zabudowa r10 (ADR 0081): zdjęcia Rakoon z Wikimedia Commons (CC0; identyfikatory stron 121537425, 121530695, 121537427,
121530694, 121537432, 104322581, 104322582, 104322590 — blok przy Rondzie Putry i okolice; kopie robocze w
`artifacts/buildings-r10/refs/`, poza gitem) posłużyły wyłącznie jako referencja wzrokowa (kolor tynku, balustrady,
zabudowy balkonów, stolarka). Atlasy `facade_atlas`, `facade_far` i `fence_concrete` są malowane kodem
(`art-source/world/materials/_src/sets_buildings.py`); `fence_concrete` bierze mikrodetal ze skanu CC0
`concrete_floor_worn_001` (Poly Haven, wpis w tabeli skanów ADR 0063). Żadne zdjęcie nie trafia do tekstur ani do buildu.

## Zdjęcia uliczne Mapillary (referencja, D42, ADR 0065)

Źródło: Mapillary Graph API v4, licencja CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). Pobierane narzędziem `tools/refs/mapillary_fetch.py` do `Data/raw/mapillary/` (poza gitem, nie trafiają do buildu). Użycie wyłącznie jako referencja (wzór, dopasowanie kadru, kalibracja koloru); piksele w teksturze zrobiłyby z niej pochodną CC BY-SA (ADR 0065). Autorzy zdjęć faktycznie użytych: [docs/ATTRIBUTION-mapillary.md](ATTRIBUTION-mapillary.md) (generowany; pojawi się po pierwszym `--use ... --attribution`).

## Skany materiałów CC0 (Poly Haven), świat (ADR 0063, decyzja D40)

Licencja sprawdzona 2026-11-10 na stronie https://polyhaven.com/license: wszystkie zasoby Poly Haven (HDRI, tekstury, modele) są na **CC0 1.0 Universal**, z prawem do użycia komercyjnego, modyfikacji i redystrybucji, bez wymogu atrybucji (podajemy ją mimo to, w napisach gry). Każdy plik jest przypięty w `art-source/world/cc0/cc0_manifest.json` (URL, rozmiar, md5 z API, **SHA256**, data pobrania). Surowe mapy 2k JPG (Diffuse, nor_gl, Rough, AO, Displacement; 65 plików, 162 MB) leżą w `art-source/world/cc0/_raw/` (**poza gitem**, pobiera i weryfikuje `art-source/world/materials/_src/cc0_fetch.py`). Do buildu trafiają wyłącznie przetworzone zestawy PBR (`_src/sets_scan.py` → `art-source/world/materials/<zestaw>/`, generowane, poza gitem), nigdy surowe pliki. ambientCG (CC0 1.0, https://docs.ambientcg.com/license/) dopuszczony przez D40, w tej wersji nieużyty (przejrzany: brak wymiarów fizycznych przy większości materiałów). Bez Google, bez generatorów AI.

Kolumna SHA256 = mapa Diffuse; SHA256 pozostałych 4 map każdego zasobu są w manifeście (test `tests/gis/test_cc0_scans.py` pilnuje, by każdy plik miał SHA256 i każdy zasób był w tej tabeli).

| ID | Zasób (rozmiar fizyczny) | URL | Autor | Licencja | Pobrano | SHA256 (Diffuse 2k) | Zestaw w grze |
|---|---|---|---|---|---|---|---|
| `asphalt_04` | Asphalt 04 (4,04 × 4,04 m) | https://polyhaven.com/a/asphalt_04 | Jenelle van Heerden (obróbka), Sergej Majboroda (zdjęcia) | CC0 1.0 | 2026-11-10 | `e02ac16d23ea97008c2507cf58bfad7c18a3b5933b5bdea14f7f90f33a784976` | `asphalt_worn` |
| `asphalt_pit_lane` | Asphalt Pit Lane (2,00 × 2,00 m) | https://polyhaven.com/a/asphalt_pit_lane | Dimitrios Savva | CC0 1.0 | 2026-11-10 | `35f41f618a4342454b9a46d136b5086e8f1872a866aa1a7db2f813be3c6059d3` | `asphalt_sma_fresh` |
| `clean_asphalt` | Clean Asphalt (2,10 × 2,10 m) | https://polyhaven.com/a/clean_asphalt | Dimitrios Savva | CC0 1.0 | 2026-11-10 | `9d58f263b695c268e391aa39ea2f6b30ab9f36d279715cc78593a4d43368039c` | `asphalt_patch` |
| `concrete_pavers` | Concrete Pavers (1,92 × 1,92 m) | https://polyhaven.com/a/concrete_pavers | Amal Kumar | CC0 1.0 | 2026-11-10 | `ac772172824543ce53a9ad60e0b7a00c02fcaf875ec6a65ae49806f6ae25539a` | `behaton_i_grey` |
| `pavement_04` | Pavement 04 (3,10 × 3,10 m; przeskalowane do kostki 20 × 10 cm → 2,28 m) | https://polyhaven.com/a/pavement_04 | Jan Burghardt | CC0 1.0 | 2026-11-10 | `1b23c4d027f59b7891ecad7e1c1e8a4c441063e407f7442a8dde4d7b4d7e095b` | `paving_20x10_grey` |
| `concrete_pavement_02` | Concrete Pavement 02 (1,80 × 1,80 m; przeskalowane do płyt 35 × 35 cm) | https://polyhaven.com/a/concrete_pavement_02 | Charlotte Baglioni | CC0 1.0 | 2026-11-10 | `a634f169ef1bb928585340f7feac69375b2bbbdfc0448e316dbaebe03bd5bf89` | `sidewalk_slab_35` (jeszcze nieprzypisany) |
| `brushed_concrete` | Brushed Concrete (2,50 × 2,50 m) | https://polyhaven.com/a/brushed_concrete | Dario Barresi (obróbka), Dimitrios Savva (zdjęcia) | CC0 1.0 | 2026-11-10 | `5af96604b20e29862b449d86981b196b18ba5cbcb8659c451dd8976411a36130` | `concrete_cast_5m_joints` (hybryda) |
| `concrete_floor_worn_001` | Concrete Floor Worn 001 (3,00 × 3,00 m) | https://polyhaven.com/a/concrete_floor_worn_001 | Dimitrios Savva (zdjęcia), Rico Cilliers (obróbka) | CC0 1.0 | 2026-11-10 | `e29b45cdcd6d02fae3c087c456196ffa750779a9b62e7071aa3831dc322a0cc4` | `concrete_slab_3x1.5`, `kerb_concrete_1m`, `concrete_precast`, `large_panel_joints` (hybrydy) |
| `painted_plaster_wall` | Painted Plaster Wall (2,00 × 2,00 m) | https://polyhaven.com/a/painted_plaster_wall | Amal Kumar | CC0 1.0 | 2026-11-10 | `6fd812ed8dd5be1873c29aeef38ce9bf1fb30a22c6d4b3a12db725e98c26a1be` | `plaster` |
| `red_brick` | Red Brick (1,40 × 1,40 m; przeskalowane do warstwy NF 75 mm → 1,51 m) | https://polyhaven.com/a/red_brick | Rob Tuytel | CC0 1.0 | 2026-11-10 | `a1ae5ba7e63026971ceaf68ebbcf8982d9c2dadde1c99996c49b8ac1160af995` | `brick` |
| `corrugated_iron_03` | Corrugated Iron 03 (2,00 × 2,00 m; przetłoczenia usunięte filtrem) | https://polyhaven.com/a/corrugated_iron_03 | Charlotte Baglioni | CC0 1.0 | 2026-11-10 | `7b3f4f849dd634f54548b3b552ebeae723266f782163341185c94094e2eb7991` | `trapezoid_sheet` (hybryda) |
| `gravel_floor_02` | Gravel Floor 02 (2,00 × 2,00 m) | https://polyhaven.com/a/gravel_floor_02 | Jenelle van Heerden (obróbka), Dimitrios Savva (zdjęcia) | CC0 1.0 | 2026-11-10 | `27c8953655dd2f289106106bb2c2c4845f77152bf1621b3d7091bd43b5083ffc` | `gravel_compacted` |
| `pine_bark` | Pine Bark (2,00 × 2,00 m) | https://polyhaven.com/a/pine_bark | Dimitrios Savva | CC0 1.0 | 2026-11-10 | `741f333ab9f8a0996d8a53905b5ac792fab77d7ccb8cac5fbaed8c99b9f6abd5` | `bark_pine` (tylko przetworzony; drzewa = zakres world-buildera) |

Modyfikacje (wszystkie w kodzie, odtwarzalne): częściowe usunięcie cieniowania (AO), spłaszczenie zmian jasności dłuższych niż ~0,35–1,5 m, balans bieli do średniej poprzedniego zestawu, kalibracja średniego albedo, wysokość całkowana z map normalnych, „bombardowanie” tekstury (4 m kafel z 16 łat obróconych o 90°), segmentacja kostek i płyt, skalowanie do polskich wymiarów (NF, 20 × 10, 35 × 35), hybrydy z naszymi generatorami układu.

## Pakiety Unity spoza szablonu

| ID | Pakiet | Wersja | Licencja | Użycie |
|---|---|---|---|---|
| `unity-gltfast` | glTFast (`com.unity.cloud.gltfast`, Unity Technologies i autorzy glTFast), rejestr Unity | 6.20.0 (`game/Packages/packages-lock.json`) | Apache License 2.0 (`LICENSE.md` w pakiecie) | import chunków GLB świata w edytorze (`scripts/import-region.ps1`, ADR 0011); w APK trafiają zaimportowane siatki oraz runtime'owe assembly glTFast (pakiet jest zależnością projektu) — przy wydaniu dołączyć tekst licencji Apache 2.0 do ekranu licencji/„O grze” |

## Audio

Wszystkie dźwięki poniżej są **w 100% syntetyzowane naszym kodem** (numpy/scipy) — bez nagrań, sampli, banków dźwięków ani generatorów AI. Brak praw osób trzecich; licencja = licencja projektu. Opis modelu: `docs/AUDIO_DESIGN.md`.

| ID | Źródło | Autor | Licencja | Data | W gicie? | Użycie / modyfikacje |
|---|---|---|---|---|---|---|
| `audio-engine-r6-synth` | `tools/audio/engine_synth.py` + `render_all.py` (synteza impulsowa R6, kolejność 1-5-3-6-2-4) | projekt (agent audio) | własna (projekt) | 2026-11-09 | generator tak; WAV nie (`art-source/audio/generated/`, odtwarzalne) | pętle silnika 16 rpm × 3 obciążenia × ext/cab, hamulec silnikowy 13 rpm × ext/cab |
| `audio-sfx-synth` | `tools/audio/sfx_synth.py` | projekt (agent audio) | własna (projekt) | 2026-11-09 | generator tak; WAV nie | gwizd turbo, lift-off, zwolnienie hamulca, hamulec postojowy, osuszacz, zmiana biegu, opony, wiatr, wycie przekładni |
| `audio-layers-synth` | `tools/audio/sfx_layers.py` (+ `render_all.py`, `render_layers_demo.py`) | projekt (agent audio) | własna (projekt) | 2026-11-09 | generator tak; WAV nie; demo OGG tak (`art-source/audio/demo/layers_*.ogg`) | opony × 6 nawierzchni (asfalt mokry, beton, kostka, żwir, trawa) + pisk, retarder, kompresor, zwolnienie hamulca postojowego, wariant „psst” osuszacza, przekaźnik kierunkowskazu (tik/tok), tło strefy przemysłowej (ruch, brum, wiatr), wózek widłowy, ptaki (wróbel, sikora, wrona), warianty kabinowe wszystkich warstw (filtr `cab_filter`). 100% synteza, bez nagrań i bez generatorów AI; brzmienie ptaków/wózka = synteza „impresyjna”, nie kopia żadnego nagrania |
| `audio-previews` | render powyższych (`art-source/audio/previews/*.ogg`) | projekt | własna (projekt) | 2026-11-09 | tak | podglądy do odsłuchu (każda pętla 2× pod rząd) |
| `audio-drive-demo` | `tools/audio/render_demo.py` (lustro runtime, skryptowana telemetria) | projekt | własna (projekt) | 2026-11-09 | tak (`art-source/audio/demo/`) | demo 30 s kabina + zewnątrz do oceny właściciela |
| `cluster-chime-procedural` | `game/Assets/_Project/Gameplay/ClusterChime.cs` (synteza w czasie działania: sinus 1,0 kHz + 2,4× , zanik wykładniczy, 0,45 s; brak pliku) | projekt (agent gameplay-ui) | własna (projekt) | 2026-11-10 | kod tak; brak pliku audio | pojedynczy sygnał zegarów przy próbie ruszenia z zaciągniętym hamulcem postojowym (ADR 0004 dodatek) |

### Narzędzia audio (biblioteki Pythona w `tools/audio`, wersje w `tools/audio/uv.lock`)
Tylko pipeline, nie trafiają do buildu: numpy (BSD-3), scipy (BSD-3), soundfile (BSD-3; dołączony libsndfile LGPL-2.1, z koderem Vorbis BSD-3 — używany tylko do zapisu plików offline), matplotlib (licencja matplotlib), Pillow (MIT-CMU, kwantyzacja PNG raportów). Formuły biquadów: RBJ Audio EQ Cookbook (wzory publiczne). K-weighting LUFS: ITU-R BS.1770-4 (współczynniki normy).

## Fonts
| ID | Source | Licence | Use |
|---|---|---|---|
| `truck-interior-a6` | own, generated by `tools/blender/truck/interior/*.py` (A6.1/r3b: switch packs, wipers, cab reflection probe for the URP-like preview, own AO-atlas packer; nothing downloaded). `Scania_S730_dash.jpg` (CC BY-SA 3.0, `docs/REFERENCES.md`) used only as a layout/proportion reference, nothing copied | project licence | cab interior LOD0–2, textures; control-render backdrop (render only) |
| `truck-exterior-a6` | own, generated by `tools/blender/truck/exterior/*.py` (`a6_export.py`); all textures baked/rasterised in the script (tread, sidewall text, plate, chequer plate, honeycomb, TRAKT wordmark from `art-source/truck/brand/trakt.svg`), no downloaded HDRI/textures/scans | project licence | TRAKT exterior LOD0–3 FBX, PBR atlases (High/Medium/Low), `glass_interface.json`, control renders (yard backdrop render only) |
| `trailer-curtainsider-13-6` | own, generated by `tools/blender/truck/trailer/*.py` (`trailer_export.py` + `trailer_build.py`, reuses the TRAKT helpers in `tools/blender/truck/exterior/`); all textures baked/rasterised in the script (rib tread, tyre sidewall text in Inter (OFL), fictional PL plate, R70 trailer marking plate), fictional unbranded design, no downloaded HDRI/textures/scans | project licence | curtainsider semi-trailer LOD0–2 FBX, PBR atlases (High/Medium/Low), `trailer_manifest.json`, control renders `docs/reports/visual/trailer-curtainsider/` (yard backdrop; coupled renders use `truck-exterior-a6`) |
| `truck-unity-a7` | own: Unity import/generator `game/Assets/_Project/Editor/Setup/TruckAssetBuilder.cs`, shaders `Rendering/Shaders/TruckExterior.shader`, `TruckGlass.shader`, `CabInterior.shader`; uses only `truck-exterior-a6` and `truck-interior-a6` assets, no external assets | project licence | TRAKT prefab, per-tier materials (generated into `Assets/_Generated/Truck`, outside the repository) |
| `font-inter` | Inter (Rasmus Andersson), file shipped with Blender 4.2 (`datafiles/fonts`) | SIL Open Font License 1.1 | rasterised text in cab display textures (art-source/truck/interior/textures); font file not in repo |
| `font-inter-ui` | Inter Regular (The Inter Project Authors), `Inter-Regular.otf` copied unmodified from the Unity URP package samples (`com.unity.render-pipelines.core` Samples~/Common/TextMesh Pro) | SIL Open Font License 1.1 (licence text shipped next to it: `game/Assets/_Project/UI/Resources/Fonts/Inter-OFL.txt`; "Inter" is a Reserved Font Name, file not modified or renamed) | all uGUI text (driving HUD, Boot menu, diagnostics overlay); in the APK |
| `cab-screens-live` | own: `game/Assets/_Project/UI/CabDisplays/*` (live cluster / navigation / DIN screens drawn in code, `Resources/CabDisplay/DisplayCanvas.shader`), glyphs from `font-inter-ui` (no new font file) | project licence | cab screen render textures at runtime |
| `nav-map-data` | `game/Assets/_Project/UI/Resources/CabDisplay/Nav/<region>.bytes`, generated by `tools/ui/build_nav_map.py` from `Data/Regions/<id>/roads.graph.json`, `buildings.geojson`, `route_start.json` (geometry, road class and names from OpenStreetMap, footprints from GUGiK BDOT10k / OSM) | ODbL 1.0 (© OpenStreetMap contributors; derived database, same `LEGAL_REVIEW_REQUIRED` note as the road graph above) + GUGiK open data | in-cab navigation map (in the APK); attribution belongs in the game credits |

## Świat — otoczenie kafla C (world-builder, 2026-11-09)

Wszystkie zasoby poniżej są **wygenerowane naszym kodem**. Nie korzystają z cudzych modeli, tekstur, zdjęć ani generatorów AI. Do 2026-11-10 tekstur CC0 nie używano; od ADR 0063 (D40) zestawy nawierzchni i fasad wymienione w sekcji „Skany materiałów CC0” biorą mikrodetal ze skanów Poly Haven, a układ i zużycie nadal z naszych generatorów. Wyjątek (2026-11-09): `world-ground-asphalt-detail` jest pochodną zdjęcia z domeny publicznej (wiersz niżej).

Wszystkie zasoby poniżej są **wygenerowane naszym kodem**. Nie korzystają z cudzych modeli, tekstur, zdjęć ani generatorów AI. Tekstur CC0 (Poly Haven, ambientCG) nie użyto, wszystko jest proceduralne. Wyjątki: `world-ground-asphalt-detail` (2026-11-09) jest pochodną zdjęcia z domeny publicznej, `world-viaduct-concrete` (2026-11-10) używa skanu CC0 Poly Haven (wiersze niżej). Atlas `world-hero-fire-station-atlas` (2026-11-10, ADR 0070) również używa skanów CC0 Poly Haven jako bazy detalu.

| ID | Źródło | Licencja | W gicie? | Użycie |
|---|---|---|---|---|
| `world-street-props` | `tools/worldgen/streetscape/props.py` + `export.py` → `art-source/world/props/street_props.glb` | własna (projekt) | tak | latarnie, słupki, tablice znaków, sygnalizatory S-1, wiaty, szlabany, bramy, słupki U-12, słupy, kratownice, ławki, kosze, szafki; generyczne auta osobowe (hatch, sedan, kombi, SUV) i lekki dostawczy bez marek, fikcyjne tablice rejestracyjne w formacie PL z ziarna, nie z rejestrów (`art-source/world/textures/car_plates.png`, `life_cars.plate_atlas`, font DejaVu Sans Bold) (3 LOD, `life_cars.py`); film brudu drogowego `art-source/world/textures/car_dirt.png` (generowany, `export.car_dirt_png`) |
| `world-sign-faces` | `tools/worldgen/streetscape/signs.py` → `art-source/world/signs/*.png` | własna; wzory znaków wg rozporządzenia (Dz.U. 2019 poz. 2311, zał. 1), narysowane od zera z prymitywów | tak | A-7, B-20, B-33, C-12, D-1, D-6, D-15, schematyczne E-2 |
| `world-gate3-sign-assemblies` | `tools/worldgen/streetscape/gate3_landmarks.py` → `art-source/world/signs/G3*.png` + prototypy `sign_g3_*` w `street_props.glb` (ADR 0125) | własna; wzory znaków wg rozporządzenia (Dz.U. 2019 poz. 2311), narysowane od zera z prymitywów; teksty: nazwa ronda (nazwa urzędowa, OSM) i ogólna tabliczka „wyjazd straży”; font DejaVu Sans Bold | tak | A-30 z tabliczką, tablica U-4a, D-3, D-6, D-1, tabliczka z nazwą ulicy (turkusowa, jak w Białymstoku); zdjęcia Mapillary (CC BY-SA 4.0) tylko jako wzór położenia, bez pikseli |
| `world-g3b-frontage` | `tools/worldgen/streetscape/frontage.py` + wpisy `g3b-frontage-*` w `overrides.yaml` (ADR 0126) | własna; geometria proceduralna z istniejących materiałów, bez nowych tekstur | tak | fasady salonów, maszty flag, totem, maszt kratowy z owalem: gładkie pola koloru, bez nazw, logo i napisów firmowych (jedynie funkcyjny szyld SERWIS z istniejącego prototypu); zdjęcia Mapillary (CC BY-SA 4.0) i ortofoto GUGiK tylko jako wzór położenia i proporcji, bez pikseli |
| `font-dejavu-sans` | DejaVu Sans Bold (dołączony do matplotlib, `mpl-data/fonts/ttf`) | Bitstream Vera License + public domain (DejaVu): wolno osadzać i rasteryzować, z zakazem sprzedaży samego fontu | rasteryzowany w PNG | cyfry B-33, „STOP”, napisy na schematycznych E-2, numery ramp, znaki fikcyjnych tablic rejestracyjnych aut. Nie jest to krój „Drogowskaz” z rozporządzenia: tablice E są schematyczne |
| `world-trees` | `tools/blender/world/make_trees.py` → `art-source/world/vegetation/trees.glb`, `trees_lod2.glb`, `impostor_*.png` | własna (projekt) | tak | sosna, brzoza, olsza, klon, lipa, krzew (3 warianty, LOD0/LOD1/impostor) |
| `world-forest-hlod` | `tools/blender/world/make_trees.py` → `art-source/world/vegetation/forest_edge_{conifer,mixed,broadleaf}.png`, `forest_canopy_*.png` | własna (projekt; wypieczone z naszych drzew LOD0) | tak | tekstury HLOD lasu (ściana brzegu, korona), ADR 0013 |
| `world-foliage-textures` | `tools/worldgen/streetscape/leaf_textures.py` → `art-source/world/vegetation/{leaves,bark}_*.png`, `grass_tuft.png` | własna (projekt) | tak | karty liści, kora, kępy trawy |
| `world-misc-textures` | `streetscape/export.py` (+ `streetscape/hedge_textures.py`) → `art-source/world/textures/{fence_mesh,dock_digits,hedge_shell_*,hedge_sprig_*}.png` | własna (projekt) | tak | siatka panelu ogrodzeniowego 3D, atlas numerów ramp; warstwa liści i pędy żywopłotów (berberys, ligustr, grab, żywotnik) rysowane z prymitywów, bez zdjęć (ADR 0049 addendum) |
| `world-plot-kit` | `streetscape/plot_kit.py` → `art-source/world/textures/plot_kit.png` | własna (projekt) | tak | atlas działek domów (ADR 0114): ogrodzenia, cegła, próbki, tuja, świerk, karty jabłoni / krzewu / bylin rysowane z prymitywów; klatki Mapillary (CC BY-SA) i Commons z `docs/refs/posesje-bialystok.md` tylko oglądane (wzór, proporcje, barwa), żaden piksel nie jest użyty |
| `world-plot-kit-conifer-r8` | [Poly Haven Fir Tree 01](https://polyhaven.com/a/fir_tree_01) `twig_diff` + `twig_alpha` (1k PNG, `art-source/world/cc0/_raw/fir_tree_01/`, poza gitem) → gałązki wycięte po składowych, sprowadzone do luminancji i zabarwione, stemplowane w rzędzie `thuja` i kartach `tall` atlasu `plot_kit.png` (`streetscape/plot_kit.py`, ADR 0124) | **CC0 1.0** ([licencja](https://polyhaven.com/license)); przetwarzanie własne | pochodna w atlasie (w gicie), raw ignorowany | tuje i świerki działek; bez pliku raw generator rysuje gałązki sam (`plot_kit.SOURCE`) |
| `world-ground-pbr` | `art-source/world/materials/_src/build_all.py` (numpy/scipy, proceduralnie, stałe ziarna) → `art-source/world/materials/<zestaw>/{High,Medium,Low}/*.png`, `materials_spec.json` | własna (projekt) | nie (generowane, `art-source/world/materials/README.md`) | zestawy PBR nawierzchni: asfalt SMA, asfalt zużyty, łaty, warstwa spękań 16 m, atlas plam oleju, beton 5 m, płyty JOMB 3×1,5, krawężnik, behaton, kostka 20×10, trawa pobocza (lato + późna jesień), żwir, makrowariacja |
| `world-ground-asphalt-detail` | pochodna zdjęcia `Worn_cracked_asphalt_pavement.jpg` (John Harvey, Wikimedia Commons, **domena publiczna**; `docs/REFERENCES.md`): wycinek bez spękań, filtr górnoprzepustowy luminancji, kafelkowanie → `art-source/world/materials/asphalt_detail_photo/` | domena publiczna (źródło) + własna obróbka | nie (generowane; zdjęcie źródłowe poza repo) | warstwa detalu 1 m na asfaltach (High/Medium) |
| `world-viaduct-concrete` | atlas `viaduct_concrete` (`art-source/world/materials/_src/sets_viaduct.py`) na bazie skanu **Poly Haven „Concrete Wall 008”** (autorzy: Charlotte Baglioni, Dario Barresi; https://polyhaven.com/a/concrete_wall_008; pliki 2k diff/disp/rough, md5 w `sets_viaduct.py`, pobierane do `Data/raw/cc0/polyhaven/`) + własne warstwy (szalunki, zacieki, farba); `art-source/world/textures/viaduct_steel.png`, `art-source/world/landmarks/viaduct_biezenstwa/*.glb` w całości z naszego kodu (`tools/blender/world/landmarks/make_viaduct.py`) | **CC0 1.0** (skan) + własna (projekt) | GLB, układ atlasu i `viaduct_steel.png` tak; PNG zestawu i skan nie (generowane / pobierane) | wiadukt nad Rondem Pamięci Bieżeństwa (ADR 0067). Kadry Mapillary (CC BY-SA 4.0) tylko jako referencja wizualna, bez pikseli w grze |
| `world-facade-pbr-life` | `art-source/world/materials/_src/sets_facade.py` (`noise_cassette`, `car_grime`; proceduralnie, stałe ziarna) → `art-source/world/materials/{noise_cassette,car_grime}/` | własna (projekt) | nie (generowane) | kasety ekranów akustycznych 4,0 × 0,5 m z brudem i zaciekami; film brudu lakieru zaparkowanych aut (2026-11-10, ADR 0041) |
| `world-ground-pbr-renders` | `art-source/world/materials/_src/render_test.py` (Blender 4.2.9) → `art-source/world/materials/_renders/` | własna; montaż `compare_street_vs_photo.jpg` zawiera wycinek zdjęcia CC0 (Rakoon, `20201102_152339_Rondo_Pamięci_Bieżeństwa…jpg`) | tak (JPG ≤ 300 KB) | rendery kontrolne nawierzchni i porównanie ze zdjęciem; nie trafia do buildu |
| `road-fidelity-qa` | `tools/worldgen/fidelity/run.py` → `Data/Regions/<id>/generated/fidelity_qa.json` (metryki zgodności dróg; OSM ways/tagi z wycinka Geofabrik 261108 + pomiary na ortofoto GUGiK) i nakładki `artifacts/fidelity-r9/overlays/*.jpg` (poza gitem) | ODbL 1.0 („© OpenStreetMap contributors”; JSON = baza pochodna, nakładki = Produced Work) + dane GUGiK (ortofotomapa, art. 40a ust. 2 pkt 1 Pgik; „Źródło danych: GUGiK”) | JSON tak, nakładki nie | QA, ADR 0075; nie trafia do buildu. Ta sama uwaga `LEGAL_REVIEW_REQUIRED` co dla grafu dróg |
| `gugik-ortho-hr-cells` | GUGiK WMS `ORTO/WMS/HighResolution` (EPSG:2180, komórki 128 m, 0,08 m/px) → `Data/raw/refs/gugik-ortho-hr/<region>/c_XX_YY.jpg` + `manifest.jsonl` (URL, czas, SHA256, bbox) | dane GUGiK, art. 40a ust. 2 pkt 1 Pgik; WMS bez ograniczeń dostępu; „Źródło danych: Główny Urząd Geodezji i Kartografii” | nie (poza gitem) | tylko referencja i pomiar zgodności (ADR 0075), nigdy tekstura w grze; data nalotu mozaiki WMS `UNVERIFIED` |
| `world-hero-fire-station` | `tools/blender/world/landmarks/make_fire_station.py` + `tools/worldgen/streetscape/hero_building.py` + `art-source/world/landmarks/fire_station_jrg2/{dims.json,atlas_layout.json}` → `fire_station_jrg2.glb`, `_meta.json`; `art-source/world/textures/fire_station_alpha.png` (`sets_fire_station.py --alpha`) | własna (projekt); wymiary z BDOT10k i GUGiK LoD2 2017 (CC BY 4.0, `lod2_roofs.json`), elewacje odwzorowane „na oko” ze zdjęć CC0 (Commons, Rakoon) i klatek CC BY-SA 4.0 użytych wyłącznie jako wzór | tak | remiza JRG nr 2 PSP, Andersa 46 (ADR 0070): budynek, ogrodzenie, tuje, maszty. Napis „PAŃSTWOWA STRAŻ POŻARNA” i „998” = nazwa służby i numer alarmowy (font DejaVu Sans Bold); bez logo, herbu i znaków graficznych PSP |
| `world-hero-fire-station-atlas` | `art-source/world/materials/_src/sets_fire_station.py` → `art-source/world/materials/fire_station/{High,Medium,Low}/*.png`; bazy: skany **Poly Haven** „Painted Plaster Wall” (Amal Kumar; https://polyhaven.com/a/painted_plaster_wall), „Brick Wall 006” (Jan Burghardt; https://polyhaven.com/a/brick_wall_006), „Concrete Wall 008” (Charlotte Baglioni, Dario Barresi; https://polyhaven.com/a/concrete_wall_008), mapy diff/disp/rough 2k JPG, md5 w `sets_fire_station.py`, pobierane do `Data/raw/cc0/polyhaven/` | **CC0 1.0** (skany) + własna obróbka (górnoprzepust luminancji, relief, szorstkość; kolory, zacieki, okna, bramy, blacha generowane) | nie (generowane; skany poza repo) | atlas 14 × 14 m obiektu hero (ADR 0070). Pierwsze użycie skanów CC0 w świecie gry |
| `world-hero-fire-station-conifer-r7` | [Poly Haven Fir Tree 01](https://polyhaven.com/a/fir_tree_01), Rob Tuytel (photography), Rico Cilliers (model); only1k twig_diff +twig_alpha PNG, SHA256/MD5/crop in `art-source/world/landmarks/fire_station_jrg2/conifer_source.json`; paired-alpha component filter, palette calibration, stem-centred short-needle spray into own fire_station_alpha cell | **CC0 1.0**, [official licence](https://polyhaven.com/license), verified2026-11-11; own generated geometry/processing | raw ignored; derivative in existing alpha atlas | JRG2 r7 conifer boughs, not a verified Picea scan. Trunk/UV strips excluded. No7197 photo pixels enter textures; route/global hedge palettes unchanged. Offline restore package under ignored `artifacts/firestation-r10/source-cache/` |
| `world-streetscape-data` | `Data/Regions/bialystok-industrial-c/generated/streetscape_sources.json` (OSM + BDOT10k) | ODbL 1.0 (© OpenStreetMap contributors) + dane GUGiK (BDOT10k, art. 40a ust. 2 pkt 1 Pgik) | tak | place, ogrodzenia, drzewa, ekrany, słupy. Ta sama uwaga `LEGAL_REVIEW_REQUIRED` co dla grafu dróg |

## Referencje z otwartych zrodel (D43, ADR 0066)

Pobierane do `Data/raw/refs/` (poza gitem, nie trafiaja do buildu). Manifest z autorem, licencja, URL i SHA256 przy kazdym pliku (`manifest.jsonl`). Bramka: tylko CC0 / domena publiczna / CC BY / CC BY-SA (`tools/refs/refs_common.normalize_license`); NC, ND, nieznane i obiekty z ograniczeniami sa odrzucane. Wygenerowane montaze w `artifacts/refs/` zawieraja miniatury z podpisem autora i licencji (do uzytku wewnetrznego, nie w repo gry).

| ID | Zrodlo | Licencja | W gicie? | Uzycie |
|---|---|---|---|---|
| `refs-kartaview` | KartaView (api.kartaview.org, openstreetcam), autorzy w manifescie | CC BY-SA 4.0 | nie | tylko referencja wizualna; pochodna (tekstura) = CC BY-SA, zabronione |
| `refs-panoramax` | Panoramax (api.panoramax.xyz), autorzy w manifescie | licencja per zdjecie (zaobserwowano CC BY-SA 4.0) | nie | tylko referencja |
| `refs-commons` | Wikimedia Commons (geosearch, kategorie, wyszukiwanie), glownie Rakoon (CC0/CC BY 3.0), Henryk Borawski (CC BY-SA), Podlaski Urzad Wojewodzki (CC BY 3.0 pl) | CC0 / CC BY / CC BY-SA, wg `extmetadata` pliku | nie | CC0 moze byc zrodlem tekstur (osobny wpis przy uzyciu); BY wymaga atrybucji; BY-SA tylko referencja |
| `refs-openverse` | Openverse (api.openverse.org), autorzy i dostawcy w manifescie | CC0 / CC BY / CC BY-SA | nie | j.w. |
| `refs-gugik-ortho` | GUGiK Geoportal WMS ORTO HighResolution | dane otwarte GUGiK (art. 40a ust. 2 pkt 1 Pgik); atrybucja: Zrodlo danych: Glowny Urzad Geodezji i Kartografii | nie | referencja i dopasowanie ukladu; rozdzielczosc mozaiki WMS UNVERIFIED |
| `refs-bialystok-open-data` | Miasto Bialystok, publiczne uslugi ArcGIS Online | dane otwarte miasta (warunki wg portalu: UNVERIFIED) | nie | kontrola pozycji obiektow (np. straz pozarna) |
| `refs-object-sheets` | `tools/refs/object_refs.py` -> `artifacts/refs/{kwadrat-park,fire-station,dusk-sodium}/` (INDEX.md z autorem, licencja, URL per plik) | kompilacja powyzszych; plan_budynki.jpg: ODbL/GUGiK (nasze dane regionu) | nie | przeglad, nie do builda |

## Quixel Megascans z Fab (decyzja D45, 2026-11-10)

Licencja **Fab Standard License** (Quixel Megascans; karta pozycji: „Licencja standardowa”, „Zezwala na użycie przy pomocy SI: Tak”). EULA zaakceptowana na koncie Epic właściciela 2026-11-10 (lider w przeglądarce aplikacji, zgoda właściciela w czacie). Użycie w grze komercyjnej (Unity, Android/iOS) bez atrybucji. **Pliki nie mogą trafić do publicznego repo** — ani źródła, ani pochodne (importy, atlasy, wypalone mapy): źródła w `Data/raw/fab/<id>/` (poza gitem), wyniki importu w `game/Assets/_Generated/` (poza gitem). W gicie tylko manifest `Data/SourceManifests/fab-megascans-2026-11-10.json` (URL, data, rozmiar, SHA256). Test `tests/gis/test_fab_not_tracked.py` pilnuje, że nic z Fab nie jest śledzone i że każda pozycja jest w tej tabeli. Pełny tekst EULA przed wydaniem w sklepie: `LEGAL_REVIEW_REQUIRED` (raport `docs/reports/FAB-PATCH-LICENSE-2026-11-10.md`). „Urban Trash” pobrał właściciel w wersji mid (karta oznaczona „Mature” — sprawdzić zawartość przed użyciem).

| id | Pozycja | Źródło | Licencja | Data | SHA256 (zip) |
|---|---|---|---|---|---|
| `street-curbs` | Street Curbs (3d) | https://www.fab.com/listings/30f9c32a-7ddb-44ce-8ac1-5c878dd752a2 | Fab Standard | 2026-11-10 | `b173f6f281577e9ce425af2b9efff0312df195658eddf4a419e7b828fb7c9178` |
| `modular-curb` | Modular Curb (3d) | https://www.fab.com/listings/5debfb8f-59d4-456f-b074-6ead0ce343aa | Fab Standard | 2026-11-10 | `81c8bd31c6ed47daf954c1b30d0eab52b2f573f0b2243677a071398387e6817a` |
| `round-manhole-cover` | Round Manhole Cover (decal) | https://www.fab.com/listings/2e07c844-34c4-4e4b-acee-b7869a66494f | Fab Standard | 2026-11-10 | `3d18d7242dfcad3c103a583e122837379621b0c1a2cf32a644d46075a0ee6eab` |
| `metal-manhole-cover` | Metal Manhole Cover (decal) | https://www.fab.com/listings/11eb03b4-09a9-475a-9721-1a4cc09b4839 | Fab Standard | 2026-11-10 | `64f151d9b6db4b6087db88bcd7a9dbc87be1b71ea6288edb491c75ec974899ed` |
| `round-drain-cover` | Round Drain Cover (decal) | https://www.fab.com/listings/16f36535-a188-4989-8d1c-5bb790290378 | Fab Standard | 2026-11-10 | `a89dc6b6bad950027ef406b7b5d7d658ff016d67dcedc4f3ca477506784c323a` |
| `square-rusty-drain` | Square Rusty Drain (decal) | https://www.fab.com/listings/2ae59500-f274-4ca6-9684-692a6957af53 | Fab Standard | 2026-11-10 | `ec67559697fb0b5df78bafa2ab9f74879836679181c693cafc000f8ad1ae38f5` |
| `trash-bag-pack` | Trash Bag Pack (3d) | https://www.fab.com/listings/e735f250-bc37-42bc-9828-0af395974b77 | Fab Standard | 2026-11-10 | `04f0b16ae3e4ecf70c4ac703c729296349ed5fc20580f191296df4a374ccb667` |
| `trash-can` | Trash Can (3d) | https://www.fab.com/listings/35267674-3634-4fd2-bca2-423fbc7da4b3 | Fab Standard | 2026-11-10 | `c94ba814a011dc81bb36c049d7da08d98b8725bacd4e1db13a28007896f8d85b` |
| `grass-clumps` | Grass Clumps (plant) | https://www.fab.com/listings/d22b2fc3-9389-4d39-894c-5369a7e49ddf | Fab Standard | 2026-11-10 | `3542bded154fbe4e946cb634dbb5ace08cb3e36c212f21d01b957bac8873f6f8` |
| `wild-grass` | Wild Grass (plant) | https://www.fab.com/listings/5848d16a-f6ab-45a7-b69f-fe21dcbe4669 | Fab Standard | 2026-11-10 | `ff6fb1b4a07768a34482f2a2c13f5f888245059a9a2cc455e34d5149a7f35533` |
| `boxwood` | Boxwood (plant) | https://www.fab.com/listings/ae90090d-cafb-4431-a74f-8cded15f93e1 | Fab Standard | 2026-11-10 | `9024cc6b4ec22da7958d83fc450b8e8dfa319e349da8a3915530695881d12376` |
| `elderberry` | Elderberry (plant) | https://www.fab.com/listings/d72dd7bb-d514-4a14-8b4b-3333c99057fb | Fab Standard | 2026-11-10 | `70b9076f24d3852b8a2068dfd373048e4bcc427d233dc15b3ee2d90ff871cc75` |
| `silver-birch-bark` | Silver Birch Bark (surface) | https://www.fab.com/listings/eb28e8b4-3198-4cf3-a42b-b3e12b612d06 | Fab Standard | 2026-11-10 | `2a3030a7c07ad56dc14ba4e515032815fdfd38c4cf1f3cf9f0f21c7506dee6c4` |
| `birch-tree-trunk` | Birch Tree Trunk (3d) | https://www.fab.com/listings/a2289955-a389-4fdb-a17b-b27c4146b03d | Fab Standard | 2026-11-10 | `b65fc13b280b0041b32029c32555dd22df39deeabc4623ca2352ba3ebe8b7635` |
| `pine-bark` | Pine Bark (surface) | https://www.fab.com/listings/5f6f6a17-3b21-470a-b74b-fbbf80c6dc11 | Fab Standard | 2026-11-10 | `b80cd5d01cae4070e71cfe3b917eed994ca022b426575855ef7ea81553fd8c4b` |
| `linden-branch` | Linden Branch (plant) | https://www.fab.com/listings/d8c3a5b3-7212-45b7-93b2-6c630333ec13 | Fab Standard | 2026-11-10 | `20973973e53d2f6fa97ba9e9abbd8f37d84e8401d986bc2708549b96b183fe71` |
| `granite-rock` | Granite Rock (3d) | https://www.fab.com/listings/01d40602-eb64-448b-af63-a7896924280a | Fab Standard | 2026-11-10 | `178df9900e3eccaf3ce21069281cdd3cfa4eead781f3b1828596570986ae5484` |
| `small-granite-rock` | Small Granite Rock (3d) | https://www.fab.com/listings/d4de5337-7536-41df-9706-2825dc0a9dad | Fab Standard | 2026-11-10 | `3af7d445e783e65254590ecd3abab12a83cc1e88f54aac82ce5c1873f420e11b` |
| `urban-trash` | Urban Trash (3d, mid) | https://www.fab.com/listings/4eb4b87c-92bf-495a-b68a-5877fc07094f | Fab Standard | 2026-11-10 | `89aab0683b618a66040d49d40241cae63db9a9eeda0d18ce1c4e61f032e96383` |

### Optional world integration (ADR 0084, gpt-megascans)

Local source manifest + `tools/worldgen/fab/review.json` control eligibility.
The observed local hashes for boxwood, granite-rock and small-granite-rock were
verified against intact ZIPs and embedded Quixel identities; original acquisition
pins remain in the manifest because the replacement chronology is UNVERIFIED.
`tools/worldgen/fab/prepare.py` produces mobile LOD libraries, alpha/albedo,
normal, roughness, AO and packed metallic/smoothness maps exclusively under
`art-source/world/megascans/_generated/`; Unity copies into `Assets/_Generated`.
Both directories are ignored; the git guard checks paths, archive/member hashes
and derived-output provenance hashes. No Fab assets or textures enter tracked art.

| Source ids | Intended local use / decision |
|---|---|
| street-curbs, modular-curb | Clean atlas crops blended into our generated road kerb material; original metric road geometry retained |
| metal-manhole-cover | Lane-centred cover detail; locations WORKING_VALUE |
| round-drain-cover, square-rusty-drain | Existing kerb-side gully mesh materials; spacing retained |
| round-manhole-cover | Rejected: embossed emblem and lettering |
| trash-bag-pack | Small grounded groups by existing shelter/gate/parking context |
| trash-can, urban-trash | Rejected: visible emblem / printed packaging and branded bin |
| grass-clumps, wild-grass | Bounded soft-verge details, LOD0/1/2; grass-clumps also supplies the private periodic grass base-map bake |
| boxwood, elderberry | Landscaping/soft-verge shrubs and explicitly authored island selections |
| silver-birch-bark, birch-tree-trunk | Bark crops mixed onto our generated birch material |
| linden-branch | Woody bark crop onto our generated linden; supplied scan contains no leaves |
| pine-bark | Rejected for trunk use: source is loose bark/mulch atlas; existing pine bark retained |
| granite-rock, small-granite-rock | Grounded roadside stone props, LOD0/1/2 |

Prepared normal maps remain disabled pending a tangent-capable reviewed mesh
path. Existing tree leaves remain. Missing licensed files preserve procedural/CC0
fallback; no licensed download is attempted by the public-clone build.

ADR0088 roślinność r2: bark_pine.png i bark_pine_lower.png oraz sosnowe partie naszych publicznych GLB/impostorów/HLOD korzystają ze skanu Pine Bark (Dimitrios Savva, Poly Haven, CC0; https://polyhaven.com/a/pine_bark). Wejście diffuse2k i SHA256: art-source/world/cc0/cc0_manifest.json, generator weryfikuje hash. Liście i geometria pozostają nasze proceduralne. Fab brzoza/lipa jest wyłącznie zatwierdzonym near override importera, nie wejściem do publicznego bake; linden-branch jest drewnem, nie liśćmi. Mapillary w artifacts/vegetation-r2 służy wyłącznie QA referencyjnemu, nie teksturowaniu ani buildowi.

ADR0088 igły sosny: pine_tree_01 (Rico Cilliers — model, Rob Tuytel — fotografia), https://polyhaven.com/a/pine_tree_01, CC0 według https://polyhaven.com/license (sprawdzone2026-11-11). Wykorzystano wyłącznie czystą gałązkę z twig_diff+twig_alpha1kPNG, crop [5,26,220,450], bez szyszek i paddingu atlasu. Jawne URL/MD5API/SHA256 i przetwarzanie: art-source/world/cc0/pine_needles_manifest.json, tools/worldgen/streetscape/pine_needles.py; raw ignorowane, legalne pochodne CC0 mogą wejść do publicznych kart/bake. Nie użyto modelu3D PolyHaven.
# ADR 0102 — dodatkowe użycie istniejących skanów CC0 (2026-11-11)

`streetscape/furniture_textures.py` wykorzystuje mikrostrukturę istniejących, lokalnych map Diffuse
`brushed_concrete` (Dario Barresi / Dimitrios Savva) i `corrugated_iron_03` (Charlotte Baglioni),
Poly Haven, CC0 1.0, opisanych wraz z hashami w tabeli ADR 0063 oraz `cc0_manifest.json`.
Wynik: tekstury `furniture_{galv,grey,concrete,bollard}` — filtr usuwa szerokie oświetlenie/przetłoczenia,
warstwy zużycia są własne. Mapillary p12/p15/p20/p26/p30 tylko jako referencja proporcji i rodzin;
żaden piksel Mapillary nie trafia do atlasów ani do builda.

### ADR 0105 — DK8 Putry underdeck (2026-11-11)

Reuses the existing CC0 `concrete_precast` material. Existing Fab Standard
`grass-clumps` vegetation is retained; additional abutment clumps are disabled
after the Low draw budget check. No new
source imagery, third-party texture pixels or Fab derivatives are versioned.
Rakoon's CC0 `7204_May_2021_in_Białystok.jpg` and Mapillary p42/p45/p47
(reference-only, as registered above) inform the structure; paint blobs are
authored WORKING_VALUE shapes without text or brands. See ADR 0105.
## ADR 0103 — fotografie w arkuszach side-by-side G3
Każde z 40 zdjęć Mapillary (CC BY-SA 4.0, tylko referencje, bez pikseli w grze) ma osobny wpis z autorem, datą, URL i SHA256 w [rejestrze SBS](refs/sbs-gate3-attribution.md). Dane maszynowe: `Data/Regions/bialystok-industrial-c/sbs_references.json`, publiczne parametry obiektywów: `sbs_intrinsics.json`. Modyfikacje panelu zdjęcia: prostowanie radialne według modelu obiektywu, kadrowanie, zmniejszenie, siatka i linia horyzontu. Panel fotograficzny i jego modyfikacje na CC BY-SA 4.0; panel renderu zachowuje warunki projektu. Oryginały i pochodne (`artifacts/sbs-gate3/rectified`) poza gitem i buildem.

## Referencje posesji jednorodzinnych — r7 (2026-11-11, tylko referencja, nie do buildu)
Zdjęcia nie wchodzą do builda ani tekstur. Rejestr: [`docs/refs/posesje-bialystok.md`](refs/posesje-bialystok.md) (autor, data, URL, SHA256 per zdjęcie); dane maszynowe `Data/raw/mapillary/posesje/manifest.jsonl` i `Data/raw/refs/posesje/manifest.jsonl` (poza gitem).
- Mapillary, 33 zdjęcia (autorzy: szurek, richlv, czadzik, strudel, grobin), CC BY-SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/. Pobrane przez Graph API v4 (`thumb_2048_url`). Użycie: wzór proporcji/typologii; każda przyszła pochodna piksele-do-tekstury wymaga osobnej decyzji (share-alike, ADR 0065). Jeżeli zostaną użyte w publicznym raporcie/arkuszu, atrybucja z rejestru.
- Wikimedia Commons, 7 zdjęć: C01 Rakoon (CC0 1.0), C02-C05 i C07 Krzysztof Popławski (CC BY 4.0), C06 Jacek Fink-Finowicki (CC BY-SA 4.0). Licencje z extmetadata Commons w dniu pobrania; strony plików w rejestrze.
- Odrzucone: `Wysoki stoczek 58 Bialystok.jpg` (wygląd jak zrzut z panoramy Google; usunięty z dysku i manifestu).
- Google Maps/Street View/Earth/3D Tiles: nie użyte.

## ADR 0120 — pochodne tekstury mebli ulicznych (2026-11-11)

`furniture_concrete`, `furniture_footing` i `furniture_plinth` korzystają z istniejącego
skanu `brushed_concrete`, Poly Haven, CC0 1.0 (Dario Barresi / Dimitrios Savva;
źródło i hash w tabeli ADR 0063 oraz `cc0_manifest.json`). Generator pozostaje
w `streetscape/furniture_textures.py`. `plate_back` to własna tekstura proceduralna.
Nie dodano nowego źródła ani pikseli Fab. Fotografie użyte w porównaniach tej rundy
służą wyłącznie jako referencje; atrybucje z istniejących rejestrów zapisano też
w `artifacts/furniture-r1/24h/reference-selection.json`. Nie trafiają do tekstur gry.
## Niebo fotograficzne — ADR 0108, light r1
- Zasób: Kloofendal 48d Partly Cloudy (Pure Sky), Poly Haven: https://polyhaven.com/a/kloofendal_48d_partly_cloudy_puresky
- Autorzy: Greg Zaal (oryginał), Jarod Guest (edycja czystego nieba). Licencja CC0 1.0: https://polyhaven.com/license (sprawdzono 2026-11-11).
- Oryginał 4K HDR poza gitem w Data/raw/cc0/sky/kloofendal_48d_partly_cloudy_puresky/; 20 674 857 B, MD5 816340c969d2e60d659051d13ac3c4dc, SHA256 3061c00a16ecae748e84fd6c44c04804f539c118bb66325db858bad87b11bf88.
- Pochodna: game/Assets/_Project/Rendering/Resources/Sky/T_ClearClouds.png, R = fotograficzna maska chmur, G = względna luminancja; usunięto tarczę słońca, zachowano kształt i cienie chmur. Dokładne metadane i oś słońca: ClearCloudsSource.json. Reprodukcja: artifacts/light-r1/build-photo-clouds.py przez pulę heavy.
- To tekstura nieba, nie zdjęcie referencyjne Białegostoku. Nie zawiera zabudowy ani oznaczeń; nie jest zasobem Fab/Megascans.

## ADR 0112 — Brown Leather we wnętrzu kabiny (2026-11-12)

[Brown Leather](https://polyhaven.com/a/brown_leather), autor Rob Tuytel, dostawca Poly Haven, [CC0 1.0](https://polyhaven.com/license). Pole źródłowe 40 × 40 cm. Użyte mapy 2K: albedo, normal OpenGL, roughness i AO. Źródłowe adresy pobierania, rozmiary plików i MD5 są zapisane w `art-source/truck/interior/cab_material_scans.json`:

| Mapa źródłowa | MD5 |
|---|---|
| brown_leather_albedo_2k.jpg | 1bd381c43817743a2affdd1ce2d193c7 |
| brown_leather_nor_gl_2k.png | 79e5a78506947a412d2b739a4bec34b4 |
| brown_leather_rough_2k.jpg | 95b48a5c95b02d87dadee46c26f1cfb5 |
| brown_leather_ao_2k.jpg | 4ff0006acb807b9ddccd387a093d89b8 |

Pochodne gry: istniejące pary Detail/Normal materiałów `MI_Cab_Leather` oraz `MI_Cab_Plastic`, rozdzielczości High/Medium/Low 1024/512/256. Konwerter `tools/blender/truck/interior/cc0_leather.py` wykonuje kadrowanie, neutralizację wariacji barwy, pakowanie kanałów, normalizację normalnych i łączenie przeciwległych krawędzi. Skóra używa pola około 12 cm. Plastic jest osłabioną i przeskalowaną pochodną tłoczenia skóry (20 cm źródła na kafel 10 cm), **nie skanem tworzywa deski**. Kolor bazowy i dotychczasowa perforacja pozostają projektowe. Oryginały w ignorowanym `art-source/truck/interior/cc0/_raw/brown_leather/`; bez zasobów Fab/Megascans w tym zestawie. Szczegóły przetwarzania i ograniczenia: `art-source/truck/interior/cc0/README.md`.

## Life r3 — referencje analityczne (nie zasoby gry)
Greg Schechter, 2200 km Later, oraz Nenad Stojkovic, Dirty back car window: CC BY 2.0; strony źródłowe, licencja i miniatury z atrybucją w artifacts/life-r3/refs/REFERENCES.md. Johann H. Addicks: wyłącznie udostępniona jako PD miniatura 250 px Salt coverd car during winter P1020038, bez oryginału. Brak kopiowania znaków/logo/tablic do gry.

## ADR 0120 r2 — wariant materiału znaków oparty o URP Lit

Szkielet `FurnitureSign.shader` oraz część funkcji Forward w
`FurnitureSignForward.hlsl` pochodzą z zainstalowanego pakietu Unity URP:
com.unity.render-pipelines.universal, copyright © 2020 Unity Technologies ApS,
[Unity Companion License](https://unity.com/legal/licenses/unity-companion-license).
Pozostałe przebiegi i funkcje są używane bezpośrednio z pakietu.
Własny dodatek to analityczny odblask i czytnik stanu istniejących reflektorów.
Wersja źródeł, hashe i skrypt odtworzenia są w
`artifacts/furniture-r2/24h/candidate-src/provenance.json` oraz
`artifacts/furniture-r2/24h/prepare-sign-prototype.ps1`. Nie użyto grafiki producentów folii.

### Kominy EC — uzupełnienie referencji ADR 0116 r3

`20200711 073128 Elektrociepłownia Białystok` — Rakoon, [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:20200711_073128_Elektrociep%C5%82ownia_Bia%C5%82ystok.jpg), [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).
Lokalna referencja jest pomniejszoną kopią 3840×2160; pary w artifacts/landmarks-r3
jawnie opisują kadrowanie, zmianę rozmiaru i autora. Oryginał 4608×2592 nie został
lokalnie zweryfikowany. Starsze `EC_Białystok.jpg` — Hiuppo, CC BY-SA 2.5
([strona pliku](https://commons.wikimedia.org/wiki/File:EC_Bia%C5%82ystok.jpg)) —
pozostaje osobną referencją z 2007 r.; jej szachownicy i logo nie przeniesiono do modelu.

`art-source/world/landmarks/ec_chimney_single/` i `ec_chimney_multi/` powstają
z własnego kodu `tools/worldgen/streetscape/ec_chimneys.py` i danych
`Data/Regions/bialystok-industrial-c/ec_chimneys.json`. Nie zawierają pikseli zdjęć,
logo ani cudzej geometrii. Odwołania do źródeł i robocze wymiary są w konfiguracji.
Położenia i obrysy: © OpenStreetMap contributors, ODbL; wysokości gruntu: istniejący NMT GUGiK.
Wymiary techniczne jednoprzewodowego komina pochodzą z opisu zamówienia ENEA 2025,
H 120 m wieloprzewodowego potwierdza tekstowy rekord EMKA. Zamknięta fotografia EMKA
nie jest dystrybuowanym assetem ani otwartą referencją obrazową D43.
