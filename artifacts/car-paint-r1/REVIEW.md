# G / ADR0089 — final independent review

Decision: SCOPED VISUAL/TECHNICAL PASS. Device GPU time and combined-main integration remain UNVERIFIED.

Root independently viewed ALL28 finalR3 contacts (324 frames, Low/High clear/overcast), allfour focused dirt-level sheets, native HighOV/Lowclear wheel before/after pairs, and earlier control/Pearl evidence. No new scoped regression found. FinalR3 removed rejectedR2 block/camouflage edges; clean0 survives, clear0..3 levels visibly differ, overcast variation is subtler. No floating opaque overlay strip.

Evidence independently parsed: final-editmode.xml231/231 passed,0failed/0skipped; fullGIS375passed/1knownxfail575.12s. Final-source actual Graphics.RenderMeshInstanced proof uses1007 imported matrices: CPU/GPUcounts253/273/226/255, maximumlevelerror0.0,18actual3LOD/origin cases incl+/-4096. Source shaderSHA b0e4510b5046cfd52ca80fc9a72242173466773d75a109bc863ecc9b25697a17 matches final proof. This is a numeric D3D12 contract test, not A16 timing.

Fresh baseline already met blackdoor goal (HighOV38.672/LowOV34.144). No floor/pigment lift. Isolated Pearl Color/HDR correction was GPU-proven with original film unchanged, and is independent of A Tint. Final door39.840High/35.226Low stays30-40. Pure bonnet78.697/71.638 equalsR1 after the Pearl correction; original pre-Pearl81.017/74.221 is kept as a separate baseline, not falsely called unchanged. Actual small dirt overlap in the original door ROI is disclosed.

Close wheel: smoother22-segment existingLOD0 outline, neutral dusty rubber/rim and dark dish. ExistingLOD0 range is25mLow/37.5mHigh, not a new8m-only subLOD; LOD1 remains10. Native wheel still stylized at2m, disclosed as a limit. Existing-prototype skin overlays removed. Four levels derive per actualinstance with rebase-stable GI-relative hashing and existing texture modulation, no added texture sample/material split.

Budget: strict59route cameras x4conditions =236 matched rows. Low drawdelta-23..0, roundedtrisK-2..0; High-42..0/-3..0. CPU before-SRP estimates, not GPUmilliseconds. All192raw hashes,15Fab-ready/fallbackFalse and90 canonical vehicle fixtures preserved. Source all-LOD0 fleet savings30000tris are separate from visible-frame counts.

Pairing:73original cameras have before/after; eight extra views are AFTER-only diagnostics. The historical car_lod/glass_front cameras can be occluded/invalid (some show trailer/body); they are retained regression frames, not wheel/LOD/glass proof. Current valid2m wheel and explicit numeric3LOD proof support claims. No world placements changed. White-van clipping and opaque car-glass/model detail pre-exist and are not solved here.

Integration: union CARPAINT-only WorldPBR changes and linearPearl helper with A/B/C/D and leader changes; preserve _Tile=set_tile||elementScan||atlas, weather||runoff, macro/panel/splash. No main merge/push, phone or ADB action by this worker. Reviewed implementation is ready for leader integration with these limits.