# Generacja świata: drogi i teren (Etap 3–4)

Generator siatek dróg i terenu dla kafla regionu. Pierwsze wdrożenie: `bialystok-industrial-c` (Andersa / Rondo Putry → DK8/DK19, baza Kwadrat Park). Wszystko powstaje z danych (OSM + GUGiK), deterministycznie, jedną komendą.

## Komendy (z katalogu repo)

```
uv run --project tools/worldgen tools/worldgen/build_region.py --region bialystok-industrial-c   # graf, NMT, budynki (geo-worldgen)
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c [--context]
blender -b --factory-startup -P tools/blender/world/render_control.py -- --region bialystok-industrial-c --out artifacts/visual/world-c/final --res 1600x900 --samples 64
uv run --project tools/worldgen tools/worldgen/roads/qa_ortho.py --region bialystok-industrial-c --render artifacts/visual/world-c/final/ortho_putry.png --out artifacts/visual/world-c/final/ortho_putry_overlay.jpg
uv run --project tools/worldgen pytest tests/gis -q
```

`--context` ponownie wyciąga `generated/osm_context.json` (przejścia, sygnalizacja, chodniki z OSM) z cache wycinka OSM. Bez tej flagi generator nie potrzebuje pliku OSM (tylko grafu, NMT i tego JSON-a). Pełny build trwa ok. 50 s, render 6 kamer ok. 3 min (EEVEE).

## Wejścia i wyjścia

| | Plik | W gicie |
|---|---|---|
| wejście | `Data/Regions/<id>/{region.yaml, roads.graph.json, terrain.json, buildings.geojson}` | tak |
| wejście | `Data/Regions/<id>/overrides.yaml` (authored overrides) | tak |
| wejście | `Data/Regions/<id>/generated/osm_context.json` (ODbL) | tak |
| wejście | `Data/raw/derived/<id>/heightmap_2049.r16` (NMT 1 m, EVRF2007) | nie |
| wyjście | `Data/raw/derived/<id>/world/chunk_<ci>_<cj>.glb` (64 pliki, ~270 MB razem, max 5,6 MB) | **nie** (regenerowalne) |
| wyjście | `Data/Regions/<id>/generated/world_manifest.json` — chunki, granice, sha256, materiały, typy nawierzchni, sha256 wejść | tak |
| wyjście | `Data/Regions/<id>/generated/roads_qa.json` — szerokości i ich źródła, pochylenia, skrzyżowania, mosty, oznakowanie, low_confidence | tak |
| wyjście | `Data/Regions/<id>/generated/control_cameras.json` — kamery kontrolne (do Blendera i później do Unity visual-qa) | tak |
| wyjście | `Data/raw/derived/<id>/world/preview_{buildings,trees}.json`, `terrain_conformed.npy` — tylko kontekst renderów / testy | nie |

**Układ:** lokalne metry względem kotwicy z `region.yaml` (E = x − origin.x, N = y − origin.y), wysokości bezwzględne EVRF2007 (ADR 0003). **glTF:** (x, y, z) = (−E, U, N); importery Unity (glTFast, UnityGLTF) negują x, więc w Unity wychodzi X = wschód, Y = góra, Z = północ. Blender importuje jako (−E, −N, U); skrypt renderu obraca to o 180° wokół Z.

**Węzły w każdym GLB:** `terrain_lod0..3` (1/2/4/8 m, ze skirtami; LOD0 = 4 prymitywy po 129² wierzchołków → indeksy 16-bit), `road` (jezdnie, łaty skrzyżowań, krawężniki, chodniki), `bridge` (pomosty, spody, balustrady, przyczółki, podpory), `markings` (oznakowanie poziome jako decal mesh +6 mm), `road_collision` (uproszczona kolizja, osobny prymityw na typ nawierzchni). Sugerowane progi LOD terenu są w manifeście.

## Jak to działa

