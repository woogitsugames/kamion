# Diagnostic validity
- before102 is immutable canonical production baseline; source and generated file hashes in baseline-fixture/fixture-proof.json.
- before-no-pane INVALID: renderer.enabled was reset by TruckVisualRig.Apply. Do not use baseline-roi-initial.* as validation.
- before-no-pane-fixed VALID all9cab panes forced off; far-window opening changes the through-cab scene and inflates standard deviation. Report this confound.
- before-near-pane-off VALID measured windscreen only forced off; far door glazing stays. Post-render force-off assertions logged.
- before-no-coat is a whole coating-model ablation, changes pigmented-base roughness too; not isolated radiance.
- before-coat-radiance-off removes only coat env*Fc+direct in a generated copy of the actual shader. Original material JSON and production source SHA restored in finally, including failure.
- D30/D35 owner methods are door vertical profile max-min and roof p99-p50 in old approved1024ROI. Radiance-only delta is a different causal measurement, not the threshold itself.
- Baseline102 exit was nonzero after full completed fresh output and mono cleanup/abort_threads without crash stack. Same explicit acceptance as scripts/visual-qa.ps1 / ADR0083; do not describe as normal Unity exit.
- Photo inputs are3Commons cab photographs with manifestSHA and docs/REFERENCES.md licences, not owner AI reference sheets or photometric albedo measurements.
