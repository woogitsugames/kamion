# S10 F / ADR0087
- Step1: read current F contract, owner glass decisions D31/D34/D44, ADR0059/0083 and project rules. Branch gpt-truck-paint at232fbada; A completed separately38149050. No source changes yet.
- NEXT COMMAND: git lfs checkout; copy ignored local sources/caches, read-only junction raw source folders, audit gitdiff, then fresh world build/import and canonical truck/trailer build/install before baseline.

- Step2: copied private Data/raw derived+cc0, CC0raw, Fab products, Unity Generated/Library, photos and PNG/NPY/NPZ material caches only. Read-only-use source junctions created. gitdiff clean. Missing ignored interiorLOD0 FBX SHA177d820ebe99b45b359789469107eaa498198e679a851a24db912ebd2a2930fe copied from main.
- NEXT COMMAND: uv run --project tools/worldgen python tools/worldgen/roads/build_world.py --region bialystok-industrial-c; then import-region +canonicalTruck/Trailer builders/install, snapshot and baseline6conditions.

- Step3: added isolated QA round17cameras x6conditions with exact LowWorldC/HighWorldC_High, actual TruckExterior Color GPU probe, true no-pane reference (disable GLASS_ renderers, not old partial qaNoGlass), and coat-off diagnostic. Canonical snapshot will preserve every GeneratedTruck/Trailer file plus raw192SHA and actual nested FabQA. No production shader/material changes. C confirms no vehicle edits; future clear-shoulder integration review remains separate.
- NEXT COMMAND: pwsh -ExecutionPolicy Bypass -File artifacts/truck-paint-r1/prepare-baseline.ps1 (queued after current world build); snapshot_fixture.py; run-round.ps1 before; run-baseline-ablations.ps1.

- Step4: root authorized merge latest main into F before any baseline captures. Stopped only verified own build_all PythonPID42312 while no Unity was active; no vehicle production edits/no baseline images. Fresh321.6s old-base world metadata persisted as WIP only.
- NEXT COMMAND: git merge main --no-edit (into F only); regenerate world and all PBR from merged sources, then canonical builders/install, raw192SHA/Fab15+320 proof and snapshot before baseline.

- Step5: merged main db1432c5 into F atf52fabf6 before captures; fresh fullPBR+world regeneration running from A-correct sources. Source diagnosis being tested: DRL160000/high80000 encoded directly in RGBAHalf(max65504) may overflow. Probe now records actual GPU texture sampling day/night/on/off alongside Color upload, before production edits.
- NEXT COMMAND: wait fresh PBR/world completion; prepare-baseline.ps1; snapshot_fixture.py; baseline102PNG plus no-pane/no-coat diagnostics.

- Step6: A-correct world finished339.5s; fullPBR near completion. Baseline preparation queued with per-Unity phone guards, canonicalTruck+Trailer+Install, shader/light GPU probe, immutable Generated snapshot including production sourceSHA then102matched images. Actual lampGPU and day/night state evidence pending; no production fix assumed.
- NEXT COMMAND: inspect baseline-prepare-a-correct.log and baseline-fixture-proof.log; then resize/view before102 and measure no-coat/no-pane references.

- Step7 CHECKPOINT: baseline102PNG complete (17cameras x6conditions), before-960 all12sheets inspected;3provenanced Commons cab photos inspected. Canonical217source/564Generated files snapshot immutable;192rawSHA verified, actual nested Fab15available/320props/954drains. GPU proves DRL/high state=Infinity in RGBAHalf; nightDRL56000/low50016/highOFF0, auto day/night correct. Baseline render exited-1073741819 only after OK102+mono cleanup;102freshframes verified with same ADR0083 acceptance as standardwrapper.
- Step8 CHECKPOINT: INVALID first before-no-pane rejected: Rig.Apply reset enabled=false. before-no-pane-fixed uses forceRenderingOff, afterrender assertions; retains initial invalid files for audit but excludes metrics. before-no-coat changes underlyingbase roughness, so is not isolatedradiance. before-coat-radiance-off GENERATEDshader changes only env*Fc+direct;3transient materials restored in finally and productionSHA identical. Separate before-near-pane-off removes only measured windscreen, retaining far door panes; all-panecontrol retained to show empty-cab confound.
- Step9 CHECKPOINT: read original owner D30/D35 metric implementation in prior paint-glass-r7/measure.py: door verticalprofile range, roof p99-p50 (not radianceABdifference). Baseline overcast roof15Low/16High alreadymeets; door1.5Low/1.9High below4. ClearHigh roofclip83.5percent belongs separate C integration; no gain trick. GPU direction sampling confirms realcube up~1.28 vsdown~.145, so no guessed cubefaceflip.
- NEXT COMMAND: collect before-near-pane-off metrics with both references; implement normalizedHalf lampcodec +float pre-exposure decode, measured local coat-roughness experiment and physically ungraded capture; rebuild canonical assets/install and render candidate1 against immutablebefore. Root C/A-r2 remain separate inputs.

