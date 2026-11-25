# STATUS neon-farfield2-s24 (dopisek do ADR 0330 — runda 2: las w dali bez stożków, podszyt/skraj, ostrość atlasu 1:1, impostory 300–1500 m)

- **krok 1 (diagnoza + Python):** `far_field.py`, `forest_hlod.py`, `test_far_field.py` (commit `59f26236a`). Dry-run: max `h` `knyszyn-w` `38,9 → 24,5 m`, `dk65-05` `43,0 → 28,7 m`, stromość koron `|dz/ds|` max `1,615 → 0,359`, impostory brzegowe High: `knyszyn-w` 828 szt., `dk65-05` 1 285 szt., podsiatki `≤ 2 / sektor`, Low tris: `knyszyn-w` 4 816, `dk65-05` 7 085, C 7 269.
- **krok 2 (baseline przed + Unity/shader + atlas 1024×4096):**
  - Import Win64 High + visual-qa **przed** (`1600×900`, PC High, clear + overcast) dla `knyszyn-w` i `dk65-05` → `artifacts/neon-farfield2-s24/before/` (`BEFORE_QA_ALL_OK`).
  - `InstanceImporter.cs`: `anisoLevel = 8`, `KaiserFilter` mips dla `forest_edge*`, `maxTextureSize = 4096` na PC dla `forest_edge_mixed_far_atlas` (Android bez zmian).
  - `Vegetation.shader`: niezależna normalizacja `T` i `B` w `_HLOD_EDGE` (koniec spłaszczania normalnych pionowych przez stos 11 slotów atlasu).
  - Wygenerowano nowy atlas `art-source/world/vegetation/forest_edge_mixed_far_atlas.png` (`1024×4096`, `pad=8`, 9 pasm kurtyn + 2 wiersze 8 pojedynczych drzew z `impostor_tree_*.png` — sprawdzone wzrokowo).
- **krok 3 (przebudowa prototypów w derived):**
  - `build_world.py --region knyszyn-w --context`: `far_field` High `93 052 → 100 267`, Low `12 359 → 11 830` (podsiatki `2/sektor`).
  - `build_world.py --region dk65-05 --context`: `far_field` High `111 935 → 123 694`, Low `15 120 → 14 585` (podsiatki `2/sektor`).
  - `far_field.py --region bialystok-industrial-c`: High `169 318 → 182 126`, Low `29 161 → 29 139` (`≤ 30 000`, `test_far_field.py` 19/19 zielone).
- **NASTĘPNY KROK:** zająć slot `unity` → `import-region.ps1 -Region knyszyn-w -Tiers High -BuildTarget Win64`, `visual-qa` High clear+overcast `after`, to samo `dk65-05`, `make_sheets.py`, oględziny PNG + crop 1:1.
