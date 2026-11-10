# Kwadrat Park (hero, ADR 0071) — STATUS

Worktree `.claude/worktrees/agent-a1409e374f8c12b4f`, gałąź `worktree-agent-a1409e374f8c12b4f` (od main 947749e).

## Ustalenia
- Obiekt: główna hala `bdot:9962cca0…` (21 399 m², LoD1 10,16 m), fasada placu = SE (130,7 m po odcięciu 3 przybudówek).
- Referencje (tylko otwarte): ortofoto GUGiK 2024-05-27 0,25 m (`refs/grid_*.jpg`), zdjęcia CC0 Rakoon / Commons
  `cm109685822` (20210904_101250: narożnik S, fasady SW+SE) i `cm157094809` (2024: fasada SW z daleka). Katalog
  `artifacts/refs/kwadrat-park/` nie istniał — refs zebrane samodzielnie w `artifacts/kwadrat-r9/refs/`.
- „11 bram” z PHOTO-LIST to wynik starej reguły generatora, NIE fakt: ortofoto nie pokazuje bram (elewacja w cieniu,
  zestawy stoją równolegle do ściany). Zachowane 11 doków w tych samych pozycjach (u0 = 7,815 m, co 4,0 m) jako
  WORKING_VALUE — fizyka/plac/trasa bez zmian.
- Widać na zdjęciach: jasnoszara blacha pozioma, cynobrowe ramy pasma okien (SE) i żaluzji (SW przy narożniku), wysoki
  cynobrowy portal na SE, ciemna attyka, wentylatory dachowe; ortofoto: dach bitumiczny z siatką świetlików, białe pole
  membrany przy SE, jaśniejszy niższy dach w pierścieniu, czerwone daszki 2 przybudówek, asfalt + auta przed rzędem lokali.

## Architektura
- Override `kind: hero_depot` (`overrides.yaml: kwadrat-park-hero`) → `tools/worldgen/streetscape/hero_depot.py`
  (`plan()` spec + sha, `apply()` instancje + kolizja odbojnic) → spec `Data/Regions/<id>/generated/landmarks/kwadrat_park.spec.json`
  → `tools/blender/world/landmarks/make_depot.py` → `art-source/world/landmarks/kwadrat_park/kwadrat_park.glb` + `_meta.json`.
- `buildings_mesh.build(heroes=…)`: doki z speca (ten sam dict co `docks_for`), widoczne warstwy hali usuwane gdy asset aktualny,
  pryzmat kolizji zostaje. Prototypy `landmark_depot_kwadrat_park_NN` (+`.lod1/.lod2`, `_roof`), LOD [100, 400, 20000] m.
- Materiały: nazwy z `streetscape/materials.py` (nowe `kp_wall`, `kp_accent`, `kp_glass_block`, `kp_roof_white`), UV0 w metrach.
- Plac: `paved_area kwadrat-park-units-forecourt` (asfalt + parking przed lokalami), `kwadrat-park-trade-units` (ściana szara).

## Dziennik
- Baseline build_world (log `logs/build_world_baseline.log`, QA `logs/streetscape_qa_baseline.json`): kwadrat_park_gate
  High 922 881 / Low 331 911 tr.
- Blender it1–it3 (`blender/it*/`, montaże `montage/it2_photo_vs_render.jpg`, `it3_photo_vs_render.jpg`, `it2_ortho_vs_top.jpg`):
  it1 pierwsza bryła; it2 dziedziniec, sufit otwartego doku, pasmo 2,0 m / parapet 6,6 m, portal 12,6 m, kamera foto
  (95 m na S od narożnika, hfov 22°); it3 attyka 0,30 m, szerokie lamele żaluzji, jaśniejsze luksfery.

## NASTĘPNY KROK
    bash artifacts/kwadrat-r9/render.sh itN [kamery]        # iteracja assetu (render kontrolny)
    blender -b --factory-startup -P tools/blender/world/landmarks/make_depot.py -- --spec Data/Regions/bialystok-industrial-c/generated/landmarks/kwadrat_park.spec.json   # eksport GLB + meta
    KAMION_BLENDER=<blender.exe> uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c

## Stan 2026-11-10 ~21:00 (WIP zapisany na polecenie lidera)
- Asset wyeksportowany: `art-source/world/landmarks/kwadrat_park/kwadrat_park.glb` LOD0/1/2 = 13 088 / 2 034 / 652 tr., 17 prototypów.
- build_world z hero OK (`logs/build_world_hero1.log`): `hero depot kwadrat-park-hero applied`, overrides_stale = [].
  Szacunek klatki kwadrat_park_gate High 922 881 → 930 134, Low 331 911 → 333 827; stretch_04 High 1 997 449 (< 2,0 M);
  stretch_02 High +61 k (auta na nowym parkingu przed lokalami).
