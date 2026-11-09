# Generacja świata: drogi, teren i otoczenie (Etap 3–4)

Generator siatek dróg i terenu dla kafla regionu. Pierwsze wdrożenie: `bialystok-industrial-c` (Andersa / Rondo Putry → DK8/DK19, baza Kwadrat Park). Wszystko powstaje z danych (OSM + GUGiK), deterministycznie, jedną komendą.

## Komendy (z katalogu repo)

```
uv run --project tools/worldgen tools/worldgen/build_region.py --region bialystok-industrial-c   # graf, NMT, budynki (geo-worldgen)
uv run --project tools/worldgen python -c "import sys; sys.path.insert(0,'tools/worldgen'); from roads import pipeline; from streetscape import sources as s; s.write('bialystok-industrial-c', s.extract(pipeline.load_region('bialystok-industrial-c')))"   # tylko po zmianie OSM/BDOT
uv run --project tools/worldgen tools/worldgen/streetscape/leaf_textures.py          # tekstury liści/kory/trawy (raz)
blender -b --factory-startup -P tools/blender/world/make_trees.py                    # biblioteka drzew (raz)
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c [--context]
blender -b --factory-startup -P tools/blender/world/render_control.py -- --region bialystok-industrial-c --out <katalog absolutny> --light both --res 1600x900 --samples 64
uv run --project tools/worldgen tools/worldgen/roads/qa_ortho.py --region bialystok-industrial-c --render artifacts/visual/world-c/final/ortho_putry.png --out artifacts/visual/world-c/final/ortho_putry_overlay.jpg
uv run --project tools/worldgen pytest tests/gis -q
```

`--context` ponownie wyciąga `generated/osm_context.json` (przejścia, sygnalizacja, chodniki z OSM) z cache wycinka OSM. Bez tej flagi generator nie potrzebuje pliku OSM (tylko grafu, NMT i tego JSON-a). Pełny build trwa ok. 2 min (w tym otoczenie), render 11 kamer × 2 oświetlenia ok. 30 min (EEVEE).

## Wejścia i wyjścia

| | Plik | W gicie |
|---|---|---|
| wejście | `Data/Regions/<id>/{region.yaml, roads.graph.json, terrain.json, buildings.geojson}` | tak |
| wejście | `Data/Regions/<id>/overrides.yaml` (authored overrides) | tak |
| wejście | `Data/Regions/<id>/generated/osm_context.json` (ODbL) | tak |
| wejście | `Data/raw/derived/<id>/heightmap_2049.r16` (NMT 1 m, EVRF2007) | nie |
| wejście | `Data/Regions/<id>/generated/streetscape_sources.json` — place, parkingi, ścieżki, ekrany, drzewa, ogrodzenia, słupy (OSM ODbL + BDOT10k, EPSG:2180) | tak |
| wyjście | `Data/raw/derived/<id>/world/chunk_<ci>_<cj>.glb` — wariant High (64 pliki, ~390 MB) | **nie** (regenerowalne) |
| wyjście | `Data/raw/derived/<id>/world/chunk_<ci>_<cj>.low.glb` — wariant Low/Medium (bez terenu 1 m i budynków LOD0; normalne int8 `KHR_mesh_quantization`, kolory 8-bit, teren bez UV0; ~85 MB) | **nie** |
| wyjście | `Data/raw/derived/<id>/world/instances_<ci>_<cj>.json` — instancje punktowe (latarnie, znaki, sygnalizatory, wiaty, bramy, słupy, drzewa) | **nie** |
| wyjście | `art-source/world/props/street_props.glb` + `props_meta.json` — prototypy wyposażenia (LOD0/LOD1/kolizja), lica znaków osadzone | tak |
| wyjście | `art-source/world/vegetation/trees.glb` (LOD0/LOD1) + `trees_lod2.glb` (impostory) + `trees_meta.json` | tak |
| wyjście | `art-source/world/{signs,textures,vegetation}/*.png` — lica znaków, siatka panelu ogrodzenia, numery ramp, liście, kora, kępy trawy, impostory | tak |
| wyjście | `Data/Regions/<id>/generated/streetscape_qa.json` — źródła i powierzchnie placów, typologie budynków, rampy, liczniki wyposażenia i drzew, **tabela budżetu siatek** | tak |
| wyjście | `Data/Regions/<id>/generated/world_manifest.json` — chunki, granice, sha256, materiały, typy nawierzchni, sha256 wejść | tak |
| wyjście | `Data/Regions/<id>/generated/roads_qa.json` — szerokości i ich źródła, pochylenia, skrzyżowania, mosty, oznakowanie, low_confidence | tak |
| wyjście | `Data/Regions/<id>/generated/control_cameras.json` — kamery kontrolne (do Blendera i później do Unity visual-qa) | tak |
| wyjście | `Data/raw/derived/<id>/world/terrain_conformed.npy` — testy | nie |

