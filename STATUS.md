# STATUS lights-79-s24 (PR #79, ADR 0197)

- 2026-11-18: worktree z origin/lights-0197 (ad93ea1ff), `git merge origin/main` (60ca658e8) bez konfliktów
  (merge 88c45970a); brand sweep: brak markowych nazw w diffie; nazwy komór naczepy `rear_lens_*_tail_/_stop_` z trailer_build.
- NASTĘPNY KROK: `dotnet test tools/lamp-check` + `blender -b -P tools/blender/truck/trailer/trailer_export.py -- --no-renders`
- Eksport naczepy `trailer_export.py -- --no-renders` 856 s, `check_export.py` PASS; manifest: 16 TAIL / 17 STOP. `dotnet test tools/lamp-check` 186/186. LOD0 kabiny z `cab-lod0.ps1 -Build` (poza gitem).
- NASTĘPNY KROK: `pwsh artifacts/lights-79-s24/unity.ps1` (BuildBatch ciągnik+naczepa, EditMode Win64)
- Unity Win64: TruckAssetBuilder/TrailerAssetBuilder BuildBatch OK; EditMode 1383/1283 pass/6 fail: 2x CarPaint DepositionChannel + LightPostPolicy glass (środowiskowe, dane _Generated), 3x TruckLampLensTests trailer (oczekiwał TAIL_BRAKE) -> test poprawiony na TAIL+STOP.
- NASTĘPNY KROK: `pwsh artifacts/lights-79-s24/chain2.ps1` (testy lamp + rendery night/dusk High/Low)
- Noc: stop był różowy (148,67,67) przez ADR 0108 dim-colour desaturację w `KamionTone`; poprawka `KamionToneScaled` (TruckExterior skaluje przez 1 − udział emisji). Po poprawce noc High/Low: stop 188–193,13–18 sRGB, pozycyjne 53–55; stosunek ekranowy ciągnik 12,0/13,6, naczepa STOP:TAIL 11,7–13,7. Kierunkowskazy 188,98,22. EditMode Win64 1286/1383 (3 środowiskowe).
- ADR 0197 Accepted + wiersz w indeksie. Dowody: `artifacts/lights-79-s24/` (kopia w main). Wypchnięte na `lights-0197` (PR #79).
- NASTĘPNY KROK (lider): visual-critic na `artifacts/lights-79-s24/view/cmp2-*.jpg`; scal PR #79; po scaleniu w main `TruckAssetBuilder.BuildBatch` + `TrailerAssetBuilder.BuildBatch`.
