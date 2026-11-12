# STATUS — biezenstwa-island (ADR 0128), gałąź `biezenstwa-island` od `junctions-r6` 21aef33f

## Sesja 12
- krok 1 (13:05–14:20): worktree + dane (robocopy, junctiony), 2 komórki ortofoto HR 0,08 m dociągnięte z GUGiK WMS
  (`artifacts/biezenstwa-island/ortho_hr`, `ORTHO_HR_EXTRA`). Diagnoza: (a) wlot N ronda Bieżeństwa — generator zaokrągla naroże
  łącznica/jezdnia ronda łukiem R 12 m (j:n1882953899 corner2), realnie krawężniki idą prosto do nosa E 540,6 N -691,9; (b) U-4a przy
  Andersa/Elewatorska: pozycja z ADR 0125 (-217,3,-240,3) to starta farba na jezdni, snap 5,4 m wyrzucił tablicę na pobocze za łącznicą;
  realny nos wyspy (-219,6,-235,3) = istniejąca wyspa autorska.
- krok 2: kod — `traffic_island.patches` (gores.py), znaki gate3 na wyspach autorskich (gate3_landmarks.py, stage.py), overrides:
  `biezenstwa-n-slip-nose` (wyspa żwir + płyta chodnika), D-6/D-3 z ortofoto+geometrii zdjęcia, U-4a na nos wyspy; test gate3: stale == ∅.
  NASTĘPNY KROK: `bash artifacts/biezenstwa-island/scripts/build.sh i1 && bash artifacts/biezenstwa-island/scripts/imp_sbs.sh i1`
- krok 3 (13:30–13:45): baza b5 = `_Generated` + `Library` skopiowane z junctions-r6 (b5 po imporcie), render SBS 43 kamer Low overcast/clear
  → `renders_b5sbs_*` (+ `stats.txt`), pary `pairs_b5/`; kamera-sonda pozy 320326 (`cams_sbs.json`, `sbs-g3-a-p0128-…`); test syntetyczny
  `patches` zielony; szkic ADR 0128. Build i1 w kolejce FIFO puli heavy (9. miejsce o 13:34), po nim automatycznie import + SBS.
  NASTĘPNY KROK (gdy `logs/i1_build.out` ma „build done”): `bash artifacts/biezenstwa-island/scripts/imp_sbs.sh i1 && bash artifacts/biezenstwa-island/scripts/pairs.sh i1 b5`
- krok 4 (13:38): baza b5 przerenderowana z kamerą-sondą (`pairs_b5/probe_320326_low_overcast.jpg`). Build i1 nadal w kolejce heavy
  (`nohup build.sh i1`, log `logs/i1_build.out`); łańcuch w tle sam odpali import + SBS po „build rc 0”. Lider 13:5x: limit 91 %, oszczędnie do 14:12.
  NASTĘPNY KROK: jeśli `logs/i1_build.out` nie istnieje / brak „build start” → `bash artifacts/biezenstwa-island/scripts/build.sh i1`;
  po „build done” → `bash artifacts/biezenstwa-island/scripts/imp_sbs.sh i1 && bash artifacts/biezenstwa-island/scripts/pairs.sh i1 b5`
  → obejrzeć `pairs_i1/sbs-g3-a-p0128-320326319617139_low_overcast.jpg`, `sbs-g3-b-381800493259507_*`, `sbs-g3-b-837235577143499_*`
  → `bash artifacts/biezenstwa-island/scripts/post.sh i1 full` → uzupełnić „Result” w `docs/adr/0128-biezenstwa-island.md`.
