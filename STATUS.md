# STATUS — D26 worldgen-perf2-0281 (ADR 0281) — GOTOWE, PR otwarty

- Wdrożone bez zmiany bajtów: K1a, K1b, K1c, K2, K3a, K4a, K4b, K5 + `tools/worldgen/tests/test_perf_0281.py` (11 passed).
- C (`--nmt flat`, 8 biegów): 319/319 plików wyjścia identyczne (sha256) main ×3 / A ×3 / B ×2; build 934,8 → 655,6 s (mediana, −29,9 %).
- Pominięte (uzasadnienie w ADR 0281): K1d, K1e (jedno pipeline.build), K2b, K3b (zmieniają bajty / niedowodliwe).
- NASTĘPNY KROK (lider): `uv run --project tools/worldgen python -m pytest tools/worldgen/tests/test_perf_0281.py -q`, potem world3 jak zwykle (wynik ma być identyczny).
