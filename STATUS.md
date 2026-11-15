# STATUS rail-dk65-0223 (ADR 0223, stacked na rail-0217 / PR #96)
- krok 1-3: OSM API 0.6 (17 kafli + way/full + relacja 2316318 ref=38) -> linia 38 tylko w dk65-01..04, dw671-tykocin-01 (+ bialystok-knyszynska, zakazany); rail_sources.json 5 kafli (manifest Data/SourceManifests/osm-api-0.6-rail-l38.json); rail.py: KEEP_TAGS, extract_osm_xml, crossing_equipment (kat. A-F, Dz.U. 2025 poz. 1105 § 6), overrides kind rail_crossing, G-2 (§ 81), markery poza kaflem; regions.py rail=True x5; pytest -k rail 46/46.
- NASTEPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis -k rail -q` po dopisaniu tests/gis/test_rail_dk65_0223.py
- krok 4: tests/gis/test_rail_dk65_0223.py (opt-in 5 kafli, provenance, dlugosci/przejazdy per kafel, tor vs jezdnia, szwy +-0,1 m, budzet, mapowanie A-F, override, G-2, markery poza kaflem, extract XML); pytest -k rail 83 passed.
- NASTEPNY KROK: ADR 0223 + LICENSES, potem `uv run --project tools/worldgen python -m pytest tests/gis -q`
- krok 5: ADR 0223 (tabela kafli, mapowanie A-F z Dz.U. 2025 poz. 1105, budzet ESTIMATED, kolejnosc scalania, komendy lidera) + LICENSES (osm-api-0.6-rail-l38).
- NASTEPNY KROK: wynik pelnego `uv run --project tools/worldgen python -m pytest tests/gis -q`, PR (baza rail-0217).