- pytest tests/gis: 172 zielone (nowy `test_hero_depot.py` 7; `test_streetscape` zna prototypy z landmarks). UWAGA: w nowym
  worktree trzeba `git lfs checkout` (trees.glb / PNG były wskaźnikami LFS → import Unity i 2 testy padały).
- Unity import OK (`logs/import2.log`): Low 113,0 MB, High 249,7 MB. Rendery WorldC w toku: `artifacts/kwadrat-r9/after1/<Tier>-<światło>/`.
- W źródłach, ale JESZCZE NIE w GLB: drabina na dach, koryto kablowe nad dokami, szafka hydrantowa (`make_depot.py`,
  `overrides.yaml: ladders`). Najbliższy build_world sam przebuduje asset (potrzebny `KAMION_BLENDER`).
- MA-003 (szlaban bramy opuszczony, bez kolizji): NIE ruszone — `kwadrat-park-gate-kit` bez zmian (`streetscape/gate.py`,
  prototyp `barrier_arm` w `life_props.py`). Do zrobienia: ramię w pozycji otwartej (pionowo) w prototypie albo kolizja ramienia.
- EditMode nie puszczony, visual-critic nie wołany, ADR 0071 = proposed.

## NASTĘPNY KROK (po kolei)
    git lfs checkout
    $env:KAMION_BLENDER='C:\Users\matma\AppData\Local\Programs\Blender4.2\blender-4.2.9-windows-x64\blender.exe'; uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c
    uv run --project tools/worldgen pytest tests/gis -q
    pwsh scripts/import-region.ps1 -Region bialystok-industrial-c
    pwsh artifacts/kwadrat-r9/qa_runs.ps1 -Phase after2
    pwsh scripts/test.ps1 -Platform EditMode

## Stan 2026-11-10 ~21:50 (cykl after2 zakończony)
- Asset przebudowany automatycznie przez build_world (drabina, koryto kablowe, szafka hydrantowa; blacha jaśniejsza
  `kp_wall` 0,62 / metal 0,1, bez zamiany UV — w after1 poziome łączenia płyt wyszły pionowo): LOD0/1/2 = 13 648 / 2 034 / 652.
- Szacunek klatki: kwadrat_park_gate High 930 206 / Low 333 827 (baseline 922 881 / 331 911); max High = stretch_04 1 997 449
  (bez zmian, < 2,0 M); stretch_02 High 1 595 056 (+62 k: auta na parkingu przed lokalami). overrides_stale = [].
- Import: Low 113,0 MB, High 249,7 MB (render_meshes 77,7 / 214,4; instances 18,3).
- Rendery Unity WorldC: `after1/` (ciemna blacha, przed poprawką) i `after2/` — Low+High × overcast+lowsun, kamery
  g3a_eye_s0012/0062/0112/0162/0212, g3a_ext34_s0040, kwadrat_park_gate, stretch_05_docks (JPG 960 px obok PNG).
  Montaże: `montage/before_after_g3a_eye_s0012_High-overcast.jpg`, `after2_lowsun.jpg`, `after2_photo_vs_unity.jpg`.
- pytest tests/gis: 172 zielone (pełny przebieg przed after2; po after2 powtórzone hero_depot + prototypes: 10/10).
- OTWARTE: (1) visual-critic nie wołany; (2) MA-003 szlaban bramy — nie ruszony; (3) przy dokach hali hero nie stoją już
  naczepy, a plac jest gęsto zastawiony osobówkami (system life; nie badane); (4) brama/portiernia/ogrodzenie, lampy i
  oznakowanie placu = stary zestaw generyczny, bez zmian; (5) tekstury = zestawy proceduralne (skany CC0 dopiero z ADR 0063);
  (6) EditMode — patrz `logs/editmode.log`.
- Po każdym Unity cofnąć: `git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings`;
  nie commitować `art-source/world/textures|signs|props` (różnice bajtowe buildu).

