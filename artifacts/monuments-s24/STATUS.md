# STATUS monuments-s24 (ADR 0325) — CRITIC s24 wave 6 pkt 1.3 (król w Knyszynie) i 1.4 (bruk Pl. Czarnieckiego)

## Krok 0 — rozpoznanie (bez zmian w kodzie)
- Worktree `.claude/worktrees/monuments-s24`, gałąź `monuments-s24` z main 3fba5b3b7; `Data/raw/derived` = kopia (-CopyDerived).
  W worktree nie ma `game/Assets/_Generated/World` ani tekstur `art-source/world/materials/<set>` → pierwszy import = build_all (~8 min) + pełny import regionu.
- Referencje (poza gitem): Commons `Data/raw/refs/knyszyn-king-commons` (cs128805425 CC BY-SA 4.0, cs7518515 CC BY-SA 4.0, cs20127375 CC BY-SA 3.0)
  + ortofoto GUGiK WMS `Data/raw/refs/tykocin-rynek-ortho/plaza_0.05.png`.
- Pomnik naprawdę: graniasty płaszcz-dzwon bez widocznych rąk, głowa z brodą, kreza, korona z fleuronami, dwa łańcuchy z klejnotem,
  futrzane wyłogi, szew z przodu; cokół z szarego granitu z ciemną tablicą. Rąk NIE dodawać (nie ma ich na rzeźbie).
- Bruk (pomiar na ortofoto, układ EPSG:2180): krata kwadratowa, normalne pasów 53,75° i 143,75° od wschodu, okres 2,255 m (reszty < 0,10 m),
  faza −18,488 m / −18,020 m względem E751808 N600236; pas ~0,5 m (FWHM 0,57 m przy rozmyciu orto), opaska obwodowa.
  Naroża płyty: NW 751786.0/600245.7, NE 751826.2/600254.8, SE 751829.8/600222.5, SW 751789.2/600218.0.
- Plan: (1) `art-source/world/materials/_src/sets_plaza.py` (kostka granitowa w wachlarze + krata czerwona; zestaw modulacyjny kostki),
  (2) `paved.py`: opcjonalna rama UV (`uv_frame`) z override, (3) figura króla w nowym module `streetscape/knyszyn_king_0325.py`,
  (4) build_world knyszyn + tykocin, import, visual-qa, SBS.
- NASTĘPNY KROK: `uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only <nowe zestawy>`