1. **Łańcuchy** (`roads/network.py`): krawędzie grafu sklejone przez węzły stopnia 2; oś wygładzona Gaussem z zachowaniem końców (p95 przesunięcia względem osi OSM 0,16 m, max 1,25 m na ostrych załamaniach dróg serwisowych).
2. **Przekrój** z tagów: `lanes`, `oneway`, klasa (`highway` → klasa techniczna, WORKING_VALUE), szerokość z BDOT10k przycięta do zakresu z rozporządzenia. Szerokość pasa: PTB2022 § 17 ust. 1 (GP 3,50 / G 3,50 / Z 3,00 / L 2,75 / D 2,50 m standardowo; trudne warunki 3,25 / 3,00 / 2,75 / 2,50 / 2,25), jezdnia jednopasowa ≥ 3,50 m (§ 17 ust. 3). Opaska GP 0,50 m (§ 23 ust. 7–8, trudne warunki). Krawężnik 13 cm (WORKING_VALUE w przedziale 12–15 cm), chodnik 2,0 m (≥ 1,80 m, § 29 ust. 1) tam, gdzie równolegle biegnie chodnik z OSM, w przeciwnym razie pas zieleni. Pas dzielący jezdni dwujezdniowych wykrywany z przeciwbieżnej jezdni jednokierunkowej po lewej. Profil zamiejski (pobocze + rów, § 23 ust. 10) jest zaimplementowany, ale cały kafel to teren zabudowany.
3. **Skrzyżowania** (`roads/junctions.py`): węzły stopnia ≥ 3, łączone w klastry, gdy odcinek między nimi jest krótszy niż potrzebne łuki (max średnica 30 m; ronda nigdy nie są sklejane w jeden klaster). Narożniki: łuk krawężnika o promieniu R (WORKING_VALUE: GP 15, G 12, Z 10, L/D 8 m) styczny do obu krawędzi jezdni, nos pasa dzielącego / wyspy kanalizującej (półokrąg), rozwidlenie (gore), krawędź prosta lub zwężenie. Łata skrzyżowania = wielokąt CCW z przekrojów końcowych ramion + łuków; triangulacja „polar” z jądra wielokąta, inaczej Delaunay z odzyskaniem brzegu, a dla wielokątów samoprzecinających się (21 z 205) naprawa przez `make_valid` (lista w `roads_qa.json`). Wysokość wewnątrz = ważona mieszanka płaszczyzn ramion. Wierzchołki przekrojów końcowych są wspólne z taśmami jezdni (test szczelności szwów).
4. **Ronda**: pierścień z OSM (`junction=roundabout`), spadek poprzeczny na zewnątrz 2 %, wyspa środkowa z przejazdowym pasem z kostki (2 m, krawężnik 4 cm) i wysokim krawężnikiem, wyspy kanalizujące między wlotem a wylotem (nosy). Rondo Putry i Rondo Bieżeństwa są dwupoziomowe: Andersa przechodzi wiaduktem nad pierścieniem.
5. **Niweleta** (`roads/profile.py`): mediana NMT w poprzek jezdni co 0,5 m → wygładzanie Whittakera z twardymi warunkami w węzłach; λ rośnie, aż krzywizna pionowa spełni minimalny promień (WORKING_VALUE: GP 800 m, G 600, Z 400, L 250, D 150). Mediana RMS względem NMT 0,01 m, na mostach dane mają wagę 0 (pomost interpolowany między przyczółkami). Pochylenie sprawdzane na bazie 10 m względem § 20 ust. 2 i § 62 ust. 2 (łącznice ≤ 7 %): **0 przekroczeń** (max: droga serwisowa 10,5 % przy limicie 12 %).
6. **Spadek poprzeczny**: 2 % (WORKING_VALUE — § 18 jest opisowy): daszkowy na jezdniach dwukierunkowych, jednostronny na jednokierunkowych, na łukach R < 400 m 2,5 % do wewnątrz z rampą 10 m.
7. **Mosty**: z `bridge`/`layer`. Pomost + kapy 1,5 m + balustrada (poręcz 1,1 m, pochwyt środkowy, słupki co 2 m), spód 1,2 m, przyczółki i podpory co ≤ 30 m omijające drogi pod spodem. Wszystko **low_confidence** (OSM nie opisuje konstrukcji).
8. **NMT pod wiaduktami**: NMT 2025 pod wiaduktem Andersa nad Rondem Bieżeństwa zawiera pomost jako „grunt” (wyspa ronda wychodziła przez jezdnię wiaduktu). Generator buduje geometrię dwa razy: po pierwszym przebiegu rasteryzuje pomosty i zastępuje komórki NMT, które leżą w grubości pomostu (fizycznie niemożliwe dla gruntu), interpolacją harmoniczną z otoczenia (12 545 węzłów). Drugi przebieg liczy niwelety i teren na poprawionym NMT.
9. **Teren** (`terrain_mesh/`): rasteryzacja wszystkich naziemnych powierzchni drogi do siatki 1 m; pod drogą teren 0,35 m niżej (kołnierze 0,5 m pod krawędziami chodników zasłaniają uskok, brak z-fightingu); poza drogą najbliższa krawędź drogi (EDT) + berma 1 m + skarpa 1:1,5 (nasyp/wykop) aż do NMT. Pod pomostami teren ≥ 0,3 m pod spodem pomostu. Chunki 256 m, LOD 1/2/4/8 m; LOD > 0 bierze minimum z okna przy drodze, więc grubszy teren nigdy nie przebija jezdni.
10. **Oznakowanie** (`roads/markings.py`): wymiary z załącznika nr 2 do rozporządzenia z 3.07.2003 (t.j. Dz.U. 2019 poz. 2311), odczytane z rysunków: P-1a 4/8 m, P-1b 2/4 m, szerokość 0,12 m; P-2a ≥ 20 m przed wlotem z sygnalizacją lub `turn:lanes`; P-4; P-7b 0,24 m na drogach dwujezdniowych (GP); P-10 pasy 0,5/0,5 m, szerokość przejścia 4,0 m, tylko w węzłach OSM `highway=crossing` innych niż `unmarked`/`no`; P-14 prostokąty 0,75 × 0,5 m co 1,0 m na wlotach z sygnalizacją (≥ 2 m przed przejściem); P-13 trójkąty 0,5/0,7 m na wlotach rond i podporządkowanych do dróg G/GP; strzałki P-8 krótkie 5,0 m (≤ 70 km/h) / długie 7,5 m, co 15/30 m, z `turn:lanes`. Liczniki w `roads_qa.json`.
11. **Kolizja**: osobna, gładka siatka (stacje co 4 m, przekrój krawędź–oś–krawędź, krawężnik z licem i górą, bez kołnierzy), osobny prymityw na typ nawierzchni (`asphalt`, `concrete_kerb`, `paving_stones`, `grass`).
12. **Eksport**: własny zapis GLB (bez znaczników czasu, posortowany JSON, float32) → te same wejścia dają identyczne bajty. Test porównuje sha256 z manifestem zapisanym przez osobny proces.

