# ADR 0287 — Knyszyn: zabudowa z danych (dachy z ortofoto, klasy obrysów OSM, nadpisania domów)

Status: Proposed, 2026-11-17 (knyszyn-look-s23). Numer potwierdzony przez lidera. Recenzja `visual-critic`
2026-11-17 (`docs/reports/REVIEW-2026-11-17-s23-knyszyn-look.md`): SCAL warunkowo — P1-1, P1-2, P2-1, P2-3 wykonane
w tej gałęzi; ocena właściciela (D51) otwarta.

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
   używa, więc w pozostałych regionach dochodzi tylko wpis w tabeli materiałów manifestu. Recenzja 2026-11-17 P1-1:
   w pierwszej wersji nazwa nie miała prefiksu z `materials._TINT_LINEAR`, więc 0,30 trafiało do shadera jako tint
   sRGB i dach w słońcu miał sRGB 178–211 („śnieg”). Teraz prefiks `roof_sheet_`, kolor liniowy 0,15 (cel ~145 sRGB:
   na zdjęciu z drona właściciela nr 10, tylko lokalnie, szare dachy z blachy mają 121–137 przy białej ścianie ~210,
   czyli ~0,6 jasności ściany; w grze tynk 239). P2-1: tekstura falista `trapezoid_sheet` (CC0, 2 m; żebra wzdłuż
   spadku, bo V siatki dachu biegnie w górę połaci) zamiast przemalowanej dachówki. Kolor WORKING_VALUE.
4. **Poprawki klas z danych** (`tools/worldgen/qa/class_fixes_data.py`, opt-in na region): obrys tylko z OSM
   z wysokością domyślną: < 60 m² → `gospodarczy`, 3,0 m; 60–250 m² → `dom`; budynek `office` / `block` z typem LoD2
   1130 / 1010 i ZMIERZONYM wzniosem ≥ 1,5 m → `roof_shape` gable / mono. Knyszyn: 99 + 49 + 20.
   Progi powierzchni i 3,0 m to WORKING_VALUE.
5. **Generator:** `roof_material` obowiązuje każdy dach spadzisty; `wall_material` także domy (dozwolony zestaw
   `HOUSE_WALL_OVERRIDES`); `typology: dom_drewniany` lub ściana `wood_planks*` wymusza dom drewniany; budynek, który
   ma tylko `roof_material`, zachowuje regułową witrynę pawilonu.
6. **Ręczne nadpisania punktów orientacyjnych** (`overrides.yaml`, id `look-*`): poczta (ściany, dach czterospadowy),
   dom narożny Grodzieńska / Rynek, Dom Klattów (drewniany wg OSM), parking dyskontu przy Szkolnej (3 poligony
   z ortofoto, ESTIMATED ±1 m). Bez nazw i marek. Recenzja 2026-11-17 P1-2: dwa małe obiekty placu wschodniego
   (OSM way 1427273958, 1,8 × 6,8 m, jasny prawie płaski dach na ortofoto, i kiosk prasowy way 300663247,
   4,9 × 2,7 m) reguła < 60 m² zamieniła w ślepe szare klocki — wpisy `look-east-square-kiosk` / `-press-kiosk`
   robią z nich parterowe korpusy z otworami (ceglany / jasny tynk, dach płaski — spadzistego dane nie pokazują,
   a `roofs.plan` odrzuca rozpiętość < 3 m). Lista pozostałych 13 obrysów `gospodarczy` w pasie 15 m od osi jezdni:
   `docs/reports/knyszyn-look/sheds_near_road_knyszyn.json` (do przeglądu na kamerach; reguła bez zmian).
7. **Kamery z wysokości oczu** (P2-3): `look_post_office`, `look_dom_klattow`, `look_rynek_corner_2e17` (1,7 m,
   18 m od obiektu, pozycje z osi najbliższej ulicy).

## Czego nie zmieniono (świadomie)

- Reguły klas w `classify` i `typology.LOD2_PITCHED` — zmiana ogólna przesunęłaby baseline'y ADR 0238 dla
  Białegostoku. **Otwarte dla lidera:** obrysy tylko z OSM z wysokością domyślną są „biurowcami” we wszystkich
  regionach; poprawka ogólna wymaga osobnej decyzji i przeliczenia baseline'ów.
