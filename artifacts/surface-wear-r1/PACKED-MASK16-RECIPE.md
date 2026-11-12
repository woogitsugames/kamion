# Packed old-road mask: CPU prototype only

ROOT selected one bounded prototype of E's corrected packing option. This supersedes the earlier 512-at-16-m proposal that reduced G/A resolution. There is no new material binding, shader change, Unity launch or render. The shipping shader remains SHA256 `1dc7db4ea4ec839f4dc8fbd301ba5aedd38a12c3fff892e66818841d125edce4`.

Run `uv run --project tools/worldgen python artifacts/surface-wear-r1/packed_mask16_prototype.py` from this worktree. The recipe reads the actual currently bound 1024-square worn MaskMap and the current 1024-square crack-layer Mask PNG from ignored Generated assets. `packed-mask16-prototype-proof.json` records their SHA256 values, material/meta hashes, native binding, recipe hash and Pillow version.

## Exact channel and coordinate contract

- Output is 4096-square RGBA8. Each of the 16 G/B/A tiles is a byte-exact copy of the original 1024-square G/B/A. It does not rebuild AO, smoothness or the detail gate from floats.
- R contains only the existing 16 m open-crack R channel. Nearest 4x replication preserves every original coverage value and mean. No sealant, new random field, newly widened damage or fabricated age mask is introduced. The source crack layer is authored procedural WORKING_VALUE data, not surveyed damage.
- All packing is integer copying. PNG reload equals the packed array. The output has no gAMA, sRGB or ICC chunks; a future importer must set `sRGBTexture=false`, retain alpha and use linear mask filtering. No gamma conversion or albedo recalibration is performed.
- The existing material is `M_road_asphalt`, shader `Kamion/World PBR`, with metallic scale zero and Tile `(4,4,16,1)`. Its current mask R is identically zero. Base/normal remain at 4 m. A separate proposed mask UV multiplier 0.25 changes only mask sampling to 16 m. Coordinate tests include negative world positions and period boundaries; the G/B/A phase and texel size remain identical.
- Android target 2048 gives 16/2048 = 4/512 = 7.8125 mm per G/B/A texel. The corrected option therefore preserves the original imported 512-per-4-m resolution. Ideal integer box downsampling gives exact G/B/A parity through every corresponding mip level; this is not proof of Unity resizing or ASTC output.

The private filename ends `_MaskMap.png`. The current importer recognizes that suffix for alpha and its existing half-resolution Android policy; 4096 source therefore plans 2048 Android, provided the future texture metadata supplies the correct size and no later cap overrides it. No importer call was made here. The private output is `packed-mask16-private/T_road_asphalt_packed16_MaskMap.png`; it must not be committed or copied as a shipping asset at this stage. Commit recipe, hashes and proof only.

## Cost and scope

ASTC 8x8 at 2048, including all mip blocks down to 1x1, is exactly 1,398,144 bytes = 1.333374 MiB. If the original mask remains resident for paint/other surfaces, this entire amount is additional. The decoded CPU prototype is 64 MiB; that is temporary generation memory, not the compressed GPU estimate. No larger atlas family or additional layer normal is proposed.

The only proposed binding is the old-road material. Fresh-road assets stay byte-identical and receive no old-road crack carrier. The same packed mask can serve Low/High only if the planned separate mask UV scale is material-scoped: G/B/A retain their existing response, High ignores R because metallic scale is zero, and High keeps its original external crack path exactly once. Low would consume R from the mask sample it already takes. Proposed additional texture fetches are zero; shader arithmetic cost and actual residency remain unverified.

The CPU recipe checks all 2441 current cached and 192 raw file hashes against the explicit END BEFORE fixture, including the separately documented signal material state. It verifies the restored production shader hash and current MaskMap GUID/linear metadata. It does not edit these inputs or the fresh-road material. Two full runs produced the same private PNG SHA256, recorded in `packed-mask16-determinism.json`.

## Gates before acceptance

1. ROOT/E must approve the exact binding and importer plan before source activation. Preserve all existing tile, weather/runoff, macro, panel and splash contracts.
2. Read back actual imported dimensions, format, alpha and linear state. Compare original and packed G/B/A at corresponding world coordinates after real Unity resize and compression, including mip boundaries. ASTC encodes channels jointly, so adding R can perturb G/B/A even when source bytes are exact. Record graphics API and actual GPU format; a desktop fallback is not an A16 cost measurement.
3. High needs actual mask/normal/material and image parity, with only one external crack evaluation. Fresh road is a negative control. No source-byte argument substitutes for these runtime gates.
4. Low must show useful localized wear at the existing 16 m phase, while matched road output mean stays within one display RGB level. Reject erased coverage, changed roughness, obvious repetition or an effect that remains visually negligible. Do not widen or amplify the mask blindly.
5. Maintain a texture-memory ledger that includes the original resident map and any importer cap changes. Zero extra fetches does not establish zero GPU time.

If a later phase is approved, finish CPU preparation first and take a fresh PHONE_RUN/GPT_UNITY_HOLD check immediately before each actual Unity launch. No new render is queued by this prototype.
