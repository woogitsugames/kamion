# H / ADR 0085 r2 — IN PROGRESS (PHONE_RUN)
- Branch: gpt-edge-r2; code checkpoint: 503a6f6e; base: argon-edge 293c5f69 + main 9e6e9fde.
- Boundary fix: full source footprints, rounded LoD rectangles and compressed rectangles clear tile + complete regional building outlines; cache /10 pins regional dependency.
- Measured source audit: 8470 -> 8447 buildings; full-region raw overlaps 19 -> 0, compressed overlaps 22 -> 0 (23 unique excluded buildings).
- Measured generated mesh: Low 24826 -> 24508 tris (-1.28%); High 118902 -> 118524 (-0.32%); forest geometry/material inventory unchanged.
- Tests: full GIS 388 passed, 1 expected xfailed (gis-after.log, 536.80s); four initial stale-generated baseline failures resolved by world/fidelity regeneration.
- Unity EditMode / WorldEdgeRecoveryTests / before-after Low-High clear-overcast renders: PENDING, no new Unity started while PHONE_RUN exists; owner confirmed measurement still running.
- Evidence so far: after-audit.json, boundary-plan.png (source plan only), generate-after.log, baseline/argon-qa.json; edge-cameras.json adds two Pietrasze horizon diagnostics.
- Cleanup: original Argon exterior/interior export/export paths absent; 204580041 bytes in local quarantine; recursive deletion blocked by automatic policy.
- Atmosphere: existing shared WorldSurface/Vegetation fog retained; 0098 can tune common globals. Exterior terrain remains NMT-border apron approximation; full-ring NMT shape UNVERIFIED.
- Budget interpretation: r2 relative to Argon + same main; inherited r1 +2..4 estimated draws relative to no-backdrop main is NOT erased or described as +0.
- Conflicts: generated JSON -> regenerate; inherited additive materials.py / WorldSurface.shader / RegionImporter / build_world.py / WorldEdgeBuilder from Argon; preserve 0086 linear tint and 0098 atmosphere.
- Next: finish full GIS, then pwsh artifacts/edge-far-r2/run-evidence.ps1 -SkipGis; finally compare_evidence.py and inspect every PNG sheet.
- No merge/push to main; only stream H.

