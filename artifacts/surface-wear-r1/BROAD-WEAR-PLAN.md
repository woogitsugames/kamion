# D / ADR0099 inactive broad-wear candidate

Status: CPU source proposal only. Production,593Generated pins and192raw pins remain byte-identical. No Unity/visual/GPU PASS.

Existing inventory (do not duplicate):
- ROADWEAR already uses lane/edge UV1, wheel darkening+polish, gutter deposits+damp and centre drip band. Valid-lane coverage62.443%old/100%new are vertex counts, not pixels/area.
- CRACKS already samples mask+normal on _KAMION_WORLD_DETAIL only. Keep it absent on Low; no new Low texture fetch.
- DECAL_PAINT already uses aggregate peaks, age, transverse wheel chipping, soot and distance prefilter. Preserve sentinel/known and existing paint/alpha contract.
- Existing patch/oil/tyre/grate decals and yard_wear/life/gate placements remain in place. No new decals/draws or guessed traffic-zone placements until actual baseline inventory.
- WorldPbrMaterials already sets aged/fresh wheel(.6/.25), gutter(.55/.3), drip(.22/.06). Candidate leaves all material constants/base albedo alone.

Concrete inactive candidate-broadwear-r1.patch (one shader,3small mask blocks):
1. Existing wheel strip smoothness increment.12 becomes.18 multiplied by already-sampled macro.b factor.65..1.05. Old maxincrement.072 ->.1134; fresh.030 ->.04725. Existing wheel albedo darkening unchanged. WORKING_VALUE, not measured road BRDF.
2. Existing gutter deposit strength varies by already-sampled macro.a factor.6..1.4, breaking uniform edge dirt. Aged maxg.77/fresh.42; centre of carriageway unaffected. Existing damp/soot layers remain separate and unchanged.
3. Longitudinal marking wheel-contact chipping gets12%of existing transverse term, only where lane UV says wheel contact. Transverse wear/aggregate threshold/paint colour/distancefilter unchanged. WORKING_VALUE incidental traffic scrub, not blanket faded paint.

Reference rationale:
- Existing Mapillary refs469512365899192/1911352299378570/1783751488818497 show regional pavement changes and restrained wheel/edge wear.
- 1026342955666337/513486983365569 show locally worn arrows/crossing/stop-area paint and patch transitions. Refprovenance.json preserves SHA/date/source; photos are visual references only, never runtime textures or absolute albedo calibration.
- Broad wear may already be adequate in actual currentD frames; proposal may be rejected. No claim that absent UV1 explains whole sterile-road task.

Bounds/contracts:
- No roads/*, geometry/index/normal/UV generator, asphalt mean/tint/basecolour, global field, Tile, weather||runoff, macro texture, panel_m/splash_h, setting/package/scene/asmdef edit.
- Original UV-sentinel candidate-r1.patch is independent; both together pass git apply --check against pristineD. Neither patch activated.
- SAMPLE_TEXTURE2D token count20before/after; no new sample/texture/material/keyword/draw. Extra scalar math and actualGPUcost remainUNVERIFIED.
- Actual ROI edge/crown/marking coverage/mean, wet response, aliasing and Low/High4condition appearance must be measured after baseline. Reject blanket dirt, polished wet ribbons, disappearing markings or unplanned sky-road brightness shift.

Next activation sequence (after F closure, D slot and explicit root Unity release):
1. Recheck source+593Generated+192raw pins; perform fresh currentD import/canonical vehicles, actual Low/High clear/overcast BEFORE and immutablecamera/material/source snapshots.
2. git apply --check artifacts/surface-wear-r1/candidate-r1.patch artifacts/surface-wear-r1/candidate-broadwear-r1.patch
3. Activate UV fix first and measure missing-vs-valid-lane control; then separately activate bounded broadwear patch for causal matched AFTER. Never apply during F final window.
4. Appropriate GIS/EditMode and matched4condition images, counts/sample/memory proof, independent review. This plan is not broadwear DoD.
