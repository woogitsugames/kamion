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
