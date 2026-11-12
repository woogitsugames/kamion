# STATUS frontage-r2 (ADR 0129, pierzeja G3-B runda 2)

## 1. Worktree + rozpoznanie (2026-11-12 13:20-14:30)
Worktree `.claude/worktrees/frontage-r2`, gałąź `frontage-r2` (main f8b85fa2, ff). Dane skopiowane (derived, cc0, megascans, _Generated, Library), junctiony gugik/osm/refs/mapillary/fab.
`_Generated` z main jest sprzed scalenia 0126 (brak frontages w streetscape_qa) -> baseline izolowany = pełny cykl z kodu main w tym worktree (`run-cycle.ps1 -Name baseline -Tag 0`, w kolejce heavy).
Rozpoznanie: szkło = `glass` z sky_occ 0.9 (czarne z założenia), maszt = `downpipe` metal 0.7 (biały przy overcast), białe ogrodzenie = OSM way 344253283 / 913217348 z hasha `fence_galv`; plac aut na ortofoto 2024: 2 rzędy furgonów/aut E -179..-167 N -334..-345.
Zdjęcia 2024 stacji #21/#22 już są lokalnie (strudel 2024-08-15: 490210580292738, 469512365899192, 1020363345994649) -> kamery kontrolne z `reference_for` w `g3b_frontage_cameras.json` (pozy SBS nietknięte).
Kod rundy 2 gotowy w kopii roboczej (scratchpad/dev; testy 12 passed) - wchodzi do worktree PO starcie builda baseline.
NASTĘPNY KROK: po `cycle-0.done`: skopiować zmiany (frontage.py, materials.py, furniture.py, stage.py, buildings_mesh.py, overrides.yaml, test_g3b_frontage.py) i `pwsh artifacts/frontage-r2/run-cycle.ps1 -Name after -Tag 1`

## 2. Stan 13:50 (limit lidera 91 %)
Baseline `run-cycle.ps1 -Name baseline -Tag 0` nadal czeka w kolejce heavy (2 przed nami); działa w tle - nie przerywać.
Kod rundy 2 (testy 12 passed w kopii roboczej) leży w `artifacts/frontage-r2/pending/` (NIE w drzewie, żeby baseline był czysty). ADR szkic: `docs/adr/0129-frontage-r2.md` (RESULTS_PLACEHOLDER do uzupełnienia). Skrypt par: `artifacts/frontage-r2/make-pairs.py <after> <Tier-Lighting>`.
NASTĘPNY KROK (po linii `build exit=` w `artifacts/frontage-r2/cycle-0.log`): `cp -r artifacts/frontage-r2/pending/* . ; uv run --project tools/worldgen pytest tests/gis/test_g3b_frontage.py -q ; git add -A tools tests Data/Regions ; git commit -m "wip(frontage-r2): round-2 code" ; pwsh artifacts/frontage-r2/run-cycle.ps1 -Name after -Tag 1 ; python artifacts/frontage-r2/make-pairs.py after Low-overcast ; python artifacts/frontage-r2/stats-diff.py after`

## 3. Kod rundy 2 w drzewie (14:0x)
Baseline build OK (597 s), import + rendery baseline lecą w tle (cycle-0). Kod rundy 2 skopiowany do drzewa: test_g3b_frontage 13 passed. Pliki generated/ i glb z builda baseline NIE są commitowane.
NASTĘPNY KROK (po `artifacts/frontage-r2/cycle-0.done`): `pwsh artifacts/frontage-r2/run-cycle.ps1 -Name after -Tag 1 ; python artifacts/frontage-r2/make-pairs.py after Low-overcast ; python artifacts/frontage-r2/make-pairs.py after Low-clear ; python artifacts/frontage-r2/stats-diff.py after`

## 4. Build after (15:4x)
build_world z kodem rundy 2 OK (653 s). Unity (import + rendery after) czeka na slot / PHONE_RUN w tle (cycle-1).
NASTĘPNY KROK (po `artifacts/frontage-r2/cycle-1.done`): `python artifacts/frontage-r2/make-pairs.py after Low-overcast ; python artifacts/frontage-r2/make-pairs.py after Low-clear ; python artifacts/frontage-r2/stats-diff.py after`

