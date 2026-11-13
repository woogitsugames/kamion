# ADR 0169 — World edge: one source of road closures, no doubled rows, sign sheeting colours, dead ends of the route graph

Status: implemented on branch `edge-0169` (base main `47ee3f123`, 2026-11-13, s17); not merged. Editor renders only
(Low); phone NOT measured. A `visual-critic` review is still required: the notes below are the author's.
Source: review `docs/reports/REVIEW-2026-11-13-s16-mistral-r5.md` (#31: "zdublowane zapory edge-west buduje C#
`WorldEdgeBuilder`", #29 / M27: 115 off-reach edges), ADR 0141 r6d, ADR 0082.

## Context

1. **Two implementations of the closures.** The importer (`WorldEdgeBuilder.ReadExits`) derives one closure per road
   cut by the region edge. `tools/worldgen/roads/barrier_audit.py` carried a Python copy of `ReadExits` and audited
   the raw result. ADR 0141 r6d merged a carriageway with its slip lane only for the visible mesh; the colliders and
   `WorldBoundary.closures` stayed doubled (36 entries), and the Python copy went on reporting the pair, which kept
   an xfail in `tests/gis/test_barrier_ends.py` for something the pictures no longer showed.
2. **What was really still doubled** (measured on the committed graph, 36 closures):
   - 2 pairs Maczka x `trunk_link` at the west edge, 0.55 m and 0.94 m apart: merged in the mesh since r6d, still two
     colliders and two runtime entries each;
   - 2 pairs of **crossing** closures nobody handled: Kombatantow x service road (south edge, centres 5.2 m apart,
     90 deg) and Batorego x service road (east edge, 3.2 m, 83 deg). Two roads leave one junction a few metres inside
     the edge; both barrier rows, both board rows and both colliders ran through each other;
   - 3 pairs of neighbouring carriageways closed 9 - 22 m apart along the road (Maczka W, Andersa E, Tysiaclecia N):
     each row is road width + 5 m long, so the rows reached 0.4 - 3.4 m into each other's span across the median and
     read as one overlapping double row from the cab (`edge-west`, `edge-east`).
3. **White.** r6d set the board white to linear 0.80 and the red to 0.52 / 0.035 / 0.030 by eye. The rest of the world's
   signs use the atlas colours of `tools/worldgen/streetscape/signs.py`.
4. **Route graph.** M27 flags 115 edges as off-reach. Open question of the review: can a route lead the truck into a
   dead end at the tile edge?

## Decision

1. **One list.** `WorldEdgeBuilder.ResolveClosures` produces the only list of closures of a region. `WorldBoundary.closures`,
   the box colliders and the render groups are all built from it. Steps:
   - `MergeOverlappingClosures` (r6d rule, unchanged thresholds): a carriageway and its slip lane become one closure;
   - parallel closures (heading within 25 deg) no more than `ClosureTrimAlongM` = 40 m apart along the road
     (WORKING_VALUE) whose spans overlap sideways: both rows end at the middle of the overlap;
   - crossing closures whose rows meet: each row is cut at the crossing point and keeps the part with its own road, and
     ends `ClosureCornerClearM` = 0.9 m (WORKING_VALUE) before the corner so the boards 0.75 m in front of one row do
     not run through the other. Applied only when each road axis lies in front of the other row; then the two kept
     parts are exactly the border of the area the driver can be in. The 0.9 m + 0.9 m opening at the corner is
     narrower than any vehicle.
   - `Build` throws if `FindClosureConflicts` still finds two rows within 0.5 m.
   `WorldBoundary.Closure` gets `spanM` (row length; 0 = road width + 5 m as before). `widthM` stays the width of the
   road, so a cut or merged carriageway keeps its B-1.
2. **No copy in Python.** `closures_from_graph` and the closure numbers are removed from `roads.barrier_audit`; the
   xfail on `test_no_overlapping_barrier_rows` is removed (rail rows: 0). `ReadExits` is a pure public function
   (graph path, anchor, rectangle), so the check runs on the committed graph without a scene.
3. **Duplicate test** (EditMode, `WorldEdgeClosureDuplicateTests`, 5 cases): detector on synthetic rows (same row
   0.4 m apart, crossing rows, 0.6 m apart = not a duplicate); the committed graph has colliding raw pairs and none
   after `ResolveClosures`, no two centres within 0.5 m; median case (Andersa coordinates); corner case (Batorego
   coordinates); idempotence.
4. **Colours.** Boards and the B-1 face take the sign atlas colours: white sRGB 245/245/242 (linear 0.913/0.913/0.888),
   red sRGB 196/30/36 (linear 0.552/0.013/0.018). One definition of "sign sheeting" for the world.
5. **Route graph: checked, not changed.** New read-only audit `tools/worldgen/navgraph/dead_ends.py` + tests.

## Regulations: what is cited and what is not

- B-1 as a white disc with a red rim: as the project's sign set (`signs.py`, source named there: zalacznik nr 1 to the
  regulation of the Minister of Infrastructure of 3 July 2003, t.j. Dz.U. 2019 poz. 2311).
- U-20 road barriers are defined in zalacznik nr 4 of the same regulation ("urzadzenia bezpieczenstwa ruchu
  drogowego"). **The text was not read for this change** (two web lookups returned no usable text; a file download
  was not made). Therefore UNVERIFIED / WORKING_VALUE, unchanged from ADR 0082 / 0141: board height 0.25 m, 0.5 m
  fields, two boards with a 0.20 m gap, top edge 1.20 m, B-1 diameter 0.90 m at 1.85 m, and whether a full closure
  needs U-20b with red lamps. The sheeting colour boxes and retroreflection classes (type 1 / type 2 film) are
  UNVERIFIED as well; the colours are the project's sign atlas, not a measured standard value.
