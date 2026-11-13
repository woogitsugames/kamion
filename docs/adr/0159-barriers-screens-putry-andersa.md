# ADR 0159 — P1 after the s16 world integration: barriers and screens at Putry / Andersa

Status: PROPOSED on branch `barriers-0159` (2026-11-13, s16); not merged. Numbers in "Validation" are measured on
the regenerated world of this branch; a visual-critic review is still required (a subagent may not start one).
Source: `docs/reports/visual/REVIEW-2026-11-13-s16-0146.md` (P1), `docs/reports/WORLD-INTEGRATION-2026-11-13-s16.md`
(P1 g3b-eye-s1482, M29 free deck ends 32 -> 2), `docs/reports/visual/REVIEW-2026-11-13-s16-world-int.md` (P1
regressions: turquoise cones, barriers starting in the air, yellow piers), lead request (merge and review PR #38).
Criterion: D51 (a driver recognises the place as on the photos).

## 1. g3b-eye-s1482: free W-beam end 3-4 m without a post (link road beside the SE ramp)

Cause, two parts:
- The run is `c:w173956083 R structure`, built by the rule of ADR 0110 "W-beam along a ground carriageway beside a
  viaduct / walled ramp" (E -416.2 N -71.3 ... E -388.0 N -98.1, 40 m; the ramp barrier is 4.9-8.5 m away, the
  ramp 0.9-2.6 m above the road). On the old main it ran further because the doubled retaining wall / screen of the
  ramp stood in front of the wall; since ADR 0146 the ramp is lower at its SE end (`profile_ties`) and the rule stops
  where the ramp is less than 1 m above the road (`STRUCT_GUARD_MIN_H`).
- Every turned-down terminal (4 m) had no post and ended with the beam top 0.33 m above the foot line (bottom edge
  0.02 m above it). The foot line of this run is the kerb top; over the grass behind the kerb the end hung in the air.

Evidence that there is no barrier at all on this link road: Mapillary 810525063224609 (taken at E -399 N -83.5) and
209622370971977 (E -430 N -54), both on the link road looking at the ramp (richlv 2020, CC BY-SA 4.0, reference
only): kerb, 6-9 m of grass with young trees, the block wall. REVIEW s14-0146 had listed this barrier as P2 on 810525
("na zdjęciu jej nie ma").

Decision:
- `overrides.yaml` `andersa-link-no-guardrail` (`kind: no_guardrail`, new kind): a polygon in which no RULE barrier
  is built (authored rails are not affected). `streetscape.furniture.guardrails` clears `want` inside the zones and
  reports the removed length (`guardrails_m.no_guardrail`); a zone that removes nothing is reported stale.
- Terminals, for every W-beam in the region (`furniture.guardrail`, `standards.GUARDRAIL_TERMINAL_END_TOP` = 0.12 m,
  WORKING_VALUE): the end is sunk (beam top 0.12 m above the foot line, the 0.31 m section below it), one short post
  stands in the middle of each 4 m terminal, and runs of 8-12 m (too short for two 4 m terminals, which used to get
  none and so started at full height) get 2 m terminals. This is the fix for "bariery W zaczynające się w powietrzu"
  (482392, 297817, 3970163 of REVIEW s16-world-int).

## 2. 810896: median barrier of the SE ramp

The stub of two beams of REVIEW s14-0146 was already gone after the integration (REVIEW s16-world-int: "kikut z
after4 zamknięty"). What the frame still had wrong, read off the GUGiK orthophoto 0.08 m (crops at E -462 N -62,
E -436 N -86, E -390 N -122, E -376 N -134, E -310 N -181; strip rectified along E -385.65 N -118.82 ->
E -302.6 N -184.4 at 22 px/m):

| What | Orthophoto / photo | Generated before |
|---|---|---|
| Barriers on the grass median | ONE, on the NE edge (facing the NW-bound carriageway), post dots every 2.0 m; on the SW edge a barrier only on the paved part at the abutment (to ~E -449), then kerb + 0.6 m paved strip + grass | a deck barrier (W-beam + upper beam, posts on the cap) on BOTH edges |
| NE barrier, SE end | straight on to the median nose at the fire-station opening: last post ~100.5 m from E -385.65 N -118.82, nose tip at ~104 m | ended at E -385.65 N -118.82 (end of the walled ramp + 12 m) |
| Photo 810896 (camera on the SE-bound carriageway) | kerb, paved strip, grass, THEN the barrier on posts, the other carriageway behind it | barrier on the near cap, grass behind it |

Along the SW edge the strip also shows dots every ~1.4 m from ~55 m to ~97 m (small posts or kerb joints; no rail
line): not built, UNVERIFIED.

Decision:
- `andersa-se-ramp-median-sw-no-guardrail` (`no_guardrail`): the SW edge of the median from E -450 to the end.
- `roads.meshing.build_median_fills` stores the filled stations per chain side (`meta["median_fill_s"]`);
  `guardrails` builds the barrier on that side as a plain W-beam on driven posts every 2 m (`dense`), not as the deck
  barrier with the upper beam.
- `andersa-se-ramp-median-barrier` (`kind: guardrail`, traced, `post_spacing_m: 2.0`, new field): from the nose
  E -306.72 N -181.02 to E -384.81 N -119.36; the rule run of the ramp cap is cut by the dedup and led onto it.

## 3. Last two free deck ends (M29 xfail)

