"""Approximate pixel observations and a pinhole estimate, not a building survey."""
import json
import math
from pathlib import Path
from statistics import mean

root = Path(__file__).resolve().parent
identity = json.loads((root / "chimney-identity-preflight.json").read_text(encoding="utf-8"))
source = json.loads((root / "chimney-source-correction.json").read_text(encoding="utf-8"))
heading = mean(identity["inferred_heading_from_each_stack_deg"])
focal_px = source["focal_35mm_equivalent_mm"] * 3840 / 36
stacks = {stack["osm_way"]: stack for stack in identity["stacks"]}
# Approximate visual picks on the existing resized 3840x2160 reference.
# Left crop origin y=300; right crop origin y=0. Gallery-obscured boundary
# on the right around y=367 is deliberately excluded from spacing estimation.
observations = {
    "left": dict(osm_way="628899554", source_x_measured=identity["measured_painted_shaft_centres_x"][0],
                 boundaries_y_source_WORKING_VALUE=[400, 482, 567, 650, 735],
                 clean_spacings_px=[82, 85, 83, 85], visible_head="three separate outlets, two close head galleries"),
    "right": dict(osm_way="628899553", source_x_measured=identity["measured_painted_shaft_centres_x"][1],
                  boundaries_y_source_WORKING_VALUE=[150, 256, 478, 584, 689],
                  clean_spacings_px=[106, 106, 105], visible_head="one large outlet, head gallery and a lower shaft gallery")
}
for side, observation in observations.items():
    stack = stacks[observation["osm_way"]]
    depth = stack["distance_m"] * math.cos(math.radians(stack["bearing_clockwise_from_north_deg"] - heading))
    observation["depth_at_inferred_heading_m"] = depth
    observation["mean_clean_spacing_px"] = mean(observation["clean_spacings_px"])
    observation["estimated_pitch_m_WORKING_VALUE"] = observation["mean_clean_spacing_px"] * depth / focal_px
result = dict(source_page=source["file_page"], author=source["author"], license=source["license"],
              attribution=source["attribution"], source_size_used=[3840, 2160],
              source_status="Resized reference; original download HTTP 429 twice, no local original claimed",
              heading_WORKING_VALUE_deg=heading, focal_pixels_assuming_36mm_equivalent_width=focal_px,
              assumptions="Rectilinear projection, small camera pitch, same stripe height; GPS rounded and equivalent focal/crop uncertain",
              estimated_uncertainty_m_WORKING_VALUE=2.0, observations=observations,
              candidate_only=dict(pitch_m=15.0, height_m_retained_from_OSM=120,
                                  alternating_phase="white 0..15 m, red 15..30 m, continuing to red 105..120 m",
                                  status="WORKING_VALUE. Check with photo-aligned r3 renders before choosing; no mesh/source changes applied"))
(root / "chimney-bands-preflight.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
