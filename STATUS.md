# STATUS mirror-mounts-s24 (krytyk day27 zestaw 3: wsporniki głowic lusterek, RT ≥ 512×1024 High, ciemniejsze szkło; dopisek 2 ADR 0340)

- Worktree `.claude/worktrees/agent-a788bb43492d27936`, gałąź `worktree-agent-a788bb43492d27936`. Nie scalane, nie pushowane. STAN: GOTOWE do oceny `visual-critic`.
- Środowisko: `game/Library`, `_Generated/{Truck,Trailer}`, `art-source/truck/interior/export` skopiowane z worktree `neon-avenue-s24` (Win64).
- [krok 1] PRZED: `artifacts/mirror-mounts-s24/before/` (DrivingLab, PC High, 1920×1080, clear; RT kl. II 171×384).
- [krok 2] Wspornik HUD zakotwiczony w słupku A (`MirrorWindowLayout.SolveMount/AimRight`, `MirrorWindowArt.Tube()/Foot()`, `DrivingHud.UpdateMirrorMount`,
  `RenderTextureMirror.CabMountWorld/ViewportOf`, `DrivingHudContext.Left/RightMirrorMountViewport`); RT kl. II min 512×1024 na PC High/Ultra → 512×1151
  (`mirrorMainMinWidth/Height`, mipmapy); `GlassTint` 0,92 → 0,80, `FilmVeil` 0,06 → 0,03; `mirrorPost` (gradacja w kamerze lusterka) zmierzone i wyłączone w tierach.
- [krok 3] PO: `artifacts/mirror-mounts-s24/after/` + zestawienia (`cmp_*.jpg`, `after_b_L.png`, `after_fov_variants.jpg`). MIRROR_BENCH (edytor): 171×384 3,75/3,77 ms/parę,
  512×1151 3,57/3,68 (szum), + post 4,27/4,43. `drawsEst`/`trisExact` kabiny bez zmian (147 / 175 023). GPU w playerze UNVERIFIED.
- [krok 4] Testy: EditMode 1639 / 1516 OK / 0 fail / 123 skip (`artifacts/tests/editmode-20261127-152203.xml`); PlayMode 5 klas HUD/lusterek 54 / 0 (`playmode-20261127-154849.xml`).
- [krok 5] Dopisek 2 w `docs/adr/0340-*.md`; dowody skopiowane do `C:\Users\matma\Documents\Claude\kamion\artifacts\mirror-mounts-s24\`.
- NASTĘPNY KROK (lider): `visual-critic` na `artifacts/mirror-mounts-s24/cmp_cab-view-b-fov70-hud.jpg` + `after_b_L.png`; po scaleniu pomiar playera
  `pwsh scripts/pc-metrics.ps1 -Exe <build> -Scene knyszyn-w -Tier High -Fps 60 -Width 1920 -Height 1080 -DurationSeconds 90 -Class zalecany` (A/B z `rq_mirror_main=0`).
