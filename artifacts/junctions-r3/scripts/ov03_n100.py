"""One-off edit of overrides.yaml (ADR 0095 step 1b): side-street junction at n10015785253 (island, P-21, lanes)."""
import io

p = "Data/Regions/bialystok-industrial-c/overrides.yaml"
s = io.open(p, encoding="utf-8").read()
a = s.index("  - id: andersa-nw-xsec-n10015785253")
b = s.index("  - id: ", a + 10)
s = s[:a] + """  - id: andersa-nw-xsec-n10015785253
    target: {edge: "w1093579589:2359253621-10015785253"}
    reason: >-
      Andersa NW-bound at the side-street island (strip xsec/and5.png station 0-20, crop trace/n100_o.jpg): median
      kerb 4.4 m, lane line 0.2 m, solid edge line 3.25 m on the other side of the OSM way: TWO through lanes. The
      third lane of the neighbouring edges ends here as the right-turn lane and starts again as the merge lane; between
      them lie 1.9 m of asphalt, the P-21 fields and the kerbed island (carriageway to 11.0 m from the median kerb).
      REVIEW 0093 P0-L: the generated median ran to zero here because both carriageways were 11.5 m centred on ways
      drawn 1.1-1.3 m towards the median.
    confidence: high
    verify: owner drive
    set: {center_offset: -1.1, lane_edges: [0.5, 4.2, 7.65], width: 11.0, edge_lines: right}
""" + s[b:]
a = s.index("  - id: andersa-nw-xsec-s1080-1210")
b = s.index("    set:", a)
e = s.index("\n", b)
s = s[:b] + "    set: {center_offset: -1.2, lane_edges: [0.7, 4.2, 7.7, 11.05], turn_lanes: \"through|through|right\"}" + s[e:]
s = s.replace("""      3.5 / 3.5 / 3.35 m, 11.05 m, centre 1.2 m right of the way.
""", """      3.5 / 3.5 / 3.35 m, 11.05 m, centre 1.2 m right of the way. The right lane is the right-turn lane into the
      side street at n10015785253 (wide broken line from station 60, solid from 108, arrows; it ends at the island),
      OSM has no turn:lanes here -> turn_lanes.
""")
s = s.rstrip("\n") + """
  # --- side street at n10015785253 (REVIEW 0093 P0-L / 0076 #1): crop artifacts/junctions-r2/trace/n100_o.jpg (2 m grid)
  - id: n10015785253-side-street-throat
    target: {edge: "w227212660:5202512922-10015785256"}
    reason: >-
      Side street at its junction with Andersa (strip xsec/n100_side.png): 7.3 m kerb to kerb (4.0 m / 3.3 m either
      side of the OSM way; OSM lanes=2 gave 5.0 m), flaring to about 16 m at the crossings where the two slip lanes
      (OSM w1093579592 / w1093579593, absorbed into the junction plate by the generator) pass either side of the
      island. width = [[t, m], ...] along the edge, t = 1 at the junction.
    confidence: medium
    verify: owner drive
    set:
      center_offset: -0.35
      width: [[0.0, 7.3], [0.6, 7.3], [0.8, 9.5], [1.0, 16.0]]
  - id: n10015785253-island
    kind: traffic_island
    surface: sidewalk_paving
    polygon_en: [[-223.1, -232.3], [-222.25, -231.3], [-221.25, -230.6], [-218.6, -228.7], [-216.25, -226.8],
                 [-215.45, -227.0], [-215.25, -227.65], [-216.75, -229.7], [-218.25, -231.7], [-219.2, -234.2],
                 [-219.6, -235.3], [-221.25, -234.2], [-222.95, -233.0]]
    reason: >-
      Kerbed paved island between the two slip lanes of the side street (refuge of both crossings), traced on the
      0.08 m orthophoto.
    confidence: high
    verify: owner drive
  - id: n10015785253-p21-west
    kind: painted_zone
    stripe_az_deg: 11
    polygon_en: [[-226.75, -230.45], [-221.5, -229.5], [-221.1, -230.3], [-222.3, -231.1], [-223.2, -232.1]]
    reason: P-21 west of the island (between the merging slip lane and the Andersa edge line).
    confidence: high
    verify: owner drive
  - id: n10015785253-p21-east
    kind: painted_zone
    stripe_az_deg: 5
    polygon_en: [[-219.1, -234.3], [-218.1, -231.9], [-217.25, -232.95], [-216.75, -234.95], [-216.3, -238.7], [-219.5, -235.5]]
    reason: P-21 south-east of the island (between the Andersa edge line and the slip lane that leaves it).
    confidence: high
    verify: owner drive
  - id: n10015785253-p21-north
    kind: painted_zone
    stripe_az_deg: 42
    polygon_en: [[-216.25, -226.6], [-212.5, -223.6], [-215.0, -227.3]]
    reason: P-21 north of the island tip, between the two slip lanes.
    confidence: high
    verify: owner drive
"""
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
