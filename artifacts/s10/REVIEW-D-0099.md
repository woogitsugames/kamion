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

Per-material native white paint area4989.216m2 exactly matches source; total
_markings layer15028.320m2 includes tyre5189.475,oil514.561,patch1613.442,
yard2195.019 and other decal materials. Layer total is not paint coverage.
Source connected-footprint inventory312patch/871oil/799tyre is neither generator
source attribution nor rendered-visible count.23bus shelters nearest oil7.04-92.11m
proves proximity only; no dedicated stop-zone attribution. Need target-specific
source/actual images before adding/moving existing wear under allowed scope.

First sentinel actual audit preserved all154positions/normals/index/UV0 hashes,
but8UVrow changes exposed96missing sidewalk vertices affected by layer-wide
policy. Assertion rejected the expected4row claim; no false proof accepted. Agent
narrows policy to asphalt/_new only and reruns import/native audit. Actual extra
UVchannels0bytes, superseding36124byte forecast. Initial12causal images retain
firstcandidate provenance; final narrower candidate must be measured independently.

Final narrowed native audit independently checked:154meshes identical positions,
normals,indices,UV0,vertex/submesh counts; EXACT4UV1rows (2_3/5_4 eachtier).
All channel-presence flags unchanged, actual extra UV allocation0bytes.96sidewalk
vertices no longer affected. Sourcefield closeups/UVtransfer feasibility remain;
this correctness fix alone is not broadwear quality acceptance.

Root viewed4field-foundation sheets/16actualframes: real rectangular repair
patches at two targetposes and small signalnear oil visible. Gate-near tyre
frame shows irregular dark yard patches/bands, not readable pairedgateentry
tracks; no gatePASS. Paint remains full/clean versus references. Allowed
wholecomponent field transfer planned using actual containingroadUV/height,
vertex+edge-mid+centroid agreement, preservepaintUV1.yage and allgeometry/UV0.
Unknownjunction/height/overlap/lane-wrapreject;131.832m2 preliminary accepted
area is an upperbound before componentclosure, not final coverage.
Greadonlybusstoppreflight1ed61e9c confirms all extracted20OSMstopnodesplatform,
no direction/stop_position; not proofrawPBF lacks them (selector omission).
Existing allowedfurniture/life flow/decal material permits future VERIFIEDsmall
footprint, not projectedallshelters.0newdraw conditional onchunk/culling, actual
matchedbudgetneeded. Source+photo/ortho verification or precisehandoff required.

Full raw-source read contains20explicit bus=yes/public_transport=stop_position
inside2048x2048mregion, pinnedPBF SHA0ff26cd42f175a5711c69b6d3087a9dcd3bb93367eda16809c75a11ce6c3869d.
Root read exacttags/IDs/coordinates and sourcebbox. Earlieragent10count was incorrect from truncatedstdout; rootcountassert rejected it before publishing proof. Extracted-source
absence was selectoromission, not rawabsence. Buspose/stain attribution still
requires actualroad containment/height/direction and sourcephotozone proof.
Targeted field+sentinel10/10pass (fullsuite pending). Wholecomponent source reviewed:
realroadonly, overlap/height/7sample gates, clonedUV1.x, age/geometry untouched.
Rootflagged indexed vscoincidentvertex closure; actual3350->3343components proves
7metadata unionsneeded. Agent will union exactposition+sameage forGROUPING only
and test splitvertexunknown closure; no geometricwelding. Initialimport not final.

Corrected grouping actualimport exit0:16accepted/502rejected components,406changed
vertices,59.519m2/tier (3decimal logged).11targetedtestsPASS. Nativeage hash
proof pending. Source-level review flags skippedunknownroadtriangles: knownroad
overlap with sameheightunknownjunction could still sample validfield. Retain
unknowntriangles as rejecting blockers or prove no actualoverlap; regressioncase
required before claiming fullunknownjunctionreject. No broad shader activation.
Root viewed busphoto1170695487387705: realrightpavedbusbay/rectangular repair edge
and curb/shelterzone. A bounded stain may use verifiedactualstopzone as explicit
WORKING_VALUE trafficwear, not claim photographed/measured engineoil coordinates.
Fullpolygon must fit generateddriveablebay/height/chunk with matchedcost; no
shelter projection/all20 placement or invented roadgeometry.

