# c-regress-cli

2026-11-21: baza 83345868e (origin/main, wyłącznie dokumentacja ponad e16a5e240).
Log wejściowy: 28 failed, 2779 passed, 4 skipped, 2 xfailed (3398 s).
Wejścia raw przez dowiązania; derived C to prywatna kopia, bez zapisów do wyników main. Bez Unity.
Krok 1: rozdzielono licznik starych instancji ogrodowych od koron ADR0308;
fixture world jawnie buduje D94; bridge_clearance weryfikuje aktualną jezdnię zamiast pozornej rekonstrukcji starej kolizji.
NASTĘPNY KROK: `uv run --project tools/worldgen pytest tests/gis/test_bridge_clearance.py -q` (slot heavy).
