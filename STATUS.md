# STATUS agy-signs-wear-s24 (znaki drogowe i słupki — zużycie i zróżnicowanie)

- Worktree `agy-signs-wear-s24`, gałąź `agy-signs-wear-s24`. Nie scalane ani nie pushowane.
- Środowisko: prywatna kopia `Data/raw/derived/dk65-07` (pozostałe kafle junction do main, bez zapisu do main), lokalny shim `artifacts/agy-signs-wear-s24/shim/uv.cmd` wskazujący na Pythona w `agent-a492e5af856a32ed3` z `PYTHONPATH` tego worktree, Win64 `game/Library`.
- [krok 1] Bazowy import `dk65-07` (High) + rendery PRZED (`before`, High PC 1920×1080, `clear` + `overcast`, `route-s0144`, `route-s0433`, `route-s0721`, `drive-kozince`, `rev-kozince`) zapisane w `artifacts/agy-signs-wear-s24/before/`.
  - Baseline `stats.txt` (`clear`/`overcast` identyczne):
    - `drive-kozince`: `drawsEst=232 trisExact=673307 | instanced: draws=173 instances=1755 trianglesExact=276020`
    - `rev-kozince`: `drawsEst=262 trisExact=686313 | instanced: draws=153 instances=489 trianglesExact=88695`
    - `route-s0144`: `drawsEst=295 trisExact=637775 | instanced: draws=137 instances=582 trianglesExact=48014`
    - `route-s0433`: `drawsEst=232 trisExact=673307 | instanced: draws=173 instances=1752 trianglesExact=282002`
    - `route-s0721`: `drawsEst=106 trisExact=408897 | instanced: draws=113 instances=1369 trianglesExact=80034`
- [krok 2] Warstwa Pythona (`tools/worldgen/streetscape/{props,materials,furniture,signs_route,built_up}.py`, `tests/gis/test_signs_wear_s24.py`):
  - `sign_post` LOD0 podniesiony z 10 do 12 boków (72 tris) pod profilowanie U-kanałowe w shaderze bez nowych prototypów i draw calli.
  - `sign_post_galv` z `"shader": "Kamion/Furniture Post"`.
  - Deterministyczne `sign_wear_params()` per znak: przechył słupka ±1,5° wokół podstawy (`tilt`, `pivot_dy`), wektor `wear` dla słupka (`finish` ocynk vs malowany szaro-biały, U-kanałowy `L`/`D`, wiek/korozja, wariant spangle/ziarno) oraz tarcz (`age` blaknięcie, `dirt` brud od dołu, `flags` rdza krawędziowa / pojedyncza naklejka, `seed`).
- [krok 3] Warstwa C# i shadery + testy Unity / Python:
  - `WorldInstanceSet.cs` (`instanceWear` Color32[]), `InstanceImporter.cs` (macierz przechyłu wokół podstawy `pivot_dy` + zapis `instanceWear`), `WorldInstances.cs` (per-instance `MaterialPropertyBlock` `_KamionSignWear` bez nowych draw calli).
  - `FurnitureSignForward.hlsl` (`ApplySignWear`: wyblaknięcie UV czerwieni→róż, kurz od dołu, rdza krawędziowa, pojedyncze wlepki, spadek retrorefleksji) oraz `FurniturePost.shader` (`Kamion/Furniture Post`: U-kanałowy profil 50×30 mm na 12-boku, ocynk zwietrzały vs malowany szaro-biały, korozja u podstawy).
  - Poprawka `built_up.py` / `limit_signs.py` (`net` opcjonalny w `_place`).
  - Testy: Unity `EditMode FurnitureSignTests` 16/16 passed, `PlayMode WorldInstancesRenderGcTests` 1/1 passed (zero GC); Python `test_signs_p1_0279` + `test_direction_signs_0236` + `test_signs_wear_s24` (46 passed, 1 skipped), `test_props_grounding_0337` + `test_furniture_signs_0120` + `test_furniture_r1` (37 passed), `test_hero_bridge` + `test_typology_0238` (34 passed).
- [krok 4] Poprawka GI/SH w `FurniturePost.shader` (`InitializeBakedGIData`, `EVALUATE_SH_*`), pełny import `dk65-07` High + `visual-qa` PO (`clear` i `overcast`, `1920×1080`) + arkusze SBS `≤960 px` w `artifacts/agy-signs-wear-s24/sbs/`.
  - `posts=24` (`painted=11`, `u_channel=3`, `tilted=24`), `plates=25`.
  - Testy Python (11 plików budżetowych i oznakowania): `167 passed, 1 skipped` w 96,47 s.
  - Dopisek dodany w `docs/adr/0337-props-grounded-benches-sign-posts.md`, raport w `artifacts/agy-signs-wear-s24/WYNIKI.md`, dowody skopiowane do `C:\Users\matma\Documents\Claude\kamion\artifacts\agy-signs-wear-s24\`.
- NASTĘPNY KROK (dla lidera): przejrzeć dowody w `artifacts/agy-signs-wear-s24/`, scalić `agy-signs-wear-s24` i przebudować kafle przy kolejnej fali regenu:
  `git log -n 4 --oneline agy-signs-wear-s24`
