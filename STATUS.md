# STATUS plaza-barn-fix-s24 (krytyk s24 dzień 27: skrzynie/kwiaty/cokół/ławki rynku Tykocina + wrota stodół) — KONIEC

- Worktree `agent-a8bad7a40407c997e`, gałąź `worktree-agent-a8bad7a40407c997e` (nie scalać — lider). `Data/raw/derived` = PRYWATNA
  kopia (`tykocin`, `dk65-07`, `cache`; NIE kopiować do main — wspólny derived przebuduje lider po scaleniu), reszta = junction.
- [krok 1] Setup + build „przed” (HEAD 0e9424aaa). [krok 2] Kod + Blender + testy. [krok 3] Unity przed/po (High, clear, Win64):
  `artifacts/plaza-barn-fix-s24/vqa-{before,after}/{tykocin,dk65-07}/`, arkusze `sbs/`.
- Wyniki: DC +0 we wszystkich kadrach; tykocin +232 trójkątów (Rynek LOD0 35 678 ≤ 36 000); dk65-07 +0.
- Testy: test_truss_bridge_0320 (12), test_rural_outbuildings_props_fix_s24 (+1 r3), test_typology_0238, test_budget_0221 — zielone.
- Dopiski ADR 0320 i 0238.
- NASTĘPNY KROK (lider): `visual-critic` na `artifacts/plaza-barn-fix-s24/sbs/*.jpg`; po scaleniu
  `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region tykocin` (+ dk65-07, knyszyn-w i inne kafle z
  `rural_outbuildings: true`) → `pwsh scripts/import-region.ps1 -Region <id> -BuildTarget Win64 -MaterialTier High`.