**Układ:** lokalne metry względem kotwicy z `region.yaml` (E = x − origin.x, N = y − origin.y), wysokości bezwzględne EVRF2007 (ADR 0003). **glTF:** (x, y, z) = (−E, U, N); importery Unity (glTFast, UnityGLTF) negują x, więc w Unity wychodzi X = wschód, Y = góra, Z = północ. Blender importuje jako (−E, −N, U); skrypt renderu obraca to o 180° wokół Z.

**Węzły w każdym GLB:** `terrain_lod0..3` (1/2/4/8 m, ze skirtami; LOD0 = 4 prymitywy po 129² wierzchołków → indeksy 16-bit; `COLOR_0` = maski podłoża: R odległość od drogi/placu /20 m, G ściółka leśna, B trawa niekoszona, A goła ziemia), `road` (jezdnie, łaty skrzyżowań, krawężniki, chodniki; `TEXCOORD_1` = współrzędna pasa i odległość od krawędzi jezdni → koleiny, brud przy krawężniku), `bridge`, `markings` (decal mesh +6 mm), `paved` (place, parkingi, fartuchy ramp, ścieżki, obrzeża; `TEXCOORD_1` = odległość od krawędzi placu i od ściany), `buildings` (LOD0 z otworami i rampami), `buildings_lod1` (bryły LOD1), `furniture` (ogrodzenia, bariery, ekrany, mury, przewody), `road_collision` (kolizja: drogi, place, budynki LOD1, ogrodzenia/bariery; tylko pozycje + indeksy, osobny prymityw na materiał/typ nawierzchni). Wariant `.low.glb` ma te same nazwy węzłów bez `terrain_lod0` i `buildings`. Pozycje są kwantowane do 1 mm, normalne i UV do 1e-4 przed zapisem float32, żeby drobne różnice numeryczne między środowiskami Pythona nie zmieniały bajtów (zgłoszenie agenta Unity: 10/64 chunków z innym sha256). Sprawdzone: build w świeżym venv (`UV_PROJECT_ENVIRONMENT` w nowym katalogu, ten sam `uv.lock`) daje 128/128 identycznych plików (High + Low). Inny system operacyjny lub CPU nie był testowany.

**Instancje** (`instances_<ci>_<cj>.json`): `{p: prototyp, e, n, z, yaw [, sz]}`; `yaw` obraca lokalne +y prototypu (front: lico znaku, wysięgnik latarni w stronę jezdni), `sz` skaluje oś pionową (wysokość słupka znaku). Drzewa: `{p: tree_<gatunek>, v: wariant, h: wysokość, lean, yaw}`, skala = `h / href_m` z `trees_meta.json`. Prototypy wyposażenia: `street_props.glb` w tej samej konwencji osi co chunki (glTF = (−x, z, y)); drzewa eksportuje Blender (`export_yup`), więc ich lokalna oś pionowa to glTF +Y. Importer powinien je instancjonować (GPU instancing / `Graphics.RenderMeshInstanced`), a nie scalać.

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

## Otoczenie (`tools/worldgen/streetscape`, Etap 3)

Etap otoczenia uruchamia się w `build_world.py` po drogach i oznakowaniu (`streetscape/stage.py`). Kolejność:

