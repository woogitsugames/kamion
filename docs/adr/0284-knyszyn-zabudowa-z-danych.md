# ADR 0284 — Knyszyn: zabudowa z danych (dachy z ortofoto, klasy obrysów OSM, nadpisania domów)

Status: WIP, 2026-11-16 (knyszyn-look-s23). Numer roboczy — lider potwierdza przy scaleniu. Wymaga oceny
`visual-critic` i właściciela (rozpoznawalność z wysokości oczu, D51).

## Kontekst

Właściciel (z Knyszyna): „dużo brakuje do podobieństwa”. Po ADR 0227 park Rynku, kościół i urząd mają własne
generatory, ale reszta miasta pochodziła z reguł pisanych dla Białegostoku (ADR 0238):

- 149 obrysów spoza BDOT10k (OSM, `function: yes`, wysokość domyślna 6,0 m; mediana 48 m²) trafiało do klasy
  `office` — płaskie „biurowce” 6 m w ogrodach (zmierzone na `Data/Regions/knyszyn/buildings.geojson`);
- budynki usługowe w zabudowie domowej (poczta, dom pogrzebowy, apteki, sklepy) miały płaskie dachy, bo
  `typology.roof_shape` przyjmuje dla `office` / `block` tylko typy LoD2 1030 / 1040 / 1070, a w Knyszynie
  dominują 1130 (535 budynków);
- kolor dachu domu był losowany z trzech materiałów (czerwony 244, brązowy 246, grafit 227 z 717 domów) —
  bez związku z miejscem; jasnoszarych pokryć (eternit, blacha) nie było wcale;
- nadpisania `wall_material` i `roof_material` działały tylko dla części klas (ściana: nie dla domów; dach: tylko
  dla domów), a dom drewniany wybierał wyłącznie skrót z identyfikatora.

## Decyzja

1. **Pliki nadpisań generowane z danych**, obok ręcznego `overrides.yaml`:
   `roads.pipeline.generated_overrides` czyta `overrides.class_fixes.json` i `overrides.ortho_roofs.json`
   i zwraca je PRZED wpisami ręcznymi — dla tego samego budynku wygrywa wpis ręczny. Pliki są w gicie, mają format
   wpisów nadpisań (id, target, reason, confidence, verify, set) i nagłówek z generatorem. Region bez plików nie
   zmienia się (test `test_regions_without_the_file_are_untouched`).
2. **Dachy z ortofoto** (`tools/worldgen/qa/roof_tones_ortho.py`): mediana sRGB nasłonecznionej części dachu
   (obrys pomniejszony o 1,2 m, bez zieleni i pikseli prawie czarnych, górne 45 % jasności) → klasa czerwony / brązowy /
   grafit / jasnoszary → materiał. Wpis powstaje przy czystości klasy ≥ 0,55 i ≥ 40 pikselach 0,25 m. Knyszyn:
   1577 z 1903 budynków; zgodność z czterema dachami odczytanymi ręcznie w ADR 0227: 4/4 (`--check`).
   Ortofoto jest wyłącznie referencją pomiarową — żaden piksel nie trafia do tekstur (docs/05 §3).
3. **Nowy materiał `roof_sheet_grey`** — tylko z nadpisań (`buildings_mesh.ROOF_OVERRIDES`); reguła losująca go nie
   używa, więc pozostałe regiony zachowują bajty. Kolor WORKING_VALUE.
4. **Poprawki klas z danych** (`tools/worldgen/qa/class_fixes_data.py`, opt-in na region): obrys tylko z OSM
   z wysokością domyślną: < 60 m² → `gospodarczy`, 3,0 m; 60–250 m² → `dom`; budynek `office` / `block` z typem LoD2
   1130 / 1010 i ZMIERZONYM wzniosem ≥ 1,5 m → `roof_shape` gable / mono. Knyszyn: 99 + 49 + 20.
   Progi powierzchni i 3,0 m to WORKING_VALUE.
5. **Generator:** `roof_material` obowiązuje każdy dach spadzisty; `wall_material` także domy (dozwolony zestaw
   `HOUSE_WALL_OVERRIDES`); `typology: dom_drewniany` lub ściana `wood_planks*` wymusza dom drewniany; budynek, który
   ma tylko `roof_material`, zachowuje regułową witrynę pawilonu.
6. **Ręczne nadpisania punktów orientacyjnych** (`overrides.yaml`, id `look-*`): poczta (ściany, dach czterospadowy),
   dom narożny Grodzieńska / Rynek, Dom Klattów (drewniany wg OSM), parking dyskontu przy Szkolnej (3 poligony
   z ortofoto, ESTIMATED ±1 m). Bez nazw i marek.

## Czego nie zmieniono (świadomie)

- Reguły klas w `classify` i `typology.LOD2_PITCHED` — zmiana ogólna przesunęłaby baseline'y ADR 0238 dla
  Białegostoku. **Otwarte dla lidera:** obrysy tylko z OSM z wysokością domyślną są „biurowcami” we wszystkich
  regionach; poprawka ogólna wymaga osobnej decyzji i przeliczenia baseline'ów.
- Park Rynku, targowica, rondo (PR #169), chodniki i Południowa × Szkolna (PR #165).
- Bryła dyskontu (dach dwuspadowy o małym spadku, 1033 m² > limit 900 m² planu dachu), szkoła, bloki — brak zdjęć.

## Budżet i walidacja

Szacunki edytora i wyniki renderów „przed / po”: `docs/reports/knyszyn-look/README.md` i raport końcowy agenta.
High clear, 75 kamer, build origin/main 64e54592e + nowe kamery vs ta gałąź (szacunek edytora przed SRP batchingiem, nie pomiar GPU): maks. draws 773 → 709, średnio −15,0 na kamerę (51 kamer mniej, 11 więcej, najgorzej +3 	ruck-34); maks. tris 1 222 802 → 1 229 717 (limit 2 mln), najgorzej +15 589 (look-szkolna-block-south). Low nie renderowano. Pytest: 92 passed (-k "knyszyn_look or knyszyn_roofs or typology_0238 or buildings_0167 or overrides or knyszyn_qa_gate or church or townhall"); pełny GIS i EditMode — do lidera.
Testy: `tests/gis/test_knyszyn_look_s23.py`.

## Otwarte

- Ocena `visual-critic` i właściciela; lista pytań do właściciela w raporcie (§3).
- Ściany pierzei Rynku i Tykockiej z Mapillary / zdjęć właściciela (dotąd 2 budynki).
- Materiał cegły licowej w kolorze poczty; dach dyskontu.
- Ogólna poprawka klas obrysów OSM (wszystkie regiony).
