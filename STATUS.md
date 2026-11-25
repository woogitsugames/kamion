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
- **krok 4 (visual-qa po + polerka podszytu/impostorów + ADR 0330 r2):**
  - Import Win64 High + visual-qa **po** (`1600×900`, PC High, clear + overcast) dla `knyszyn-w` i `dk65-05`, druga iteracja polerki (chłodne zamglenie impostorów `k=0,16 / vis=0,68`, gęstszy podszyt/krzewy przy podstawie i narożnikach, smoothstep końców `0,52`), reimport + ponowny render + oględziny wszystkich 6 arkuszy (`sbs-*`, `crop-1to1-*`).
  - Finalne liczby `far_field`: `knyszyn-w` High `93 052 → 104 569`, Low `12 359 → 11 830`; `dk65-05` High `111 935 → 130 148`, Low `15 120 → 14 585`; C High `169 318 → 188 322`, Low `29 161 → 29 139` (`≤ 30 000`); podsiatki `2/sektor`, **Δ `drawsEst` = 0** na wszystkich kamerach.
  - Dowody skopiowane do `C:\Users\matma\Documents\Claude\kamion\artifacts\neon-farfield2-s24\sheets\`.
  - Dopisek rundy 2 dodany do `docs/adr/0330-brzeg-ciagly-row-jeden-most-tykocin-dal-lasu.md`.
- **NASTĘPNY KROK (dla lidera po scaleniu):** przebudować `far_field` dla pozostałych kafli (`uv run --project tools/worldgen tools/worldgen/streetscape/far_field.py --region <id>` — wymagane ze względu na 11-slotowy atlas `1024×4096`) i reimportować.