- Park Rynku, targowica, rondo (PR #169), chodniki i Południowa × Szkolna (PR #165).
- Bryła dyskontu (dach dwuspadowy o małym spadku, 1033 m² > limit 900 m² planu dachu), szkoła, bloki — brak zdjęć.

## Budżet i walidacja

Szacunki edytora i wyniki renderów „przed / po”: `docs/reports/knyszyn-look/README.md` i raport końcowy agenta.
High clear, 75 kamer, build origin/main 64e54592e + nowe kamery vs ta gałąź (szacunek edytora przed SRP batchingiem, nie pomiar GPU): maks. draws 773 → 709, średnio −15,0 na kamerę (51 kamer mniej, 11 więcej, najgorzej +3 `truck-34`); maks. tris 1 222 802 → 1 229 717 (limit 2 mln), najgorzej +15 589 (look-szkolna-block-south). Low nie renderowano. Pytest: 92 passed (-k "knyszyn_look or knyszyn_roofs or typology_0238 or buildings_0167 or overrides or knyszyn_qa_gate or church or townhall"); pełny GIS i EditMode — do lidera.
Testy: `tests/gis/test_knyszyn_look_s23.py`.

## Otwarte

- Ocena `visual-critic` i właściciela; lista pytań do właściciela w raporcie (§3).
- Ściany pierzei Rynku i Tykockiej z Mapillary / zdjęć właściciela (dotąd 2 budynki).
- Materiał cegły licowej w kolorze poczty; dach dyskontu.
- Ogólna poprawka klas obrysów OSM (wszystkie regiony).
- ~~Zestaw tekstur desek `wood_siding`~~ — zrobione, patrz „Aktualizacja 2026-11-17 (alt-wood-s24)”.

## Aktualizacja 2026-11-17 (knyszyn-look-s23b)

Właściciel po renderach 0,15: szare dachy z blachy „za jasne” → `roof_sheet_grey` kolor liniowy 0,105
(WORKING_VALUE). Zmierzone sRGB w słońcu (High clear, edytor): tykocka-into-town 135 → 119, rynek-above 152 → 133
(grafit ~100, biały tynk ~239).

## Aktualizacja 2026-11-17 (alt-wood-s24): deski `wood_siding` ze skanu CC0 (decyzja D-17.11)

Domy drewniane (`dom_drewniany`, materiały `wood_planks` / `wood_planks_green`, w tym Dom Klattów) wskazywały zestaw
`wood_siding`, którego nie było, więc renderowały się gładkim kolorem.

1. **Skan:** Poly Haven `raw_plank_wall` (Dimitrios Savva, CC0 1.0, 1,87 × 1,87 m, 2k JPG, 5 map) w
   `art-source/world/cc0/cc0_manifest.json` (URL, md5 z API zgodne, SHA256) i `docs/LICENSES.md`; licencja sprawdzona
   na https://polyhaven.com/license 2026-11-17. `cc0_fetch.py --resolve --only <id>` dodaje zasób bez przepisywania
   zapisanych wpisów pozostałych skanów.
2. **Zestaw** (`sets_scan.py`, `SCAN_SETS` + `SCAN_ONLY_META`): modulation_set (średnia 0,5 na kanał, kolor z tabeli
   materiałów), UV0 w metrach (u wzdłuż ściany, v w górę), deski poziome, kafel 1,87 m w skali skanu. Rozstaw desek
   zmierzony z fug mapy displacement: mediana 0,093 m (0,043–0,106 m, 23 fugi). Źródła szerokości deski domów
   podlaskich w repo nie ma — bez przeskalowania (WORKING_VALUE). Skan to mozaika szarych / miodowych / ciemnych desek
   (najciemniejsza 0,33 × sąsiednia), która pod jednym kolorem farby wyglądała jak ściana z palet: nowa funkcja
   `flatten_boards` wyrównuje ton wzdłuż desek (filtr anizotropowy 0,015 × 0,08 m, 100 %; fugi 1–3 mm i słoje
   zostają), plamy farby > 1,3 × tonu deski ściśnięte 5:1, odcień lokalny w 12 %. Zmierzone na zestawie High:
   CV tonu desek 0,124 → 0,016 (`source.board_tone_cv_before_after` w `materials_spec.json`), najciemniejsza deska
   0,89 × sąsiednia, 0 % tekseli przyciętych. Albedo w silniku (2 × kolor × mapa, liniowo, luminancja):
   `wood_planks` p01 / p50 / p99 / max = 0,078 / 0,163 / 0,209 / 0,252 (średnio sRGB 128 / 108 / 85),
   `wood_planks_green` 0,060 / 0,127 / 0,162 / 0,196 — kolory materiałów bez zmian. Parametry obróbki WORKING_VALUE
   (ocenione na podglądach z odcieniem, bez renderu w grze).
3. **Generator:** `wood_planks*` dostały `set_tile` (bez niego shader użyłby kafla 4 m — deski 0,20 m zamiast 0,093 m).
   Reguły wyboru domu drewnianego bez zmian.
4. **Testy:** `tests/gis/test_wood_siding_cc0.py` (wyrównanie desek na danych syntetycznych, kolano jasnych plam,
   podpięcie materiałów, wpis w spec, `--resolve --only` z atrapą API).

Otwarte: render kontrolny `look_dom_klattow` po przebudowie Knyszyna i imporcie (lider) + ocena `visual-critic` /
właściciela; pozostała mała jasna plama farby na jednej desce powtarza się co 1,87 m (do oceny z wysokości oczu).

## Aktualizacja 2026-11-18 (knyszyn-p1-s24): P1 z recenzji s24 → ADR 0295

Recenzja `docs/reports/REVIEW-2026-11-18-s24-knyszyn.md` (FAIL anti-slop) — poprawki P1-1…P1-4 są regułami generatora
dla wszystkich regionów, dlatego mają własny rekord: **ADR 0295** (dom drewniany: deski narożne, lisice, listwa cokołowa,
szczyt pionowo, opaski z nadokiennikiem; przebiegi desek krótsze niż kafel; mozaika pól i spokojniejsze ogrody w masce
suchości terenu; autorskie cofnięcie zamknięcia krawędzi świata — `Data/Regions/knyszyn/world_edge.authored.json`).
Dom Klattów (`look-dom-klattow-wooden`) bez zmian w nadpisaniu — detale bierze z reguły `dom_drewniany`.
