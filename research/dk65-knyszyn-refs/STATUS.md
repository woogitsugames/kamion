# STATUS — K1 DK65 Białystok → Knyszyn (gałąź research/dk65-knyszyn-refs)

## 2026-11-15 — WIP 2 (wznowienie po resecie limitu)
- Dodane: `data/osm_corridor.json` (API 0.6 /map co 500 m, ±300 m: słupki DK65 km 161→143, przystanki, linia kolejowa 38,
  przejazdy na drogach bocznych, 0 latarni `highway=street_lamp`), narzędzia `osm_corridor.py`, `raildist.py`, `sheets_fix.py`.
- Ustalone: S19 Krynice–Dobrzyniewo–Białystok Zachód oddany 20.10.2026 (źródło prasowe); komunikat GDDKiA 14.10.2025 (objazd
  wiaduktu w Fastach zlikwidowany); MI 10.12.2024: rondo DK65×DW671 w Knyszynie (ZRID złożony VII 2024); ortofoto 2025-05-27 = skrzyżowanie skanalizowane.
- Następny krok: szpalery drzew (orto 200 m), manifest.csv, README, sources.md, audyt 20 %, PR.

## 2026-11-15 ~10:30 UTC — WIP 1
- Zrobione: próbkowanie trasy wariantu A co 1 km (km 8,8–28,0 + punkty pośrednie, `data/km_points.json`),
  wycinki ortofoto GUGiK WMS HighResolution (najnowszy arkusz 2025-05-25/27, 0,1 m) dla 30 punktów + 10 skrzyżowań/Rynek
  (`files/orto/`), profile poprzeczne (`data/analysis.json`), tagi OSM 41 odcinków trasy (`data/osm_route_ways.json`),
  geometria rond z OSM, wyszukiwania Panoramax/Commons/Openverse/KartaView (`data/query_log.json`),
  42 zdjęcia Commons pobrane (≤1600 px) i obejrzane (miniatury 2×2), dokument MI 10.12.2024 (interpelacja 5277).
- Następny krok: manifest.csv + README + sources.md + audyt 20 %.
  Komenda: `cd /tmp/claude-0/-workspace-kamion/f4a38e02-1bbc-5042-8a92-a3868938a174/scratchpad/k1 && .venv/bin/python -I tools/build_manifest.py`
