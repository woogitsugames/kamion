# Why the rejected polish probe cannot fix missing Low wear

Read-only plan after ROOT's rejection. No new shader, generator, atlas or render is implemented here. The selected shader is restored byte-for-byte to SHA256 `1dc7db4ea4ec839f4dc8fbd301ba5aedd38a12c3fff892e66818841d125edce4`. Paint, UV transfer, bus oil and gate version 2 remain selected; overall asphalt sterility is still open.

Update: ROOT selected E's corrected 4096-source / 2048-Android packing for a CPU-only prototype. It repeats the actual G/B/A bytes at full original per-metre resolution and costs 1.333374 MiB if the original stays resident. PACKED-MASK16-RECIPE.md and its proofs supersede the historical lower-resolution candidate below. Shader/material activation and runtime parity remain unapproved and unverified.

## Attribution from actual data

The source-field proof rasterizes the actual road triangles and Half UV1 through recorded camera matrices inside inspected clear-asphalt ROIs. Both old and fresh road regions have 100% known lane data. Positive wheel masks cover 42.2% and 50.1% of the respective ROIs. The real old-road material has `_ROADWEAR`, `_CRACKS`, `_PHOTO_DETAIL`, `_WheelPolish=0.6`, `_GutterDirt=0.55`, worn base/normal/mask textures and bound crack mask/normal. Fresh road has `_ROADWEAR`, `_PHOTO_DETAIL`, values 0.25/0.3 and fresh textures, without a crack texture. These bindings are from native readback and unchanged material-file hashes.

On those actual wheel masks, the rejected change produces only 0.047-0.278 display-luma levels on old asphalt and 0.100-0.333 on fresh asphalt across four conditions. It changes smoothness of an already rough surface; it does not introduce a visible repair seam or crack. The source mask is active, so missing keywords are not its explanation. The proposed gutter variation also only redistributes an existing edge response. All 56 runtime poses and rounded counters match, and the complete END AFTER cache matches END BEFORE, including the explicit two signal serialization exceptions.

Low's `worldDetail=false` disables both `_CRACKS` and `_PHOTO_DETAIL` code through `_KAMION_WORLD_DETAIL`. A material can therefore list `_CRACKS` and have real textures bound while Low executes neither crack nor close-photo sampling. Low plain asphalt samples base, normal, mask and one macro map; it does not sample Var. Medium/High execute the existing separate 16 m crack layer and 1 m photo detail. The 4 m base was deliberately designed to omit distinctive cracks, so merely adjusting polish cannot restore the feature that Low does not evaluate.

The existing 16 m crack input is an authored procedural layer, not surveyed or photographically located damage. Its source defines 1-5 mm open cracks, 25-40 mm sealant bands, sparse alligator zones and a ravelled halo. Medium source coverage averages are about 0.366% open crack and 0.764% sealant. Road class distinguishes worn and fresh surfaces; road UV1.y is distance to an edge, not a chronological age measurement. Patch/paint age fields are existing working rules, not a dated road-condition survey.

The six reviewed Mapillary references support localized transverse repairs, contrast between old/new courses and worn readable paint. They do not justify random blanket grime or a newly invented dense crack network on every road. Preserve the existing sparse layer and macro wear gate; do not infer exact crack placement or physical albedo from those exposed photographs.

## Channels that really are available

| Current input | Actual content and use | Constraint |
|---|---|---|
| BaseColor | RGB, 4 m sampling, calibrated mean 0.08 for worn asphalt | No stored alpha. Adding alpha can alter compression; putting a complete 16 m pattern into 4 m UV shrinks its physical scale. |
| MaskMap R | Identically zero on worn asphalt; metallic scale is zero | Potential material-scoped carrier. It is not globally free: other materials use metallic. |
| MaskMap G/A | Existing AO/smoothness; worn means about 247.74/24.78 out of 255 | Must preserve response, filtering and correlation with the 4 m normal map. |
| MaskMap B | Identically 255, used as the photo-detail gate | Unused by plain Low asphalt only. High still needs the original gate; it cannot be overwritten globally. |
| Var G | Identically zero in this unsegmented scan | Not a free Low fetch. Var.B is scan-derived micro-cavity, not the 16 m crack network. |
| Macro RGBA | Tone, wear and mottling at 64 m; shared by many materials | No genuinely free global channel. Replacing it risks unrelated surfaces and a scale mismatch. |

The actual copied Medium PNGs are 1024 square. Android imports MaskMap/Var at half size (512 here), while crack/detail layers retain their full tier size. The worn mask is ASTC 8x8 with mips. This distinction matters: copied PNG dimensions are not proof of resident Android dimensions.

## Smallest defensible candidate to review with packaging owner

Consider one **Low-only old-road mask/material binding**, retaining the existing single MaskMap sample. Pack existing open-crack coverage into R and sealant into B, at the original 16 m period. G/A would carry the existing AO/smoothness repeated four times within that period. Base and normal remain on their original 4 m UV; only that Low material's mask uses the existing `_Tile.z=16` scale. Use existing `_ROADWEAR` plus `_CRACKS` material identity and the Low detail condition to apply the already authored sparse layer; do not enable the full detail path or add a normal/detail fetch.

This is a proposal with real costs, not an automatically safe free-channel fix. At 512 ASTC 8x8, a complete mip chain is 87,424 bytes (0.0834 MiB) for one additional resident mask if the original remains used by paint/other surfaces. A 1024 variant would be 349,568 bytes (0.3334 MiB); it is not selected. A single Low material copy adds an asset and must keep each chunk's existing road group/draw count. The importer currently shares the Medium material between Low and High scenes, so binding isolation is a necessary implementation issue, not an assumed capability.

At a 16 m period, 512 pixels resolve 31.25 mm per texel. Thin cracks are subtexel coverage, and ASTC 8x8 can erase them; the sealant band is only about one texel wide. Repeating G/A four times also reduces their effective resolution per 4 m tile from 512 to 128. These losses must be measured against actual compressed GPU readback and images. Do not silently upscale an atlas or widen damage to compensate. E independently reviews the packaging/binding route and memory ledger before any implementation.

High must keep its original mask/material and existing crack path, so it cannot receive the packed Low layer twice. Fresh asphalt must retain its original mask and no crack coverage. Preserve material mean within one display RGB level against matched controls, with explicit local-contrast and paint-readability checks; this is a future measured criterion, not a result. Reject if compression removes the feature, roughness becomes coarse, 16 m repetition becomes obvious, High changes, or the new-road negative acquires old-road damage.

Rejected shortcuts: squeezing a whole 16 m layer into a 4 m texture; cropping it to a repeating 4 m signature; treating Var as already sampled on Low; overwriting global macro channels; bit-packing coverage into lossy compressed values; increasing polish/dirt again without a new cause. There is no universally free, scale-correct channel substitution in the current shared binding.

If approved later, separate all CPU map preparation from the Unity import, then check PHONE_RUN and GPT_UNITY_HOLD immediately before every actual Unity start. A guard taken before a long PBR build is insufficient. Preserve the selected-source baseline and limit the first actual test to matched old-road, fresh-road and High controls. Full route/editor validation waits for the final selected source. No new render is queued by this plan.