Unknownoverlap source fixb5cd75b3 reviewed: matchingheightnull/sentinel road
triangles retained as blockers, otherheight unknown roads do not veto. Actual
latest targetedXML14/14/0skip independently parsed PASS; older copied artifact
XMLstill11, so rootusedactualtests/editmode-20261111-151057.xml. Final blocker
import/currentcoveragepending; prior16component result remains provisional. Age
comparison firstrejected PythonrawUV orientation, then NumPyvsUnity halfrounding;
verifyuploaded age against originalGlbReader plus UnityFloatToHalf before PASS.
Generator flips both UVsets onexport and GlbReader unflips; no newUVconvention.

Root independently checked finalblocked transfer native data:154meshes invariant
positions/normals/index/UV0/vertex/submesh counts;150UV1.y hashes match original
GlbReader+Unityhalf sourcecontract,4channels absent. RoadmissingUVy5 is intentional
sentinel policy; paint/decal age is original. Exactly10UV1buffers changed:4road
sentinel+6marking buffers in3chunks,0newchannels. Final blocked logged counts11accepted/
507rejected/356verts/58.319m2 pertier. No fullwear visual/budgetPASS from this.

Coverage correction: root initially read lane-field-import-proof.json (prior16),
not lane-final-import-proof.json. Current final proof independently parsed11/507/
356/58.319 per tier. Native154geometry/150yhash verification remains unchanged.

Root viewed4 final-field-before sheets/16views: stop464 actualroad/curb/shelter
context visible before newstain; supported/unknown paint are hatch/lines, not
provenP8arrow. Additional actualcompactglyph closeup pending before worldbuild.
G readonly gate-source coordinate preflight assigned, no D source/cache/Unity
overlap. Newstop metadata selector may add20stopnodes andbus=yes to20existing
platformnodes; unchanged geometry/otherobjects must be measured separately.

Root independently hashed all192bus BEFORE backups/current files and checked
every ordered primitive in the2changed4_5GLBs.190files/all64instances exact;
onlyoil tail+10vertices/+9tris per tier, no newgroups.95High/57Low otherprimitives
exact, materialdefinitions/node-transforms exact. Agent's material-name dictionary
had hidden3duplicate terrain_grass primitives; root checked them too (unchanged).
Source proof savedD-bus-world-independent-check.json; runtimebudget still pending.
Root viewed all4gatekerb sheets/8frames: realbarriers/raisedcurbscuffs visible,
no pairedasphaltpaths. Bounded pairedcandidate authorized after BEFORE/source
footprint/height/clearance and unchangedmaterialgroups; WORKING sizes/strength,
no scuff2.5 blackribbons. Bus-only source remained frozen during its build.
Root viewed genuine P8HighOV baseline and actualwearOFF: fullarm/head reconnects
with samegeometry. Runtime mask caused severedarrow, notgeometry. Do not call
this baseline qualityPASS. One diagnostic wheelstrength.85->.425 approved on
P8/P10 with sameage/dirt and exactfinallyrestore; no globaladoption before review.

CPU source review of gate_wear/bus_stop_wear: existing-asphalt-only support, exact
projected polygon coverage (including holes), height ambiguity rejection, paint/
kerb clearance, pair-atomic rejection and existing chunk-materialgroup required.
TyreUVxmetres/UV1length matches production shader; .9strength is separate from
existing2.5curbscuff. Gate64tris/72verts from4strips, dimensions WORKING. Full
world build/ordered proof reports only6_6delta vsbus,190raw unchanged, preserved
bus4_5 and allinstances; cached2441Generated stillbus-only, so pending BEFORE
captures remain from explicitlypinned cache even though source/raw advanced.
D private-scene audit: all40native serializedcamera worldmatrices/FOV/clip and
truck/trailer root transforms match baseline in bothscenes. Two prefabbytes differ,
but553truck/253trailer serialized records match after fileID identity normalization,
161/73localtransforms exact. This does not recover historic actualruntimeposes;
recorder prepared for nextplannedrender, no372pixelstable claim.
