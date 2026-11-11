# ADR 0101: Kalibracja pigmentów r2 po kontrakcie `_Tint` (0086) — metoda stosunkowa na ≥ 2 kamerach

Status: zaimplementowane na gałęzi `tint-r2` (rendering-perf), 2026-11-11. Do recenzji visual-critic. Kontrakt ADR 0086
(jeden liniowy `_Tint`, `SetLinearTint`) zostaje bez zmian; zmieniają się wyłącznie wartości pigmentów i metoda
kalibracji. Źródło zadań: `docs/reports/visual/REVIEW-2026-11-11-s10-0086.md` (P0-1, P0-2, P1-2, P2-1, P2-2, P2-4).

## Kontekst
Po przejściu na poprawny kontrakt 0086 (x1,6 do x12,9 w liniowej przestrzeni dla 57/119 definicji) lokalna kalibracja
była robiona na pojedynczych ROI i bezwzględnych poziomach sRGB ze zdjęć zrobionych w innej pogodzie. Skutek (pomiar
krytyka, potwierdzony tu na świeżym baseline = main 99b96327): hala Kwadrat Park przy bramie przepalona w High-clear
(250 sRGB, 82 % ROI z kanałem ≥ 250), ekrany kasetowe ciemniejsze niż zmierzony stosunek ADR 0069.

## Decyzja

### 1. Metoda (P1-2) — narzędzie i test w repo
`tools/worldgen/qa/tint_ratio.py` + `tools/worldgen/qa/tint_ratio_spec.json` + `tests/gis/test_tint_ratio.py`:
- każdy kalibrowany pigment ma ≥ 2 kamery i co najmniej jedną stronę `lit` i jedną `shaded` (w `clear`); walidator
  odrzuca kalibrację z jednego ROI (test);
- miarą jest **stosunek** średniego poziomu wyświetlania (sRGB 0..255, średnia R,G,B) materiału do neutralnego
  odniesienia **w tym samym kadrze** (niebo, cokół, asfalt), a cel wyprowadza się z tej samej pary powierzchni na
  zdjęciu (`photo_refs`/`photo_notes` w specyfikacji). Bezwzględny poziom z fotografii nie jest celem;
- dodatkowo `clip_250` (udział pikseli ROI z kanałem ≥ 250), `spread` (p90–p10 luminancji, czytelność żeberek) i
  `ratio_linear` (informacyjnie);
- `--masks` sprawdza, że ROI leży na materiale (≥ 90 % pikseli maski `-qaMask`), a odniesienie poza nim (≤ 2 %).
  Materiały instancjonowane / hero (kp_wall, kontenery, tuja) nie mają slotów rendererów, więc ich ROI potwierdza
  maska zmian baseline→runda (`artifacts/tint-r2/diff_frames.py`).
Polecenie: `uv run --project tools/worldgen python tools/worldgen/qa/tint_ratio.py --round <runda> --before <baseline> --masks artifacts/tint-r2/masks`.

### 2. Wartości (WORKING_VALUE, zweryfikowane metodą z pkt 1)
| Materiał | 0086 | r2 | Uzasadnienie |
|---|---|---|---|
| `kp_wall` (`streetscape/materials.py`) | 0,56/0,57/0,57 | **0,37/0,38/0,38** | hala/niebo w overcast 0,6–0,88 (zdjęcie CC0 cm157094809: najczystszy panel 0,86 nieba; krytyk: typowo ~0,6), clear bez clipu |
| `noise_panel_dark` (`streetscape/materials.py`) | 0,022/0,024/0,023 | **0,039/0,041/0,040** | albedo 0,04 z ADR 0069 (p40: kaseta/cokół 0,34–0,38 na tej samej ścianie), odcień starego 0,068/0,072/0,070 |
| `bridge_concrete` (`roads/build_world.py`) | 0,42/0,42/0,40 | **0,26/0,26/0,25** | dźwigar/asfalt w kadrze 1,26–1,36 vs zdjęcie CC0 Bieżeństwa filar/jezdnia 0,95–1,02 |

Pomiar baseline (świeży build+import main 99b96327, identyczny z 0086 after-final) → r2, stosunek do odniesienia
w tym samym kadrze (`artifacts/tint-r2/r2-ratio.json`; 62 kamery x Low WorldC / High WorldC_High x overcast/clear,
2340x1080):

