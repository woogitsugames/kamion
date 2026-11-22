# STATUS fix-b4-s24 (błędy buildu #4: brama Maczka, terrain_walls C, water_0210, world_roads, most 12 t)
- krok 0: worktree z main 1c0596b94, derived = kopia (-CopyDerived). Brama widoczna w shot_t0250 (ciężarówka pos (404,5) jedzie na zachód, brama ~20 m przed nią).
- NASTĘPNY KROK: zlokalizować mesh bramy w chunkach bialystok-maczka: `cd tools/worldgen; uv run --with trimesh python <scratch>/glbnodes.py <chunk>.glb 370 -2 15`
