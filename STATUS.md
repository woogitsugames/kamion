# STATUS dojlidy-0242 (F9 Dojlidy — rozpoznawalność)
- [15.11] Krok 1: wysokości brył z GUGiK NMPT 0,5 m (WCS) zamiast ze zdjęć: Rosti 18,92 (LoD1 potwierdzone, 16,9 wycofane), skrzydło 13,2,
  K3 15,4, Kuronia 2: hala 11,9 (okap), front 9,35/9,9, przybudówka 5,35. K3 → okładzina kasetowa, zacieki ×0,25, drzwi/bramy hal na gruncie,
  bramy Rosti 5,9×6,6. Skrypt `tools/worldgen/qa/dsm_roof_levels.py`. C#: `runoff_strength` (nieskompilowane w chmurze).
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis -k "dojl or 0185 or 0196 or 0183 or 0242" -q` (2 stare testy do aktualizacji), potem ADR 0242 + PR.
