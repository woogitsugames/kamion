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
- NASTĘPNY KROK: implementacja w C# (`WorldInstanceSet.cs`, `InstanceImporter.cs`, `WorldInstances.cs`) oraz shaderach (`FurnitureSignForward.hlsl`, `FurniturePost.shader`), potem testy Unity (`FurnitureSignTests`, `WorldInstancesRenderGcTests`) i przebudowa `dk65-07`:
  `pwsh scripts/test.ps1 -Platform EditMode -Filter FurnitureSignTests -BuildTarget Win64`
