# Inactive D candidate / UV mask contract

- `candidate-r1.patch` is prepared against pristine D source; `git apply --check` passes without activation.
- Applied only inside artifact `candidate-sandbox`; production source and copied Generated cache remain pristine.
- Missing road UV1 gets(-1,5), preserving real(0,0), existing values and zero defaults in other layers.
- A ROADWEAR material forces UV1 allocation even if every road primitive omitted that attribute.
- No road geometry, shader, material calibration, texture/sample, global asphalt/sky, scene, package or asmdef change.
- Predicted extra UV1 buffer36,124bytes per tier in chunk5_4(9031road-layer vertices); actual importer memory/budget unverified.
- Three meaningful EditMode cases prepared: missing-vs-valid UV, other-layer default, geometry/index/submesh preservation. C# compilation/NUnit have NOT run.
- Readback uses the [official Editor MeshUtility API](https://docs.unity3d.com/ja/current/ScriptReference/MeshUtility.AcquireReadOnlyMeshData.html), which can inspect uploaded non-readable meshes.
- This tiny correctness patch does NOT resolve the broad sterile-road task; broader wear tuning requires real D baseline/activation diagnosis first.

Activation sequence (only after G closure, D slot and new explicit ROOT Unity release):
1. Verify pristine source/cache pins and192raw/Fab15; fresh import plus canonical vehicle fixtures, then actual Low/High clear/overcast BEFORE matrix.
2. Save source/Generated/camera/material pins; `git apply --check artifacts/surface-wear-r1/candidate-r1.patch`, then `git apply artifacts/surface-wear-r1/candidate-r1.patch`.
3. Import, run the three prepared EditMode cases/full checks, capture matched AFTER; verify geometry/index/normal invariance and actual buffer/draw/sample cost.
4. Compare real road references; design broader wear changes causally, preserving calibrated asphalt mean and Low crack-sampling policy. No D PASS/DoD claimed here.

## Additional inactive source-only broadwear proposal

See BROAD-WEAR-PLAN.md and candidate-broadwear-r1.patch: three bounded existing-mask changes (wheelpolish smoothness, variableexistinggutter deposits, weakincidental longitudinal paintcontact). Existingtexture/detail/decal/meancontracts stayintact. Bothpatchescombined gitapply-checkPASS; production/593Generated/192rawunchanged. No activation/Unity/visualclaim. F finalvalidation takespriority atnextrootrelease.
