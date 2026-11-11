# D / ADR0099 — inactive candidate source review

Decision: SOURCE REVIEW ONLY; no D visual or runtime acceptance.
Root read candidate-r1.patch at D checkpointdba4855d. Production and Generated
remain pristine; git-apply-check and artifact sandbox only. Actual D BEFORE matrix
is still required before applying the patch.

The proposed Compact option fills missing UV1 with(-1,5) only for road-layer wear
policy. Existing valid(0,0) and supplied data remain unchanged. Other layers retain
legacy zero defaults. RegionImporter forces the channel when a ROADWEAR road
node has no supplied UV1, avoiding silent lane0/maxgutter interpretation. No road
positions, normals, indices, submesh topology, material colour or sample change.
No source-level blocker found. Extra UV1 buffer is predicted36124bytes/tier in
one9031-vertex layer, not measured runtime/device memory.

Three prepared EditMode cases exercise actual packed mesh bytes: validzero versus
missing sentinel, other-layer legacy defaults, and geometry/index/submesh invariance.
Compilation/NUnit execution remains pending. Must union RegionImporter additive
changes with C and leader work during eventual integration.

This narrow correctness fix does not solve the broad sterile-road appearance task.
D still needs baseline, reference-guided patches/ruts/cracks/oil/marking/tyre wear,
two reviewed rounds, preserved asphalt calibration and Low sampling policy, full
GIS/EditMode/budgets, ADR0099/REPORT. G closure has priority before activating D.
## Actual pristine baseline / activation review (14:43)
D a59fc1a9 has372actual fresh frames:93views x Low/High clear/overcast. Primary
57=23nativeworld+26Gate3+8wear; legacy36=17vehicle+19architecture. Canonical59
controls retained in union. Requested ortho_putry is unavailable because scene
builder imports only perspective; explicitly excluded before matching, no pose edit.
Root independently viewed all4wear-target contact sheets: visible road surfaces,
no truck/blank frames; missingUV1 pole remains outside central target. Newroad
negative valid. gate_tracks has no readable twin treads; mark_signal shows distant
longitudinal lines, patch_putry no distinct patch. Names do not prove feature coverage.
Source/raw/canonical fixtures pinned, patches inactive at capture. UVsentinel-only
causal activation authorized with4condition missingUV1/2+newroad negative controls.
Broad patch separate; add actual source-field glyph/oil/busstop/gate controls first.
No protected roads producer edits; robust allowed-import UVfield transfer or precise
upstream handoff required where authored paint has no lane coordinates.

## Native imported mesh/reference review (14:53)
Root read actual native-before154meshes/21materials,521419road+mark vertices per
tier. All road mesh assets have UV1 at merged-asset level; missing source primitive
fields may still become zero within that channel. Only two marking assets lack
channel (682/20verts). Do not conflate asset channel presence with valid lane field.
Actual buffer-size afterproof must supersede predicted36124extraUVbytes.
Constant-half marking area572.831m2/tier (geometry, not pixel/visible coverage).
Root viewed all6Mapillary refs: large transverse rectangular repair boundaries
on Putry and locally abraded paint are clear; smooth uniform noise cannot substitute
for those features. Exact locations/coverage of existing patches still required.
