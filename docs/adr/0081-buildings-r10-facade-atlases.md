# ADR 0081: Zabudowa r10 — atlasy fasad (LOD0), rzędy kondygnacji (LOD1), prefabrykowany płot betonowy

Status: propozycja (world-builder, gałąź `worktree-agent-ac404823e7d8b56e7`), 2026-11-10. Uzupełnia ADR 0012/0015 (LOD1
zabudowy, „far facade”), ADR 0022 (zestawy PBR), ADR 0063 (skany CC0), ADR 0067 (`set_tile`, atlasy-pasy).

## Kontekst
Runda bazowa r10 (`artifacts/buildings-r10/base/`): okna bloków, biur i domów to jednolite czarne szyby w białej ramie
z geometrii (4 quady ramy + słupek = 20 trójkątów na okno), każde okno identyczne; LOD1 rysował siatkę okien shaderem
z TEXCOORD_1 (jeden prostokąt szkła na przęsło). Balustrady balkonów — jedna szara blacha. Płot betonowy (OSM
`barrier=wall`) — wstęga pochylona po terenie z jedną kafelkowaną teksturą. Zdjęcia CC0 bloku przy Rondzie Putry
(Wikimedia Commons, `artifacts/buildings-r10/refs/cm1215374*.jpg`) pokazują to, czego brakowało: firanki, rolety,
kwiaty, różne balustrady, zabudowy balkonów, anteny, pranie.

## Decyzja
1. **`facade_atlas`** (zestaw PBR 16 × 16 m, kalibrowany, `set_tile`, UV0 w metrach atlasu): 103 komórki — okna z ramą
   i tym, co za szybą, drzwi balkonowe, drzwi wejściowe, bramy garażowe, fronty balustrad, zabudowy balkonów,
   klimatyzatory, czerpnie, skrzynki, próbki kolorów. Układ: `tools/worldgen/streetscape/facade_atlas.py` (czysty
   Python, wspólny kontrakt), malarze: `art-source/world/materials/_src/sets_buildings.py`. Wszystko z kodu, bez
   zdjęć i bez generatorów AI.
2. **LOD0**: wypełnienie otworu = komórka atlasu (`buildings_mesh.cells`), ościeża i parapet zostają geometrią,
   rama i słupki znikają (są w komórce). Balkon: front balustrady z komórki `balf`, 14 % zabudów, 18 % anten,
   30 % prania; klimatyzatory przy 5 % okien bloków i 10 % okien biur (udziały WORKING_VALUE). Hale: czerpnie
   ścienne, jedna drabina z koszem na większą halę (odstępy wg PN-EN ISO 14122-4, wymiary WORKING_VALUE).
3. **LOD1**: `facade_far` (zestaw modulacyjny 24 × 40,2 m, 14 rzędów po 8 przęseł złożonych z tych samych komórek).
   Strefa okien = jeden quad na paczkę kolejnych rzędów (`FA.far_plan`), dwa quady marginesów i attyka dopięta do
   ostatniej paczki; UV0 w metrach atlasu rzędów, bez TEXCOORD_1 i bez shadera siatki. LOD0 czyta **ten sam plan**,
   więc oba LOD-y pokazują te same okna w tych samych miejscach. Parapet i wysokość okna skalują się z wysokością
   kondygnacji (k = sh / 2,8 m) na obu LOD-ach.
4. **Typologia**: biuro ma jedną stolarkę na budynek (biała PVC albo antracyt), bloki mieszają okna jak na zdjęciach;
   balkony od parteru (wysoki parter); kolor akcentu tylko na faktycznych ścianach szczytowych (wcześniej każda
   krawędź < 16 m, przez co bloki ze skokami w rzucie wychodziły całe w kolorze akcentu).
5. **Płot betonowy** (`furniture.concrete_fence`, zestaw `fence_concrete` 16 × 4,5 m, hybryda ze skanem CC0
   „Concrete Floor Worn 001”): przęsła 2,0 m od narożnika do narożnika, każde poziome i schodkowane na słupkach,
   cztery płyty 0,5 m albo panel ramowy (jeden typ na ogrodzenie), inny odlew na każdym licu, słupki 12 × 14 cm
   wystające 8 cm; przęsła ze sprayem / zamalowane rzadko (ok. 1 na 7).
6. **Koszt LOD1**: gzyms attyki LOD1 to jedna pochylona ściana zamiast czoła i wierzchu (−2 trójkąty na krawędź),
   maszynownie bez spodu — płaci za quady rzędów.

## Liczby
Patrz `tools/worldgen/streetscape/STATUS-buildings-r10.md` (tabela budżetu: `streetscape_qa.json` baza vs r10) i raport
końcowy agenta. Pamięć tekstur (szacunek ASTC z mipami z `materials_spec.json`): `facade_atlas` 39,8 / 7,8 / 1,4 MB,
`facade_far` i `fence_concrete` — wartości w `materials_spec.json` (High / Medium / Low). To nowy koszt pamięci;
wcześniej LOD1 nie miał tekstury okien.

## Znane braki / UNVERIFIED
- Nie zmierzone na telefonie (zakaz adb w tym zadaniu); budżet = estymata generatora + `stats.txt` z edytora.
- Kolory tynków i udziały (zabudowy, anteny, pranie, klimatyzatory) to WORKING_VALUE do sprawdzenia ze zdjęciami
  właściciela.
- Okna LOD0 są płaskie w ościeżu (rama namalowana); z bliska pod ostrym kątem widać brak głębi ramy.
- `facade_far` jest zestawem modulacyjnym: zawartość okien i balustrady lekko przejmują kolor ściany.
- `FarFacadeMaterial` / `window_grid` w `RegionImporter.cs` zostają jako martwa ścieżka (do usunięcia przez lidera).
