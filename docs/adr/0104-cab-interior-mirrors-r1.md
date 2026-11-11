# ADR 0104 — Cab r1: interior detail and usable mirrors

Status: audit in progress, 2026-11-11. Stream K only, branch `gpt-cab-r1`, base `9e6e9fde`.

## Context

Gate 3 requires a final cab fragment and useful mirrors from the driving eye. ADR 0020 supplies live instruments;
0044 supplies the interior lighting/wear contract; 0042 supplies all six mirror views; 0045 owns the glazing; 0068
caps mirror rendering cost. Historic visibility findings are hypotheses to re-check against the current export.

The isolated checkout initially lacked the ignored LOD0 interior FBX. Copying the local truck source directories
from main restored the reproducible input; Blender `check_export.py` passes with 103285 / 44190 / 21479 triangles.
The source instrument/head-box sightline test passes. GIS baseline: 370 passed, 1 xfailed (643.87 s).

## Audit and evidence contract

- Original driver-eye cameras (`cab-driver`, `cab-dash`, left/right and mirror views) remain the acceptance views.
  Add inactive, generated `cab-seat` relative to `DriverHPoint` and `cab-materials` to expose the driver's bolster,
  seams and moulded grain. These detail views cannot establish legibility from the driving eye.
- `CabMirrorAudit.Run` writes native render textures and TSV configuration. Native images have not undergone the
  horizontal flip applied by the glass material. Record resolution, FOV, aspect, near/far, LOD scale and shared cap.
  Interval columns describe configuration; actual round-robin cadence depends on visibility and is not measured Hz.
- `mirror_sightlines.py` diagnoses obstruction on 315 samples per exterior-manifest mirror glass. It excludes
  transparent glazing and removed shell placeholders and applies the export's interior fit. Read glass-adjuster
  targets from the owning C# builder; `--include-exterior` includes opaque exterior FBX geometry in the same frame.
  This tests visibility of the glass, not the reflected R46 field or transparency attenuation. Confirm in renders.
  Initial interior-only/unadjusted check: WideR 314/315 clear, other five 315/315.
  Full adjusted baseline: MainL 315/315, MainR 312/315, WideL 265/315, WideR 236/315, Kerb and Front 315/315.
  Blockers: left wide CAB_Body 50; right wide CAB_Body 60, DOOR_R 17, interior win_channel 2.
  A solid housing face behind glass which the builder tilts by ~6 degrees is a candidate cause; inspect native
  mirror frames and the rendered glass before choosing a fix. Evidence `mirror-full-before.json` / `.log`.
- `artifacts/cab-r1/render-matrix.ps1` serializes BuildBatch, InstallBatch and Low/High × overcast/clear captures,
  using WorldC / WorldC_High respectively. It waits for both PHONE_RUN and the coordinator's GPT_UNITY_HOLD before
  every Unity launch, and restores rendering settings / ProjectSettings after each run.
- `artifacts/cab-r1/measure.py` writes full-frame sRGB statistics, matched-image absolute deltas and review sheets
  at most 960 pixels wide. Full-frame dark percentage is a diagnostic, not a substitute for checking instruments.

## Constraints

Keep ADR 0068's mirror resolution, far clips, optics, LOD/culling and shared scheduling budgets. Do not edit exterior
paint, glazing, TruckExterior.shader or TruckLights.cs. Do not use adb. No merge or push to main.

The leader's saved A16 cab frames (integration-s10, dirty APK `43bc53a769`) are auxiliary evidence only: speed and
wheel stitches can be read; the dash looks smooth; front glass is visible in the front-mirror frame. They are not
fresh editor baseline/candidate comparisons and cannot close the clean-build or device-performance gate.

## Validation still required

Fresh editor baseline, bounded fixes based on it, rebuilt candidate, inspected before/after PNGs, EditMode without
new failures, Low stats and mirror configuration comparison, independent visual review and leader phone validation.
No visual PASS or device-performance claim is made while those items remain open.
