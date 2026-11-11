"""One-off edit of overrides.yaml (ADR 0095): link Andersa -> Rondo Putry at the fork (s 1410-1480), P-21 band."""
import io

p = "Data/Regions/bialystok-industrial-c/overrides.yaml"
s = io.open(p, encoding="utf-8").read().rstrip("\n") + """
  # --- fork Andersa / link to Rondo Putry (route s 1410-1480; REVIEW 0093 "s 1440 strefa rozjazdu", ADR 0093 open #1)
  - id: putry-link-fork-placement
    target: {edge: "w606396463:2840742308-2840742310"}
    reason: >-
      Link to Rondo Putry after the fork (strips xsec/fork_link_raw.png along the raw OSM way, xsec/fork_link.png).
      OSM starts the link on the axis of Andersa and kinks 10 m later; the real lane starts as the right lane of
      Andersa (4.65 m right of the OSM line of the 3-lane edge, see andersa-nw-xsec-s1355-1410) and from station 177 of
      the chain runs with its kerb 2.25 m and the P-21 band 1.1-3.1 m either side of the way: carriageway 5.35 m,
      centre 0.45 m left of the way. The fork alignment held its 4.65 m shift for 40 m and faded it over 93 m, which
      put the link 4-4.8 m beyond the real kerb, on the verge and the barrier (edge_sides: left -2.8, right +5.3 m).
      center_offset / width = [[t, m], ...], t = 0 at the fork node.
    confidence: medium
    verify: owner drive
    set:
      center_offset: [[0.0, -4.65], [0.07, -2.3], [0.15, 0.3], [0.3, 0.45], [0.75, 0.45], [1.0, 0.2]]
      width: [[0.0, 3.6], [0.15, 4.5], [0.3, 5.35], [0.75, 5.35], [1.0, 6.5]]
  - id: s1440-diverge-p21-band
    kind: painted_zone
    stripe_az_deg: 4
    polygon_en: [[-386.6, -98.1], [-370.4, -109.2], [-358.5, -120.0], [-352.5, -127.5], [-354.2, -130.8],
                 [-363.9, -120.0], [-376.3, -109.2]]
    reason: >-
      P-21 band on the left side of the link beside the paved separator with the barrier, from the tip E -386.6
      N -98.1 to the nose zone s1440-diverge-p21 (outline traced for ADR 0093, crop artifacts/junctions-r1/trace/
      z_s1440_o.jpg; not built then because the generated link was narrower and displaced). Stripes about 49 deg to
      the direction of travel (xsec/fork_link_raw.png).
    confidence: high
    verify: owner drive
"""
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
