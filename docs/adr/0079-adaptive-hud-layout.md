# ADR 0079 - Adaptive HUD layout for 1:1 … 21:9 screens and foldables

Status: proposed (gameplay-ui), 2026-11-10. Phone verification UNVERIFIED (no adb used by this agent; the owner's
Galaxy Z Fold inner screen and the A16 are the lead's check). Supersedes the fixed 1920×1080 height-matched layout of
the driving HUD, the control-settings panel, the start menu and the diagnostics overlay. D39 (developer panel stays in
the APK) is kept.

## Context (owner report, screenshots from the Fold's inner screen, about 1.1–1.2 : 1)
- Every canvas used `CanvasScaler` 1920×1080 matched by HEIGHT. On a near-square screen that gives a canvas of only
  ≈ 1297 × 1080 units (2176×1812 px), while the layouts needed 1900+ units of width: the 620-unit developer button
  grid, the 560-unit readout + warning strip and the mirror insets (±460 from the centre) all landed on the same
  pixels; the settings panel (1520 units wide, fixed) was cut on both sides.
- Because the scale followed the height, the controls also grew with the screen: the same wheel, pedals and gear rows
  were ≈ 1.76× larger in millimetres on the Fold than on the phone and reached 57 % of the screen height (right group
  616 of 1080 units, left group 590) - "about half of the view".
- Positions were fixed offsets from different anchors (top centre, top right, bottom left/right); nothing checked that
  the groups do not meet.

## Decision
1. **One scale rule for every screen-space canvas** (`Game.UI.Layout.UiScale`, pure maths): canvas units follow the
   SHORTER side of the safe area and the physical size, not a fixed pixel count.
   `shortUnits = clamp(1080 · (shortSide[in] / 2.8)^0.6, 1080, 1700)`; unknown DPI → 1080. Then at least 1680 units of
   width are guaranteed (near-square / portrait-ish screens get a smaller pixels-per-unit instead of a narrower canvas).
   The reference phone (1080 px, ≈ 2.8 in short side) keeps 1 unit = 1 px, so the A16 layout scale does not change.
   Exponent 0.6, 2.8 in, 1700 and 1680 are WORKING_VALUES (to tune with the owner on the Fold). `Screen.dpi` on the
   target devices is UNVERIFIED; the clamp bounds a wrong DPI to a layout that is still valid (tests run DPI 0, 160,
   nominal, 640).
2. **`UiViewport`** (one per canvas): applies that scale (`CanvasScaler` in constant-pixel mode) and the safe-area
   rect; `Refresh()` is polled every frame (a few float compares, no allocation) and reports a change of pixel size,
   safe area or DPI - rotation, folding / unfolding, split screen. `OnRectTransformDimensionsChange` only invalidates.
   Tests and captures can pin a device screen (`OverrideScreen(pixels, safeAreaPx, dpi)`).
3. **HUD = zones placed by a pure solver** (`Game.UI.Driving.HudLayout.Solve`, structs in / out, no Unity objects, no
   allocation). It runs only when the viewport or the HUD state (gyro, developer panel, telemetry, mirror insets,
   reversing view, developer text) changes. Zones never overlap and always lie in the safe area:
   - top centre: ONE cluster 440×156 (speed, gear, parking brake, rpm bar; ABS / STOP / HS / RET lamps and both
     circuit pressures in a strip) instead of readout 560×150 + warning strip 560×92 (−49 % area); the mirror insets
     flank it; parking-brake warning and reversing view below it in the same column;
   - top right: one developer button (150×60). Its panel (2×5 buttons, 424×378) drops down under it and collapses
     again; the lab page (spawn presets, ABS fault, reversing camera, mirror insets) replaces the grid in place;
   - top left: telemetry (developer), width = the free column, text wraps;
   - bottom left: wheel 400 (was 440) or gyro panel, turn signals above, retarder stalk 104×376 beside;
   - bottom right: throttle and brake pedals unchanged in travel (360 / 300 units), gear selector BESIDE them (R N D /
     + − A/M / parking brake) instead of two rows above: the group tops out at 392 units instead of 616;
   - bottom centre: developer status / coupling text (was top left, over the horizon).
   Low zones cover the dashboard in the cab view, not the road - a simulator HUD, not a mobile-game button wall.
4. **Developer overlays yield nothing to the driver, the mirror insets yield to them**: when the open developer panel
   or the telemetry panel does not fit beside a mirror inset (narrow canvases), the panel first moves under the inset
   when the screen is tall enough (near-square foldables); otherwise that inset is hidden while the overlay
   is shown and comes back when it closes. While driving (no overlay) both insets are always shown.
5. **Settings panel** always fits the safe area: two columns when ≥ 1520 units are available, otherwise one; rows
   scroll (ScrollRect, slim position bar) between a fixed title and a fixed footer; rebuilt on a viewport change.
   **Start menu / diagnostics overlay** use the same viewport (their 1600-unit block fits the 1680 minimum).

## Consequences
- Fold inner screen (2176×1812, nominal 368 dpi): canvas 1819 × 1515 units; right control group tops out at 26 % of
  the height (was 57 %), left at 33 % (was 55 %), cluster bottom 12 % from the top (was 25 %).
  Numbers from `HudLayoutTests` (solver), editor; on-device look UNVERIFIED.
- Phone 21:9: same scale as before; wheel 9 % smaller, gear buttons moved beside the pedals, developer buttons one tap
  further away (Menu is still also the Android back key). Thumb reach of the gear column needs the owner's feel test.
- Portrait is still not a supported orientation (player settings: landscape only); the solver is nevertheless valid
  there (tested), nothing overlaps if a device ignores the lock.
- `Editor/VisualQA/VisualQaRunner.cs`: one line (`hud.RefreshNow()` before the UI render) so control-camera captures
  lay out for the capture size. Existing control-camera references with the HUD need a re-render (layout changed).
- No change to ProjectSettings, packages or asmdefs. Tests live in the PlayMode assembly (the EditMode test assembly
  does not reference `Game.UI`).

## Verification
- `Game.Tests.HudLayoutTests` (PlayMode): solver over 2400×1080, 2340×1080, 2176×1812, 1968×2184, 2560×1600 (and
  1080×2400) × 4 DPIs × with/without cutout × 128 states, plus an aspect sweep 0.45 … 3.2; the real uGUI rects of the
  HUD equal the solved zones and every graphic stays in its zone; settings panel and start menu inside the safe area;
  relayout on a screen change; developer panel collapsed by default.
- Captures: `artifacts/hud-r10/<device>-{1-driving,2-dev-panel,3-dev-everything,4-settings,5-menu}.png`
  (explicit test `HudLayoutTests.Capture_AllDevices`).
