# islands-r10 (ADR 0077) — STATUS

Gałąź: worktree-agent-a2afb96d89584cca6 (worktree .claude/worktrees/agent-a2afb96d89584cca6).

- 21:35 Baseline fidelity na main ffcc7b7 odtworzony: wysepki bez pokrycia 4, pas→wysepka 3, brakujące 18, krawędź p95 2,04 m.
- Obejrzane zoomy (artifacts/islands-r10/before/*.jpg, ortofoto 0,08 m). Wnioski:
  * 2 z 3 „pas→wysepka” (wlot ronda Bieżeństwa w188397875) to fałszywy alarm narzędzia: na wprost od wlotu ronda zawsze
    jest wyspa środkowa → run.py pomija wloty rond. Wysepka 570,7/−688,2 istnieje naprawdę (brukowana wysepka rozdzielająca).
  * „18 brakujących wysepek” to głównie auta/cienie/chodniki (green_frac 0); realne: dłuższy nos mediany przy bramie
    Kwadrat Park (619,−599), szersza mediana Andersa (−229,−244: krawędzie), nosy mediany przy straży (−290,−187).
  * Prawdziwe fałszywe wysepki: klin łącznica/Andersa (−84,−342), Putry N (−575,107), pola P-21 przy s610 (348,−540 i
    337,−574: w rzeczywistości SAMA FARBA — zgłoszenie właściciela „malowana wysepka = sama farba”).
- 22:20 `tools/worldgen/roads/gores.py` (nowy etap, NIE ruszam compute_corners/align_forks — uzgodnione z 0076):
  szczeliny < 2,0 m (≤ 60 m) i kliny między jezdniami tego samego kierunku < 4,0 m (≤ 90 m) = asfalt + krawężnik
  schowany; override `paved_gore` (punkt+promień, opcja hatch P-21), `traffic_island` (poligon). Kafel: 20 wypełnień
  329 m², 382 m krawężnika schowane, 18 odrzuconych (różne wysokości — rampy).
- Commit 952c1eb.
- NASTĘPNY KROK: dodać overrides paved_gore (+hatch P-21) dla s610, Putry N, −392/−134; potem
  `uv run tools/worldgen/build_region.py --region bialystok-industrial-c` →
  `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` →
  `uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art artifacts/islands-r10/fidelity` →
  `uv run --project tools/worldgen pytest tests/gis -q`; zaostrzyć ratchet w tests/gis/test_road_fidelity.py.
- 22:45 (przejęcie po limicie) Stan zastany: overrides s610 + regeneracja były zrobione, niezacommitowane → commit ebebfd8.
  Uczciwy „przed” na tym samym kodzie (WORLDGEN_NO_GORES=1, artifacts/islands-r10/fidelity_before_qa.json): oś p95 0,129
  (max 3,25 = align_forks z 0074, nie nasze), krawędź p95 2,483 (n 618), wysepki bez pokrycia 4, pas→wysepka 0, brakujące 16.
  (BASELINE 2,04 / 0,032 w teście pochodził z raportu sprzed scalenia 0074 — raport na main był nieaktualny.)
- MA-010 zdiagnozowane (after3/ma010_chains.jpg): oś OSM w180144451 biegnie po południowym krawężniku → symetryczna
  jezdnia 7 m kładła prawy pas na prawdziwym trawniku. edge_sides: na Andersa/DK8 jezdnia jest przesunięta względem osi
  OSM o 0,5–1,0 m (L+ / R−). Nowy override `set: {center_offset: m}` (network.apply_edge_overrides + prepare_chain;
  NIE dotyka align_forks/taper_forks/assign_sides agenta 0076) + 8 wpisów w overrides.yaml. Commit: patrz git log.
- s1440 (−366,−119 506 m² i −391,−135): na ortofoto P-21 + bariera; to korytarz agenta 0076 (s1432–1480) — NIE ruszam.
- NASTĘPNY KROK (w toku): `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` →
  `uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art artifacts/islands-r10/fidelity` →
  obejrzeć artifacts/islands-r10/after4/*.jpg → `uv run --project tools/worldgen pytest tests/gis -q` → ratchet w tests/gis/test_road_fidelity.py
  → `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` → `pwsh scripts/visual-qa.ps1 -Scene WorldC ...`.
