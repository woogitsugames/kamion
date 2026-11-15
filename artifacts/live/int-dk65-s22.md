# int-dk65-s22 (live)
## 15.11 krok 1 — worktree + merge
- Worktree `.claude/worktrees/int-dk65-s22`, gałąź `int-dk65-s22` z main 612185470.
- Scalone: origin/dk65-k1-0220 (#98; konflikty: overrides dk65-02..05 = suma, Ełcka 6,6 m zachowana; kamery dk65-03/05 = obie listy; markings.py = unmarked + edge_dashed), origin/roundabout-0218 (#97; network.py = construction + truck_apron), origin/treerows-0222 (#101; czysto). #93 NIE włączony.
- Rondo: override `knyszyn-roundabout-truck-apron` (way 1426801304, width 5.0, truck_apron 3.2 m / 0.04 m / kostka_jasna) nałożony na `Data/Regions/knyszyn/overrides.yaml` (na początku listy — Codex knyszyn-rynek-0227 edytuje dalsze części pliku) + kamera `rondo_dk65_top`.
- Pomiar na zdjęciu 9 właściciela (ESTIMATED, skala z Ø zewn. 22,6 m): wyspa Ø ~16,4 m, strefa wewn. Ø ~11,6 m, opaska ~2,4 m, asfalt pierścienia ~3,1 m (override: asfalt 5,0 + opaska 3,2) — do decyzji lidera.
- pytest -k "0220 or 0218 or apron or treerow or marking or edge_lines or 0233 or swept": 117 passed, 2 skipped, 1 xfailed.
NASTĘPNY KROK: `Start-Process pwsh -WindowStyle Hidden -ArgumentList '-NoProfile','-File','artifacts/int-dk65-s22/tools/chain.ps1','-Tiles','knyszyn-s,knyszyn,dk65-01,dk65-02,dk65-03,dk65-04,dk65-05,dk65-06,dk65-07,dk65-08,dk65-09,dk65-10,dk65-11,knyszyn-w'` (w worktree; status artifacts/int-dk65-s22/logs/chain.status)
