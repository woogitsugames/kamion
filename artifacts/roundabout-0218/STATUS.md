# STATUS roundabout-0218 (C2, ADR 0218)
- krok 1-2: analiza generatora (network ISLAND/apron) + skrypt swept path `tools/worldgen/roads/swept_path.py`, tabela w `swept_path_table.txt`.
- krok 3-4: override `truck_apron` (network.py), testy `tests/gis/test_truck_apron_0218.py`, `test_swept_path_0218.py` (20 zielonych), przykład `tools/worldgen/roads/examples/knyszyn-roundabout-apron.yaml`; regresja side arrays 9 regionów identyczna.
- krok 5: ADR 0218 napisany.
- krok 6: pełne testy 1286 passed, 1 failed (fidelity_qa.json stale hash network.py - wymaga Data/raw, lider).
- NASTĘPNY KROK (lider): `uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c`, potem komendy z ADR 0218 §7.
- FIX s22 (D7): `truck_apron` = jedyny mechanizm pasa przy wyspie (wspólny z #93/ADR 0226: `{width_m}` = samo położenie krawężnika; zakres 0,2–6,0 m), kod 8 `kostka_jasna` → `sidewalk_paving`; przykład Knyszyn `material: kostka_jasna` (opis zdjęć właściciela); ADR 0218 §5a/§6. Testy `-k "putry or 0226 or 0198 or roundabout or 0218 or apron"` — wynik w komentarzu PR.
- NASTĘPNY KROK (lider): scalić #93, potem #97; `uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c`; komendy z ADR 0218 §7.