1. **Źródła** (`sources.py`): z wycinka OSM i BDOT10k powiatu 2061 wyciągane są place (`OT_PTPL_A` z `MATERIALNAWIERZCHNI`), parkingi i stacje paliw (`OT_KUKO_A`, OSM `amenity=parking`), ścieżki i drogi rowerowe (`OT_SKRP_L`), ekrany akustyczne (`OT_OIKM_L`), przystanki (`OT_OIKM_P`, OSM `highway=bus_stop`), drzewa pojedyncze, szpalery i kępy (`OT_OIPR_P/L`), lasy z kategorią (`OT_PTLZ_A`), mury oporowe (`OT_BUUO_L`), słupy i linie energetyczne (`OT_BUWT_P`, `OT_SULN_L`) oraz z OSM ogrodzenia (`barrier=*`), bramy, szlabany, latarnie, ławki i kosze. Wynik to `generated/streetscape_sources.json` (~440 KB).
2. **Budynki** (`buildings_mesh.py`): typologia z funkcji BDOT10k i powierzchni (hala, biurowiec/usługi, blok, dom, budynek gospodarczy, wiata). Ściany mają prawdziwe otwory (dekompozycja kolumnowa) z ościeżami. Hala: cokół betonowy, płyta warstwowa (UV u = metry wzdłuż ściany, v = metry nad gruntem; żebra i styki paneli w materiale), obróbka attyki, dach z membraną i attyką, świetliki na halach > 3000 m², drzwi i okna taśmowe. Magazyn z elewacją od strony placu (≥ 60% pasa 2–14 m przed ścianą utwardzone) dostaje rampy co 4 m: brama segmentowa 3 × 3 m na wysokości 1,20 m, uszczelnienie (fartuchy z żółtym pasem), odboje, pomost wyrównawczy z pasami ostrzegawczymi, numer rampy (atlas cyfr), sygnalizator, prowadnice kół oraz betonowy fartuch 18 m przed rampami. Dom: dach dwuspadowy (typ dachu i wysokość okapu z LoD2, nachylenie 35°, WORKING_VALUE). Warstwy: `buildings` (LOD0), `buildings_lod1`, kolizja.
3. **Place** (`paved.py`): priorytet override → fartuchy ramp → OSM parking z `surface` → BDOT plac/parking → OSM parking bez `surface` → ścieżki. Całość jest przycinana obrysem jezdni (z trójkątów drogi) i budynków. Wysokość: wygładzony NMT (σ 3 m) wtopiony w wysokość krawędzi drogi na 12 m. Siatka dzielona co 4 m. Nawierzchnie: kostka szara (`yard_paving`), beton z nacięciami co 5 m (`yard_concrete`), płyty drogowe 3 × 1,5 m (`yard_slabs`), asfalt, kruszywo, czerwona droga rowerowa, kostka chodnikowa. Obrzeże betonowe 8 × 30 cm tylko przy kostce i tylko tam, gdzie plac nie styka się z jezdnią. Teren jest konformowany do dróg i placów razem.
4. **Teren** (`conform.tidy`): wąskie zamknięte pasy (pasy dzielące, wyspy, szczeliny droga–plac) dostają harmoniczną powierzchnię między krawędziami dróg, bez garbów. Pas 1,5–12 m od drogi jest wygładzany (σ 1,2 m), co usuwa fasety stożka nasypu.
5. **Przekrój zamiejski** (`network.assign_sides`): strona jezdni GP/G przy ≥ 70 km/h bez chodnika ani ścieżki w promieniu 7 m dostaje pobocze utwardzone 1,0 m i nieutwardzone 0,75 m, rów i brak krawężnika. Pas dzielący takiej drogi (lub drogi 90 km/h) ma opaskę 0,5 m, trawę i barierę. Drogi serwisowe biegnące przez plac z BDOT/OSM są bez krawężnika.
6. **Wyposażenie** (`furniture.py`, reguły w docstringu, liczby w `standards.py`):
   - latarnie co 30–36 m wg klasy drogi;
   - A-7 + C-12 na każdym wlocie ronda;
   - A-7 i D-1 na skrzyżowaniach bez sygnalizacji z drogą wyższej klasy;
   - B-20 z OSM;
   - B-33 na początku każdego łańcucha z `maxspeed` ≠ 50, powtarzany za skrzyżowaniem (tam ograniczenie się kończy);
   - D-6 po obu stronach przejść bez sygnalizacji i D-15 na przystankach;
   - schematyczne E-2 przy łącznicach z `destination`;
   - S-1 na wlotach skrzyżowań z sygnalizacją (maszt z wysięgnikiem przy ≥ 3 pasach);
   - bariery stalowe na mostach, pasach dzielących dróg zamiejskich i nasypach > 2 m;
   - ekrany akustyczne, ogrodzenia panelowe 3D na cokole, ogrodzenia z płyt betonowych, mury oporowe z poręczą, linie energetyczne ze zwisem.

   Wysokość dolnej krawędzi znaku: 2,00 m, a na chodniku 2,20 m (Tabl. 1.11 zał. 1, Dz.U. 2021 poz. 2066). Lica znaków to nasze własne rysunki wektorowe (`signs.py`).
