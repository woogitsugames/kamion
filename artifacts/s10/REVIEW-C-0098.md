# Independent review - S10 C / ADR0098

Verdict: visual/source review PASS within C scope; final EditMode completion pending.
Reviewed source9e7e0b45, all20 after contact sheets covering236frames, prior causal
shadow/glass comparisons, native and70percent floor edge/cab crops, final JSON.

Fullmatrix Highclear sky3px highfrequency RMS1.827->0.555; overcast1.198->0.615.
FinalURPdither remains, preLUTsky noise removed onlypost tiers. Bothdithersoff
was rejected for visible banding. RCAS0 adds a real softness tradeoff at floor:
paintedge2.218->2.551px, windowgradient-15percent, cabcontrast128->126 stilllegible.
The floorcheck is an effective-resolution proxy, not deviceEASU performance proof.

Highclear gable RGB254.671/243.840/212.340 ->240.836/229.444/195.223, redp95=241,
zero>=250 clipping in thisROI. This meets approximate240 target; it is not<=240.
Fixed asphalt/midgrey anchors retained; Low lighting/URP sourcepolicy unchanged,
all118LowCPUstats rows byteidentical. Low sparse foliage-edge pixel differences
remain disclosed, not asserted byteidentity.

Glass offset8cm is smallest tested acceptable value, explicitkp_glass_block only,
Medium/Highdefault, capped8cm. Realtime-only shadow ablation identifies the cause;
bakedGI untouched, shadowcasters preserved. Narrow frame shadow6.59LSB remains
versus realtimeoff; broadtriangleerror13.62->1.00LSB. Trailer/contact controlMAX0.
Highcascades keep2048/3 with reviewed splits; Medium keeps oldsplit and biasonly.

Limits: fixed4f7 preTint baseline makes causal comparisons valid, but combined
A/B/ADR0101main integration remains leader work. Do not interpret this as resolving
KP pigment calibration, remiza geometry, truck glass or parked-carblackpaint.
No phone/ADB tests or measured GPUmilliseconds. Source changes additive and
common-file conflicts RegionImporter/WorldSurface must be unioned with B/D.
Finalcanonical truckfixture rebuild is after matchedmatrix and onlyfor tests.
