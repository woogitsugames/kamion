# G R4 P2 plate preflight (read-only)

2026-11-11, actual G worktree after R4 focus. No source/Unity/cache changes; no new atlas or plate strings. G owns rear/dirt QA independently. This is an implementation plan, not compiled or rendered acceptance.

## Actual binding, not the car-grime contract

`game/Assets/_Generated/World/bialystok-industrial-c/Materials/M_car_plate.mat` currently binds **Universal Render Pipeline/Lit**, GUID `933532a4fcc9baf4fa0491de14d08ed7` (installed URP Lit.shader.meta). It does NOT use WorldPBR/_CARPAINT. BaseMap and MainTex GUID `d5bb4170d87f3704080c3bfdd6dc3d72` resolve to the existing `Textures/car_plates.png`. Both texture scale/offset are **(1,1)/(0,0)**. There is no `_Tile` property in this saved material. The actual car-paint Tile4x4 audit must NOT be applied to these plates.

Native saved properties: no valid/invalid keywords; instancing enabled; opaque queue -1, Cull2, ZWrite1, AlphaClip0, AlphaToMask0; BaseColor/Color=(1,1,1,1), Smoothness .55, Metallic0, no normal/metallic/occlusion map. Smoothness .55 comes from plate roughness .45. These are serialized native properties, not a GPU-colour measurement.

Owning factory: `tools/worldgen/streetscape/materials.py:208` declares texture car_plates; `RegionImporter.cs:374-390` falls through to its existing LitMaterial, whose factory begins at499 and explicitly resets shader to URP Lit at506. `InstanceImporter.ProtoMaterial:517-525` reuses that region material. Any eventual shader hook must run in the **exact car_plate factory route after LitMaterial**, survive repeated normal imports and leave every other Lit/PBR material unchanged. A manual YAML change would be lost.

## Atlas and independently decoded meshes

Atlas generation is existing `tools/worldgen/streetscape/life_cars.py:68-166`; export registration is `streetscape/export.py:136`. Actual imported PNG is RGB1024x512, SHA256 `9bf6239e666489c0dd5bf52307169f74d6415e08907bd70e5f9684bc5a095bd8`.

- Grid4 columns x8 rows =32 cells, each256x64. The plate content248x54 is inset4 pixels horizontally and5 vertically; remaining cell pixels carry a resized plate image, not a guaranteed constant/extruded gutter.
- `plate_atlas(n=31)` draws **31 deterministic fictional strings at cells0..30**; cell31 is the grey-band far placeholder. The 27 existing model prototypes use only cells0..26 (24 cars plus3 vans), via `_plate_index` at1815. No registry or uniqueness guarantee is involved.
- `_vehicle2` at1536 applies each prototype's same cell to front and rear on LOD0 AND LOD1, correctly mirrored in geometry so the EU stripe reads on the correct side. Some older comments say LOD1 uses far31: that comment is stale. `car()/van()` at1839 build the actual three runtime meshes, with `_vehicle_far` for LOD2.
- Independent GLB accessor plus actual serialized `Instances.asset` vertex/index-buffer decode: **81 native car/van meshes, 54 plate-bearing LOD0/1 meshes, 27 plate-free LOD2 meshes**. Each plate submesh has8 vertices /12 indices (two quads). LOD2 has no plate to remap; do not add one under a no-new-geometry claim.
- UV0 is already normalized atlas coordinates, NOT metres. Actual native channel is Float16x2 at offset16; R4 car meshes have stride24 because paint UV1 is also retained. Remapping UV arithmetic requires no new channel/mesh bytes.

Exact per-model/native corners and input SHA pins: `G-plate-native-uv-proof.json`. Example estate_white cell15: U [.75390625,.99609375], V [.509765625,.615234375], submesh7,12 indices. The whole 54-mesh audit resolves exactly the used cells0..26.

## Conversion, endpoint and mip risks

`terrain_mesh/gltf.py:139-146` flips generator V to glTF top-down and rounds UV to four decimals. `GlbReader.cs:134,194-199` flips it back for Unity. Its position reader mirrors glTF X; exporter uses source(-x,z,y), so Unity has source(x,z,y). `WorldMeshBake.cs` then stores UV0 as Half. Decode confirms this double V conversion; do not flip again in shader.

`life_cars.plate_uv:199-204` uses bottom-up generator coordinates. For cell k, col=k%4, rowTop=k//4:

```
lo = (col/4 + 4/1024, (7-rowTop)/8 + 5/512)
hi = (col/4 + 252/1024, (7-rowTop)/8 + 59/512)
```

