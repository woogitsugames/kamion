# STATUS — M65 (cloud p22-red-bike-paths)

- [x] Overpass (maps.mail.ru) 2026-11-14T16:49Z, osm_base 2026-11-14T16:48:34Z → `overpass-result.json` (zapytanie: `overpass-query.ql`)
- [x] `tools/inventory.py` → `inventory.json` (C: 71 odcinków, Dojlidy: 22), `tools/crossings.py` → `crossings.json`
- [ ] kadry (P11-001, P11-056, Panoramax/KartaView/Commons) — pobrać, obejrzeć, opisać
- [ ] manifest.csv, README.md, sources.md, fetch.py, audit_20_percent.json, PR

NASTĘPNY KROK: wyszukać kadry: `curl 'https://api.panoramax.xyz/api/search?bbox=23.1437,53.1488,23.1760,53.1683&limit=500'` oraz Commons geosearch w obu kaflach; pobrać do files/.
