# JRG2 r7 — technical validation
- Branch `gpt-firestation-r7`; baseline `901c427f`; 160 before + 160 final frames (40 cameras × Low/High × clear/overcast), all 20 final contact sheets inspected.
- Asset LOD0/LOD1/Far: 9344/2828/164 triangles, 3/2/1 slots; near Low can select LOD0. Rooted CC0 fir cards, +4m foreground placement, three irregular thuja forms.
- High-quality-only hero leaf runtime copy; Low remains URP Lit even at LOD0. Factory reimport byte-idempotent, source asset unchanged; global hedge palettes preserved.
- Brown clinker, sparse flashing runoff; existing splash/vents/flag retained. Protected source-atlas texels (D48 plaster/roof/trim/office/flag) and nine auxiliary PBR maps preserved; not all scene pixels.
- 80 Low and 80 High matched stats: maximum per-view delta 0 drawEst / 0 ktri. Peaks unchanged: Low 968 / 487k, High 1778 / 2476k. Extra High depth-pass GPU/timing cost UNVERIFIED.
- Latest-product GIS: 375 passed, 1 xfail (517.58s); all 784 pins unchanged, including 192 raw files and canonical vehicle. Target NUnit: 1/1 PASS (two factory imports, Low→High→Low).
- Full EditMode PENDING renewed explicit ROOT release after PHONE hold; no Unity queued. Technical DoD remains incomplete.

# Appearance goals and limits
- Glass overcast mean Y: Low 63.42–66.81 / High 70.12–73.24, PASS 60–75. Clear: 81.83–96.76 (round pane ~98), FAIL; no collective appearance PASS.
- Thuja 15 paired interior ROIs: median High/Low ratio 1.0889 overcast / .9945 clear; coherent hue, no exact all-crown equality claim.
- Conifers remain narrow/column-like versus photo7197; runoff subtle. Coarse alpha-mip differences disclosed; device/temporal shimmer unverified.
- 17 vehicle-relative views have limited causal parity; some show background/framing shifts. Canonical asset SHA equality does not prove scene-pose parity; fixed hero views remain relevant. See `VEHICLE-CAMERA-AUDIT.md`.
- Proof: `round2/`, `round2-sheets/`, ROI/paint/thuja metrics, `actual-alpha-mips/`, `SELF-REVIEW.md`, independent High review; ROOT final Low review pending.
- CC0 Fir inputs are SHA-pinned and packaged in ignored `source-cache/`; run `restore_cc0_inputs.py` after artifact copy. No merge or push.
