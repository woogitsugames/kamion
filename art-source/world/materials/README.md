# World C ground materials (generated PBR sets)

The texture sets are **not versioned** (lead decision 2026-11-09: public repo, LFS limits, "everything as
code"). Only the generator, `materials_spec.json` and small JPG previews in `_renders/` are in git. Any machine
rebuilds the same bytes.

## Build

From the repo root (PowerShell 7 or bash):

```
uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py
uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --tier High
uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --tier Medium,Low --only behaton_i_grey,grass_verge
```

- `--tier`: comma list of `High`, `Medium`, `Low` (default all three). Every tier is box-filtered from the
  same 2048 px generation, so `--tier Low` costs about as much as all three.
- `--only`: comma list of set names (see `materials_spec.json` → `sets`).
- `--photo`: source of `asphalt_detail_photo`, default `Data/photos/nowe/Worn_cracked_asphalt_pavement.jpg`
  (public domain, John Harvey, Wikimedia Commons; `docs/REFERENCES.md`). If the file is missing, that layer
  is skipped with a message and the other sets still build.
- Output: `art-source/world/materials/<set>/<High|Medium|Low>/T_<set>_*.png` and an updated
  `materials_spec.json` (slots, tile size in metres, albedo stats, ASTC block, PNG and GPU sizes).

**Time (measured 2026-11-09, Windows 11, Python 3.12 from `tools/worldgen/uv.lock`):** 167 s for all sets and
all tiers; per set 3–22 s (kerb 2.9 s, grass 21.8 s).

**Determinism:** fixed seeds per set, periodic FFT noise, periodic KD-tree Voronoi, no time or random-state
input. Verified: a full rebuild produced 148/148 PNGs with sha256 identical to an earlier build. Bytes depend on
the numpy/scipy/pillow versions pinned in `tools/worldgen/uv.lock`; another OS or CPU was not tested.

Size of one full build: PNG High 245 MB, Medium 66 MB, Low 16 MB. ASTC estimate with mips (blocks in the
spec): High 107 MB, Medium 21 MB, Low 3.7 MB if every set were resident at once.

## Test renders

```
blender -b --factory-startup --python art-source/world/materials/_src/render_test.py -- --out <abs dir> [--tier High] [--only street,yard,tiling]
```

Blender 4.2.9, EEVEE, overcast preset of `tools/blender/world/render_control.py`, camera at 2.5 m (driver eye).
Writes JPG. `_renders/` holds the reviewed set (each ≤ 300 KB, ≤ 1600 px); `compare_street_vs_photo.jpg`
puts the street render next to the CC0 photo of Rondo Bieżeństwa.

## Files

| File | Role |
|---|---|
| `_src/pbrkit.py` | periodic noise, Voronoi, hashing, normals, Toksvig smoothness, tier writer |
| `_src/sets_asphalt.py` | SMA, worn asphalt, patch, 16 m crack layer, oil atlas |
| `_src/sets_other.py` | concrete, JOMB plates, kerb, behaton, 20x10 paving, grass, gravel, macro, photo detail |
| `_src/build_all.py` | entry point, spec writer |
| `_src/render_test.py` | Blender control renders |
| `materials_spec.json` | contract for the engine integration (packing, slots, UV scale, tiers) |
