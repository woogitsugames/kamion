# STATUS neon-outbuildings2-s24 (budynki gospodarcze r2: brama, rynny, blacha z żebrami, cokół i zacieki; dopisek ADR 0238 d. props-fix)

- Worktree `neon-outbuildings2-s24`, gałąź `neon-outbuildings2-s24`. Nie scalane ani nie pushowane (do przeglądu lidera).
- Środowisko: prywatne kopie `Data/raw/derived/{dk65-07,knyszyn-w}` (bez zapisu do main), Win64 `game/Library` + `_Generated` lokalnie.
- [krok 1] Rendery PRZED (`before`, Win64 High PC 1920×1080, clear + overcast): `dk65-07` (`drive-kozince`, `route-s0144`, `route-s0433`) i `knyszyn-w` (`dk65-goniadzka`).
- [krok 2] Implementacja (+0 materiałów, DC ≤ +0):
  - `tools/worldgen/streetscape/buildings_mesh.py`: (1) wrota stodoły z pionowych desek (`facade_atlas` wycinek `balf(2/5)`) + 16 tr. nadproża/ościeżnicy/4 zawiasów pasowych w `facade_atlas`, wiejskie `garage(0/1/5)` bez graffiti, także na długiej ścianie okapowej od drogi (`barn_edges`); (2) rynny L (4 tr./okap) i rury spustowe V (4 tr./rura) LOD0-only w `facade_atlas`; (3) `roof_weather` COLOR_0 na spadzistych dachach `rural_outbuildings`; (4) cokół 0,45–0,65 m (slope-safe) i ciemniejszy (`pl 0,38..0,54`) + zacieki pod okapem (`lod0_ro` → `_RUNOFF`).
  - `game/Assets/_Project/World/Import/WorldPbrMaterials.cs` + `game/Assets/_Project/Environment/Shaders/WorldPBR.shader`: `_RoofWeather.w = 1` dla `roof_metal_*` / `roof_sheet_*` → żebra trapezowe T-18 / faliste w kierunku spadku (`tn.x` + antyaliasing `fwidth`), cieniowanie korytek, zakładki arkuszy co 1,05 m i subtelne przebarwienia/nalot rdzy.
  - `tests/gis/test_rural_outbuildings_props_fix_s24.py`: +2 testy (wrota/rynny/COLOR_0/cokół/runoff + budżet ≤ +5 % `dk65-07`).
- [krok 3] `build_world.py --context` (`dk65-07` 521,6 s, `knyszyn-w` 431,3 s):
  - `dk65-07` `world_manifest.json`: `buildings` LOD0 104 376 → 107 204 (**+2 828 = +2,71 %** ≤ +5 %), `buildings_lod1` +0, 0 nowych materiałów (−1 w `7_1`).
  - `knyszyn-w` `world_manifest.json`: `buildings` LOD0 140 061 → 142 241 (**+2 180 = +1,56 %**), `buildings_lod1` +0, 0 nowych materiałów (−1 w `0_6`, `2_4`, `3_2`).
- [krok 4] Import Win64 (`IMPORT_RESULT: OK` oba regiony) + visual-QA PO (`after`, High PC 1920×1080 clear + overcast) + inspekcja PNG i cropów 1:1:
  - `drive-kozince`: `drawsEst` 459 → 458 (−1), `trisExact` 1 160 324 → 1 160 644 (+320).
  - `route-s0144`: `drawsEst` 504 → 503 (−1), `trisExact` 993 132 → 993 198 (+66).
  - `route-s0433`: `drawsEst` 457 → 456 (−1), `trisExact` 1 166 669 → 1 166 989 (+320).
  - `dk65-goniadzka`: `drawsEst` 328 → 328 (+0), `trisExact` 1 098 119 → 1 098 711 (+592).
- [krok 5] Dopisek ADR 0238, kopia dowodów do `C:\Users\matma\Documents\Claude\kamion\artifacts\neon-outbuildings2-s24\`, pełny pytest (84/84 zielone), commit końcowy.
- NASTĘPNY KROK (dla lidera): obejrzeć cropy w `artifacts/neon-outbuildings2-s24/sbs/`, scalić gałąź `neon-outbuildings2-s24` do `main`, a potem przebudować i zaimportować pozostałe kafle z `rural_outbuildings: true`: `pwsh scripts/import-region.ps1 -Region dk65-07 -Build -BuildTarget Win64` (oraz pozostałe kafle wg `artifacts/props-fix-s24/outbuildings-per-tile.txt`).

## codex-patches-edges-s24

- [krok 1] Przeczytane zasady i ADR-y. Zastąpiono junction prywatną kopią derived `knyszyn-w`; SHA pierwszej bryły zgodny z manifestem, Python 3.12.16 dostępny. Kamery i shim zapisane w lokalnych artefaktach.
- Następny krok: `pwsh artifacts/codex-patches-edges-s24/qa.ps1 -Stage before`.

- [krok 2] Zjazdy: istniejące pasy asfaltu i żwiru tworzą profil rampy w siatce renderu i kolizji; zjazd w mieście obniżono do 2 cm. Test zjazdów po skorygowaniu wartości bazowego spadku: 7/7. Import bazowy trwa i generuje lokalne mapy PBR.
- Następny krok: skończyć `pwsh artifacts/codex-patches-edges-s24/qa.ps1 -Stage before`, zapisać obraz przed, wdrożyć maskę łaty.
