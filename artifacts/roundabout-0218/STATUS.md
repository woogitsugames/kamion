# STATUS roundabout-0218 (C2, ADR 0218)
- krok 1-2: analiza generatora (network ISLAND/apron) + skrypt swept path `tools/worldgen/roads/swept_path.py`, tabela w `swept_path_table.txt`.
- krok 3-4: override `truck_apron` (network.py), testy `tests/gis/test_truck_apron_0218.py`, `test_swept_path_0218.py` (20 zielonych), przykład `tools/worldgen/roads/examples/knyszyn-roundabout-apron.yaml`; regresja side arrays 9 regionów identyczna.
- krok 5: ADR 0218 napisany.
- NASTĘPNY KROK: wynik pełnych testów + PR: `uv run --project tools/worldgen python -m pytest tests/gis -q`