## 5. Sesja 13: wznowienie, merge main, poprawka szkła (16:5x)
cycle-1 (import + rendery after, przed merge) ukończony 16:40; pary `pairs-after-Low-{overcast,clear}`, `pairs-2024-after-Low-overcast`; draws G3-B: delta 0..+39 (mediana 0; +31..+39 w 4 kadrach z placem aut = instancje car_row).
Ocena renderu after: owal dwutonowy OK, auta OK, ogrodzenie frontowe ciemne OK; szkło NADAL czarne (env=0 przy patrzeniu na wprost) -> `showroom_glass` albedo 0.26/0.31/0.37 (odbicie nieba niesie człon dyfuzyjny); poza kontrolna 1020363345994649 poprawiona resekcją (E -227 N -256.5).
`git merge main` czysto (bb0dce01b; generated nie były commitowane). Stary czekający run-pytest zniknął, zostawił slot heavy `claude-frontage-r2-py` - przejęty.
W tle: `run-final-heavy.ps1` (build_world -> fidelity -> pytest gis+gate3; status `final-heavy.status`) i `run-final-unity.ps1` (import -> rendery `merged` Low overcast/clear -> EditMode; `final-unity.status`, `cycle-2.done`).
NASTĘPNY KROK (po `cycle-2.done`): `python artifacts/frontage-r2/make-pairs.py merged Low-overcast ; python artifacts/frontage-r2/make-pairs.py merged Low-clear ; python artifacts/frontage-r2/stats-diff.py merged` ; uzupełnić ADR 0129 (RESULTS_PLACEHOLDER) ; commit generated ; kopia artifacts do main.

## 6. Pierwszy przebieg po merge (17:14)
build_world OK (518 s), fidelity OK, pytest gis+gate3: 823 passed, 1 xfailed, 2 failed: `test_world_has_the_frontage` (stara lista propów bez car_row - poprawiona) i `test_cars_v4::test_parking_mix_and_neighbours` (2 x van_white obok siebie w rzędzie dealera - drugi to teraz `van_white2`).
W tle: Unity (import -> rendery `merged` -> EditMode, `cycle-2.done`) oraz `run-final-heavy2.ps1` (rebuild + fidelity + pytest, `final-heavy2.status`).
NASTĘPNY KROK: po `cycle-2.done` i `heavy2 done`: pary `make-pairs.py merged Low-overcast|Low-clear`, `stats-diff.py merged`, ADR, commit generated, kopia do main.

## 7. Koniec (17:58) - gotowe do scalenia
Przebieg 2: build_world OK, fidelity OK, `pytest tests/gis tests/gate3`: 825 passed, 1 xfailed (`pytest-gis-gate3-3.log`); EditMode 403/403 (`editmode.log`); import OK (64 chunki); rendery `merged` Low overcast+clear (20 SBS + 6 kontrolnych); pary `pairs-merged-Low-{overcast,clear}`, `pairs-2024-merged-Low-overcast`; draws `stats-diff-after.txt` (ta sama baza: 0..+39, mediana 0), `stats-diff-merged.txt` (-34..+65, mediana 0, zawiera dryf main).
ADR 0129 uzupełniony. Otwarte: kominy EC na Low (far clip 900 m < 1187 m), białe ogrodzenie plot_kit sąsiada, kontrast SERWIS.
NASTĘPNY KROK (lider): `git merge frontage-r2` (generated/*.json, *.glb, *_meta.json -> --ours) ; build_world ; import-region ; fidelity/run.py ; visual-critic na `artifacts/frontage-r2/pairs-merged-Low-overcast` + `pairs-2024-merged-Low-overcast`.

## 8. Drugi merge main (18:0x)
Main poszedł dalej (g3b-lowread) -> `git merge main` ponownie: LICENSES unia ręczna, pliki generowane = wersja main (do regeneracji przy integracji; do tego czasu `test_world_has_the_frontage` czerwony na starych danych main - oczekiwane). `git merge-tree main frontage-r2` czysto. Pełne testy (825 passed) dotyczą stanu z main f30837474.