- Step10 candidate1: confirmed finite-range fix uses1000nits/unit in same16x1RGBAHalf and float decode*exposure, with6meaningful day/night/on-off/actualGPU tests. Local WORKING experiments: OrangePeel.012->.004 (F0/coatenergy unchanged), physical capture bypasses Low scene toe and restores globals in finally, windscreenT1.0 with doorT.42/farclutter.35 retained, mildcapturefootprint filter and premultfog. Baselineall102 immutable; prior0059 aquarium rejection is explicit visual gate for this experiment.
- NEXT COMMAND: canonicalTruckAssetBuilder+TrailerAssetBuilder+WorldTruckInstaller, run candidate1 sixconditions, lampGPU readback, matchedD30/D34/D44 and nativeheadlamp/glass checks. Reject or refine based on actual images.

- Step11 PHONE_RUN: leader phone lock observed before any candidate Unity launch; all F Unity held. Added GPU exposed-lamp readback at controlled exposure0.0001 (dayDRL/high/nightlow/nightDRL/off), restoring previous globals in finally. Candidate rebuild wrapper checks/waits PHONE_RUN before each of4Unity steps and capture. Six regression tests added; baseline cache untouched.
- NEXT COMMAND: pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/truck-paint-r1/rebuild-candidate.ps1 -Round candidate1 (waits for lock release before launching Unity); then measure/inspect candidate102.

- Step12 PHONE WINDOW: observed transient leader lock gap: candidateTruck launched only after PHONE_RUN absent, then lock recreated. Initial licencewarnings recovered; actual TRUCK_RESULT OK, no compile/shader errors. No F Unity remains. Stopped only own waiting PowerShellPID73772 before Trailer. ROOT explicitly holds Unity until release; added shared GPT_UNITY_HOLD alongside PHONE_RUN in every F launch wrapper. No further launch until explicit root message. Baseline remains immutable.
- NEXT COMMAND AFTER ROOT RELEASE ONLY: pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/truck-paint-r1/rebuild-candidate.ps1 -Round candidate1; until then CPU metrics/ADR preparation.

- Step13 CPU-only during explicithold: ADR0087 WIP records measured Infinity, diagnostic validity, exact baseline and separate A/C integration caveat; no visual or performance PASS asserted. measure_contract.py reproduces owner legacy1024 metrics plus native rawROI counterpart and placement proof.
- NEXT COMMAND: wait explicit ROOTrelease (bothlocks absent); resume rebuild-candidate.ps1, then candidate102 inspection and quantified acceptance/refinement.

- Step14 CPU source-review followup: explicitly documented legacy serialized Paint/Decal/Dirt Color encoding without changing any values. White stored.78/.785/.78 ->actualGPU multiplier.5704816/.5787147/.5704816, then_CMap; not physical linear albedo. Dirt stored.15 ->GPU.01960665. Builder comments and ADR corrected; no broad gamma conversion. Shared Unity hold remains active, no launch.
- NEXT COMMAND: wait explicit ROOTrelease; resume guarded candidate rebuild/render.

- Step15 CPU binary proof: candidateTruck first build changes0mesh/FBX files and0semantic hierarchy/local-pose values (161nodes before/after); prefab byte churn is fileID reallocation.16current changedfiles are material values+prefab only. Narrowed OrangePeel experiment toPaint slot so nonpaint unused fields stay legacy. Corrected encoded-unit comments. No Unity launched; repeat this proof after full final canonical rebuild.
- NEXT COMMAND: after explicit ROOTrelease and bothlocks absent, resume rebuild-candidate.ps1 candidate1; then compare_fixture.py candidate1 and measure_contract.py candidate1.

- Step16 durability: copied current baseline/refs/diagnostics/immutablefixture and sourceproof to main artifacts/truck-paint-r1 using /E /XJ (no sources/main commit touched). Production consumer audit: only TruckExterior samples state texture; trailer shares it; existing indicator UI test threshold remains valid at encoded25. Final runtime/visual tests still pending explicit release.
- NEXT COMMAND: wait explicit ROOTrelease; verify PHONE_RUN and GPT_UNITY_HOLD absent; rebuild-candidate.ps1 candidate1.

- Step17 CPU reproducibility check: pinned asphaltphoto already present in initial F privatecopy; verified SHAe26237d85c097af9560537c60e6ed6f67ed0090e284398a5d7a7a2bf41889135 per coordinator. No raw copy/regeneration and no locked generated map changes; proof asphalt-input-proof.json. Unity hold continues.
- NEXT COMMAND: wait explicit ROOTrelease; then verify bothlocks absent and resume guarded candidate1.

- Step18 resume: explicit ROOTrelease11:56:56 after stable phone-window end. Bothguards independently absent, branchba61eec7 clean. Candidate wrapper now stops rather than auto-resumes if either guard returns.
- NEXT COMMAND: pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/truck-paint-r1/rebuild-candidate.ps1 -Round candidate1; then actual102PNG/metrics/GPU evidence and refinement.

- Step19 actual candidate proof: canonicalTruck/Trailer/Install allOK after explicitrelease. GPUactualRGBAHalf nowDRL160/high80/night56/50/off0 finite; productionshaderdecode at controlledExposure0.0001 yields16/8/5.6/5/0. Allstateflagsday/night correct.102candidate frames in progress (Low51done), no visualPASS claim.
- NEXT COMMAND: preview.py candidate1; measure_contract.py candidate1; compare_fixture.py candidate1; render fresh candidate1-near-pane-off, inspect full102 and rootreview before finaltests.
