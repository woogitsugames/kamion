# STATUS mirror-housing-s24 (krytyk build #10 pkt 8: obudowa lusterek 3D w okienkach, przod naczepy w lusterku, papiery na desce, kafel POSTOJOWY)

- Worktree `agent-a4a29737953b3f1da`, galaz `worktree-agent-a4a29737953b3f1da`. Nie scalac (lider). KONIEC zadania agenta.
- Srodowisko: Library + `_Generated` + `art-source/truck/interior/export` skopiowane z main; Blender = `C:\Program Files\Blender Foundation\Blender 4.2\blender.exe`
  (sciezka z AGENT-RULES p. 8 nie istnieje na tym PC). Efekty uboczne build-lab (DrivingLab.unity, graybox prefaby) cofniete `git checkout`.
- [krok 0] Diagnoza: "szara tafla naczepy" w lusterku = czolo przedniego slupka naroznego naczepy, nie firanka.
- [krok 1] Blender: slupek przedni jako profil (kanal, rowek, stopa, odlew, sruby, nity) - naczepa LOD0 88 999 / 90 000, check PASS;
  kartki z zalamaniami + nadruk w tincie + albedo 0,84 -> ~0,57 lin. - kabina LOD0 106 130 -> 107 305 / 120 000, CHECK PASS, SIGHTLINE PASS;
  `a6_export.py --keep-plastic-maps` (SAC blokuje python venv kroku plastic_grain).
- [krok 2] HUD: okienko lusterka jako glowica (obudowa 9-slice, 2 ramiona, szklo kl. IV z zywa tekstura, film z welonem kontrastu),
  `RenderTextureMirror.ForceWide`, kafel ostrzezen jako lampka. drawsEst kamer bez zmian (cab-driver 236 | 236).
- [krok 3] Testy: EditMode 1481/0/123, PlayMode HUD (5 klas) 56/0. Dopiski ADR 0340, 0343, 0344.
  Dowody: `artifacts/mirrors-trailer-s24/r2/` (kopia w main `artifacts/mirrors-trailer-s24/r2/`).
- NASTEPNY KROK (lider): `visual-critic` na `artifacts/mirrors-trailer-s24/r2/cmp_*.jpg`; po scaleniu w win-build:
  `blender -b --factory-startup --python tools/blender/truck/interior/a6_export.py -- --lods 0 --keep-leather-maps --keep-plastic-maps`
  (LOD0 fbx poza gitem), TruckAssetBuilder + TrailerAssetBuilder, potem pomiar
  `pwsh scripts/pc-metrics.ps1 -Exe <build>/Kamion.exe -Scene knyszyn-w -Tier High -Fps 60 -Width 1920 -Height 1080 -DurationSeconds 90 -Class zalecany`.
