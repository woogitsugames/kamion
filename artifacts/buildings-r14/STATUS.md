# buildings-r14 (ADR 0107, zabudowa r6 + działki domów) — STATUS

Gałąź `buildings-r6`, worktree `.claude/worktrees/buildings-r6`, z main `ff400569`.

## krok 1 — przygotowanie, kod P1-e/f/g
- Skrypty r13 skopiowane do `artifacts/buildings-r14/` (+ `extra.ps1`, `seq.ps1`, `snap.ps1`, `roof_parts.py`, `plots_plot.py`);
  blokady PHONE_RUN i GPT_UNITY_HOLD respektowane w `run_round.ps1` / `extra.ps1`.
- UWAGA: `game/Assets/_Generated` skopiowane z main było importem sprzed r5 (konfetti balustrad na renderze) — pierwszy
  „baseline” (`base_stale_import/`) jest nieważny; baza = snapshot danych main (`_snap/base`, region High 4028 submeshy /
  14,03 mln tris, Low 3009 / 4,497 mln) importowany na nowo.
- Zestawy PBR (`art-source/world/materials/<set>`) nie były w worktree — skopiowane z main (robocopy), przebudowany tylko `facade_far`.
- P1-e: `balcony_slab` 0,30 → 0,52, `sky_occ` [0, 0] (blok addytywny na końcu `materials.py`); krawędź płyty w `facade_far` 0,30 → 0,50.
- P1-f: tryb „sill-local” w `WorldPBR.shader` (v ≥ 112, addytywnie): dwa wąsy od końców parapetu + szeroki słaby pas;
  generator `sill_marks` (połówki parapetu, 40 % okien bez śladu, niższe kondygnacje dłuższe).
- P1-g: `MultiRoof` — domena części nie wchodzi w prostokąt innej części, małe części = jedna połać (lean-to / przedłużenie
  połaci głównej), ściany zamykające uskoki (`step_walls`), obróbka kosza +3 cm. roof_scan: 99 MultiRoof, 0 dziur.
- P2-h pranie pod poręczą (bez czerwieni), P2-i wyjątki balustrad neutralne (bez maty trzcinowej), P2-j próg szary,
  P2-k fugi wysokiego cokołu (`plinth_joints`), P2-m kamery r13 na NMT + omijanie drzew.
- P1-h: `streetscape/plots.py` (plan działek z reguł + OSM barrier, przęsła / bramy / furtki / podjazd / tuje jako instancje
  26 prototypów, krzewy i drzewka z istniejących prototypów, maska trawnika) + 2 linie w `props.py`, 3 wstawki w `stage.py`.
- Testy: `tests/gis/test_buildings_r6.py` 11 passed, r5 dostosowane.
- NASTĘPNY KROK: (build_world r1 w toku) → `pwsh artifacts/buildings-r14/snap.ps1 -Name r1` →
  `pwsh artifacts/buildings-r14/seq.ps1 -Rounds base,r1`
