# F / ADR 0087 — independent review WIP

Decision: NOT ACCEPTED YET. Reviewed candidate1, not a final stream report.

Actual matched baseline/candidate each contain 102 frames (17 cameras, Low/High,
clear/overcast/lowsun). Root viewed representative native/960 pairs and independently
viewed the five-way gate-step-layer-classification.png and 128/256 native board.

- Lamp state failure is real: original day DRL160000/high80000 overflow RGBAHalf.
  Candidate same-format encoding at1000nits/unit samples160/80; controlled exposed
  production decode gives16/8 at exposure0.0001. Night56/50 and OFF0 are correct.
- All102 stats rows unchanged, all source meshes/FBX and161 local node poses unchanged.
- Candidate1 OV door profile range1.57Low/2.01High still misses4. Roof14.17/15.72
  meets its distinct p99-p50 criterion. Do not replace these with radiance A/B delta.
- Glass OV median18.77Low/22.61High misses23-45; sigma5.92/5.32 remains weak.
- Actual coat/AO masks and mapped normals exist. nWS is transformed normal-map
  normal (TruckExterior line348), so a missing normal-map fix would be unjustified.
- Actual dominant-horizontal cube orientation is correct. High256 size control has
  negligible median/sigma delta and does not remove the hard gate shape. No default
  capture-size increase is justified by this test.
- Valid near-pane-off and all-pane-off controls retain the house/window/upper hard
  silhouette. This dominant boundary is transmitted scene/cab geometry, not evidence
  of near-pane cube rasterization. Do not blur real geometry to meet a presumed bug.
- Suspected new ground checker was retracted: two native control ROIs are100percent
  byte-identical to baseline. This is not a candidate regression or a new F scope item.

Next: isolated box-mip versus GGX-prefilter sampling experiment with unchanged F0,
unchanged analytic fallback, guarded actual renders after phone release, final GIS/
EditMode and geometry/budget verification, at least two reviewed candidate rounds,
ADR/REPORT with remaining limitations. Existing failed rows must remain visible.
No phone/GPU timing or final visual acceptance is claimed.
## Bounded C3 source/visual review (13:33)
Root independently viewed HighOVside and Lowclear34 native960 pairs plus all four
remaining condition sheets (LowOV, Highclear, Low/Highlowsun): all18 OFF/ON camera
views covered. Fixed3.6mm shading crown is subtle/plausible, without an obvious
inflated wave or boundary seam; RETAIN this bounded candidate. It is qualitative
WORKING_VALUE, not measured reference depth. No amplitude increase justified.
Actual6HLSL/canonicaldoor/transform GPU tests pass after replacing invalid legacy
CommandBuffer metadata readback with realURP Camera.Render. Actual pipeline mask
provesonlyDOORbit10, body/fender/trim unaffected. Keep failed firstXML as invalid
probe-path history, not a production defect or a passing test.
Owner appearance remains PARTIAL/FAIL: OV door3.32Low/2.73High stillbelow4;
Lowlowsun3.23 below4. Clear5.21Low/6.69High andHighlowsun6.04 pass. Glass unchanged.
Normal delta affects diffuse+coat together, not pure specular. Full final102,
canonical lamp probe, two focused coat-radianceOFF and fullEditMode still required.
Do not call final owner-qualityPASS merely because runtime tests/budgets pass.
## Final bounded closure verified (14:43)
Final head2086e780, validated source9a29204d. Actual final102 paired frames and
two isolated coatOFF controls reviewed; canonical Truck/Trailer/Install and lamp
GPU probe pass; EditMode238/238/0skip; GIS370/1xfail. Raw192,217source assets,
0mesh/FBX/161pose deltas,102 before-SRP estimate/counter rows unchanged.
Final OVdoor3.32Low/2.77High FAIL, clear5.21/6.67 PASS, lowsun3.23FAIL/6.11PASS.
Glass thresholds and Highclearroof2.59 remain FAIL; no owner-qualityPASS. Earlier
pending final-validation paragraphs above are superseded by this closure.
Retain bounded implementation, explicit remaining appearance limitations and
actual shader math/device timing UNVERIFIED; no further ungrounded amplification.

F2 source-only fast-fog check on main7265bd65: TruckGlass vertex stage first
stores optical depth, then fast keyword replaces it with exp(-tau). FragFast
currently lerps full haze into its additive reflection/body term and outputs
alpha=1-trans; full frag already weights haze by alpha. Before nonlinear tone,
with fog transmittance t and background B=t*S+(1-t)*H, premultiplied OVER requires
glass additive t*R+alpha*(1-t)*H: plus (1-alpha)*B yields one haze term. The old
full-H lerp yields (2-alpha)*(1-t)*H, an extra veil. Future fast correction should
multiply H by alpha and reuse i.fogFactor directly, not exponentiate it again.
This is source/algebra evidence only. KamionTone is nonlinear and applied before
blend, so do not claim exact final-image physical equivalence from this algebra.
Actual Low/Medium pane gradient/interior and matched cost remain required. No
production patch applied; D/G remain the active streams ahead of F2.