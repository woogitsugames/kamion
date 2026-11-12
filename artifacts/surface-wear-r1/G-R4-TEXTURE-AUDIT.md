# Independent G R4 texture accounting audit

Verdict: arithmetic/content PASS; residency/binding terminology needs the limits below. Read-only CPU audit of G worktree; no Unity, reimport or source changes. Detailed inputs, hashes and per-mip block sums: G-R4-TEXTURE-AUDIT.json.

- Eight generated Texture2D entries have eight unique GUIDs, all matching current .png.meta files. Four legacy PNGs exactly match the pinned pre-R4 Medium maps. Normal and Var clean copies are byte-identical PNGs and decoded pixels to legacy, but separate GUIDs: no content-based runtime deduplication can be assumed.
- ASTC 6x6, 512x256, 10 mips = 79,696 B per base/normal. ASTC 8x8, 256x128, 9 mips = 10,976 B per mask. Var has one mip = 8,192 B, NOT a full chain. Recalculated every row with ceil(width/block)*ceil(height/block)*16 at each mip, clamping dimensions to one.
- Both reported scene unions: 348,928 B versus counterfactual 178,560 B = +170,368 B (0.162476 MiB). Profiler totals: 3,766,304 - 1,953,288 = +1,813,016 B. All sums and path-substitution uniqueness verify. Generated eight, dependency seven and counterfactual four are different sets; do not sum the two scenes as separate allocations when shared assets are deduplicated.
- The apparent +3 instead of +4 follows the reported union replacing old Var by clean Var while retaining old base/mask/normal. Static beige/green .mat files still serialize old Var; this is not a reason to override Unity's reported dependency graph. It does show serialized references, recognized shader bindings and scene dependencies must not be conflated.

Required precision: R4TextureInventory.cs:27 uses AssetDatabase.GetDependencies, not a draw/GPU residency query. `additionalBoundObjects` should mean (or be renamed to) additional scene dependency Texture2D objects. A dependency can be unloaded/streamed/unused by a variant; this audit does not measure actual resident GPU bytes. The JSON interpretation already states scene-dependency estimates and NOT D3D12 VRAM, so the numerical accounting remains useful with this wording correction.

R3 comparison is honestly labeled counterfactual in method/arrays/profiler field: R4TextureInventory.cs:28 substitutes clean paths into current imported legacy Texture2D rows. It is NOT a historical R3 editor capture or historical Profiler delta. Legacy PNG parity is verified, but historical import settings/objects were not reconstructed. Keep `r3NativeMipPayload` explicitly qualified as counterfactual in summaries.

Reported texture formats are ASTC on D3D12. Block payload is a reported-format estimate, not proof the driver stores ASTC natively. Profiler includes engine/native/CPU overhead; neither PNG length nor its difference is GPU memory. Android overrides project the same blocks from power-of-two dimensions and square ASTC formats, but actual A16 residency/streaming/allocation remain UNVERIFIED. Helper projection is valid for these eight inputs; it is not a general NPOT/non-square-block importer model.

P0: independently recomputed 584,576 B = sum(vertices*4) across 81 CPU rows; that source explicitly calls it an estimate. This audit does not certify native P0 allocation. P2: existing native parity report records stride 24 before/after and zero added vertex bytes; its SHA is pinned, not remeasured here. Vertex payload and texture payload remain separate costs.

No numerical defect found. One terminology correction reported immediately to ROOT/G; no new render/test work required by this audit.
