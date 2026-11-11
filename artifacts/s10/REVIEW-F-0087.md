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