# STATUS — D32 typology-bitid-s23 (ADR 0238, dopisek D32 + r2)
- r1: dach domu odporny na szum float (`roofs.PLAN_TOL_M`), baseline przeliczony; CI na 813b8a923: Dojlidy zielone, C pada na `…B14F` (510 vs 524).
- r2: wersje pakietów identyczne (uv.lock); przyczyna to szum ULP w progach: B14F okap 130.65±ulp → okno poddasza (profil zaokrąglany do 1 µm), B45E pas < 1 mm obwiedni (przejmuje go sąsiednia połać, `SLIVER_M`). 61/61 domów stabilnych przy przesunięciach 1e-12…1e-6 m; C 0 zmian w całym regionie. Baseline przeliczony: C −1 804 / −1 087, Dojlidy −1 081 / −755; kamery Δ ≤ 0 (stretch_04 −1 071).
- pytest `-k "typology or 0238 or 0242 or dojlidy or building or roof or house or multi or facade or kamienica"` 241 passed, 5 skipped.
- NASTĘPNY KROK (lider): CI `gis` na PR #159; na Windows `uv run --project tools/worldgen python -m pytest tests/gis/test_typology_0238.py -q` (24 passed).
