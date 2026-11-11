from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/edge-far-r2"
adr = ROOT / "docs/adr/0085-far-field-backdrop.md"
base = adr.read_text(encoding="utf-8").split("\n## Revision r2", 1)[0]
adr.write_text(base + """
## Revision r2 — stream H (2026-11-11)

Status: implemented and validated in the editor; leader review/device gate pending. Branch `gpt-edge-r2`, based on `argon-edge` 293c5f69 merged with main 9e6e9fde. Final source and meshes match tested checkpoint c05e8f06 (see `artifacts/edge-far-r2/VALIDATION.json`).

### Boundary ownership
The r1 centroid filter admitted buildings whose footprints crossed the tile. The extractor now excludes any source component touching the tile or a complete regional building outline, including regional outlines extending beyond the tile. It separately checks rounded minimum rectangles before and after distance compression; the mesh builder repeats those defensive checks. Cache schema /10 pins all source hashes, regional buildings.geojson SHA256, origin, half-size and ring extent. Full source footprints are checked before selecting a MultiPolygon component. Regressions include every edge, contact, a concave outline, a small crossing component, compression overlap and cache invalidation after a regional-outline change.

Buildings: 8470 -> 8447 (23 excluded: 2 blocks, 18 halls, 3 offices; no additions). Against the full region-building union, raw rectangle intersections 19 -> 0 and compressed intersections 22 -> 0 (overlapping sets). `edge-south` in all four conditions now shows the regional office instead of the false red-fascia hall; the false yellow hall at left is also gone.

### Scene and atmosphere contracts
`WorldEdgeBuilder` groups the four sector renderers under the identity transform `WorldEdge/WorldFarField`. This satisfies the existing recovery test without weakening it; no colliders/shadow casters are added. Common `WorldSurface`/`Vegetation` atmosphere remains authoritative for ADR 0098: no edge-specific fog constants, keywords or colour blends. Optical depth still uses compressed render distance; full-ring NMT relief is not implemented. The apron extrapolates the NMT-derived border, not measured terrain across the entire ring. These inherited approximations remain UNVERIFIED for physical fidelity.

### Named forest evidence and limits
The pinned OSM extract contains Las Pietrasze (pyosmium Area.id 11153179; not a direct OSM relation/node/way ID), local bounds E -676.23..1712.76 / N -306.91..2889.50. Target E -500 / N 1300 is inside that source polygon. Source extraction: `forest_identity.py`; summary: `pietrasze-source-summary.json`. Standard `dk8-dk19-exit` stays unchanged. Supplemental cameras look NE from the DK8/DK19 exit. Near crowns obscure the road-eye/18.2m helpers, so `edge-pietrasze-skyline` is explicitly a 40m diagnostic view, not driver-eye or phone evidence. It shows the forest closing the horizon in Low/High clear/overcast (`compare-skyline.jpg`). Elevated views still expose layered forest cards; no claim of photographic equivalence or full gate-3 approval. Existing canopy geometry retained; a shallow-fill experiment produced broad flat planes and was rejected.

### Validation and budget
64 final PNGs / 32 matched pairs inspected. GIS: 388 passed, 1 expected xfailed; EditMode: 226/226; PlayMode WorldEdgeRecoveryTests: 3/3, no skips. Final XMLs are `tests/editmode-20261111-120601.xml` and `tests/playmode-20261111-120628.xml` in the evidence directory. One skyline High-overcast editor shutdown hit the known mono-cleanup issue after writing its complete frame; the existing visual-QA wrapper accepted it under ADR 0083 and PNG integrity was verified.

| Metric | Before (Argon + same main) | r2 |
|---|---:|---:|
| Low mesh triangles, all four sectors | 24826 | 24508 (-1.28%) |
| High mesh triangles, all four sectors | 118902 | 118524 (-0.32%) |
| Max Low draw delta across 16 paired views, static + instanced | baseline | 0 |
| Max Low triangle delta across paired views, rounded stats trisK | baseline | 0 (some -1k) |
| New materials / textures / colliders / shadow casters in r2 | baseline | 0 |

These are generated mesh counts and editor frustum estimates, not phone GPU measurements. The r1 backdrop's inherited +2..4 estimated draws relative to main without a backdrop is not erased. Independent visual-critic and device validation belong to the leader. Redundant Argon `export/export` directories were moved to `artifacts/edge-far-r2/quarantine` (204580041 bytes); recursive deletion was rejected by automatic policy, so disk space was not reclaimed. No merge or push to main performed.
""", encoding="utf-8")