Wszystkie liczby projektowe z odnośnikami i oznaczeniem `WORKING_VALUE` są w `tools/worldgen/roads/standards.py`.

## Authored overrides

`Data/Regions/<id>/overrides.yaml` jest stosowany po wczytaniu grafu, przed geometrią, i adresuje obiekty stabilnymi identyfikatorami z OSM (`edge`, `osm_way`, `node`). Dzięki temu przeżywa każdą regenerację. Cel, którego już nie ma w danych, trafia do `overrides_stale` w manifeście i w raporcie QA; nic nie jest pomijane po cichu. Obsługiwane pola: `lanes`, `lane_width`, `edge_strip`, `surface`, `side_left/side_right` (`sidewalk`, `verge`, `median`, `flush`), a dla węzła `curb_radius` i `z`.

Przykład w repo (baza Kwadrat Park): droga dojazdowa do placu ma w OSM tylko `highway=service`, więc generator dał klasę D (2 × 2,50 m). Ortofoto pokazuje ok. 7 m asfaltu, więc override ustawia 2 × 3,50 m. Na placu nie ma krawężników (`flush`), a łuk wjazdu ma 15 m dla naczepy. Każdy wpis ma `reason`, `confidence` i `verify` (pozycję z listy zdjęć właściciela). Test `test_overrides_applied_and_not_stale` pilnuje, że wpisy działają po regeneracji.

## Kontrola jakości

- Testy: `tests/gis/test_world_roads.py` (szczelność szwów skrzyżowań: >300 szwów, każdy wspólny wierzchołek po wierzchołku i krawędź po krawędzi; pochylenia ≤ limit; brak szumu NMT w niwelecie; wierzchołki jezdni ≤ 0,2 m od wygenerowanego przekroju; przesunięcie osi przez wygładzanie p95 ≤ 0,5 m; teren ≥ 0,30 m pod drogą; wspólne krawędzie chunków; deterministyczność; struktura GLB; overrides; wymiary z rozporządzeń).
- Rendery kontrolne i porównanie z ortofoto: `docs/reports/visual/world-c/README.md`.

## Znane braki (kolejne kroki)

- **Place, parkingi i podwórza** nie są modelowane: poza drogami jest trawa (widać to na kamerze bramy Kwadrat Parku, gdzie w rzeczywistości jest utwardzony plac). Następny krok: BDOT10k `OT_PTKM_A`/`OT_PTPL_A` + OSM `amenity=parking`, `landuse=industrial` z nawierzchnią.
- **Chodniki oddalone od krawężnika** (ścieżki OSM > 3,5 m od jezdni) nie są generowane.
- **21 łat skrzyżowań** naprawianych przez `make_valid` (nakładające się rozwidlenia łącznic, gęste klastry przy Rondzie Putry): bez dziur, ale z możliwym nakładaniem się na taśmy i krawężnikami tylko na zewnętrznym obrysie.
- **Rozwidlenia o różnej szerokości** dają uskok krawężnika zamiast płynnego zwężenia (`kwadrat_park_gate`); potrzebne jest zwężanie `hw` na ramieniu.
- **Mosty**: wymiary konstrukcji i rozstaw podpór to WORKING_VALUE; zakres `bridge` z OSM bywa krótszy niż obiekt (Bieżeństwa).
- **Szerokości**: BDOT10k (zaokrąglone do 0,5 m) albo standard klasy. Trzeba je potwierdzić pomiarem na ortofoto 5 cm lub zdjęciami.
- Roślinność i budynki w renderach są tylko kontekstem (BDOT10k `OT_PTLZ_A`/`OT_PTRK_A` + bryły LoD1) i nie są zasobami gry.
- Import Unity (`scripts/import-region.ps1`) jeszcze nie istnieje; manifest jest gotowy jako jego wejście.
