# STATUS — R9 next-region-ring

## 2026-11-14 17:20 UTC — krok 1
- Worktree /workspace/wt/next-region-ring, gałąź research/cloud2-next-region-ring.
- Proponowany bbox (propozycja): EPSG:2180 764683,584959 → 787211,605439 (11×10 kafli 2048 m, 461,4 km²), siatka zgodna z istniejącymi regionami.
- Overpass: overpass-api.de niedostępny przez proxy (reset), działa mirror maps.mail.ru (504 losowo, retry). Węzły S8/S19 pobrane.
- GUGiK: skorowidze ORTO/NMT/NMPT 2018–2026 (27 zapytań, HTTP 200), pokrycie policzone (gugik/skorowidze_coverage.json); BDOT10k/LoD1/LoD2 GetFeatureInfo; PRG gminy.
- Uwaga: powiat białostocki = TERYT 2002 (nie 2010) — potwierdzone GetFeatureInfo.
- NASTĘPNY KROK: `python3 research/cloud2/next-region-ring/tools/ovp.py highways research/cloud2/next-region-ring/overpass/queries/highways.ql research/cloud2/next-region-ring/files/overpass_raw research/cloud2/next-region-ring/overpass/_log.jsonl` (i pozostałe .ql), potem analiza tagów.
