# Integracja rynek-s23 — PR #139 (Rynek i targowica Knyszyn, ADR 0227) + PR #144 (rondo Knyszyn, ADR 0274)

Data: 2026-11-16 · wykonawca: lider (rynek-s23, D78) · gałąź `knyszyn-rynek-0227` · sha startowy `c7038676b`
Bazą jest main `2fde0d09d`, ostatnio scalony do gałęzi. Kafel knyszyn przebudowano po scaleniu c-regen3 (`40f4a4ef7`). Późniejsze zmiany main (`2fde0d09d`) nie dotykają generatora knyszyn: zawierają tylko `qa/dense_lod_estimate.py`, docs i fizykę.

## 1. Wynik: **PARTIAL** — werdykt scalenia: **TAK (warunkowo)**, gdy `tests.status` pokaże zielony GIS i EditMode (sekcja 4)
Oba PR-y robią to, co obiecują. Park Rynku zastępuje las sosnowy. Targowica stoi we właściwym miejscu, w układzie 3+1. Rondo ma długie wysepki DK65 i oznakowanie P-13/P-10. Budżet Low na `dk65-inlet-south` przyjęto decyzją D78. Visual QA kończy się wynikiem „lepiej niż było”, a nie akceptacją wizualną: lipy, pomnik i wierzba nadal mają status PROXY/WORKING_VALUE. Przeglądu `visual-critic` nie było, bo zadanie wykluczało subagentów. Do zrobienia przez lidera.