7. **Roślinność** (`vegetation.py`, `tools/blender/world/make_trees.py`):
   - gatunki: sosna, brzoza, olsza, klon, lipa, krzew;
   - rozmieszczenie: siatka z rozrzutem w lasach (miks gatunków wg kategorii BDOT), pas krzewów na skraju lasu, drzewa pojedyncze i szpalery z BDOT/OSM oraz rzadki samosiew na nieużytkach;
   - drzewa: korony z kart liści na rekurencyjnym szkielecie, normalne kart od środka korony, 3 warianty na gatunek;
   - LOD: LOD0, LOD1 i impostor (2 skrzyżowane płaty z renderem ortogonalnym).

   Modele 3D drzew GUGiK (1,07 GB) nie są pobrane, więc pozycje pochodzą z BDOT10k i OSM.
8. **Budżet** (`mesh_budget`): trójkąty i materiały statyczne na chunk (High/Low) oraz szacunek klatki dla kamer kontrolnych wg `LOD_POLICY`.

Rendery kontrolne (`render_control.py`) budują materiały proceduralne z tymi samymi maskami, które dostanie shader silnika:
- asfalt: łaty, spękania z zalewaniem, polerowane ślady kół i koleiny z `TEXCOORD_1`, plamy oleju w osi pasa, brud przy krawężniku, szew między pasami;
- krawężnik: segmenty 1 m ze stykami;
- place: fugi, mech przy krawędziach, brud przy ścianach, ślady opon i oleju;
- ściany: zacieki i strefa rozbryzgu przy gruncie;
- teren: z masek podłoża, kępy trawy w promieniu 55 m od kamery (wyższe w trawie niekoszonej).

Oświetlenie `--light overcast|lowsun|both`: AgX, bez bloomu, winiety i aberracji. Horyzont to mgiełka i daleka płaszczyzna terenu.


## Authored overrides

`Data/Regions/<id>/overrides.yaml` jest stosowany po wczytaniu grafu, przed geometrią, i adresuje obiekty stabilnymi identyfikatorami z OSM (`edge`, `osm_way`, `node`). Dzięki temu przeżywa każdą regenerację. Cel, którego już nie ma w danych, trafia do `overrides_stale` w manifeście i w raporcie QA; nic nie jest pomijane po cichu. Obsługiwane pola: `lanes`, `lane_width`, `edge_strip`, `surface`, `side_left/side_right` (`sidewalk`, `verge`, `median`, `flush`), a dla węzła `curb_radius` i `z`. Otoczenie: `target: {building: <id z buildings.geojson>}` z `set: {typology, hero, docks, wall_material, max_docks_per_facade}` (przykład: magazyn Kwadrat Park, który BDOT10k opisuje jako obiekt handlowo-usługowy) oraz `kind: paved_area` z `polygon_epsg2180` i `material` (plac, którego nie ma w danych).

Przykład w repo (baza Kwadrat Park): droga dojazdowa do placu ma w OSM tylko `highway=service`, więc generator dał klasę D (2 × 2,50 m). Ortofoto pokazuje ok. 7 m asfaltu, więc override ustawia 2 × 3,50 m. Na placu nie ma krawężników (`flush`), a łuk wjazdu ma 15 m dla naczepy. Każdy wpis ma `reason`, `confidence` i `verify` (pozycję z listy zdjęć właściciela). Test `test_overrides_applied_and_not_stale` pilnuje, że wpisy działają po regeneracji.

## Kontrola jakości