Important correction to the preliminary shorthand: native endpoints are NOT all exactly ideal.40/54 meshes happen to have exact ideal corners; the others retain a tiny export-round/half residual. Measured maximum native-vs-ideal UV error is5.7220459e-6 (upper bound .00586 source texel), and native-vs-exported-GLB error3.439188e-5. Therefore use a measured tolerance to reconstruct local plate coordinates, not exact endpoint equality or integer casts of boundary UVs.

Actual texture meta: sRGB, trilinear, aniso2, Repeat U/V, mipmaps on, Android override1024 format50 =ASTC6x6 (confirmed ImportTexture source at635-638); no extra atlas mip policy is proposed. At mip1 the original4/5px gutter is2/2.5px, mip2 is1/1.25px, mip3 is.5/.625px. At coarser mips and ASTC blocks adjacent cells/characters can mix. Existing mip coverage settings do not fix RGB text bleed. An inset/corner remap cannot promise new sharpness at20/45m or collision-free letters after minification. Keep the present texture/import settings initially and inspect actual native mips/text edges in the eventual bounded QA. No device ASTC result is claimed here.

## One smallest feasible route (ROOT refinement: reuse existing UV1)

**Plate-only Lit forward vertex wrapper + exact-id factory binding; retain the same atlas and existing plate submesh/material slot.** Editing WorldPBR alone would do nothing to current plates. Switching plates to generic WorldPBR would change shading/Tile semantics and is not the minimal parity-preserving route.

Use repository-owned shader source, no edits in PackageCache. Installed URP17.3 `Shaders/Lit.shader:97-181` forward pass and `LitForwardPass.hlsl:158-180` expose the feasible wrapper: include the same LitInput/LitForwardPass, rename the original vertex entry through a local preprocessor alias, then call it from a small wrapper after adjusting only `input.texcoord`. Preserve LitPassFragment, material property contract, instancing variants and existing lighting keywords/passes; keep opaque shadow/depth/depth-normal behaviour. This is a plan, **compile UNVERIFIED**. If using UsePass for opaque auxiliary passes, verify keyword/property parity and selected renderer path; do not claim the extra shader/variant is cost-free just because draw count is unchanged.

**Prefer explicit local plate UV1 over endpoint/frac decoding.** Independent second native audit confirms ALL81 current car meshes have stride24 and UV1 Float16x2 at offset20; ALL54 plate submeshes currently contain only UV1=(0,0). R4 paint already allocates the channel over the entire combined mesh. Replacing those existing plate entries with exact local0/1 corners adds **zero stride, zero vertices, zero vertex-buffer bytes** in this current input set. Do not claim this for a future mesh that drops the paint UV1 channel; validate the descriptor first.

Small source-data extension: `life_cars.paint_deposition:330-342` already runs after normal splitting and only adds paint UV1. Extend its exact `car_plate` branch to write local plate UV1 corners from the known plate orientation (or validated UV0 bounds once on CPU); leave positions, indices, normals, UV0, all paint UV1 and other primitives byte-exact. UV0 stays the original atlas fallback and comparison input. The exporter flips UV1 V and GlbReader flips it back, so write bottom-up local coordinates in generator space. Exact0/1 survives export rounding/Half. `WorldMeshBake.Compact` already copies supplied UV1 for all primitives after paint causes the mesh-wide allocation; no new primitive/material slot is needed.

Installed LitForwardPass.Attributes unconditionally exposes `float2 staticLightmapUV : TEXCOORD1` at line26. These instanced cars use LightProbeUsage.Off, no per-car baked lightmap binding, and current plate material has no LIGHTMAP_ON keyword. A wrapper can read this existing input member without adding an interpolator. If a future path enables LIGHTMAP_ON/DYNAMICLIGHTMAP_ON or needs UV1 for baked lighting, fail closed to original Lit/UV0, rather than treating lightmap coordinates as plate coordinates.

Vertex algorithm (conceptual, not an installed patch):

1. `UNITY_SETUP_INSTANCE_ID(input)` BEFORE reading object-to-world. Obtain `TransformObjectToWorld(float3(0,0,0)).xz` (instance ground origin), not the plate vertex world position, vertexID, prototype index or unity_InstanceID.
2. Read valid existing global `_KamionGIRect.xy`; compute the same signed-quarter-metre region-relative cell/hash used by `WorldPBR.CarInstanceFilm:166-173`, with uint wrap semantics. Then `target = h % 27`, selecting existing cells0..26 only. This is variation, NOT uniqueness: collisions remain inevitable among1009 cars and27 strings.
3. `t=input.staticLightmapUV` carries the explicit local0/1 plate corners. Form new normalized UV using target col and bottom row `(7-target/4)` with4/5px inset and248/54px span, as above. **No frac on UV0 endpoints** and no Tile4, extra fetch, extra interpolator or per-fragment hash. Preserve old UV0 in the asset; only forward shader input is redirected.
4. Call unchanged LitPassVertex; it applies `_BaseMap_ST`. Require actual identity ST and preserve original material colour/smoothness/metal/cull/opaque properties. Front and rear carry appropriately oriented localUV, so both show the same registration and correct EU-band direction. LOD0/1 share instance origin/hash; LOD2 remains plate-free.
5. Migration must fail closed. Old plateUV1=(0,0) is indistinguishable from a valid lower-left vertex in isolation; a vertex-only magic-zero test is UNSAFE. Validate all54 native plate submeshes on import (expected four0/1 corners, descriptor/UV0/geometry/parity), then enable the exact shared material's versioned remap only after the combined library is valid. Default remap enable/version must be0; stale/mixed inputs, missing shader/global rect or unsupported lightmaps/backend retain ordinary Lit and original UV0. No runtime manager or per-instance material clone is proposed.

