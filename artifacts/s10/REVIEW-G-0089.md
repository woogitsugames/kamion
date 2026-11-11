# G / ADR 0089 — independent review WIP

Decision: SOURCE REVIEW ONLY; candidate appearance and runtime budget pending.

Fresh baseline73cameras x4conditions =292 frames is the comparison basis. Historical
s9 numbers are not substituted for current source/fixture evidence. Fresh blackdoor
HighOV38.672/LowOV34.144 already meets the30-40 target; no pigment/reflection lift.

Pearl-only Color contract correction has actual production-shader GPU evidence:
authored linear HDR1.6/1.9/3.2 uploaded raw yields2.8123/4.1045/12.922; gamma
encoding before Color upload returns intended values. This is separate from A Tint.
Isolated original-film-state capture: HighOV door38.672->38.356, cleanbonnet
81.017->78.519; LowOV34.144->33.854 and74.221->71.475. No broad colour lift.
The old mixed wiper/trim ROI is retained under its legacy label, not used as cleanhood.

Root reviewed2b5e88dd source against43bc53a7: existing LOD0 wheel14->22segments,
LOD1 remains10; disclose full LOD0 distance range rather than claiming an8m-only
runtime subLOD. Neutral dusty rims/tyres preserve other geometry contracts. Duplicate
film meshes removed. New shader reconstructs legacy lower-film albedo/roughness
before applying four instance levels, retains upper/horizontal finish and uses the
existing region GI corner for rebase-relative hashing. Shared macro/runoff/tile
rules remain. No source-level blocker identified in this review.

Still required: visually verified unoccluded camera/ROI identity, actual instanced
GPU seed/LOD/rebase proof, clean-case old-band absence, bonnet control at known
film state, full route Low/High stats versus fixed baseline, GIS/EditMode, two rounds,
ADR/REPORT and conflicts. Source fleet-triangle estimates are NOT visible-frame or
GPU-budget proof. Phone hold currently prevents new Unity launches.