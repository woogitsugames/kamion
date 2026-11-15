# STATUS roundabout-0218 (C2, ADR 0218)
- krok 1-2: analiza generatora (network ISLAND/apron) + skrypt swept path `tools/worldgen/roads/swept_path.py`, tabela w `swept_path_table.txt`.
- krok 3-4: override `truck_apron` (network.py), testy `tests/gis/test_truck_apron_0218.py`, `test_swept_path_0218.py` (20 zielonych), przykład `tools/worldgen/roads/examples/knyszyn-roundabout-apron.yaml`; regresja side arrays 9 regionów identyczna.
- krok 5: ADR 0218 napisany.
- krok 6: pełne testy 1286 passed, 1 failed (fidelity_qa.json stale hash network.py - wymaga Data/raw, lider).
- NASTĘPNY KROK (lider): `uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c`, potem komendy z ADR 0218 §7.
