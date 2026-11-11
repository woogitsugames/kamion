"""One-off edit of overrides.yaml (ADR 0095 step 1c): DK8 / Andersa viaduct W of Rondo Putry + the ramp split (kerb_merge)."""
import io

p = "Data/Regions/bialystok-industrial-c/overrides.yaml"
s = io.open(p, encoding="utf-8").read()
s = s.rstrip("\n") + """
  # --- viaduct over Rondo Putry, westbound carriageway + the ramp split at E -782 N 77 (owner video; REVIEW 0093 P0-L)
  # OSM tags lanes=3 on w490398852 / w490398851 / w173985169 / w23844386. Both the 0.08 m WMS mosaic (cell c_01_08
  # fetched for this ADR, artifacts/junctions-r2/ortho_hr) and the dated 0.25 m sheet of 2024-05-27 (xsec/km_sheet.png)
  # show TWO lanes on the main carriageway from the viaduct to the end of the ramp's lane; the third lane of OSM is the
  # ramp from Rondo Putry running beside it (its own way w240542867, laid abreast by the generator). With 3 x 3.5 + 1 m
  # centred on the OSM way the generated deck was 3.3 m wider than the real one on the median side - the lamp
  # "in the left lane" of the owner's video (E -589 N 19.5) stood on the real barrier line.
  - id: dk8-viaduct-w-xsec-w490398852
    target: {edge: "w490398852:4825844768-1832991672"}
    reason: >-
      Strips xsec/km_trunk0.png (stations 0-70) and xsec/km_trunk.png (60-150): median kerb 3.6 m on the median side
      of the OSM way, lane line 0.1-0.3 m on the same side, line to the ramp lane 3.3-3.65 m on the other side:
      two lanes of 3.4-3.6 m; the ramp lane (3.7 m, kerb at 7.0-7.25 m) is w240542867.
    confidence: high
    verify: owner drive
    set: {center_offset: 0.0, lane_edges: [0.2, 3.5, 7.1]}
  - id: dk8-viaduct-w-ramp-lane-width
    target: {edge: "w240542867:1847044963-1832991672"}
    reason: >-
      Ramp from Rondo Putry beside the main carriageway: 3.7 m (stations 0-40 of the main chain, xsec/km_trunk0.png),
      4.6 m in the curve at station 60 (xsec/km_trunk.png). One width per edge: 4.2 m (WORKING_VALUE); was 5.5 m.
    confidence: medium
    verify: owner drive
    set: {width: 4.2}
  - id: dk8-viaduct-w-xsec-w490398851
    target: {edge: "w490398851:4825844766-4825844768"}
    reason: "Viaduct, strip xsec/km_t130.png: barrier kerbs 3.6 m (median side) / 4.6 m, edge lines 3.1 / 3.75 m, lane line 0.1 m."
    confidence: high
    verify: owner drive
    set: {center_offset: -0.5, lane_edges: [0.5, 3.7, 7.35, 8.2], edge_lines: both}
  - id: dk8-viaduct-w-xsec-w173985169
    target: {edge: "w173985169:1847263320-4825844766"}
    reason: "Viaduct, strip xsec/km_t130.png (stations 150-246): same section as w490398851."
    confidence: high
    verify: owner drive
    set: {center_offset: -0.5, lane_edges: [0.5, 3.7, 7.35, 8.2], edge_lines: both}
  - id: dk8-viaduct-w-xsec-w23844386
    target: {edge: "w23844386:1166108055-1847263320"}
    reason: >-
      Viaduct, strips xsec/km_t250.png and xsec/km2.png (station 300-324): the two lanes drift from 0.8 m (station
      250) to 1.65 m (station 365) off the OSM way, away from the median; at station 310 barrier 2.4 m (median side) /
      5.6 m, edge lines 2.25 / 4.9 m, lane line 1.4 m. Edge direction is against the chain: start = station 358.
    confidence: high
    verify: owner drive
    set: {center_offset: [-1.6, -0.8], lane_edges: [0.15, 3.8, 7.3, 8.0], edge_lines: both}
  - id: dk8-viaduct-w-xsec-w173985172
    target: {edge: "w173985172:1847263305-1166108055"}
    reason: >-
      Viaduct, strip xsec/km2.png (station 390-414): edge lines 2.25 m (median side) / 5.0 m, lane line 1.4 m; back to
      0.6 m off the way at station 465 (next edge).
    confidence: high
    verify: owner drive
    set: {center_offset: [-0.8, -1.6], lane_edges: [0.25, 3.9, 7.5, 8.1], edge_lines: both}
  - id: dk8-viaduct-w-xsec-w1101181473
    target: {edge: "w1101181473:10076968415-1847263305"}
    reason: >-
      East approach of the viaduct, strip xsec/km2.png (station 500-524): kerb 3.6 m (median side), edge line 3.1 m,
      lane line 0.3 m on the other side, kerb 4.6 m there (no edge line on that side).
    confidence: high
    verify: owner drive
    set: {center_offset: -0.5, lane_edges: [0.5, 3.9, 7.4, 8.2], edge_lines: left}
  - id: dk8-ramp-split-island
    kind: traffic_island
    surface: sidewalk_paving
    polygon_en: [[-781.9, 76.5], [-781.2, 77.1], [-768.1, 77.3], [-753.0, 76.9], [-753.3, 73.5], [-781.3, 75.6]]
    reason: >-
      Kerbed concrete separator with barriers between the main carriageway and the ramp from Rondo Putry, rounded nose
      at E -781.9 N 76.5 (the kerb of the owner's video), running east onto the viaduct (xsec/km_trunk.png stations
      106-135).
    confidence: high
    verify: owner drive
  - id: dk8-ramp-split-p21-front
    kind: painted_zone
    chevron_axis: [[-800.4, 76.4], [-781.9, 76.5]]
    polygon_en: [[-800.4, 76.4], [-793.3, 77.5], [-781.6, 78.4], [-781.2, 77.2], [-781.9, 76.5], [-781.3, 75.6], [-782.3, 75.5]]
    reason: P-21 chevrons in front of the separator nose, tip at station 88 (xsec/km_trunk.png).
    confidence: high
    verify: owner drive
  - id: dk8-ramp-split-p21-side
    kind: painted_zone
    stripe_az_deg: 35
    polygon_en: [[-781.6, 78.4], [-778.1, 78.7], [-765.9, 79.8], [-760.8, 79.7], [-753.1, 79.0], [-753.3, 76.9], [-768.1, 77.4], [-781.2, 77.2]]
    reason: >-
      P-21 on the ramp side of the separator (REVIEW 0093: "P-21 w lacznicy E -757...-782"), oblique stripes
      (xsec/km_trunk.png stations 106-135).
    confidence: high
    verify: owner drive
  - id: dk8-ramp-split-line-solid
    kind: painted_line
    line: P-2b
    polyline_en: [[-847.6, 75.6], [-828.5, 76.6], [-800.4, 76.4]]
    reason: Solid line between the ramp lane and the main carriageway, stations 41-88 (xsec/km_trunk0.png, km_trunk.png).
    confidence: high
    verify: owner drive
  - id: dk8-ramp-split-line-dashed
    kind: painted_line
    line: P-1e
    polyline_en: [[-888.6, 72.4], [-850.6, 75.5]]
    reason: Broken line between the ramp lane and the main carriageway, stations 0-38 (xsec/km_trunk0.png).
    confidence: high
    verify: owner drive
"""
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
