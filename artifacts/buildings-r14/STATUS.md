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

## krok 2 — baza (świeży import) i r1 zrenderowane, kod r2
- Baza: `base/` (import danych main ze snapshotu, High/Low overcast + High clear + 15 kamer `extra/`).
- r1 (P1-e/f/g + działki + P2-h/i/j/k): region High 4028 submeshy / 14,05 mln tris (baza 4028 / 14,03), Low 3009 / 4,501 mln
  (baza 3009 / 4,497). Działki: 99 z 104 grup (270 domów), 4471 przęseł, 60 bram, 192 furtki, 362 płyty podjazdu,
  166 tuj, 197 krzewów, 29 drzewek = 5477 instancji.
- Budżet Low 57 kamer baza → r1: draws 16695 → 16695 (+0,0 %), tris 15256k → 15304k (+0,3 %, maks. r10_block_5 +1,7 %),
  kamer > 400 draws 10 → 10 (`budget.py`). Instancje działek nie wchodzą do `drawsEst` (rysuje je WorldInstances);
  górne oszacowanie w promieniu 120 m: 21 prototypów / 38 submeshy (`plot_instances.py`) → r2 redukuje.
- P1-e zmierzone (`underside.py`, r10_block_4, ten sam prostokąt): spód 42 → 71 sRGB, spód/ściana 0,38 → 0,63 (High
  overcast), 0,36 → 0,61 (Low overcast).
- Obejrzane: r10_house_2 — ogrodzenie panelowe, brama, podjazd z kostki czytelne; wąsy spod parapetów widoczne, ale
  cienkie i za długie (→ r2: szersze, krótsze); podwójne płoty w V między sąsiadami (→ r2: reguła 2,5 m / 25°).
- r2 kod: słupki i ramy w materiale siatki (1 submesh), działki cięte do modułu 2,5 m i grupa brama+furtka na module →
  bez prototypów połówkowych (26 → 19 prototypów), dryf tonu dachówki (P2-n).
- NASTĘPNY KROK: (build r2 w toku, potem sam `seq.ps1 -Rounds r2`) → obejrzeć `r2/extra/960`, potem
  `uv run --project tools/worldgen python artifacts/buildings-r14/budget.py artifacts/buildings-r14/base/Low-overcast artifacts/buildings-r14/r2/Low-overcast`
