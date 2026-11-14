# knyszyn-0204 (ADR 0204) — live
- 11-14: worktree, przeczytane ADR 0203 (plan kafli). Decyzja: kafle siatki `knyszyn` (-8,8) 760587,611583–762635,613631 (miasto, Rynek, rondo DK65/DW671) i `knyszyn-s` (-8,7) 760587,609535–762635,611583 (wlot DK65, rondo w budowie 762502,609913). Kolejność: knyszyn → knyszyn-s → ewent. (-9,8).
- regions.py: wpisy knyszyn, knyszyn-s (powiat 2008). osm_extract: BBOX (22.80,53.05,23.32,53.38) + bbox w kluczu cache (wg ADR 0203, do cherry-pick przez 0205).
- NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/ingest.py --region knyszyn --dry-run` → ingest → build_region.
