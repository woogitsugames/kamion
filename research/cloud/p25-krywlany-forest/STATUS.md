# STATUS — M68 (cloud p25-krywlany-forest)

- [x] 2026-11-14 16:47 UTC — OSM (Overpass mirror mail.ru) lasy/zarośla/drogi/lotnisko: 130 lasów+zarośli, zapytanie `tools/osm_query.overpassql`.
- [x] BDOT10k PTLZ (paczka powiatowa 2061 GML, opendata.geoportal.gov.pl) — 718 obiektów, 197 w oknie.
- [x] BDL: 141 wydzieleń Nadl. Dojlidy, leśn. Solnicki Las (OGC API + opis taksacyjny) → `data/bdl_wydzielenia.csv`.
- [ ] NMPT−NMT (WCS GUGiK, kafle 250 m, 1 m) — pobieranie w toku (92 kafle).
- [ ] Kadry: Commons chwilowo HTTP 429; Panoramax 0 kadrów w oknie Krywlan (są na N od miasta); KartaView 0 w promieniu 500 m.

NASTĘPNY KROK: dokończyć pobieranie DEM (`tools/dem_fetch.py`), policzyć CHM (`tools/chm_edges.py`), zebrać kadry Commons, manifest.
- [x] 17:45 UTC — BDL poza LP (gminne/prywatne; ArcGIS REST WMS_BDL_kat_wlasnosci) 175 wydz. → `data/bdl_poza_lp.csv`.
- [x] NMPT−NMT: 715 stacji profili (Mickiewicza 355, Ciołkowskiego 238, lotnisko 108, Dywizjonu 303 14) → `data/chm_edges.csv`, `chm_stations.csv`, `chm_profile_mean.json`; WCS = lot 2025-04-18 (bezlistny), arkusze ASC = 2023-09-15 (ulistniony).
- [ ] Kadry: Panoramax 13 obejrzanych (DK19 Puszcza Knyszyńska); Commons: oryginały HTTP 429 (retry-after 600) → miniatury 1280 px, 23/42 pobrane i oglądane.

NASTĘPNY KROK: dokończyć oglądanie miniatur Commons (scratch `cthumb.py`), zbudować manifest (`tools/build_manifest.py`), fetch.py, audyt, README, PR.
