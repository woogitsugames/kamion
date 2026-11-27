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
- [krok 4] 27.11: `build_world --region tykocin` DZIAŁA mimo Smart App Control (exit 0, 630 s; blokada dotyczy tylko DLL rasterio, której ten
  przebieg nie ładuje — niczego nie obchodzono). Przed: `vqa-before/` (import stanu main). Po r1: `vqa-after1/`, r2: `vqa-r2/` (ciemniejsze drewno,
  mniejsze tablice, jaśniejszy kamień), r3: `vqa-after/` (ciemniejsze futro, kwiaty jako kępki). Arkusze `sbs/`, podglądy `view/`.
  Ustalenie: stary posąg stał TYŁEM do DW671 (kadr `czarniecki_figure_0320b` przed) — nowy asset stoi frontem na południe.
- [krok 5] Dopisek ADR 0320 + LICENSES. Jeden skrypt całego łańcucha: `pwsh artifacts/tykocin-plaza-s24/rebuild.ps1 -Out artifacts/tykocin-plaza-s24/vqa-after`
  (Blender → pytest → build_world w PRYWATNYM derived → import Win64 → VQA; odmawia pracy, gdy `Data/raw/derived` jest junctionem).
- NASTĘPNY KROK (lider): ocena `visual-critic` arkuszy `artifacts/tykocin-plaza-s24/sbs/*.jpg`; po scaleniu w main:
  `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region tykocin` → `pwsh scripts/import-region.ps1 -Region tykocin -BuildTarget Win64 -MaterialTier High`
  (build_all sam dobuduje zestaw `sandstone_weathered_tint`; asset npz jest w gicie, Blender niepotrzebny).
