# STATUS dojlidy-0242 (F9 Dojlidy — rozpoznawalność)
- [15.11] Wysokości brył z GUGiK NMPT 0,5 m (WCS): hala północna 18,92 (LoD1 potwierdzone, 16,9 wycofane), skrzydło 13,2, K3 15,4,
  Kuronia 2: hala 11,9 (okap), front 9,35/9,9, przybudówka 5,35. K3 → okładzina kasetowa; zacieki ×0,25; drzwi/bramy hal na gruncie
  (opt-in); bramy 5,9×6,6; rama bloków K2 jaśniejsza od hali. C#: `runoff_strength` (nieskompilowane w chmurze).
- Testy: pytest `-k "dojl or 0185 or 0196 or 0183 or 0186 or 0179 or 0202 or 0242"` 65 pass / 1 skip / 1 xfail. Różnicowo: budynki C i knyszyn
  identyczne (SHA-256), Dojlidy LOD0 −738 tris, LOD1 −144, materiały ±0.
- ADR `docs/adr/0242-dojlidy-rozpoznawalnosc-wysokosci-z-nmpt.md`.
- NASTĘPNY KROK (lider): `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy` →
  `pwsh scripts/import-region.ps1 -Region bialystok-dojlidy -Build` → `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -OutputDir artifacts/dojlidy-0242/Low`
