# STATUS kerbs-0237 (F4, ADR 0237)
- Zrobione: `streetscape/pavements.py` (reguła typów chodnika, obniżenia krawężników na przejściach przez plan_plots → apply_drops, retype eksportowy), materiały `sidewalk_slabs` / `sidewalk_paving_red` / `cycle_red` z zestawem `paving_20x10_tint`, behaton przeskalowany per oś (pomiar skanu 275 × 160 mm → 201 × 144,5 mm), GULLY_SIZE 0,42 × 0,62, overrides C i Dojlidy, C# `BlockPavingElementSize` + test EditMode (nieskompilowane w chmurze).
- Testy: `tests/gis/test_pavements_0237.py` 21/21.
- Otwarte: hak retype w `roads/build_world.py` NIE nałożony (plik w budget-fix-s21) — łatka `docs/adr/0237-build-world-hook.patch`.
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis -k "pavements or cycleways or fab_details or buildings_r7 or yard_wear or cc0" -q`
- [krok 3] ADR 0237 + łatka haka (`git apply --check` OK na main i budget-fix-s21), poprawki testów fab_details / yard_wear pod nowe parametry, `paving_20x10_tint` średnia 0,4994. Wybrane pytest gis: 144 pass, 1 fail znany (test_world_v31 frame budget).
- NASTĘPNY KROK (lider): `git apply docs/adr/0237-build-world-hook.patch` po scaleniu 0221, potem przebudowa C i Dojlid (komendy w opisie PR).
