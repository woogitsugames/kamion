# STATUS agy-clouds-s24 (chmury: warianty, miękkie krawędzie i usunięcie „kropki” na niebie; dopisek ADR 0332)

- Worktree `agy-clouds-s24`, gałąź `agy-clouds-s24`. Nie scalać / nie pushować (lider).
- [krok 0–2] Baseline visual-qa + diagnoza i usunięcie ciemnego punktu `(1170, 142)`: plama owada `B=214` w `T_Windscreen_Grime.png` (`obj=(-0.314, 1.702)`), obecna w Clear (`+51,3 sRGB`) i Overcast (`+75,7 sRGB`). Naprawa w `tools/rendering/windscreen_grime.py` (`y > 1.45, |x| < 0.85`), pokrycie brudu `3,81 %` (pasmo 3–6 %). Po poprawce: Clear `+7,7` (faktura chmury), Overcast `+1,0`, 0 pikseli `B > 60` w strefie nieba.
- [krok 3–5] 3 miękkie warianty map chmur CC0 (Poly Haven 4K Pure Sky: `kloofendal_48d_partly_cloudy_puresky`, `sunflowers_puresky`, `kloofendal_38d_partly_cloudy_puresky`) z adaptacyjnym miękkim matte (gradient krawędzi `p90/p99`: `0,162/0,459 → 0,059/0,172` = 2,7× miękcej), deterministyczny wybór z ziarna/sceny/pory dnia + odbicie południkowe Householder (6 układów o spójnym słońcu), leniwe ładowanie 1 tekstury (+0 MB VRAM, +0 odczytów tekstur, ~6 ALU w `Sky.shader`), D100 (×2 błękit) i Overcast (`mean diff 0,00000`) zachowane.
- [krok 6–7] Walidacja:
  - EditMode Sky/Cloud/Windscreen (`-BuildTarget Win64`): **39 passed, 0 failed, 0 inconclusive, 1 skipped** (`artifacts/tests/editmode-20261127-102754.xml`).
  - Budżety GIS + CC0 (`test_budget_0221.py`, `test_typology_0238.py`, `test_world_v31.py`, `test_hero_bridge.py`, `test_cc0_scans.py`): **68 passed, 0 failed**.
  - Audyt licencji (`tools/licenses/audit.py`): **4410/4410 covered, 0 unverified, 0 suspicious**.
  - Dopisek 3 do ADR 0332 + wpisy CC0 w `docs/LICENSES.md` + dowody w `C:\Users\matma\Documents\Claude\kamion\artifacts\agy-clouds-s24\`.
- KONIEC zadania agenta.
- NASTĘPNY KROK (lider): review + scalenie `agy-clouds-s24`, opcjonalnie weryfikacja `pc-metrics` na buildzie Windows (czas GPU `UNVERIFIED` w playerze).
