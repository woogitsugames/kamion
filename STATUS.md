# STATUS mirror-mounts-s24 (krytyk day27 zestaw 3: wsporniki głowic lusterek, RT ≥ 512×1024 High, odbicie mniej jasne/mgliste; dopisek 2 ADR 0340)

- Worktree `.claude/worktrees/agent-a788bb43492d27936`, gałąź `worktree-agent-a788bb43492d27936`. Nie scalane, nie pushowane.
- Środowisko: `game/Library`, `_Generated/{Truck,Trailer}`, `art-source/truck/interior/export` skopiowane z worktree `neon-avenue-s24` (Win64).
- [krok 1] Rendery PRZED: `artifacts/mirror-mounts-s24/before/` (DrivingLab, PC High, 1920×1080, clear, wszystkie kamery + `mirror_L/R.png` 171×384).
  Diagnoza: (a) okienka HUD stoją nad lewą krawędzią słupka A / w szybie po prawej; stare ramiona = sztywny kikut 68 j. z tuleją, bez związku z kabiną;
  (b) RT kl. II 171×384 (szkło TRAKT ma proporcję 0,445, nie 0,55); (c) kamera lusterka bez HDR/post — obraz bez krzywej tonalnej widoku głównego (blady) + welon filmu 0,06.
- [krok 2] Implementacja (WIP, kompilacja i rendery w toku):
  - wspornik: `MirrorWindowLayout.SolveMount/AimRight` (czysta geometria), `MirrorWindowArt.Tube()/Foot()` (rura 9-slice + stopa ze śrubami), `DrivingHud.UpdateMirrorMount`
    — rura pozioma + zastrzał od głowicy do rzutu punktu mocowania na słupku A (`RenderTextureMirror.CabMountWorld`, offsety z `body.py mirrors()`), punkt podaje `DrivingHudContext.Left/RightMirrorMountViewport`.
  - RT: `VehicleCameraBudget.MainMirrorHeight` + pola tieru `mirrorMainMinWidth/Height` (PC High/Ultra 512×1024 → 512×1151 dla szkła 0,445), mipmapy + trilinear gdy RT > okienko.
  - obraz: `mirrorPost` (PC High/Ultra) — HDR + post (ta sama gradacja co widok główny) w kamerach lusterek pokazywanych w okienkach HUD; `FilmVeil` 0,06 → 0,03.
  - A/B: `rq_mirror_main=<px|0>`, `rq_mirror_post=<0|1>`; edytor `KAMION_MIRROR_MAIN`, `KAMION_MIRROR_POST`, `KAMION_QA_MIRROR_MOUNT=0`.
  - testy: `MirrorMount0340Tests` (EditMode, 8), `MirrorHeadArtTests` (PlayMode) zaktualizowany.
- NASTĘPNY KROK: `pwsh -File <scratchpad>/run_qa.ps1 -Out iter1 -TestFilter Game.Tests.MirrorMount0340Tests -Bench` (lub ręcznie: `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 -Filter Game.Tests.MirrorMount0340Tests`,
  potem `$env:KAMION_MIRROR_DUMP=<dir>; pwsh scripts/visual-qa.ps1 -Scene DrivingLab -Tier High -Pc -Width 1920 -Height 1080 -Lighting clear -BuildTarget Win64 -Cameras cab-view-b-fov70-hud,cab-left,cab-right -OutputDir artifacts/mirror-mounts-s24/iter1`), obejrzeć PNG, poprawić.
