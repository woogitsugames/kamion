"""One-off edit of overrides.yaml (ADR 0095 step 1a): measured Andersa cross-sections + the bay at s 1040-1080."""
import io

p = "Data/Regions/bialystok-industrial-c/overrides.yaml"
s = io.open(p, encoding="utf-8").read()
a = s.index("  - id: gore-andersa-merge-s1060-plain")
b = s.index("  # ---------------------------------------------------------------- ADR 0093: junction geometry")
s = s[:a] + s[b:]
# existing placements replaced by measured cross-sections (ADR 0095)
for oid in ("andersa-placement-s1100-1270", "andersa-placement-s1300-1355"):
    a = s.index("  - id: " + oid)
    b = s.index("  - id: ", a + 10)
    s = s[:a] + s[b:]
s = s.rstrip("\n") + """
  # ---------------------------------------------------------------- ADR 0095: lanes and widths measured on the orthophoto
  # lane_edges = distances (m) from the LEFT carriageway edge in the direction of travel to [start of lane 1,
  # lane line 1|2, ..., end of the last lane]; the first value is the left gutter / edge strip, the last one the
  # carriageway width. Read off straightened strips of the GUGiK 0.08 m orthophoto (WMS HighResolution) drawn along
  # the OSM way with a 1 m lateral scale (artifacts/junctions-r2/scripts/xbatch.py; strips in
  # artifacts/junctions-r3/xsec/, reading accuracy about +-0.15 m). center_offset as above (left of the OSM way).
  # edge_lines = painted edge lines actually on the photo (default with lane_edges: none - kerbed edges on Andersa).
  # Replaces the generic "lanes x 3.50 m + 2 x 0.50 m" (11.5 m) the generator fell back to because BDOT10k says 8.0 m.
  - id: andersa-nw-xsec-s1100-1270
    target: {edge: "w249640399:1881569071-131612943"}
    reason: >-
      Andersa NW-bound carriageway before the bay (strips xsec/and1.png, stations 20-44 and 100-124 of the chain):
      median gutter 0.6 m, lane lines 3.9 / 7.45 m from the median kerb, right asphalt edge 10.8 m; carriageway centre
      0.2 m right of the previous placement (-0.8, edge_sides ADR 0077) -> -1.0.
    confidence: high
    verify: owner drive
    set: {center_offset: -1.0, lane_edges: [0.6, 3.95, 7.45, 10.8]}
  - id: andersa-nw-xsec-bay-s1040-1080
    target: {edge: "w249640399:131612943-1852176912"}
    reason: >-
      Andersa NW-bound beside the paved bay (REVIEW 0093 P0-L, route s 1040-1080; strips xsec/s1060_full.png,
      xsec/and1.png): median kerb 4.3 m left of the OSM way, lane lines 0.4 m left / 3.0 m right of it, solid edge line
      6.6 m right -> three lanes 3.35 / 3.4 / 3.5 m, 10.9 m kerb to edge line, centre 1.15 m right of the OSM way.
      The generator had 11.5 m centred on the way plus the bay as a 4 m asphalt lane: 15 m of asphalt with 5 rows.
    confidence: high
    verify: owner drive
    set: {center_offset: -1.15, lane_edges: [0.65, 4.0, 7.4, 10.9]}
  - id: andersa-nw-xsec-s1080-1210
    target: {edge: "w1093579590:1852176912-2359253621"}
    reason: >-
      Andersa NW-bound after the bay (strips xsec/n100_w1093590.png, xsec/and2.png stations 10-34 and 95-119): median
      kerb 4.3 m left of the OSM way, lane lines 0.1 m left / 3.4 m right, right kerb 6.75 m right -> lanes
      3.5 / 3.5 / 3.35 m, 11.05 m, centre 1.2 m right of the way.
    confidence: high
    verify: owner drive
    set: {center_offset: -1.2, lane_edges: [0.7, 4.2, 7.7, 11.05]}
  - id: andersa-nw-xsec-n10015785253
    target: {edge: "w1093579589:2359253621-10015785253"}
    reason: >-
      Andersa NW-bound at the side-street island (strip xsec/and5.png, station 0-20): median kerb 4.4 m, lane line
      0.2 m, solid right-lane line 3.25 m on the other side, mouth of the side street 6.6 m -> 11.0 m, centre 1.1 m
      right of the OSM way. REVIEW 0093 P0-L: the generated median ran to zero here because both carriageways were
      11.5 m centred on ways drawn 1.1-1.3 m towards the median.
    confidence: high
    verify: owner drive
    set: {center_offset: -1.1, lane_edges: [0.5, 4.2, 7.65, 11.0]}
  - id: andersa-nw-xsec-s1300-1355
    target: {edge: "w266084693:10015785253-12620261934"}
    reason: >-
      Andersa NW-bound after the side street (strips xsec/n100_w266.png, xsec/and2.png station 30-54, xsec/and5.png
      station 2-26): median kerb 5.4-5.9 m left of the line placed at -0.8 (ADR 0077), lane lines 1.25-1.6 m left /
      1.95-2.2 m right, right kerb 5.4-5.6 m right -> 11.1 m, centre 0.1 m left of the previous placement -> -0.7.
    confidence: high
    verify: owner drive
    set: {center_offset: -0.7, lane_edges: [0.7, 4.2, 7.7, 11.1]}
  - id: andersa-nw-xsec-s1355-1410
    target: {edge: "w266084693:12620261934-2840742308"}
    reason: >-
      Andersa NW-bound before the fork to Rondo Putry (strip xsec/and5.png station 18-42): median barrier kerb 4.7 m
      left of the OSM way, lane lines 0.6 m left / 3.0 m right (solid), right kerb 7.25 m right at station 30 where
      the exit lane is already 4.25 m wide; one width per edge: 11.6 m (WORKING_VALUE between the 11.1 m of the
      previous edge and 11.95 m measured), centre 1.2 m right of the way.
    confidence: medium
    verify: owner drive
    set: {center_offset: -1.2, lane_edges: [0.6, 4.1, 7.7, 11.6]}
  - id: andersa-se-xsec-w560802655
    target: {edge: "w560802655:12620261936-1946476472"}
    reason: >-
      Andersa SE-bound carriageway (strip xsec/and3.png station 30-54): median kerb 4.3 m left of the OSM way, lane
      lines 0.2 m left / 3.3 m right, right kerb 6.9 m right -> 11.2 m, centre 1.3 m right of the way.
    confidence: high
    verify: owner drive
    set: {center_offset: -1.3, lane_edges: [0.7, 4.1, 7.6, 11.2]}
  - id: andersa-se-xsec-w266084684
    target: {edge: "w266084684:1946476472-4103450292"}
    reason: >-
      Andersa SE-bound with the bus lane (strips xsec/and3.png stations 120-144 and 200-224): median kerb 4.3 m left
      of the OSM way, lane line 0.2 m left, solid bus-lane line 3.25 m right, right kerb 6.8 m right -> 11.1 m,
      centre 1.25 m right of the way.
    confidence: high
    verify: owner drive
    set: {center_offset: -1.25, lane_edges: [0.7, 4.1, 7.55, 11.1]}
  - id: andersa-se-xsec-w560802656
    target: {edge: "w560802656:4103450292-277320063"}
    reason: >-
      Andersa SE-bound past the bay (strip xsec/and4.png stations 20-44 and 85-109, chain reversed): median gutter
      edge 4.1 m on the median side of the OSM way, lane lines at the way and 3.45 m on the other side, right kerb
      7.0 m -> 11.1 m, centre 1.45 m right of the way (direction of travel).
    confidence: high
    verify: owner drive
    set: {center_offset: -1.45, lane_edges: [0.5, 4.05, 7.55, 11.1]}
  # --- the bay at route s 1040-1080 (REVIEW 0093 P0-L / 0077 #6)
  - id: andersa-bay-s1060-service-lane
    target: {edge: "w174545870:131612943-1852176912"}
    reason: >-
      OSM service way (access=no) = the sett-paved bay beside Andersa. On the 0.08 m orthophoto (xsec/s1060_full.png)
      the bay behind the kerbed strip is 4.9 m wide (8.35-13.25 m right of the Andersa OSM way), granite setts; the
      OSM line runs 0.6 m left of its centre. Was: 4 m of asphalt.
    confidence: high
    verify: owner drive
    set: {width: 4.9, center_offset: -0.6, surface: sett}
  - id: gore-andersa-bay-s1060-sett
    kind: paved_gore
    at_en: [-82.6, -342.8]
    radius_m: 45.0
    surface: sett
    reason: >-
      Between the Andersa edge line and the bay the surface is continuous (setts) at both ends of the bay; the kerbed
      strip in between is the traffic_island below. Replaces gore-andersa-merge-s1060-plain (asphalt, ADR 0077).
    confidence: high
    verify: owner drive
  - id: andersa-bay-s1060-kerb-strip
    kind: traffic_island
    surface: sidewalk_paving
    polygon_en: [[-100.3, -328.2], [-100.6, -328.1], [-100.9, -328.2], [-101.2, -328.4], [-101.3, -328.7], [-101.3, -329.0],
                 [-101.1, -329.3], [-63.7, -358.1], [-63.4, -358.2], [-63.1, -358.2], [-62.8, -358.0], [-62.7, -357.7],
                 [-62.7, -357.3], [-62.9, -357.0]]
    reason: >-
      Raised kerbed strip 1.35 m wide, 48.5 m long, rounded ends, between the Andersa edge line and the bay
      (xsec/s1060_full.png: stations 10-58.5, 7.0-8.35 m right of the OSM way; trace/bay_nw_o.jpg, bay_se_o.jpg).
    confidence: high
    verify: owner drive
  - id: andersa-bay-s1060-edge-solid
    kind: painted_line
    line: P-7b
    polyline_en: [[-63.9, -358.5], [-101.5, -329.5]]
    reason: Solid edge line along the kerbed strip of the bay (xsec/s1060_full.png, stations 10.5-58).
    confidence: high
    verify: owner drive
  - id: andersa-bay-s1060-edge-dashed-nw
    kind: painted_line
    line: P-7a
    polyline_en: [[-102.3, -328.9], [-111.7, -321.5], [-128.9, -307.6]]
    smooth: false
    reason: Broken edge line across the NW opening of the bay (xsec/s1060_full.png 59-71, xsec/and2.png 10-22).
    confidence: high
    verify: owner drive
  - id: andersa-bay-s1060-edge-dashed-se
    kind: painted_line
    line: P-7a
    polyline_en: [[-19.4, -390.9], [-56.0, -365.1], [-63.1, -359.2]]
    smooth: false
    reason: >-
      Broken edge line across the SE opening / entry taper of the bay (xsec/s1060_full.png 0-9.5, xsec/and1.png
      stations 0-45 of w249640399:1881569071-131612943).
    confidence: high
    verify: owner drive
"""
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
