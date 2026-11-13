# STATUS p1b-0172 (agent #3, zatrzymany na limicie 93 %)
Nic nie działa w tle. Brak zmian w kodzie/danych świata.
Ustalenia 182011 (ortofoto td/hr_182arm.png): słup E-532.5 N37.9, łukowy wysięgnik ~8.8 m na WNW (koniec E-540.5 N41.7),
głowica nad linią pasa E-539.4 N40.7; cień wysięgnika z 2 plamami głowic (E-541.5 N45.3, E-543.5 N47.3) => 2 głowice na
wysięgniku + 1 na słupie; słup na wyspie żwirowej E-545 N40 (cień prosty). Prototyp `signal_mast` = signal_pole(6.8, 6.0)
(props.py:824), głowica tylko na 5.0 m (gate3_landmarks.py:419-423).
PLAN: (1) props.py: P["signal_mast_9m"]=signal_pole(S.SIGNAL_MAST_H, 8.8); (2) gate3_landmarks: opcje `arm_m` (wybór
prototypu) i `arm_heads_m: [..]` (lista odległości głowic) + `pole_head: true`; (3) overrides.yaml
putry-ring-s-approach-signal-mast: arm_m 8.8, arm_heads_m [5.5, 8.3], pole_head true; (4) poza kamery: sondy r1 gotowe
(r1/cameras.json, e15/e30/e45 = przesunięcie na wschód 1.5/3/4.5 m) -> render, wybór, finalize.py; (5) cm924 znaki
F-10/D-6/tablica ulicy jako kind gate3_sign (FACE_DIM ma F-10, D-6, street_name) — pozycje z td/hr_cm924s.png.
NASTĘPNY KROK (komenda): pwsh artifacts/p1b-0172/tools/render.ps1 r1   # render sond pozy 182011 (sprawdź param. w render.ps1)

## Agent #4 (wznowienie, 13.11 ~19:00)
- merge origin/main czysty (6d47a7818). Kod+dane @ push: props `signal_mast_9m` (8.8 m, S.SIGNAL_MAST_ARMS), gate3_signal `arm_m/arm_heads_m/pole_head`,
  twarze `F-10-ls` (lewo|prosto, pionowa 0.9x1.2) i `C-12` (dysk), nowy kind `gate3_lamp`; overrides: maszt 182011 (arm 8.8, głowice 5.5/8.3 + słup),
  wyspa EC cm924: ec-island-f10 / a7-c12 / d6 / lamp / street-name (stopy z cieni na ortofoto 0.08 m, td/hr_cm924z.png); filary x0.7 (P2).
- pytest: tests/gis/test_p1b_0172.py zielone (2 testy QA czekają na przebudowę świata).
- W TLE: `pwsh artifacts/p1b-0172/tools/regen.ps1` (build_world + import), log `artifacts/p1b-0172/logs/regen-r1.log`.
NASTĘPNY KROK: po „EXIT 0” w logu: `pwsh artifacts/p1b-0172/tools/render.ps1 r1` (sondy pozy 182011) + pary SBS Low/High.
- 19:0x lider: decyzja właściciela 2026-11-13 potwierdzona — 182011 wg ortofoto 2024 (do ADR 0172).
- 19:2x build_world r1 OK (675 s): gate3 stale=[], 5 obiektów wyspy EC snapped 0.0, maszt signal_mast_9m + 3 głowice + słupek; import czeka na PHONE_RUN (regen.ps1 w tle); pytest gis w tle.
- ~20:0x import r1 OK (preflight OK). W TLE: after.ps1 -Tag r1 (sondy r1 -> sbs-low-pairs -> vqa_low,vqa_high,editmode), status artifacts/p1b-0172/logs/after.status; pytest gis (po fidelity) w tle. NASTĘPNY KROK gdy przerwane: pwsh artifacts/p1b-0172/tools/after.ps1 -Tag r1
- ~20:1x r1 zweryfikowane: pytest gis 1077 passed/2 xfailed, EditMode 517/518 (1 skipped), SBS Low 42 pary, vqa Low/High. Obejrzane: maszt 8.8 m z 2 głowicami OK;
  cm924: skupisko jest, ale F-10 po złej stronie latarni i poza kamery nietrafiona -> resekcja 4-param. (latarnia/A-7/D-6/2 kominy, reszty <=0.6°): E533.9 N-737.1 h134.7 hfov67.6 eye2.1 (pewność B);
  182011 poza s1 (E-534.5 N10.5). r2: F-10 -> E539.1 N-741.6 tb200, tablica ulicy tb130, azyl brukowany z powrotem ON. finalize.py --write zrobione (sbs_*).