| Materiał / kontrola (strona) | Low-ov | High-ov | Low-clear | High-clear |
|---|---|---|---|---|
| kp_wall / gate_lit (hala/niebo) | 0,97→**0,78** | 0,94→**0,72** | 1,69→**1,42** | 1,76→**1,52** (clip ROI 82→0,1 %) |
| kp_wall / docks_shaded | 0,60→**0,47** | 0,55→**0,45** | 0,97→**0,82** | 0,97→**0,84** |
| kp_wall / hall4_right_of_portal | 0,64→**0,52** | 0,57→**0,47** | 1,04→**0,88** | 0,94→**0,81** |
| noise_panel_dark / putry_entry_right (kaseta/cokół) | 0,26→**0,32** | 0,28→**0,35** | 0,37→**0,44** | 0,38→**0,45** |
| noise_panel_dark / g3b_right_band | 0,29→**0,35** | 0,31→**0,37** | 0,39→**0,47** | 0,41→**0,49** |
| noise_panel_dark / house1_band | 0,28→**0,33** | 0,30→**0,36** | 0,40→**0,46** | 0,42→**0,48** |
| noise_panel_dark / g3b_left_under_deck (cień wiaduktu) | 0,37→**0,42** | 0,39→**0,44** | 0,45→**0,51** | 0,47→**0,53** |
| bridge_concrete / putry_girder (dźwigar/asfalt) | 1,26→**0,95** | 1,26→**0,96** | 0,85→**0,69** | 0,86→**0,71** |
| bridge_concrete / g3b_girder | 1,36→**1,02** | 1,33→**1,01** | 0,85→**0,68** | 0,84→**0,69** |
| bridge_concrete / biez_above_cornice (z góry) | 2,62→**2,02** | 2,76→**1,94** | 2,05→**1,67** | 2,18→**1,61** |

Poziomy bezwzględne (High): hala przy bramie clear 250→217 sRGB, overcast 186→144; kaseta `route-putry-entry-signs`
overcast 34→42; dźwigar overcast 102→78; gzyms z góry clear 221→164. Clip całego kadru (wszystkie kanały ≥ 250,
High-clear): `kwadrat-park-gate` 1,55→0,29 %, `biezenstwa-above` 1,10→0,39 %; `r10_hall_4` 2,98→2,94 % i
`r10_hall_1` 0,48 % bez zmiany — to biały lakier aut (pkt 3), nie `kp_wall`.

Uwaga do metody: dolną granicę `docks_shaded` (overcast) obniżono z 0,45 do 0,40 po r1 — ROI nieba w tym kadrze to
jasna chmura (233 vs 199 przy bramie w tym samym warunku), więc stosunek do nieba jest tam systematycznie niższy.
To słabość nieba jako odniesienia; dla hali docelowo lepszy byłby drugi neutral (kostka placu) — otwarte.
Strona zacieniona ekranu (pod wiaduktem) ma cokół także w cieniu, więc dostała tylko zakres kontrolny 0,30–0,60.

### 3. Bez zmian (z pomiarem)
- Tynk remizy: D48 (cel 110/126/145 ±10) — nie ruszany.
- `hedge_thuja` (P2-4): tuja/tynk High-overcast 0,28 (render) vs 0,26–0,30 (zdjęcie 7197) — jasność zgodna; render
  bardziej żółtozielony (35/45/30 vs 32/38/37). Low-overcast 0,49–0,52: niespójność tierów roślinności (stream B), nie pigment.
- `bed_soil` (x8,5): materiał nieużywany w obecnym świecie (żadna wyspa nie ma `fill: soil`, brak w manifeście chunków).
- `container_rust`, `booth_panel`: nowe kadry `r2_container_rust`, `r2_gatehouse_booth`
  (`artifacts/tint-r2/cameras_r2.json`) — kolor tlenkowej czerwieni i jasnoszara płyta warstwowa wiarygodne, bez clipu.
- `car_paint_white` 0,68 (P2-2): pozostały clip w `r10_hall_1` (100 % pikseli clip w rzędzie aut) i `r10_hall_4`
  (97 % w białym vanie) to biały lakier; na zdjęciu CC0 cm109685822 van w słońcu też ma 68–88 % ROI ≥ 250. Albedo
  0,68 mieści się w zakresie białego lakieru (UNVERIFIED 0,65–0,85), więc to sprawa tonemappingu/ekspozycji clear
  (ADR 0098, GPT), nie pigmentu. Propozycja na wypadek decyzji lidera: 0,62 (jak krytyk), bez zmian shaderów aut.
- `bridge_soffit`: ROI krytyka (`photo-biezenstwa-ground` 440–520 x 225–235) leży na hero-wiadukcie (`viaduct_*`,
  ADR 0067), nie na `bridge_soffit` — stąd „brak zmiany mimo x7,65”. Prawdziwe pokrycie: `route-putry-entry-signs`
  i `g3b-rondo-putry-approach` (maski). Soffit/asfalt 0,57–0,66 vs zdjęcie 0,52 (mokra jezdnia) — w tolerancji, bez zmiany.

## Konsekwencje
- Brak zmian w kodzie runtime, shaderach, ustawieniach i scenach; zmiana danych w 2 plikach generatora + narzędzie QA.
  `WorldPbrTintRound` dostał opcjonalny `-tintOutDir` (narzędzie edytora, domyślnie jak w 0086).
- Pamięć świata bez zmian (Low 111,3 MB / High 239,7 MB z importu).
- Konflikty: `materials.py` (linie `kp_wall`, `noise_panel_dark` + komentarze) — gałęzie `gpt-furniture-r1`,
  `gpt-firestation-r7` zmieniają ten plik w innych miejscach; `build_world.py` (jedna linia `bridge_concrete`) — agent
  dróg 0100 / `gpt-viaduct-r1` mogą dotykać tego słownika; `fidelity_qa.json` (hash wejścia build_world.py) trzeba
  przeliczyć po każdym scaleniu, które zmienia build_world.py (`tools/worldgen/fidelity/run.py`).
- Nie jest to pomiar z telefonu ani bramka wizualna całego świata.