Both remaining "free" ends are ends that the dedup + join of two merging decks led onto the BODY of the other rail:
`c:w177895177 L` at E 669.4 N -781.9 (0.2 m from `c:w175157461 L`) and `c:w240542867 R` at E -739.6 N 74.1 (0.2 m
from `c:w1101181473 L`, dz 0.57 m). The audit only looked for another run END within 2.5 m.
`roads.barrier_audit.find_free_ends`: an end within `FREE_END_ON_RAIL_M` = 0.6 m of any point of another run at
the same level (`FREE_END_DZ`) is continued. `deck_run_ends_free` 2 -> 0; the xfail of
`tests/gis/test_barrier_ends.py::test_no_free_deck_ends` is removed. The pair of edge-west closures (C#
`WorldEdgeBuilder`) is unchanged and stays xfail.

## 4. Noise screens (494288 right half, 810896 centre)

- Posts: `noise_post` 0.17 / 0.21 / 0.18 (pale mint in clear light) -> 0.050 / 0.058 / 0.054 linear (sRGB ~0.25).
  494288 is back-lit (posts near black), 810525 sunlit (mid grey with a green cast): one paint cannot be both; the
  value sits between. WORKING_VALUE. `test_tysiaclecia_screen_posts_are_dark` now asserts both paints are dark and
  the Tysiąclecia one is the greener.
- Sheet: the printed lines of `noise_glass_lined` (ADR 0127 / 0139, they exist on Mapillary 494288258686575) keep
  their pitch and width; strength 0.30 -> 0.10. At 0.30 they aliased into a raster between the posts on Low - a mesh
  fence on 494288 and a light fence against the trees on 810896 (dark on the photo because the trees show through).

## 5. Deck barrier of the Putry decks (494288)

`bridge_style` key `barrier: dark_rails` (set on `andersa-viaduct-putry-style`): on the deck stations the W-beam,
its posts and the upper beam are painted `noise_post` (the paint of the screen posts of the same deck - no new
material, no new draw call in the bridge chunk) and two flat rails (0.08-0.20 m and 0.25-0.37 m above the cap) close
the 0.44 m under the beam to slots of 5-8 cm. The collision face is unchanged. Rail count and heights are
WORKING_VALUE (the photo shows a dark multi-rail barrier; its members cannot be measured at this resolution).
Kerb: `BRIDGE_KERB_H` is 0.20 m (WORKING_VALUE), not the ~0.3 m estimated in the review; not changed - the photo
does not resolve the kerb height (UNVERIFIED), and with the closed dark barrier the cap no longer reads as a track.

## 6. Piers of the span (209622, 468026, 4312632, 339463, route-putry-*)

The piers ARE painted yellow: CC0 photo `7204_May_2021_in_Białystok.jpg` (Rakoon, `docs/REFERENCES.md`, the ground
truth of this viaduct) shows ochre piers under the green deck; on Mapillary 468026894483428 they are dark ochre in
the shade of the deck. "Szary beton" of the reviews is therefore not applied. What was wrong is the value: the
clear preset lights the piers with a low sun (pale yellow cylinders), while under a deck they are in shade for most
of the day. `viaduct_underdeck.json` `pier_paint.color_linear` 0.46 / 0.40 / 0.17 -> 0.253 / 0.220 / 0.094 (same hue,
x 0.55): a baked shade until an under-deck occlusion exists. WORKING_VALUE.

## 7. Block wall of the ramps (810525, 209622)

`ramp_wall_blocks` named the texture set `concrete_blocks_split`, which did not exist (flat colour). New set in
`art-source/world/materials/_src/sets_facade.py`: split-face blocks 1.0 x 0.5 m, half-bond, recessed joints 25 mm at
0.42 of the block albedo, tile 2 x 1 m, `set_tile`. Block size read off the photos against the 3.0 m screen
(WORKING_VALUE +-0.1 m).

## 8. Turquoise cones (1801374, 182011)

Garden blue spruces of the plot kit (`plot_kit._spruce_card`, three crossed cards): palette with G = B up to
72 / 96 / 94, turquoise in sun on Low. New on these frames since ADR 0132 r4b placed garden trees from the orthophoto
crowns. Palette -> grey-green with a slight blue cast, darker (up to 60 / 80 / 68). WORKING_VALUE.

## 9. PR #38 (Mistral M30, fence teeth at r16_drive_3) - merged into this branch, with one fix

- General rule, not an exception: yes - `layout()` drops a run shorter than `STUB_M` whose direction deviates from
  both frame axes by more than `SKEW_DROP_DEG` unless it starts on a gate post; no plot id, no coordinates.
- Mutation: with the rule disabled (`SKEW_DROP_DEG = 180`) the synthetic test fails; restored, it passes.
- Defect found and fixed here: a tooth joined at both ends was dropped without a replacement, leaving a hole in the
  fence line (2 m in the synthetic test; 1.14 m + 0.76 m at r16_drive_3), also on a street front (the skew test now
  precedes the `front` test). The dropped teeth that touch are chained and replaced by their chord when the chord
  lies along a frame axis, is 0.6 m ... 2 x `STUB_M` long and both its ends meet a run that is still built
  (`teeth_bridged`). The region test bound `diag == 7` became `<= 7`.
- The comment for the PR is in `artifacts/barriers-0159/pr38-comment.md`; it is NOT posted (the repository is
  public; posting needs the owner's consent, an agent message is not one).

## Validation

VALIDATION_PLACEHOLDER

## Open

OPEN_PLACEHOLDER
