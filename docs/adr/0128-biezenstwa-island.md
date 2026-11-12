# ADR 0128 — kerbed nose with the crossing landing and D-3 / D-6 at the northern slip of Rondo Bieżeństwa; U-4a on the Andersa island nose

Status: implemented on branch `biezenstwa-island` (base `junctions-r6` 21aef33f, 2026-11-12); not merged. Gate 3 is NOT
re-judged here (visual-critic).
Source: `docs/reports/visual/REVIEW-2026-11-11-s11-sbs-r1-D51.md` (#11: no D-3 / D-6, no crossing landing, "grass
island"), `REVIEW-2026-11-12-s11-0125.md` (open blocker 2; P2: chevron board ~5 m off), owner decision D51.

## Findings (measured before anything was changed)

Two different places were mixed under "island at the roundabout":

| Item | What the data says |
|---|---|
| D-3 / D-6 stale at Rondo Bieżeństwa, northern slip (frame G3-A 320326319617139) | The generator closes the corner between the slip road and the ring carriageway that turns under the viaduct with a 12 m kerb return (`j:n1882953899` corner2, road face from E 529.8 N -686.2 to E 533.1 N -701.2). On the ground both kerbs run straight to a pointed nose. GUGiK 0.08 m orthophoto (WMS HighResolution, cell c_12_02 fetched for this ADR): light kerb band along the slip from the zebra end (E 537.1 N -690.0) to E 540.6 N -691.9 +- 0.5 m, where a dashed edge line starts; two blue sign plates at E 537.2 N -690.7 and E 539.1 N -692.1. Mapillary 320326319617139 (richlv 2020): gravel nose with weeds between two kerbs, D-3 near the tip, D-6 beside the crossing, paved landing with a yellow tactile slab. The generated zebra (E 533.5-540, N -682..-689) already matches the orthophoto (E 533.6-539.7, N -681.5..-689.6); it only ended on asphalt. |
| Photo geometry of 320326319617139 | Zenith vanishing point of the two posts -> pitch 18.3 deg, roll 2.6 deg; vertical FOV 73.74 deg (f = 700 px at 1400 x 1050); horizon from the bus (3 m tall) -> camera 0.9 m above the road (WORKING_VALUE). Post bases on the ground plane: D-6 3.9 m ahead / 1.25 m right, D-3 2.8 m ahead / 1.0 m left, 2.5 m apart (orthophoto: 2.4 m). Kerb lines: 290 deg (slip, generated axis 297) and 217 deg (ring side; nose -> start of the generated ring kerb = 218 deg). Anchored on the zebra corner the camera stood at E 541.5 N -690.4, heading ~244 deg: the SBS pose (E 538.2 N -687.8, heading 241, eye 1.6 m, WORKING_VALUE) is ~4 m off, from there both signs are left of the frame. |
| "Chevron board 5 m too far, island ends too early" at Andersa / side street (frames G3-B 381800493259507, 837235577143499) | The 0.08 m orthophoto (cell c_06_06) has the kerbed island nose at E -219.6 N -235.3, exactly the authored island `n10015785253-island`, with the P-21 triangle down to E -216.3 N -238.7. E -217.3 N -240.3 (ADR 0125, read on the 0.25 m sheet) is worn paint on the carriageway. Because that point is on the carriageway the sign was snapped 5.4 m - to the far verge of the slip lane (E -212.0 N -239.1), the wrong side of the lane. The island does not end too early; the sign position was wrong and islands (which lie on the carriageway footprint) were not a valid place for a sign. |

## Decision

1. **Authored island, not a generator rule.** `kind: traffic_island` `biezenstwa-n-slip-nose` (36.9 m2): the two real kerb
   lines, a 0.6 m nose radius (WORKING_VALUE) and, on the verge side, the road face of the generated kerb return
   pushed 4 cm into that kerb (no asphalt sliver, same kerb height 0.13 m). The 12 m kerb return itself is left alone:
   the junction generator belongs to the parallel ADR 0123 stream, and a per-corner radius would still not give the
   gravel / paving surfaces. The polygon carries coordinates of build b5 - re-trace if the generator moves that kerb.
2. **`patches` on `traffic_island`** (roads/gores.py): `[{surface, polygon_en}]` gives parts of the island top another
   surface inside the one kerb ring. Here: `island_gravel` nose (the material of the centre island) + a
   `sidewalk_paving` landing of the crossing. Collision follows the surface.
3. **Signs may stand on authored islands** (streetscape/gate3_landmarks.py, one call argument in stage.py): a
   `gate3_sign` whose authored point lies inside a built island stays there, on the island top (`Island.top_z`), instead
   of being pushed off the carriageway footprint; QA reports `island: <id>`.
4. **Data**: D-6 at E 537.3 N -691.0, D-3 at E 539.3 N -692.4 (mean of orthophoto plate and photo geometry, +- 0.7 m),
   bearings 297 / 285 deg, lower edges 2.4 / 2.5 m (photo geometry, WORKING_VALUE); U-4a moved to E -219.9 N -234.75,
   0.6 m behind the orthophoto nose.
5. `tests/gis/test_gate3_landmarks.py`: `stale` must be empty; signs on islands are not snapped; new synthetic test of
   the patches in `tests/gis/test_gores.py`.

## Result

RESULTS_PENDING

## Not done / open

- The footpath continues SSW under the viaduct from the landing (photo); the generator has verge there. Not built.
- W-beam along the ring-side kerb from ~7 m behind the nose (E 536.3 N -697.2, photo geometry) and the barrier along
  the slip west of the zebra (frame 482392746429891): barrier stream (ADR 0123).
- Yellow tactile slab at the crossing, the second blue sign at the right edge of the frame (unreadable), the dashed
  edge line from the nose (3 dashes on the orthophoto): not modelled.
- SBS pose of 320326319617139: the probe pose above is evidence only (`artifacts/biezenstwa-island/cams_sbs.json`,
  id `sbs-g3-a-p0128-320326319617139`); promoting it is the SBS stream's decision.
- Pier rows under the deck next to the nose do not match the frame (nearest pair ~12 m from the camera): ADR 0123.
- Phone measurement: none (no APK in this round).

## Evidence

`artifacts/biezenstwa-island/`: `ortho/` (0.08 m crops `bz_hr7.jpg`, `and_hr7.jpg`, lifted shadow `bz_hr9g.jpg`),
`ortho_hr/` (2 cells + manifest, GUGiK WMS HighResolution, reference only), `plan_b5/` (before) and `plan_<tag>/`
(after) plan views, `renders_<tag>sbs_low_{overcast,clear}/` + `stats.txt`, `pairs_<tag>/` (photo | before | after),
`logs/`.