Backend/pass audit: authored Low/High URP assets point to Mobile_Renderer GUID65bc7dbf4170f435aa868c779acfb082, serialized `m_RenderingMode:0` (Forward); Mobile_Renderer_SSAO is also0. This is source/serialized evidence, not a new frame-debugger readback. Keep the same forward Lit fragment/keyword set and instancing. Opaque alphaClip0 means old Lit shadow/depth/depth-normal passes need no remapped colour UV for silhouettes. Do not silently claim deferred support by reusing Lit GBuffer unchanged: it would sample old UV0. Either explicitly support the corresponding GBuffer vertex hook with matched tests, or enforce forward-only/fail-closed material migration when an active deferred renderer is selected. The bounded proposal chooses the latter. Meta/baked-lightmap generation remains original Lit/no remap; these runtime instanced vehicles are not being newly baked. Preserve pass availability rather than dropping shadows/depth as an apparent optimisation.

Origin source: `WorldInstances.SyncOrigin:242-257` preserves local TRS and adds region root translation; `FlushBatch:525-559` uses RenderMeshInstanced with the same matrix for all submeshes. `_KamionGIRect` is updated by `WorldSkyVisibility.Push:72-87` from the corresponding transformed region origin before rendering. Thus the same relative hash can be stable across LOD and rebasing. Verify global rect validity and synchronisation on every actual draw: if no map/current rect is available, fail closed to original UV rather than hashing stale/zero globals. Multi-region interleaving and float precision at quarter-cell boundaries are explicit integration risks; current shared global behaviour is not a general multi-region guarantee.

## Required bounded tests / four target cases

No tests were run for this proposed hook. Before implementation acceptance:

1. **Near white estate:** r10_wheel_02 / r10_front_04, identify the same instance; front/rear quad must agree and letters/EU band must not mirror. No new slot, atlas pixels, normal or body change.
2. **Rear pair:** r10_rear_04, name the visible SUV and separate white rear target; do not assign a plate to the estate side hidden behind the SUV. If occluded, report unmeasurable instead of moving cars for the matched proof.
3. **Repeated black prototypes:** use visible targets from g_dirt_level_0/1/2/3 plus r4_dirt_candidate_3 with actual instance IDs/origins. Assert deterministic hash choices across LOD0/1 and both front/rear, not guaranteed four unique registrations. Show the target body mask, not a neighbouring plate.
4. **Fleet/LOD controls:** use actual r10b_black_20, r10b_grey_20, r10b_blue_20 sources behind historical sheet_far. Its fourth tile is r10b_black_45, already documented as wall-occluded/invalid fleet proof, NOT a silver45 camera. LOD2 has no plate, so disappearing text there is current geometry behaviour, not a remap bug or proof of readable far plates.

Add exact-id reimport/idempotence and unaffected-material tests. Verify original UV0/positions/normals/index bytes, paint UV1 bytes and all81 stride24 are unchanged; only the54 plate UV1 entries may differ. Require explicit0/1 corner coverage, default-disabled migration and stale/mixed-library fallback; exercise forward renderer eligibility/lightmap rejection. Compare actual shader/texture/ST/properties after normal factory import. Exercise LOD0->1->2->1 and origin shifts with camera-relative matrices/global rect, including negative cells and near-quarter boundaries; use real vertex shader readback against CPU uint reference. Origin/hash must not change because draw batching order or instanceID changes. Current camera packets and projected target identity are required. Final visual proof needs matched clear/overcast Low/High plus native mip crops; default PNG size does not prove internal rendering scale. Counts must remain the existing draws/geometry/textures; zero new fetches is source accounting, not a measured A16 timing result.

Hand-off: G may implement only after ROOT approves this narrow binding path. No new registrations, geometry, atlas variants, collision guarantee, runtime manager or plate-texture generator rebuild is needed for this experiment.
