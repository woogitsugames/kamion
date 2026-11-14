# STATUS — M68 (cloud p25-krywlany-forest)

- [x] 2026-11-14 16:47 UTC — OSM (Overpass mirror mail.ru) lasy/zarośla/drogi/lotnisko: 130 lasów+zarośli, zapytanie `tools/osm_query.overpassql`.
- [x] BDOT10k PTLZ (paczka powiatowa 2061 GML, opendata.geoportal.gov.pl) — 718 obiektów, 197 w oknie.
- [x] BDL: 141 wydzieleń Nadl. Dojlidy, leśn. Solnicki Las (OGC API + opis taksacyjny) → `data/bdl_wydzielenia.csv`.
- [ ] NMPT−NMT (WCS GUGiK, kafle 250 m, 1 m) — pobieranie w toku (92 kafle).
- [ ] Kadry: Commons chwilowo HTTP 429; Panoramax 0 kadrów w oknie Krywlan (są na N od miasta); KartaView 0 w promieniu 500 m.

NASTĘPNY KROK: dokończyć pobieranie DEM (`tools/dem_fetch.py`), policzyć CHM (`tools/chm_edges.py`), zebrać kadry Commons, manifest.