- W TLE: regen r2 (`pwsh artifacts/p1b-0172/tools/regen.ps1`, log logs/regen-r2.log) -> potem `pwsh artifacts/p1b-0172/tools/after.ps1 -Tag r2 -Steps sbs,vqa_low,vqa_high,editmode`.
- ~20:2x r2 obejrzane (sbs-r2/pairs): cm924 = azyl brukowany + latarnia + F-10 z lewej + tablica ulicy + D-6 jak na zdjęciu (poza B); 182011 jezdnia na całej szerokości + narożnik wiaduktu + maszt 2+1. EditMode 517/518.
  Poprawka r3: A-7/C-12 na wyspie była krawędzią do kamery (tb 31) -> tb 5. W TLE: regen r3 -> after.ps1 -Tag r3 -> fidelity -> pytest (logs/regen-r3.log, after.status, pytest-gis-r3.log).
NASTĘPNY KROK gdy przerwane: `pwsh artifacts/p1b-0172/tools/regen.ps1; pwsh artifacts/p1b-0172/tools/after.ps1 -Tag r3 -Steps sbs,vqa_low,vqa_high,editmode`, potem ADR §4 + kopiowanie dowodów do main artifacts/p1b-0172.

## Agent #5 (s19, 13.11 20:27)
- regen r3 z s18 wciąż działa (pwsh 66800, build_world od 20:16) — czekam na koniec, drugiej regeneracji nie uruchamiam.
NASTĘPNY KROK: po zakończeniu procesu 66800: `pwsh artifacts/p1b-0172/tools/after.ps1 -Tag r3 -Steps sbs,vqa_low,vqa_high,editmode`
- 20:29 build_world r3 OK (773 s, 'done'); regen.ps1 padł w finally (osierocona konsola, EXIT 1) przed importem — slot heavy zwolniony ręcznie. W TLE: `regen.ps1 -SkipBuild` (sam import) -> after.ps1 -Tag r3, log logs/regen-r3b.log.
NASTĘPNY KROK gdy przerwane: `pwsh artifacts/p1b-0172/tools/regen.ps1 -SkipBuild; pwsh artifacts/p1b-0172/tools/after.ps1 -Tag r3 -Steps sbs,vqa_low,vqa_high,editmode`
- 20:45 r3 OK: import + preflight OK, SBS Low 42 pary, vqa Low/High exit 0, EditMode 517/518 (1 skipped), fidelity exit 0. Obejrzane r3 (sbs-r3/pairs + kadry 1:1): A-7/C-12 widoczne tyłem jak na zdjęciu (OK), 182011 maszt łukowy 2+1 jak na ortofoto (OK).
  Odstaje (pomiar na zdjęciu, poza B, ogniskowa 2868 px, horyzont 1137 px): F-10-ls 0,90x1,20 -> rzeczywista ~0,80x0,80 (338 px na 6,75 m); A-7/C-12 za nisko o ~0,6 m (tarcza 2,58-3,27, trójkąt 3,56-4,18) -> lower_edge 2,7; tablica ulicy 3,3 -> 3,1.
- r4: poprawki w gate3_landmarks.FACE_DIM + overrides.yaml + test. W TLE po pytest r3: regen r4 (log logs/regen-r4.log) -> after.ps1 -Tag r4.
NASTĘPNY KROK gdy przerwane: `pwsh artifacts/p1b-0172/tools/regen.ps1 *> artifacts/p1b-0172/logs/regen-r4.log; pwsh artifacts/p1b-0172/tools/after.ps1 -Tag r4 -Steps sbs,vqa_low,vqa_high,editmode`, potem fidelity + pytest tests/gis, ADR §4, robocopy dowodów do main.
