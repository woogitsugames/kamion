# STATUS tykocin-plaza-s24 (CRITIC s24 fala 11 pkt 10: posąg niskopoligonowy, ławki identyczne i równo)

- Worktree `agent-a76ed41d86bc4e5a3`, gałąź `worktree-agent-a76ed41d86bc4e5a3`. `Data/raw/derived` = PRYWATNA kopia (tylko `tykocin` + `cache`),
  reszta `Data/raw/*` = junction do main; Library / `_Generated/World/tykocin` / zestawy tekstur skopiowane z worktree `win-build` (Win64).
  Blender na tym PC: `C:\Program Files\Blender Foundation\Blender 4.2\blender.exe` (4.2.16; ścieżka z AGENT-RULES pkt 8 nie istnieje).
- [krok 1] Rozpoznanie: pomnik Czarnieckiego to PIASKOWIEC (1762), nie brąz — „patyna brązu” z zadania nie dotyczy kamienia; zrobione
  zwietrzenie kamienia (skorupa, zacieki, porosty) + zielony karwasz i złocona buława jak na zdjęciach Commons. Kamery QA `*_0320b` dodane.
- [krok 2] Asset `art-source/world/landmarks/tykocin_czarniecki` (generator `tools/blender/world/landmarks/make_czarniecki.py`, 3 rundy look-dev
  `artifacts/tykocin-plaza-s24/lookdev/r1..r3`): LOD0 26,5 k / LOD1 1,9 k trójkątów, wietrzenie w COLOR_0 (`facade_tint`), zestaw `sandstone_weathered_tint`.
- [krok 3] `tykocin_rynek_0320.py`: asset + ogrodzenie z grotami, tablice, słupki z łańcuchem, 12 donic, 6 ławek w 3 wariantach (obrót 2–9°, zużycie desek).
  Rynek razem LOD0 33,9 k / LOD1 3,2 k. `pytest tests/gis/test_truss_bridge_0320.py`: 10 passed.
- NASTĘPNY KROK: `pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner tykocin-plaza-s24; uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region tykocin; pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner tykocin-plaza-s24`
  potem `pwsh artifacts/tykocin-plaza-s24/run-unity.ps1 -Region tykocin -Out artifacts/tykocin-plaza-s24/vqa-after -Cameras "<lista z run>"`.