- Testy: `tests/gis/test_world_roads.py` (szczelność szwów skrzyżowań: >300 szwów, każdy wspólny wierzchołek po wierzchołku i krawędź po krawędzi; pochylenia ≤ limit; brak szumu NMT w niwelecie; wierzchołki jezdni ≤ 0,2 m od wygenerowanego przekroju; przesunięcie osi przez wygładzanie p95 ≤ 0,5 m; teren ≥ 0,30 m pod drogą; wspólne krawędzie chunków; deterministyczność; struktura GLB; overrides; wymiary z rozporządzeń).
- Rendery kontrolne i porównanie z ortofoto: `docs/reports/visual/world-c/README.md`.

## Znane braki (kolejne kroki)

- **Place** są tylko tam, gdzie opisują je BDOT10k/OSM. Utwardzenia widoczne na ortofoto, ale nieobecne w danych (np. część placu wokół długiej hali na wschód od Kwadrat Parku), wymagają override `paved_area` po sesji zdjęciowej.
- **21 łat skrzyżowań** naprawianych przez `make_valid` (nakładające się rozwidlenia łącznic, gęste klastry przy Rondzie Putry): bez dziur, ale z możliwym nakładaniem się na taśmy i krawężnikami tylko na zewnętrznym obrysie.
- **Zwężenia na rozwidleniach:** ta sama droga zmieniająca szerokość w węźle (ten sam typ, kierunkowość, różnica połowy szerokości 0,25–1,25 m) jest zwężana skosem 1:10 (`network.taper_forks`, lista w `roads_qa.json` → `fork_tapers`). **Nie** dotyczy to rozdzielenia jezdni dwukierunkowej na dwie jednokierunkowe z wyspą (brama Kwadrat Parku): tam uskok krawężnika jest nadal widoczny i wymaga osobnej geometrii „nosa” rozdzielenia.
- **Mosty**: wymiary konstrukcji i rozstaw podpór to WORKING_VALUE; zakres `bridge` z OSM bywa krótszy niż obiekt (Bieżeństwa).
- **Szerokości**: BDOT10k (zaokrąglone do 0,5 m) albo standard klasy. Trzeba je potwierdzić pomiarem na ortofoto 5 cm lub zdjęciami.
- Import Unity (v2, ADR 0012): `scripts/import-region.ps1` czyta GLB bezpośrednio i piecze siatki per kafel i tier: `WorldC` (Low/Medium, z `.low.glb` + budynki LOD0 do 100 m od trasy startowej) i `WorldC_High` (pełne chunki, w APK tylko z `build-android.ps1 -WorldHigh`). Teren LOD0 drobny tylko w pasie 15 m od dróg/placów. Instancje z `instances_*.json` rysowane GPU instancingiem (`WorldInstances`), drzewa LOD0/LOD1/impostor. **Uwaga dla world-buildera:** 88 instancji stoi na jezdni (`artifacts/world/<id>-props-on-road.txt`: 55 × `lamp_8m`, 24 × `sign_post`, 6 × `lamp_12m`, …; np. `lamp_12m` E 326,6 N −579,6 na wlocie Ronda Bieżeństwa) — importer nie daje im kolizji.
- **Rozmiar:** High ~390 MB (z czego 217 MB to teren 1 m), Low ~85 MB na 4 km². Na telefon trzeba jeszcze kompresji siatek przy buildzie (`EXT_meshopt_compression`, obsługiwane przez glTFast; zwykle 3–5× mniej) albo terenu 1 m tylko w pasie przy drodze. Pomiar na A16 jest przed nami.
- Mesh budget (`streetscape_qa.json` → `mesh_budget`): szacunek klatki dla kamer kontrolnych (klin 120°, bez occlusion cullingu): Low 0,24–0,81 mln trójkątów (cel z docs/06 §6: 0,4–0,6 mln; przekracza go stretch_04 przy Andersa), High 1,0–3,1 mln, a w lesie przy DK8 8,1 mln (do zrobienia: gęstsze impostory, HLOD lasu, occlusion culling). Statycznie na chunk: mediana High 152 tys. / Low 46 tys. trójkątów, max 286 tys. / 126 tys., do 55 materiałów. Liczby klatki trzeba potwierdzić na urządzeniu; politykę LOD opisuje `LOD_POLICY` w `build_world.py` (WORKING_VALUE).
