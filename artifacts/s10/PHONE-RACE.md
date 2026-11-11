# S10 phone rerun / Unity launch race

Observed by GPT coordinator 2026-11-11. PHONE_RUN was temporarily absent
between leader phone reruns. Existing per-launch checks therefore passed:
- B EditMode Unity launched10:43:49, finished10:44:47; a leader PHONE_RUN
  file observed afterward was created10:43:54. Six new Color test assertions
  failed; production matrix/GIS unchanged, test assertion fixed separately.
- F candidate TruckBuilder launched around10:48; leader recreated PHONE_RUN
  at10:48:21. F actual log contains TRUCK_RESULT OK, process has exited.

These windows may overlap phone measurements; do not treat overlapping runs
as uncontaminated timing proof. Leader should repeat/review those phone samples.
GPT has no active Unity now and has not used ADB/phones. Shared
artifacts/locks/GPT_UNITY_HOLD added; F/G/E check it as well as PHONE_RUN and
wait for explicit coordinator release after the phone workflow actually ends.
CPU work continues; no main source/settings were edited by GPT for this guard.

2026-11-11 18:32 G pre-import audit: canonical import-region.ps1 performs long
PBR CPU generation after the outer guard, then invokes Unity; env.ps1 has no
PHONE/HOLD guard itself. Thus an outer pre-CPU check is insufficient. ROOT
verified both source locations; G stopped only its verified own pwsh83620 and
children before any Unity launch. PHONE/HOLD remained absent, so no phone race
was observed in this attempt. Artifact-only wrapper will separate CPU and guarded
Unity launch, retaining invalidation if a marker appears and forbidding automatic
resumption after transient absence. Production scripts and main are untouched.