## 2. Ustalenia
1. **Sprzątanie P1 (#139).** Z indeksu zdjąłem 40 jednorazowych skryptów z `artifacts/knyszyn-rynek-0227/`. W gicie zostały `AUDYT.md`, `TYPOLOGIA.md` i `roof-plan.md`. Usunąłem 8 diagnostycznych kamer koron `rynek_crown_side_*`; kamer authored jest teraz 30 zamiast 38.
2. **Brak śladu w QA innych regionów (P1).** Sześć generatorów `knyszyn_*_0227` zapisuje wpis QA dopiero po sprawdzeniu regionu. `vegetation.place` dodaje `park_replacements` tylko przy wpisie `kind: park_replacement`. Pilnuje tego test `tests/gis/test_knyszyn_qa_gate_0227.py`.
3. **`far_field.load_heightfield` zostaje.** Stara ścieżka awaryjna czytała `z_min_m`/`z_max_m`, a tych kluczy nie ma w żadnym z 21 plików `terrain.json`. Kończyła się więc `KeyError`. Opis jest w ADR 0227 § rynek-s23.
4. **Scalenia.** Codex scalił main wcześniej (`a2f62a442`). Ja scaliłem #144 (`491dd7d9b`, STATUS.md wzięty z HEAD), main c-regen3 (`4b63d144c`) i main `2fde0d09d`. Konfliktów nie było. `overrides.yaml` knyszyn ma 46 id i 0 duplikatów. Wpisy ronda `compact`, `truck-apron`, `feeders-width`, `dk65-split-s/n` i `island-plantings` są obecne.
5. **Rondo przeskalowane wg zdjęcia właściciela 9.** Skala: średnica zewnętrzna 22,6 m ≈ 137 px.
   - Wysepka S: ok. 29 m od krawędzi pierścienia, zgodnie z wartością authored 29,2 m. Bez zmian.
   - Wysepka N: zaczyna się ok. 2,7 m od krawędzi i wychodzi poza kadr, więc ma ≥ 34 m (ESTIMATED, dolna granica). Zdjęcie 10 też pokazuje ją jako długą. Zmieniłem `knyszyn-roundabout-dk65-split-n` z `length_m` 17 na 32, co daje ok. 35 m. Zakres w `test_roundabout_0274` zaktualizowany.
   - Promienie wyokrągleń z PR (6 / 8 m) zgadzają się ze zdjęciem w granicach odczytu: narożniki ok. 6–9 m.
6. **Przebudowa r2 kafla knyszyn** na kodzie #139 + #144 + main: build_world, export-route, `export-region-catalog --check`, fidelity C, import i VQA Low/High — wszystko exit=0. Wszystkie 192 sumy sha chunków (glb, low, instances) w `Data/raw/derived/knyszyn/world` zgadzają się z `generated/world_manifest.json`. Import szedł z tego worktree.
7. **`Data/raw/derived/knyszyn`** w worktree był lokalnym katalogiem, a nie junction, więc nie kolidował z world2-s23. Skopiowałem go do main (`robocopy /MIR`, exit=1, czyli pliki skopiowane). Najnowszy plik `world/` przed kopią: 15.11 15:55. Po kopii: 16.11 13:02.

## 3. Zmienione pliki (względem main)
`Data/Regions/knyszyn/{overrides.yaml, control_cameras_place.authored.json, generated/*}`, `Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json`, `game/Assets/_Project/UI/Resources/CabDisplay/Nav/knyszyn_route.bytes`, `tools/worldgen/streetscape/{knyszyn_*_0227.py, vegetation.py, stage.py, far_field.py, paved.py, plantings.py, buildings_mesh.py}`, `tools/worldgen/roads/{pipeline.py, compact_roundabout.py, carriageway_split.py, …}` (#144), `tools/blender/world/make_trees.py`, `tests/gis/*0227*.py`, `tests/gis/test_roundabout_0274.py`, `docs/adr/0227-knyszyn-rynek.md`, `docs/adr/0274-*.md`, `artifacts/knyszyn-rynek-0227/{AUDYT,TYPOLOGIA,roof-plan}.md`.

## 4. Dowody
- Testy kierunkowe: `pytest tests/gis/test_roundabout_0274.py test_truck_apron_0218.py test_knyszyn_qa_gate_0227.py` → **92 passed**. `*_0227` + far_field → **52 passed**. `test_road_fidelity.py` → **9 passed, 1 xfailed**.
- Pełny GIS (slot heavy) i EditMode `StartClearanceTests`: `artifacts/rynek-s23/tests.status`, logi `gis-full.log` i `editmode.log`. **Wynik dopisany niżej po zakończeniu.**
- Rendery (69 kamer na wariant, 1920×1080): `artifacts/rynek-s23/vqa/` (r1) i `vqa-r2/` (r2), podglądy 960 px w `view/` i `view-r2/`. Pary ze zdjęciami właściciela oglądałem tylko lokalnie; zdjęcia nie trafiają do gita.
- Budżet to szacunek CPU edytora (siatki + instancje, przed SRP batching), nie GPU ani telefon. Punkt odniesienia po ADR 0262: pozycja startowa 90 m. Bazowy pomiar sprzed tej zmiany (240 draw calls) jest nieporównywalny, a wzrost przyjęto w D78.

| Wariant | Low `dk65-inlet-south` | Low max draws | Low max tris | High max tris | High max draws |
|---|---:|---:|---:|---:|---:|
| R29 (Codex, przed scaleniem) | 304 | 485 | 372 304 | 1 250 321 | 848 |
| r1 (scalony #139) | 304 | 485 | 372 316 | 1 250 176 | 848 |
| r2 (#139 + #144 + main) | 309 (+5, rondo / main) | 493 (`goniadzka-jagiellonska`) | 371 655 | 1 249 330 | 850 |

## 5. Napisane / zbudowane / uruchomione / zmierzone
- Napisane: bramka QA, test bramki, opis w ADR, przeskalowanie wysepki N.
- Zbudowane: kafel knyszyn r1 i r2, import Unity.
- Uruchomione: VQA Low/High clear, fidelity C, testy kierunkowe, pełny GIS i EditMode (w toku).
- Zmierzone: szacunki edytora z tabeli, sumy sha chunków.
- Niezmierzone: GPU, FPS w buildzie PC, telefon.

## 6. Oględziny vs zdjęcia właściciela (r1/r2, High i Low clear)
- **Park Rynku (kadry 03 i 05):** lipy, alejki z szarej kostki, trawniki i płyta fontanny zamiast lasu. Kościół w osi alei, urząd z pomnikiem. Między r1 i r2 nic się nie pogorszyło (kadr 05 identyczny). Korony lip wyglądają sztucznie: płaskie karty i ciemne pionowe szwy. Pomnik króla to proxy, fontanna jest sucha.
- **Targowica (kadry 12 i 14):** układ zgadza się ze zdjęciem 12. Wiaty 3+1, PV na skrajnej wiacie, ciemnoszare dachy czterospadowe, pasy czerwonej kostki, długi budynek, płot panelowy od ulicy.
- **Rondo DK65 (`rondo-dk65-top`, `-from-south`):** długie wysepki N i S, krótsze W/E, cztery przejścia P-10 przy pierścieniu, wyspa z piaskiem, krzewami i kamieniami. Ogólny układ zgadza się ze zdjęciem 9.

## 7. Otwarte (ryzyka i znane braki)
- **Średnica ronda.** Z długości aut na zdjęciu 9 wychodzi ok. 26 m. OSM daje 22,6 m, a generator bierze promień z OSM i nie ma klucza do nadpisania. Wymaga ortofoto po 2025 albo klucza `ring_r_m` (zmiana kodu, osobny ADR).
- **Wysepka E** na zdjęciu 9 ma ok. 19 m, w modelu jest krótka (wynika z OSM). W `rondo-dk65-from-south` widać wysoką krawędź jezdni po prawej (uskok teren / droga) — do sprawdzenia.
- **Targowica:** trzy wiaty stykają się okapami, a na zdjęciu 12 stoją z przerwami. Żółtego pawilonu w narożniku nie ma; w tym miejscu jest szary budynek. Wyspa przy wjeździe jest zbyt zielona.
- **Rynek:** korony lip, figura króla (PROXY_NOT_APPROVED), strumienie fontanny i wierzba — ESTIMATED / WORKING_VALUE / OPEN, zgodnie z ADR 0227.
- **Długi techniczne:** przegląd `visual-critic` i ocena właściciela. Recenzja P2-2: wywołania generatorów `knyszyn_*` wpisane na sztywno w `stage.py`, docelowo rejestr generatorów sterowany z overrides. P2-4: wpisy „trial” lip w overrides.
- **Ślad w QA innych kafli:** usunięty dopiero po ich następnej regeneracji. Kafle z c-regen3 zbudowano bez kodu 0227, więc diffu nie dostaną.

## 8. Następny krok
Gdy `tests.status` = `TESTS DONE` z `gis exit=0` i `editmode exit=0`: lider scala `knyszyn-rynek-0227` do main (`git merge --no-ff origin/knyszyn-rynek-0227`, STATUS.md = main), zamyka #139 i #144, potem `visual-critic` na `artifacts/rynek-s23/view-r2/`.
