# ARGON-S20 — ADR 0189 (`hospgate-0189`)

- **Gałąź i SHA:** `hospgate-0189` @ `88df4559f` (runda `r4`, po scaleniu `origin/main` z `M62-FIX`)
- **Co zrobiono (rundy r1..r4 wg `M62 §7` i `M62-FIX`):**
  - Kierunek wjazdu `~242°` (`anchor.at_en: [327.1, 808.4]`), mur z jasnej cegły `~6,2 m` z nakrywą betonową, filarem końcowym i 5 bordowymi tablicami (`2+3`).
  - Ganek N z 2 filarami i wspólnym ciemnym daszkiem (`z_m: 2.65`), `B-20 STOP` + `WJAZD NA PODSTAWIE`, `IZBA PRZYJĘĆ` na osobnym białym słupku przed prawym filarem.
  - Własny szlaban (`own_mesh: true`, zastępuje 1 `lift_gate` OSM): czerwony napęd, biało-czerwone ramię z `OPŁATA ZA WJAZD 3 zł`, słupek z latarenką + `C-2` + `B-33 „20”`, `B-2` w głębi (`a = -24 m`).
  - Tło: obniżono `bdot:2BE4B431-...` do `6.2 m` (`plaster_beige`), dodano 2 parterowe budynki szpitalne, 2 smukłe kominy (`13.5 m`) i 5 kolumnowych iglaków (`PLT.thuja`, `8.0–9.5 m`).
  - Budżet `photo-P11-129c` (`r4`): Low `drawsEst=329`, `trisExact=440 709` (`WORLD_MEMORY 97.5 MB`); High `drawsEst=621`, `trisExact=915 806` (`WORLD_MEMORY 212.8 MB`) — brak regresji (`masonry_gate`: `576` tris, `1` draw).
- **Testy (po `r4`):**
  - `pytest tests/gis/test_masonry_gate_0189.py -q`: `10 passed`.
  - Pełny `pytest tests/gis -q`: `1239 passed, 3 skipped, 3 xfailed, 2 failed` (wyłącznie nieprzebudowany `bialystok-industrial-c/world` w worktree, poza zakresem).
  - Pełny `EditMode`: `587 total, 586 passed, 0 failed, 1 skipped`.
- **Dowody i recenzja:**
  - `artifacts/hospgate-0189/sbs/sbs-P11-129-{Low,High}-overcast-r4.jpg`
  - ADR: `docs/adr/0189-brama-szpitala-masonry-gate.md` (`PROPOSED`)
  - Recenzja niezależna: `docs/reports/REVIEW-ARGON-hospgate-0189.md` — werdykt **SCAL** (0 P0, 0 P1).
- **Otwarte:** P2 w zakresie (podest pod gankiem, długość ramienia szlabanu, ściana portierni) i poza zakresem (chodnik pod murem, okna tła, zrzut z Galaxy A16 przed bramką 3).
- **Komenda scalenia:** `git merge --no-ff origin/hospgate-0189`
- **Gotowe do scalenia:** TAK
