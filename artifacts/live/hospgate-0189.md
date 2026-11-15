# hospgate-0189 (ADR 0189, brama szpitala P11-129) — GOTOWE (`r4` / M62-FIX)
Worktree: `.claude/worktrees/hospgate-0189`, gałąź `hospgate-0189` (wypchnięte na `origin/hospgate-0189`).

- **Scalono `origin/main` (M62-FIX)** i wykonano rundę **`r4`** wg `REVIEW-2026-11-14-s20-mistral-m62.md` §7 i `research/mistral/p19-hospital-gate/` (`M62-FIX`, kierunek wjazdu `~242°` w siatce EPSG:2180):
  - **Mur i brama**: mur z jasnej cegły ograniczony do `~6,2 m`, płaska nakrywa betonowa, pojedynczy filar końcowy, 5 poziomych bordowych tablic w układzie `2 + 3`, wspólne zadaszenie z ciemnej blachy na białej belce nad 2 filarami N, `B-20 STOP` + niebieska tablica `WJAZD NA PODSTAWIE`, niebieska tablica `IZBA PRZYJĘĆ` na osobnym białym słupku przed prawym filarem.
  - **Szlaban i znaki**: czerwona obudowa + biało-czerwone ramię z niebieską tabliczką `OPŁATA ZA WJAZD 3 zł`, słupek z latarenką + `C-2` + `B-33 „20”`, znak `B-2` na osobnym słupku w głębi (`~24 m` za bramą).
  - **Tło i zieleń**: 4-kondygnacyjny szary blok (`bdot:2BE4B431-AAE9`) obniżony do 2 kondygnacji beżowych + 2 niskie 1-kondygnacyjne budynki (`plaster_beige`) + 2 smukłe kominy (`13,5 m`); 5 kolumnowych iglaków (`PLT.thuja`) za lewym murem i w głębi.
- **Walidacja `r4`**:
  - `pytest tests/gis/test_masonry_gate_0189.py -q`: **10/10 passed**.
  - `pwsh scripts/test.ps1 -Platform EditMode`: **587 total, 586 passed, 0 failed, 1 skipped (Ignored)**.
  - `pytest tests/gis -q`: **1239 passed, 3 skipped, 3 xfailed, 2 failed** (oba niepowodzenia tylko na przestarzałym `Data/raw/derived/bialystok-industrial-c/world` w worktree; wszystkie testy `bialystok-dojlidy` i `masonry_gate` przeszły).
  - Wizualne SBS (`r4` Low & High): `artifacts/hospgate-0189/sbs/sbs-P11-129-Low-overcast-r4.jpg`, `artifacts/hospgate-0189/sbs/sbs-P11-129-High-overcast-r4.jpg` (obejrzane, zgodne z `P11-129` i `M62-FIX`).
  - ADR: `docs/adr/0189-brama-szpitala-masonry-gate.md` (`PROPOSED`).