(OUT / "REPORT.md").write_text("""# H / ADR 0085 r2 — ready for leader review
- Branch `gpt-edge-r2`; tested implementation/source/data checkpoint c05e8f06; later commits add evidence/docs. Final equivalence checked in VALIDATION.json.
- Base: argon-edge 293c5f69 + main 9e6e9fde; only stream H; no main merge/push.
- Fix: reject full source footprints, rounded and compressed rectangles overlapping tile + complete regional outlines; cache /10 pins regional dependency.
- Buildings 8470 -> 8447 (23 excluded, 0 added); full-region raw overlaps 19 -> 0, compressed overlaps 22 -> 0; regional office restored in edge-south.
- Mesh Low 24826 -> 24508 tris (-1.28%); High 118902 -> 118524 (-0.32%); no new materials/textures/colliders/shadow casters.
- Low across 16 matched views: static+instanced draws delta 0; max rounded trisK delta 0 (some -1k); meets +0 draws / <=+2% tris relative to Argon + same main.
- Tests: GIS 388 passed / 1 expected xfailed; EditMode 226/226; WorldEdgeRecoveryTests 3/3, no skips. Final XML: tests/*120601.xml and *120628.xml.
- Unity fix: identity WorldEdge/WorldFarField parent for four sectors, required by existing PlayMode assertion (test unchanged).
- Evidence: 64 final PNGs, 32 pairs Low/High x clear/overcast; before/, after/, skyline/; compare-*.jpg and compare-skyline.jpg inspected.
- Las Pietrasze verified in pinned OSM; forest_identity.py + pietrasze-source-summary.json. 40m skyline diagnostic at DK8/DK19 exit explicitly is not driver-eye evidence.
- Atmosphere stays on shared WorldSurface/Vegetation globals (0098 contract); exterior terrain remains NMT-border apron approximation, full-ring NMT relief UNVERIFIED.
- Open: leader independent visual review/device gate; elevated views expose inherited layered forest cards. SELF-REVIEW.md states limits; no full gate-3 claim.
- Cleanup: both original Argon export/export paths absent; 204580041 bytes in quarantine/; recursive deletion blocked by automatic policy, so no disk-space reclamation.
- Known editor shutdown issue after final skyline High-overcast frame accepted by existing wrapper (ADR 0083); frame integrity verified; full logs retained.
- Conflicts: generated JSON -> regenerate; inherited additive WorldSurface.shader/materials.py/RegionImporter/build_world/WorldEdgeBuilder changes; preserve 0086 linear tint, _Tile rules, weather/runoff and 0098 common fog.
- Leader: merge gpt-edge-r2, regenerate build_world.py + fidelity report on integrated main, import-region.ps1, rerun Unity checks/independent review; no commands executed on main here.
- Delivery: artifacts/edge-far-r2 copied to main artifacts/edge-far-r2; logs/, tests/, VALIDATION.json retain proofs.
""", encoding="utf-8")

review = (OUT / "SELF-REVIEW.md").read_text(encoding="utf-8")
review = review.replace("28 before/after pairs", "32 before/after pairs (28 primary + 4 skyline)")
review = review.replace("A separate 40m diagnostic view is being captured; it is not a driver-eye or phone view.",
                        "The separate 40m diagnostic view was inspected in all four conditions: forest closes the horizon, but elevated views expose layered cards. It is not a driver-eye or phone view.")
review = review.replace("Test audit: GIS 388 pass / 1 expected xfail; initial EditMode 226/226. PlayMode found missing WorldFarField container; builder corrected without weakening test; final reruns pending.",
                        "Test audit: GIS 388 pass / 1 expected xfail; final EditMode 226/226 and PlayMode 3/3, no skips. WorldFarField hierarchy fixed without weakening the existing assertion. Final source/meshes verified identical to tested checkpoint.")
review = review.replace("Open: final skyline diagnostic, final Unity reruns, leader independent review and phone gate.",
                        "Open: leader independent review and phone gate; full-ring NMT relief and physical-distance haze remain unverified. Shallow canopy experiment rejected because it added flat planes; original canopy retained.")
(OUT / "SELF-REVIEW.md").write_text(review, encoding="utf-8")