## Stan 2026-11-10 ~22:30 (r10, WIP)
- `git merge main` zrobione (0ded0fb), build_world po scaleniu OK (`logs/build_world_merged0.log`), Data/raw/derived = kopia (nie junction).
- Naczepy przy dokach: znikły przez `life.START_CLEAR_*` (reguła r5: zero pojazdów ciężarowych 120 m od startu) — doki hero wyłączone z tej reguły.
- Plac zastawiony osobówkami: BDOT `OT_KUKO_A rodzaj=parking` 8328 m² obejmuje cały plac (od 605,694 do 733,838) → rzędy aut na placu manewrowym; do wycięcia (TODO `no_parking`).
- MA-003 (zgłoszenie właściciela): `game/Assets/_Project/World/Runtime/DepotBarrier.cs` (pętla obecności, otwieranie 3,5 s, kinematyczna belka = kolizja, break-away > 1,5 m/s), importer `InstanceImporter.Barrier` + `WorldSceneBuilder.BuildBarriers`, generator `barrier_base` + `barrier_boom` (gate.py). NIE skompilowane / nie testowane jeszcze.
- NASTĘPNY KROK: testy PlayMode `DepotBarrierTests.cs`; `pwsh artifacts/kwadrat-r9/cycle.ps1 -Phase merged`; `pwsh scripts/test.ps1 -Platform PlayMode`.
- 22:50 PlayMode `DepotBarrierTests` 3/3 zielone (`logs/playmode_barrier1.xml`): otwarcie 3,46 s, zestaw przejeżdża, zamknięcie; zamknięta belka blokuje 1,5 t @ 1 m/s; przejazd na siłę 6 m/s → belka uwolniona, ciężarówka 5,99 m/s.
- Dodane: `streetscape/depot_yard.py` + override `kwadrat-park-yard` (no_parking, lampy łukowe `lamp_arc_9m` wg cieni z ortofoto, 2 kontenery), gate kit `sliding_gate: false`, `fence: false` (zdjęcie CC0 2021 + ortofoto: otwarty wjazd).
- NASTĘPNY KROK: build_world w toku (`logs/build_world_r10a.log`); potem `uv run --project tools/worldgen pytest tests/gis -q`; `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c`; `pwsh artifacts/kwadrat-r9/qa_runs.ps1 -Phase r10a`.

## Stan 2026-11-10 ~22:25 (r10b, przejęcie po ubitym agencie)
- Cykl r10a był w rzeczywistości ukończony (build_world done, import OK, rendery High-overcast/High-lowsun/Low-overcast; brak Low-lowsun).
- pytest gis po r10a: 215 zielone, 4 czerwone (`logs/pytest_r10a.log`): `test_region_yard` (lamp_8m w wielokącie clear_lamps — override
  poprawiony po starcie buildu, wymaga rebuild), `test_report_not_stale` (fidelity: `tools/worldgen/fidelity/run.py`), 2x korytarz trasy
  s≈1432–1480 = znany P0 z main (HANDOVER, agent 0076), nie z tej gałęzi.
- Szlaban na scenie WorldC: nowy `WorldCBarrierTests` (PlayMode, prawdziwa scena + zestaw 40 t po trasie): 1. przebieg CZERWONY — w trybie
  `SimulationMode.Script` FixedUpdate szlabanu nie chodził w kroku symulacji (belka zamknięta, |dv| 6,06 m/s). Naprawa: `DepotBarrier.Tick(dt)`
  (FixedUpdate tylko w trybie FixedUpdate, jak VehicleBody), testy Script krokują szlabany (`WorldCRouteTests` też), bufor pętli 32 → 128.
  2. przebieg: 4/4 zielone (`logs/playmode_worldc_barrier2.log`, `artifacts/tests/worldc-barrier.txt`): 2 belki z kolizją (ray wzdłuż pasa
  trafia collider), otwarcie od s=216,5 m (belka s=247,4 m), pełne otwarcie 3,49 s, 85° gdy ciągnik 8 m przed belką przy 20 km/h, 0 kontaktów,
  zamknięcie przy s=308,4 m, druga belka nieruszona, max |dv| 0,050 m/s, pętla widzi max 11 colliderów.
- Render r10a: belka bliższa cała czerwona, dalsza cała biała — pasy `boom_red_white` szły po obwodzie (Mesh.tube: u = kąt). Naprawa
  `life_props._boom_tube` (u = metry wzdłuż belki) + test `test_boom_bands_run_along_the_boom`.
- NASTĘPNY KROK:
    $env:KAMION_BLENDER='C:\Users\matma\AppData\Local\Programs\Blender4.2\blender-4.2.9-windows-x64\blender.exe'; uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> artifacts/kwadrat-r9/logs/build_world_r10b.log
    uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c ; uv run --project tools/worldgen pytest tests/gis -q
    pwsh scripts/import-region.ps1 -Region bialystok-industrial-c ; pwsh artifacts/kwadrat-r9/qa_runs.ps1 -Phase r10b
