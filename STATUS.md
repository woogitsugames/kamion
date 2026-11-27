# STATUS mirror-housing-s24 (krytyk build #10 pkt 8: obudowa lusterek 3D w okienkach, bok/przod naczepy w lusterku, papiery na desce, plakietka POSTOJOWY)

- Worktree `agent-a4a29737953b3f1da`, galaz `worktree-agent-a4a29737953b3f1da`. Nie scalac (lider).
- Srodowisko: Library + `_Generated` + `art-source/truck/interior/export` skopiowane z main; prefaby TRAKT/naczepy zbudowane
  (TruckAssetBuilder, TrailerAssetBuilder, build-lab) - efekty uboczne build-lab (DrivingLab.unity, graybox prefaby) cofac `git checkout`.
- [krok 0] Diagnoza: "szara tafla naczepy" w lusterku = CZOLO przedniego slupka naroznego naczepy (0,11 m, widziane na wprost obok
  naroznika kabiny), nie firanka (firanka to pasek 5-14 %). Rendery PRZED: `artifacts/mirrors-trailer-s24/r2/before/` (11 kamer + mirror_L/R).
- [krok 1] Blender: `trailer_build.py front_wall()` - slupek jako profil (kanal kedrowy, rowek boczny), stopa i odlew ocynk, sruby, nity;
  `build_interior.py build_dash_items()` - kartki z zalamaniami (wlasne kolumny wierzcholkow), nadruk w tincie, albedo 0,84 -> ~0,57 lin.
  Bake w tle: `artifacts/logs/bake-chain.status` (naczepa -> wnetrze -> odbicie szyby).
- NASTEPNY KROK: UI okienek lusterek (obudowa, ramiona, szklo szerokokatne, film) w `UI/Driving/MirrorGlassImage.cs`, potem
  render PO: TruckAssetBuilder + TrailerAssetBuilder + `pwsh scripts/build-lab.ps1 -SkipAudio -BuildTarget Win64` +
  `pwsh scripts/visual-qa.ps1 -Scene DrivingLab -Pc -Tier High -Width 1920 -Height 1080 -Lighting clear -BuildTarget Win64 -Cameras cab-driver,cab-hub,cab-dash,cab-mirrors-left,cab-mirrors-right,cab-view-b-fov70-hud -OutputDir artifacts/mirrors-trailer-s24/r2/after`.
