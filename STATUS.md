# STATUS — D26 worldgen-perf2-0281 (ADR 0281)

- Wdrożone bez zmiany bajtów: K1a, K1b, K1c, K2, K4a, K4b, K5 (+ `tools/worldgen/tests/test_perf_0281.py`, 11 testów).
- Bieg C (`--nmt flat`): 319/319 plików wyjścia identyczne (sha256) base1 vs after1; 934,8 → 778,3 s (base1 zakłócony). Trwają powtórzenia base2/after2.
- Pominięte (uzasadnienie w ADR): K1d, K1e (jedno pipeline.build), K2b, K3.
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tools/worldgen/tests/test_perf_0281.py -q` + uzupełnić tabelę czasu w ADR 0281 z `runs/*/stages.json`.
