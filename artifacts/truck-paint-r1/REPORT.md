PARTIAL OWNER QUALITY: bounded physical fixes/improvements; owner appearance thresholds still FAIL.
Branch gpt-truck-paint; validated source9a29204d (later commits docs/artifacts only); locked inputdb1432c5, C/A0101 separate.
Finite16x1RGBAHalf lamps:1000nits/unit, float scale*exposure decode; authored nits WORKING_VALUE, no new texture/pass.
ActualGPU encoded160/80/56/50/0 ->exposed16/8/5.6/5/0 finite; day/night/on-off behaviour confirmed.
Capture: real scene/radiance look-off contract+finallyrestore; angular boxmip approximation, existingGGX fallback/F0 retained.
Paint legacy stored.78/.785/.78 ->GPU.57048/.57871/.57048 times_CMap preserved; not measured physical albedo.
Coat orangePeel.012->.004 WORKING; nominalroughness.08/F0.04/basepigment unchanged. No arbitraryreflectance gain.
Fixed3.6mm/<1deg genericcrown onlyactualdoor/all3LOD; coherentdiffuse+coat; geometry/base roughness/pigment unchanged.
Finaldoor: OVLow3.32/High2.77 FAIL; clear5.21/6.67 PASS; lowsun3.23 FAIL/6.11 PASS (required4-10points).
Glassmedian/sigma stillFAIL severalconditions; actualnearT~.745/F~.082 andcorrectnear/far flags, no extraoverlay.
Near-radianceOFF OVsd10.43/7.83 vsreal5.92/5.33: additivebody/reflection cutsdisplaycontrast; noT/clutterboost.
High-clearroof2.59 FAIL onlockedC0; separate Cshoulder integration. IsolatedcoatOVdoor mean+1.28/+1.66displaypoints.
Validation: canonicalTruck/Trailer/Install+102matchedframes+2coatOFF; EditMode238/238/0skip incl6lamp+6crownGPU; GIS370/1xfail.
Proof:192rawSHA valid,217sourceassets unchanged,0mesh/FBX/161pose deltas; all102estimate/counterrows unchanged.
Budget: rows are before-SRPestimates, notGPUcalls; actualnewshaderGPUmathcost/Androidtiming UNVERIFIED.
PNG candidate3-final-960/all6conditions; truecrownOFFON candidate3-off-on-960; independentREVIEW.md retainsqualityFAIL.
References: provenancedCommonsDAF/Volvo via docs/REFERENCES.md, qualitativeonly; originalbaselinefixture immutable.
Conflicts: reservedrenderingbit10/0x400DOORsemantic keepslightbit0; TruckExterior/Glass,builder,capture,lights. No mainmerge/push/phone.
Open: unmetownerthresholds andjointC/A0101 integrationreview; no evidence-backedfurtheramplitude/T/clutter tuning.
