"""One-off edit of overrides.yaml (ADR 0095): n10015785253 solid line from the lane geometry, fork separator island."""
import io

p = "Data/Regions/bialystok-industrial-c/overrides.yaml"
s = io.open(p, encoding="utf-8").read()
a = s.index("  - id: n10015785253-edge-line-clear")
b = s.index("  - id: n10015785253-crossing-west")
s = s[:a] + """  - id: n10015785253-edge-line-clear
    kind: paint_clear
    polygon_en: [[-197.9, -256.3], [-215.0, -242.7], [-231.5, -230.1], [-248.7, -216.3], [-249.5, -217.3],
                 [-232.3, -231.1], [-215.8, -243.7], [-198.7, -257.3]]
    reason: >-
      The generated broken lane line 2|3 on the approach and across this junction plate; on the orthophoto it is one
      solid line from station 108 of w1093579590 to station 22 of w266084693 (next override).
    confidence: high
    verify: owner drive
  - id: n10015785253-edge-line
    kind: painted_line
    line: P-2b
    smooth: false
    polyline_en: [[-198.3, -256.8], [-215.4, -243.2], [-231.9, -230.6], [-249.1, -216.8]]
    reason: >-
      Solid 0.24 m line on the right edge of the two through lanes of Andersa before, across and after the side-street
      junction (strips xsec/and2.png stations 108-119, xsec/and5.png, xsec/n100_w266.png stations 0-22): 3.4 / 3.25 /
      2.9 m right of the three OSM ways = the lane boundary 2|3 of the measured cross-sections. (A first trace on the
      crop trace/n100_o.jpg put its SE end 3 m off, on the kerb line: superseded by the strip measurements.)
    confidence: high
    verify: owner drive
""" + s[b:]
s = s.rstrip("\n") + """
  - id: s1440-diverge-separator
    kind: traffic_island
    surface: sidewalk_paving
    polygon_en: [[-346.2, -138.1], [-346.4, -137.3], [-362.3, -121.7], [-382.2, -102.2], [-383.0, -103.0],
                 [-363.1, -122.4], [-347.1, -138.0]]
    reason: >-
      Paved kerbed separator with the barrier between Andersa and the link to Rondo Putry, 1.1 m wide, from the nose
      at station 173 of the link chain (xsec/fork_link_raw.png: 3.25-4.3 m left of the OSM way in the direction of
      travel) for 51 m to NW.
    confidence: medium
    verify: owner drive
"""
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
