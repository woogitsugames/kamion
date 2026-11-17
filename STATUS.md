# STATUS trailer-rims-s23 (P1 recenzji s23: czerwone felgi naczepy, atlas Metal)
Gałąź `trailer-rims-s23` z origin/main 0fd0e048a; worktree ze standardowymi junctionami.
- krok 1: audyt `tools/blender/truck/trailer/uv_wheel_audit.py` na eksporcie z main: Metal - koła 42 953 teks. @1024, wspólne z CHASSIS 30 024, czerwone (R-G>0,2) 2 358. Przyczyna (UVREPORT `--uv-only`): wheel_1L_rim i wheel_1L_tyre (zachowane UV lathe, cylindrical_atlas) nie są UV-zaznaczone -> pack_islands ich nie przesuwa -> leżą w (0,0) pod wyspami podwozia. Zapas (spare_*) ma własne wyspy (overlap 0) - teza recenzji o wspólnym UV z 1L niepotwierdzona.
- krok 2 (w toku): fix = zaznaczenie pętli UV przed pack_islands + strażnik (raise przy overlap kół/statyki). Problem: po fixie gęstość Metal 308 -> 151 px/m, Curtain 361 -> 296 (bada się dlaczego, uvdbg0/uvdbg1).
- NASTĘPNY KROK: porównaj artifacts/trailer-rims-s23/uvdbg0|1/uv_*.png, potem pełny eksport odłączony.
