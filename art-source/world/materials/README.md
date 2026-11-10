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

## CC0 scans (ADR 0063, owner decision D40)

Since 2026-11-10 most ground and facade sets take their micro-detail from CC0 scans (Poly Haven). First fetch the scans
(162 MB, not in git, sha256-verified against `art-source/world/cc0/cc0_manifest.json`):

```
uv run --project tools/worldgen python art-source/world/materials/_src/cc0_fetch.py
```

`build_all.py` then builds every set listed in `sets_scan.SCAN_SETS` from its scan (and falls back to the procedural
generator when a scan is missing). `--procedural` forces the old purely procedural sets (A/B comparisons). Every scan
set carries a `source` entry in `materials_spec.json` (assets, authors, licence, scaling, bombing, element count).

| Mode | Sets | What the scan gives / what stays procedural |
|---|---|---|
| direct, bombed into a 4 m tile | `asphalt_sma_fresh`, `asphalt_patch`, `gravel_compacted` | all of the surface; 16 m cracks, 64 m macro, wear, patches, oil stay layers |
| direct | `asphalt_worn` (4.04 m scan), `behaton_i_grey`, `paving_20x10_grey`, `sidewalk_slab_35`, `plaster`, `brick`, `bark_pine` | surface + element layout of the scan, scaled to Polish sizes where needed (holland 20x10, NF course 75 mm, slabs 35x35); Var.G ids from the scan's displacement |
| hybrid | `concrete_cast_5m_joints`, `concrete_slab_3x1.5`, `kerb_concrete_1m`, `concrete_precast`, `large_panel_joints`, `trapezoid_sheet` | layout (5 m sawn joints, JOMB plates, kerb units, panel joints, trapezoid ribs) procedural; scan micro relief, albedo ratio, roughness and AO on top |

Calibration: albedo means stay on the targets of the procedural sets (asphalt_worn 0.08 etc.), hue balanced to the old
set means, so the paint/asphalt contrast (D37) and the asphalt level of review r8 do not move.

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
| `_src/build_all.py` | entry point, spec writer (`--procedural`: ignore the scans) |
| `_src/cc0_fetch.py` | download + sha256 check of the CC0 scans (`--resolve` re-queries the Poly Haven API) |
| `_src/sets_scan.py` | scan processing: de-lighting, flattening, hue/albedo calibration, Frankot-Chellappa height, texture bombing, block segmentation, hybrids |
| `_src/render_test.py` | Blender control renders |
| `materials_spec.json` | contract for the engine integration (packing, slots, UV scale, tiers) |
