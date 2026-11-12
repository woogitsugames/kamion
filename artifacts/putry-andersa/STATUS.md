# putry-andersa (ADR 0146) STATUS
2026-11-12 19:59 sha 63ed45d91 (main 1b002a730 merged). Worktree .claude/worktrees/putry-andersa, branch putry-andersa.
W TLE: build_world (heavy slot claude-putry-andersa, PID: 58060  37696  62476  55936  73232  59520  5412  ) -> artifacts/putry-andersa/logs/build-world-1.log (+ .log.done z "build exit=N"); start 19:50, ~10 min.
ZROBIONE (kod + dane, testy lamp 6/6, ADR 0146 szkic docs/adr/0146-putry-andersa-world.md):
 - Latarnie Putry: slupy stoja na GRUNCIE w szczelinie (orto 0,08 m), glowice 10,3 m nad jezdnia (WORKING_VALUE 9,4-11,3; bylo 12,0). Ogniskowa zdjecia 494288 zmierzona w kadrze = 1900 px/2048 (vfov 44 st.), nie SfM 1.27 -> "6 m nad okiem" z 0143 to blad FOV. Prototypy lamp_double_10m / lamp_double_mast_10m (ramiona lukowe, LOD1 r 0,06 m), rzad 14 -> 18 slupow (do E -282).
 - Pobocze Putry: bridge_style cap_w 1.2, cap_mat bridge_fascia_red, barrier_face_m 0.70, ramp_fascia red; slupy ekranu dwuteowe.
 - Andersa 810896: OSM layer=1 -> NMT bez wagi; jezdnia NW 134,5 vs SE 132,6 przy E -395. profile_ties.json (authored_override) + wypelnienie pasa dzielacego (80 m). Po: obie ~133,2.
 - "Znak od tylu" = sygnalizator awaryjny strazy (OSM 1847044938), nie znak. B-23 brak w atlasie (otwarte).
NIEZROBIONE: import, rendery, pary, pomiar portalu Andersa (tablice +0,6 m), beam _b6 vs 0,55, tablice ostrzegawcze 275528, testy, koszt Low.
NASTEPNY KROK (po "build exit=0"): pwsh artifacts/putry-andersa/tools/run-import.ps1 ; pwsh artifacts/putry-andersa/tools/run-renders.ps1 ; pwsh artifacts/putry-andersa/tools/run-pytest.ps1 ; pwsh artifacts/putry-andersa/tools/run-editmode.ps1
Gotowe do scalenia: NIE (warunki: import + rendery obejrzane + testy zielone + ADR uzupelniony).
Dowody: artifacts/putry-andersa/{look,data,tools,logs}