- krok 5 (14:14): build i1 działa od 14:02 (slot heavy), na bazie junctions-r6 21aef33f (b5). junctions-r6 ma 3 nowe commity (b6: nasyp żwirowy
  na wyspie centralnej) — merge PO końcu i1 (nie zmieniam źródeł w trakcie buildu), kolejny build i2 będzie już z b6.
  NASTĘPNY KROK (po „build done” w `logs/i1_build.out`; import + SBS i1 odpali łańcuch w tle, inaczej ręcznie):
  `bash artifacts/biezenstwa-island/scripts/imp_sbs.sh i1 && bash artifacts/biezenstwa-island/scripts/pairs.sh i1 b5` → obejrzeć pary →
  `git merge junctions-r6` (generated/* → ours) → `bash artifacts/biezenstwa-island/scripts/build.sh i2 && bash artifacts/biezenstwa-island/scripts/imp_sbs.sh i2 && bash artifacts/biezenstwa-island/scripts/post.sh i2 full`
- krok 6 (15:28–15:58): import i1 rc 0 (64 chunki), SBS Low overcast/clear, pary `pairs_i1/` (zdjęcie | b5 | i1). Budżet Low overcast, 43 kamery
  SBS: draws max +1, tris max +0,3 % (`logs/i1_stats_low_overcast.txt`). 320326 z pozą-sondą: D-3 z lewej, D-6 z prawej na wysepce jak na zdjęciu.
  U-4a stoi na nosie wyspy z ortofoto 2024, ale w kadrach 837235/381800 jest 18/39 m od kamery (zdjęcie 2019: ~6,5 m) — wyspa w 2017–2019 była
  dłuższa (nos ok. -210,-242 wg promowanej pozy), przebudowana przed 2024. Decyzja lidera: świat 2024 czy stan ze zdjęć.
  Uwaga: dwa łańcuchy importu wystartowały naraz (stary w tle + ręczny), jeden import rc 1, rendery ręcznego szły ~2 min bez pliku slotu.
  NASTĘPNY KROK: `git merge junctions-r6` (generated/* → ours) → `bash artifacts/biezenstwa-island/scripts/build.sh i2 && bash artifacts/biezenstwa-island/scripts/imp_sbs.sh i2 && bash artifacts/biezenstwa-island/scripts/pairs.sh i2 b5 && bash artifacts/biezenstwa-island/scripts/post.sh i2 full`
- krok 7 (16:05): `git merge junctions-r6` (605182b7, b6: nasyp żwirowy wyspy centralnej) bez konfliktów. Uruchomione `all.sh i2` (jeden slot heavy:
  build → fidelity/swept/pytest pełny; równolegle w puli unity import + SBS + EditMode). Wynik: `logs/i2_all.out`.
  NASTĘPNY KROK: jeśli `logs/i2_all.out` nie kończy się „all done” → `bash artifacts/biezenstwa-island/scripts/all.sh i2 > artifacts/biezenstwa-island/logs/i2_all.out 2>&1`;
  potem obejrzeć `pairs_i2/`, uzupełnić „Result” w ADR 0128, `robocopy artifacts\biezenstwa-island C:\Users\matma\Documents\Claude\kamion\artifacts\biezenstwa-island /E /XF *.pkl`
- krok 8 (16:1x): i1 obejrzane natywnie (`pairs_i1/probe_i1_low_clear_960.jpg`: D-3 z lewej, D-6 z prawej, płyta chodnika, żwirowy nos — układ jak na
  zdjęciu 320326; żwir ciemniejszy niż na zdjęciu). `all.sh i2` w tle (nohup), czeka / działa w puli heavy.
  NASTĘPNY KROK: `tail artifacts/biezenstwa-island/logs/i2_all.out` — gdy „all done”: obejrzeć `pairs_i2/sbs-g3-a-p0128-320326319617139_low_*.jpg`,
  sprawdzić `logs/i2_pytest.log`, `logs/i2_editmode.log`, `swept_i2`, wpisać liczby do „Result” w `docs/adr/0128-biezenstwa-island.md`, commit, potem
  `robocopy artifacts\biezenstwa-island C:\Users\matma\Documents\Claude\kamion\artifacts\biezenstwa-island /E /XF *.pkl`. Jeśli brak procesu i brak „all done”:
  `bash artifacts/biezenstwa-island/scripts/all.sh i2 > artifacts/biezenstwa-island/logs/i2_all.out 2>&1`
- STOP (limit lidera, ok. 16:35): nic nowego nie zaczynam. W TLE DZIAŁA (nie zabite): `nohup bash artifacts/biezenstwa-island/scripts/all.sh i2`
  → log `artifacts/biezenstwa-island/logs/i2_all.out` (kolejka heavy → build i2 → fidelity/swept/pytest pełny; równolegle import + SBS + EditMode,
  log `logs/i2_imp.out`; na końcu `pairs_i2/` i linia „all done”). Slot heavy/unity zwalnia sam skrypt. Stan gałęzi: i1 zweryfikowane (stale puste,
  draws max +1, tris max +0,3 %), junctions-r6 605182b7 scalone, ADR 0128 „Result” = RESULTS_PENDING, dowody jeszcze NIE skopiowane do main.
  NASTĘPNY KROK: `tail -20 artifacts/biezenstwa-island/logs/i2_all.out` — gdy „all done”: `git add -A Data art-source/world/props art-source/world/signs && git commit -m "wip(island): i2"`,
  obejrzeć `pairs_i2/`, uzupełnić „Result” w `docs/adr/0128-biezenstwa-island.md`, `robocopy artifacts\biezenstwa-island C:\Users\matma\Documents\Claude\kamion\artifacts\biezenstwa-island /E /XF *.pkl`;
  gdy brak „all done” i brak procesu: `bash artifacts/biezenstwa-island/scripts/all.sh i2 > artifacts/biezenstwa-island/logs/i2_all.out 2>&1`.
  Do decyzji lidera: U-4a przy Andersa — świat 2024 (ortofoto, krótsza wyspa) czy stan ze zdjęć 2017–2019.

## Sesja 13
- krok 9 (16:45): wznowienie. `all.sh i2` z s12 nadal żyje (PID 44241) i czeka w kolejce heavy (build NIE wystartował, `i2_all.out` pusty).
  Zanim dostał slot: `git merge junctions-r6` (61f8eda5, konflikt world_manifest → ours) i `git merge main` (bedc52d1; konflikty generated/*.json,
  street_props.glb → ours; WorldPBR.shader CBUFFER → obie strony: _VertexGrime/_LowNoShadow + _KerbWear/_GroundWearExclude/_GroundGrimeBase).
  Build i2 pójdzie więc już na drzewie scalonym z main (0d412990).
  NASTĘPNY KROK: `tail -20 artifacts/biezenstwa-island/logs/i2_all.out` — gdy „all done”: obejrzeć `pairs_i2/`, `logs/i2_pytest.log`, `logs/i2_editmode.log`,
  uzupełnić „Result” w `docs/adr/0128-biezenstwa-island.md`, commit, robocopy do main. Brak procesu i brak „all done”:
  `bash artifacts/biezenstwa-island/scripts/all.sh i2 > artifacts/biezenstwa-island/logs/i2_all.out 2>&1`