- Retroreflection is not modelled (no headlight response on Low); the material is plain `Kamion/World Surface`.
  Adding it would need a material keyword or a second material (+1 draw per group) and is not done.

## Validation

- Rebuild (`RebuildEdgeBatch`, both tiers): 36 graph closures -> 34 resolved, 6 render groups, 7754 tris (main:
  8060). Colliders 36 -> 34.
- EditMode full: 500 total, 497 passed, 2 failed, 1 skipped. The 2 failures are
  `CarPaintMaterialTests.DepositionChannel_*` (known on main, not this branch). All `WorldEdge*` cases pass.
- pytest `tests/gis/test_road_fidelity.py tests/gis/test_barrier_ends.py tests/gis/test_barriers_0159.py
  tools/worldgen/navgraph/tests`: 82 passed, 1 xfailed (the xfail is in `test_road_fidelity.py`, not from this
  branch). `fidelity/run.py` rerun: only the input hash of `barrier_audit.py` changed in `fidelity_qa.json`.
  The full `tests/gis` / `tests/gate3` set was NOT run.
- PlayMode `Game.Tests.WorldEdgeRecoveryTests` on the rebuilt WorldC: 3 total, 3 passed (ray at each of the 34
  closures hits its collider at 5.2 - 6.2 m).
- Budget, Low, editor estimate (`stats.txt`), before = importer of main on the same scene:

| camera | draws before -> after | shadow casters | tris |
|---|---|---|---|
| edge-east | 42 -> 42 | 20 -> 20 | 85329 -> 85177 |
| edge-west | 32 -> 32 | 12 -> 12 | 74483 -> 74439 |
| edge-north | 39 -> 39 | 18 -> 18 | 68005 -> 68005 |
| edge-south | 101 -> 101 | 63 -> 63 | 138207 -> 138207 |
| edge-corner-east-batorego | 40 -> 40 | 20 -> 20 | 74374 -> 74222 |
| edge-corner-south-kombatantow | 102 -> 102 | 60 -> 60 | 99317 -> 99207 |

  Draws +0, shadow casters +0, triangles down. Clear and overcast give the same counts.
- Pairs (before over after, 960 px) and full-resolution crops: `artifacts/edge-0169/pairs/`.

### What the pictures show (author; visual-critic pending)

- `edge-west`, `edge-east`: the two carriageway rows no longer overlap in the median; each ends at its middle. One
  B-1 per carriageway, as before.
- Corner cameras: before, the rows of Batorego / Kombatantow and of the service road run through each other; after,
  they meet in a corner.
- White: overcast and sunlit boards (`edge-east`) read white. In `edge-west` clear the boards face away from the sun
  and are lit by ambient only; the white is lighter than before but still reads light grey. That is the lighting of
  the tier, not the albedo (0.913); not changed here.
- Not improved: a closure is still a barrier across an otherwise open road with nothing announcing it (no advance
  sign, no lamps). It reads as a road closed for works, not as a wall, but it appears without warning at speed.

## Route graph: can a route end in a dead end at the edge?

Measured on the committed `bialystok-industrial-c_route.bytes` (550 nodes, 646 edges, main component 411 nodes):

- **Off-reach (the 115 edges / 113 nodes of M27): no risk.** 22 of the nodes are one-way entries from the tile edge
  (a start there routes into the main part); the other 91 belong to parts with no connection inside the tile. The
  truck cannot drive onto any of them from the main part.
- **No-return edges: yes, this is a real dead end.** 30 edges, 2730 m, end in 26 nodes that can be driven to from the
  main part but have no directed way back: the outbound one-way carriageways of Andersa (8 edges, 1085 m), Maczka
  (6, 494 m), al. Tysiaclecia (5, 311 m) and unnamed links (11, 839 m). They are not flagged, so the destination pin
  can be set on them and the planner routes there; past the last junction the only thing ahead is the closure, and
  every later plan from there is `NoPath`. Nine points of no return (region E, N): Tysiaclecia (-821.7, 861.1) and
  (-298.5, -892.8); Andersa (-340.0, -148.8) and (297.6, -583.7); links (-574.5, 63.5), (-569.2, 92.4),
  (-238.3, -994.4), (557.2, -739.8), (1014.6, -892.7).
- **Not fixed here** (navigation UI and the route file are outside this task). Proposed, in order of value:
  1. node flag bit2 "no return" written by `mark_reachability`; `SetPin` treats such an edge like off-reach (snap to
     the nearest main-component road) - no route ever ends there;
  2. a HUD warning at the point of no return for free driving;
  3. a median crossover in front of the closure on dual carriageways (road generator), so a truck that got there can
     turn back legally.

## Risks / open

1. `WorldBoundary.closures` has 34 entries instead of 36 and the centres of 10 closures moved along their row.
   `WorldEdgeRecoveryTests` (PlayMode) passes; the rest of the PlayMode suite was not run.
2. Scenes imported before this ADR keep the old layout until `import-region` or `RebuildEdgeBatch` runs.
3. `ClosureTrimAlongM`, `ClosureCornerClearM` and all sign dimensions are WORKING_VALUE; the U-20 text is UNVERIFIED.
4. The corner rule is skipped when one road axis lies behind the other row (not present in this region); `Build`
   then stops with the conflict message instead of building a doubled closure.
5. `docs/adr/README.md` index not regenerated here (leader).
