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