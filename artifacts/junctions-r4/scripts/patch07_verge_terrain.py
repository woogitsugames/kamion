"""ADR 0110 step 2e: verge strips are exported inside the terrain primitives (draw budget: +1 draw in 23 road chunks
that had no verge_grass material) and are not footprint (plantings / holes of the streetscape stage unchanged)."""
p = 'tools/worldgen/roads/meshing.py'
s = open(p, encoding='utf-8').read()
old = '''        buf.add("road", "verge_grass", V, V[:, :2].copy(), T, footprint=fp, src=src, UV1=UV1)'''
new = '''        # not footprint: the conformed terrain under the strip stays as it was (road edge - 0.03 m, below the crown), so
        # the footprint mask the streetscape stage reads (plantings in island holes, yards, trees) is unchanged
        buf.add("road", "verge_grass", V, V[:, :2].copy(), T, footprint=False, src=src, UV1=UV1)'''
assert old in s
s = s.replace(old, new)
s = s.replace('''    collision ground behind a kerb stays the terrain); the top is footprint (terrain conforms under it, "soft")."""''',
              '''    collision ground behind a kerb stays the terrain). Exported inside the terrain primitives of its chunk
    (build_world.merge_verge_into_terrain): same grass, no extra draw call."""''')
open(p, 'w', encoding='utf-8', newline='\n').write(s)

p = 'tools/worldgen/roads/build_world.py'
s = open(p, encoding='utf-8').read()
old = '''    terrain = CH.build_chunks(zc, mask, e0, n0, w.region["bbox"]["width_m"], col=st["col"])
    log("terrain chunks", len(terrain))
    roads = assemble(w.buf.parts, LAYERS, half)
'''
new = '''    terrain = CH.build_chunks(zc, mask, e0, n0, w.region["bbox"]["width_m"], col=st["col"])
    log("terrain chunks", len(terrain))
    w.stats["verge_strips"] = merge_verge_into_terrain(terrain, w.buf.parts, half, st["col"], e0, n0)
    log("verge strips in terrain", w.stats["verge_strips"])
    roads = assemble([p for p in w.buf.parts if not _is_verge(p)], LAYERS, half)
'''
assert old in s
s = s.replace(old, new)
old = '''# --------------------------------------------------------------------------------------------
def route_polyline(region_id, w):'''
new = '''def _is_verge(p):
    return p.layer == "road" and p.src.endswith(":vg")


def merge_verge_into_terrain(terrain, parts, half, col, e0, n0):
    """ADR 0110: the grass strips behind kerbs (roads.meshing._emit_verge, src "...:vg") become part of the terrain
    primitives of their chunk (every LOD; LOD0: the 128 m sub-grid they lie in) instead of a `verge_grass` primitive
    of the road mesh: same grass as the ground around (terrain shader, ground masks sampled at the nearest node) and
    no extra draw call (23 road chunks had no verge_grass material before). Returns counts."""
    tris = 0
    add = {}
    for p in parts:
        if not _is_verge(p) or not len(p.T):
            continue
        Nn = smooth_normals(p.V, p.T)
        cen = p.V[p.T].mean(1)
        ci, cj = chunk_of(cen[:, 0], cen[:, 1], half)
        # LOD0 sub-grid (2 x 2 per chunk, order: rows from north, columns from west)
        si = np.clip(((cen[:, 0] + half) - ci * CH.CHUNK_M) // CH.SUB_M, 0, 1).astype(int)
        sj = np.clip(((half - cen[:, 1]) - cj * CH.CHUNK_M) // CH.SUB_M, 0, 1).astype(int)
        for key in sorted(set(zip(ci.tolist(), cj.tolist(), (sj * 2 + si).tolist()))):
            sel = (ci == key[0]) & (cj == key[1]) & (sj * 2 + si == key[2])
            T = p.T[sel]
            u, inv = np.unique(T.ravel(), return_inverse=True)
            add.setdefault(key, []).append((p.V[u], Nn[u], inv.reshape(-1, 3)))
            tris += len(T)
    nsub = (CH.CHUNK_M // CH.SUB_M) ** 2
    for (ci, cj, sub), items in sorted(add.items()):
        V = np.concatenate([it[0] for it in items])
        Nn = np.concatenate([it[1] for it in items])
        off = np.cumsum([0] + [len(it[0]) for it in items[:-1]])
        T = np.concatenate([it[2] + o for it, o in zip(items, off)])
        C = None
        if col is not None:
            i = np.clip(np.round(V[:, 0] - e0).astype(int), 0, col.shape[1] - 1)
            j = np.clip(np.round(n0 - V[:, 1]).astype(int), 0, col.shape[0] - 1)
            C = col[j, i]
        for li, prims in terrain[(ci, cj)].items():
            pr = prims[sub] if len(prims) == nsub else prims[0]
            base = len(pr["V"])
            pr["V"] = np.vstack([pr["V"], V])
            pr["N"] = np.vstack([pr["N"], Nn])
            pr["UV"] = np.vstack([pr["UV"], V[:, :2]])
            pr["T"] = np.vstack([pr["T"], T + base])
            if pr.get("COL") is not None and C is not None:
                pr["COL"] = np.vstack([pr["COL"], C.reshape(len(V), -1)])
    return {"tris": int(tris), "chunks": len({k[:2] for k in add})}


# --------------------------------------------------------------------------------------------
def route_polyline(region_id, w):'''
assert old in s
s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
