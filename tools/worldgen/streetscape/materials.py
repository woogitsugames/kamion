"""Engine material table for streetscape surfaces (glTF base factors + metadata).

Linear albedo / roughness = WORKING_VALUE placeholders in the ranges of docs/06 §3 (measured albedo of
concrete 0.25-0.40, asphalt 0.05-0.12, painted steel, galvanised steel 0.45-0.6 metal, vegetation 0.05-0.2),
to be replaced by the calibrated table. `surface` = physics surface type; `texture_set` names the tiling
texture set of the engine material (art-source/world/textures, procedural, see docs/WORLD_GENERATION.md).
The Blender control renders build equivalent procedural shaders (tools/blender/world/render_control.py).
"""


def _set_mean(name, default):
    """Mean linear albedo of a generated texture set (materials_spec.json), so a calibrated set gets tint 1."""
    import json
    from pathlib import Path
    p = Path(__file__).resolve().parents[3] / "art-source" / "world" / "materials" / "materials_spec.json"
    try:
        return [round(float(x), 3) for x in json.loads(p.read_text(encoding="utf-8"))["sets"][name]["albedo"]["mean_rgb_linear"]]
    except (OSError, KeyError, ValueError):
        return default


M = {
    # paved areas
    "yard_paving": {"color": [0.26, 0.255, 0.245], "rough": 0.85, "surface": "paving_stones", "texture_set": "paving_20x10_grey"},
    "yard_concrete": {"color": [0.30, 0.297, 0.288], "rough": 0.85, "surface": "concrete", "texture_set": "concrete_cast_5m_joints"},
    "yard_slabs": {"color": [0.27, 0.267, 0.258], "rough": 0.85, "surface": "concrete", "texture_set": "concrete_slab_3x1.5"},
    "yard_asphalt": {"color": [0.081, 0.08, 0.079], "rough": 0.9, "surface": "asphalt", "texture_set": "asphalt_worn"},
    "yard_gravel": {"color": [0.20, 0.19, 0.17], "rough": 0.95, "surface": "gravel", "texture_set": "gravel_compacted"},
    "path_asphalt": {"color": [0.081, 0.08, 0.079], "rough": 0.9, "surface": "asphalt", "texture_set": "asphalt_worn"},
    "cycle_red": {"color": [0.20, 0.06, 0.05], "rough": 0.88, "surface": "asphalt", "texture_set": "paving_red"},
    # buildings
    "hall_wall_grey": {"color": [0.46, 0.47, 0.46], "rough": 0.5, "metal": 0.2, "texture_set": "sandwich_ribbed"},
    "hall_wall_silver": {"color": [0.40, 0.42, 0.43], "rough": 0.45, "metal": 0.4, "texture_set": "sandwich_ribbed"},
    "hall_wall_white": {"color": [0.55, 0.56, 0.55], "rough": 0.5, "metal": 0.2, "texture_set": "sandwich_ribbed"},
    "hall_wall_ivory": {"color": [0.52, 0.47, 0.36], "rough": 0.5, "metal": 0.2, "texture_set": "sandwich_ribbed"},
    "hall_plinth": {"color": [0.25, 0.25, 0.24], "rough": 0.9, "texture_set": "concrete_precast"},
    "hall_flashing": {"color": [0.045, 0.05, 0.055], "rough": 0.5, "metal": 0.3},
    "roof_membrane": {"color": [0.07, 0.07, 0.07], "rough": 0.85},
    "skylight": {"color": [0.55, 0.57, 0.58], "rough": 0.3},
    "reveal_hall": {"color": [0.30, 0.31, 0.31], "rough": 0.6},
    "reveal_plaster": {"color": [0.40, 0.38, 0.34], "rough": 0.85},
    "plaster_light": {"color": [0.52, 0.50, 0.46], "rough": 0.9, "texture_set": "plaster"},
    "plaster_grey": {"color": [0.36, 0.36, 0.35], "rough": 0.9, "texture_set": "plaster"},
    "plaster_beige": {"color": [0.50, 0.44, 0.34], "rough": 0.9, "texture_set": "plaster"},
    "plaster_cream": {"color": [0.55, 0.48, 0.33], "rough": 0.9, "texture_set": "plaster"},
    "plaster_pastel_blue": {"color": [0.36, 0.42, 0.47], "rough": 0.9, "texture_set": "plaster"},
    "brick_red": {"color": [0.26, 0.10, 0.07], "rough": 0.9, "texture_set": "brick"},
    "plinth_dark": {"color": [0.16, 0.16, 0.16], "rough": 0.9},
    "roof_tiles_red": {"color": [0.22, 0.07, 0.04], "rough": 0.7, "texture_set": "roof_tiles"},
    "roof_tiles_brown": {"color": [0.12, 0.06, 0.04], "rough": 0.7, "texture_set": "roof_tiles"},
    "roof_metal_graphite": {"color": [0.05, 0.05, 0.055], "rough": 0.5, "metal": 0.5, "texture_set": "roof_metal_tile"},
    "glass": {"color": [0.03, 0.035, 0.04], "rough": 0.05},
    "window_frame": {"color": [0.6, 0.6, 0.58], "rough": 0.5},
    "window_sill": {"color": [0.45, 0.45, 0.45], "rough": 0.4, "metal": 0.6},
    "door_steel": {"color": [0.30, 0.31, 0.32], "rough": 0.5, "metal": 0.4},
    "door_glass": {"color": [0.04, 0.045, 0.05], "rough": 0.05},
    "garage_door": {"color": [0.42, 0.42, 0.40], "rough": 0.5, "metal": 0.4, "texture_set": "sectional_door"},
    "dock_door": {"color": [0.42, 0.43, 0.44], "rough": 0.45, "metal": 0.4, "texture_set": "sectional_door"},
    "dock_shelter": {"color": [0.025, 0.025, 0.025], "rough": 0.7},
    "paint_yellow": {"color": [0.60, 0.42, 0.02], "rough": 0.5},
    "steel_checker": {"color": [0.30, 0.30, 0.30], "rough": 0.5, "metal": 0.8},
    "hazard_stripes": {"color": [0.5, 0.4, 0.05], "rough": 0.5, "texture_set": "hazard_stripes_45deg"},
    "rubber_black": {"color": [0.02, 0.02, 0.02], "rough": 0.85},
    "plate_white": {"color": [0.7, 0.7, 0.68], "rough": 0.5},
    "dock_digits": {"color": [1, 1, 1], "rough": 0.5, "texture": "dock_digits"},
    "dock_light": {"color": [0.05, 0.05, 0.05], "rough": 0.5},
    "steel_painted": {"color": [0.12, 0.13, 0.13], "rough": 0.5, "metal": 0.5},
    "canopy_fascia": {"color": [0.6, 0.6, 0.6], "rough": 0.5},
    # furniture
    "concrete_base": {"color": [0.30, 0.30, 0.28], "rough": 0.9},
    "steel_galv": {"color": [0.42, 0.43, 0.43], "rough": 0.55, "metal": 0.9},
    "steel_galv_dark": {"color": [0.30, 0.31, 0.31], "rough": 0.6, "metal": 0.9},
    "luminaire_housing": {"color": [0.12, 0.12, 0.13], "rough": 0.5, "metal": 0.5},
    "concrete_pole": {"color": [0.36, 0.36, 0.34], "rough": 0.9},
    "steel_painted_grey": {"color": [0.22, 0.23, 0.23], "rough": 0.6, "metal": 0.3},
    "luminaire_old": {"color": [0.30, 0.31, 0.30], "rough": 0.55, "metal": 0.2},
    "lamp_glass_sodium": {"color": [0.42, 0.33, 0.20], "rough": 0.25},
    "lamp_glass": {"color": [0.35, 0.35, 0.33], "rough": 0.2},
    "plate_back": {"color": [1, 1, 1], "rough": 0.5, "metal": 0.6, "texture": "plate_back"},
    "signal_housing": {"color": [0.03, 0.03, 0.03], "rough": 0.6},
    "signal_backplate": {"color": [0.02, 0.02, 0.02], "rough": 0.7},
    "signal_border": {"color": [0.7, 0.7, 0.7], "rough": 0.5},
    "signal_red_on": {"color": [0.9, 0.05, 0.02], "rough": 0.3, "emissive": [6.0, 0.3, 0.1]},
    "signal_red_off": {"color": [0.12, 0.02, 0.02], "rough": 0.3},
    "signal_yellow_off": {"color": [0.15, 0.10, 0.02], "rough": 0.3},
    "signal_green_on": {"color": [0.05, 0.9, 0.5], "rough": 0.3, "emissive": [0.2, 5.0, 2.5]},
    "signal_green_off": {"color": [0.02, 0.10, 0.06], "rough": 0.3},
    "shelter_roof": {"color": [0.15, 0.16, 0.16], "rough": 0.5, "metal": 0.4},
    "shelter_glass": {"color": [0.05, 0.06, 0.06], "rough": 0.05},
    "bench_wood": {"color": [0.18, 0.11, 0.06], "rough": 0.8},
    "gate_boom": {"color": [0.6, 0.6, 0.6], "rough": 0.5, "texture_set": "boom_red_white"},
    "fence_green": {"color": [0.03, 0.09, 0.05], "rough": 0.5, "metal": 0.3},
    "fence_anthracite": {"color": [0.05, 0.055, 0.06], "rough": 0.5, "metal": 0.3},
    "fence_galv": {"color": [0.40, 0.41, 0.41], "rough": 0.55, "metal": 0.9},
    "fence_green_mesh": {"color": [0.03, 0.09, 0.05], "rough": 0.5, "texture": "fence_mesh", "alpha_cutoff": 0.5},
    "fence_anthracite_mesh": {"color": [0.05, 0.055, 0.06], "rough": 0.5, "texture": "fence_mesh", "alpha_cutoff": 0.5},
    "fence_galv_mesh": {"color": [0.40, 0.41, 0.41], "rough": 0.55, "texture": "fence_mesh", "alpha_cutoff": 0.5},
    "concrete_plinth": {"color": [0.30, 0.30, 0.28], "rough": 0.9},
    "concrete_fence": {"color": [0.30, 0.29, 0.27], "rough": 0.9, "texture_set": "concrete_fence_panel"},
    "concrete_fence_post": {"color": [0.28, 0.28, 0.26], "rough": 0.9},
    "concrete_wall": {"color": [0.30, 0.30, 0.28], "rough": 0.9},
    "barrier_post": {"color": [0.40, 0.41, 0.41], "rough": 0.55, "metal": 0.9},
    # ADR 0060 (r7 N-2, D42 Mapillary 2018-07 / 2024-07 at g3b_eye_s1482 / s1632, reference only): the absorbing
    # cassettes along Andersa / Putry are dark powder-coated (anthracite / moss-green class), read near-black under the
    # glass panes; 0.30 read as a light grey wall. WORKING_VALUE (no RAL plate seen).
    "noise_panel": {"color": [0.05, 0.06, 0.055], "rough": 0.6, "metal": 0.1, "texture_set": "noise_cassette"},
    # ADR 0069 noise barriers after Mapillary p38/p40 (2024, overcast): cassettes 36-40 sRGB next to a plinth of 105
    # sRGB on the same vertical face -> linear ratio 0.135 x concrete_plinth 0.30 = 0.04; 0.07 keeps the cassette
    # relief readable on Low overcast (0.17 + metal 0.3 read near-black in r5). Posts 98/108/100 sRGB (green-grey).
    "noise_panel_dark": {"color": [0.068, 0.072, 0.070], "rough": 0.7, "metal": 0.05, "texture_set": "noise_cassette"},
    "noise_post": {"color": [0.17, 0.21, 0.18], "rough": 0.55, "metal": 0.3},
    "car_sill": {"color": [0.035, 0.033, 0.03], "rough": 0.8},
    # contact shadow / AO patch under parked vehicles (ADR 0050): Kamion/World Vehicle Contact, parameters per
    # prototype from the LOD0 node extras ("contact", life_props.contact_spec)
    "vehicle_contact": {"color": [1.0, 1.0, 1.0], "rough": 1.0, "shader": "vehicle_contact"},
    "wire": {"color": [0.11, 0.11, 0.105], "rough": 0.5, "shader": "wire"},   # weathered aluminium conductor, ribbon
    "concrete_pole": {"color": [0.33, 0.33, 0.31], "rough": 0.9},
    "insulator": {"color": [0.5, 0.5, 0.5], "rough": 0.3},
    "paint_white_reflective": {"color": [0.7, 0.7, 0.7], "rough": 0.4},
    "cabinet_grey": {"color": [0.35, 0.36, 0.35], "rough": 0.6},
    # static life props (streetscape.life_props): vehicles, yard props, gate kit
    "car_paint_silver": {"color": [0.42, 0.43, 0.44], "rough": 0.28, "metal": 0.6, "texture_set": "car_grime"},
    "car_paint_grey": {"color": [0.13, 0.135, 0.14], "rough": 0.26, "metal": 0.5, "texture_set": "car_grime"},
    "car_paint_black": {"color": [0.018, 0.018, 0.02], "rough": 0.2, "metal": 0.3, "texture_set": "car_grime"},
    "car_paint_white": {"color": [0.68, 0.68, 0.66], "rough": 0.3, "texture_set": "car_grime"},
    "car_paint_white2": {"color": [0.62, 0.63, 0.62], "rough": 0.36, "texture_set": "car_grime"},
    "car_paint_blue": {"color": [0.03, 0.05, 0.12], "rough": 0.24, "metal": 0.4, "texture_set": "car_grime"},
    "car_paint_red": {"color": [0.32, 0.03, 0.025], "rough": 0.28, "metal": 0.2, "texture_set": "car_grime"},
    "car_paint_green": {"color": [0.035, 0.07, 0.045], "rough": 0.35, "metal": 0.4, "texture_set": "car_grime"},
    "car_paint_beige": {"color": [0.36, 0.32, 0.24], "rough": 0.4, "metal": 0.3, "texture_set": "car_grime"},
    "car_glass": {"color": [0.012, 0.014, 0.016], "rough": 0.65},     # opaque (LOD1 / LOD2): does not mirror the sky
    # LOD0 car glazing: dark tint, alpha blended (importer: "blend"), the dark interior shows through
    # v4 (REVIEW r6 W-N8): transmission 0.35 per face onto the dark interior (both faces drawn), thinner dust film
    "car_glass_tint": {"color": [0.010, 0.016, 0.016], "rough": 0.05, "alpha": 0.65, "blend": True, "shader": "car_glass",
                       "dust": 0.35, "privacy_alpha": 0.80, "reflect": 1.0},
    # road film overlays of car LOD0 / LOD1 (ADR 0041 par. 8): alpha texture x per-level alpha, three dirt levels
    # v4: darker grey-brown, lower alpha (the salt-pale level 3 at alpha 1.0 read as beige paint on red / dark cars)
    "car_dirt_1": {"color": [0.15, 0.13, 0.10], "rough": 1.0, "alpha": 0.45, "blend": True, "texture": "car_dirt"},
    "car_dirt_2": {"color": [0.16, 0.14, 0.11], "rough": 1.0, "alpha": 0.62, "blend": True, "texture": "car_dirt"},
    "car_dirt_3": {"color": [0.18, 0.165, 0.135], "rough": 1.0, "alpha": 0.78, "blend": True, "texture": "car_dirt"},
    "car_lamp": {"color": [0.045, 0.047, 0.05], "rough": 0.12, "metal": 0.5},     # smoked lamp housing behind the lens
    # alloy under brake dust (v4: 0.115 rendered as a black disc on LOD1 at 12-45 m on Low, read as "no rim")
    "rim_dusty": {"color": [0.27, 0.25, 0.22], "rough": 0.58, "metal": 0.45},
    "tyre_dusty": {"color": [0.05, 0.045, 0.038], "rough": 0.95},
    # r10 (ADR 0078): LOD0 car tyres with the tread / sidewall texture (modulation, mean ~0.78; colour raised to match)
    "car_tyre": {"color": [0.033, 0.033, 0.033], "rough": 0.85, "texture": "car_tyre"},
    "car_tyre_dusty": {"color": [0.066, 0.059, 0.050], "rough": 0.95, "texture": "car_tyre"},
    "car_interior": {"color": [0.022, 0.022, 0.024], "rough": 0.9},
    "rim_dark": {"color": [0.05, 0.05, 0.052], "rough": 0.6, "metal": 0.5},
    "rim_steel": {"color": [0.07, 0.07, 0.072], "rough": 0.55, "metal": 0.6},
    # fictional Polish plates (life_cars.plate_atlas, REVIEW r6 W-N9): one atlas cell per prototype, LOD1 the far cell
    "car_plate": {"color": [1.0, 1.0, 1.0], "rough": 0.45, "texture": "car_plates"},
    "car_trim": {"color": [0.025, 0.025, 0.025], "rough": 0.6},
    "car_light_head": {"color": [0.5, 0.5, 0.5], "rough": 0.1},
    "car_light_tail": {"color": [0.22, 0.010, 0.012], "rough": 0.12},
    "reflector_red": {"color": [0.4, 0.02, 0.02], "rough": 0.2},
    "tyre": {"color": [0.025, 0.025, 0.025], "rough": 0.85},
    "rim": {"color": [0.50, 0.51, 0.52], "rough": 0.36, "metal": 0.7},
    "trailer_curtain_grey": {"color": [0.20, 0.21, 0.21], "rough": 0.7, "texture_set": "curtain_folds"},
    "trailer_curtain_blue": {"color": [0.03, 0.06, 0.14], "rough": 0.7, "texture_set": "curtain_folds"},
    "trailer_curtain_white": {"color": [0.55, 0.56, 0.55], "rough": 0.7, "texture_set": "curtain_folds"},
    "trailer_curtain_red": {"color": [0.18, 0.045, 0.035], "rough": 0.7, "texture_set": "curtain_folds"},
    "trailer_curtain_green": {"color": [0.045, 0.08, 0.06], "rough": 0.7, "texture_set": "curtain_folds"},
    "trailer_curtain_silver": {"color": [0.36, 0.37, 0.37], "rough": 0.6, "texture_set": "curtain_folds"},
    "trailer_box_white": {"color": [0.60, 0.61, 0.60], "rough": 0.45, "texture_set": "box_panel"},
    "tractor_paint_white": {"color": [0.66, 0.66, 0.64], "rough": 0.3},
    "tractor_paint_silver": {"color": [0.40, 0.41, 0.42], "rough": 0.3, "metal": 0.6},
    "tractor_paint_blue": {"color": [0.025, 0.06, 0.16], "rough": 0.3, "metal": 0.3},
    "tractor_paint_red": {"color": [0.30, 0.025, 0.02], "rough": 0.3, "metal": 0.2},
    "tractor_paint_green": {"color": [0.03, 0.08, 0.05], "rough": 0.3, "metal": 0.3},
    "tractor_paint_black": {"color": [0.02, 0.02, 0.022], "rough": 0.3, "metal": 0.3},
    "container_rust": {"color": [0.17, 0.06, 0.04], "rough": 0.75, "texture_set": "container_corrugation"},
    "container_blue": {"color": [0.05, 0.09, 0.16], "rough": 0.7, "texture_set": "container_corrugation"},
    "container_grey": {"color": [0.22, 0.23, 0.23], "rough": 0.7, "texture_set": "container_corrugation"},
    "container_green": {"color": [0.06, 0.11, 0.07], "rough": 0.7, "texture_set": "container_corrugation"},
    "container_beige": {"color": [0.36, 0.31, 0.22], "rough": 0.7, "texture_set": "container_corrugation"},
    "container_white": {"color": [0.55, 0.55, 0.53], "rough": 0.7, "texture_set": "container_corrugation"},
    "container_frame": {"color": [0.06, 0.06, 0.06], "rough": 0.7, "metal": 0.4},
    "container_doors": {"color": [0.20, 0.20, 0.19], "rough": 0.7, "metal": 0.3},
    "coupling_red": {"color": [0.35, 0.03, 0.02], "rough": 0.5},
    "coupling_yellow": {"color": [0.55, 0.40, 0.02], "rough": 0.5},
    "trailer_front": {"color": [0.40, 0.41, 0.41], "rough": 0.5, "metal": 0.3},
    "trailer_alu": {"color": [0.45, 0.46, 0.46], "rough": 0.4, "metal": 0.9},
    "trailer_doors": {"color": [0.50, 0.51, 0.50], "rough": 0.45, "metal": 0.3},
    "trailer_chassis": {"color": [0.03, 0.03, 0.032], "rough": 0.6, "metal": 0.5},
    "trailer_strap": {"color": [0.10, 0.10, 0.10], "rough": 0.6, "metal": 0.4},
    "reefer_unit": {"color": [0.48, 0.49, 0.48], "rough": 0.5},
    "reefer_grille": {"color": [0.03, 0.03, 0.03], "rough": 0.6},
    "pallet_wood": {"color": [0.36, 0.28, 0.18], "rough": 0.9, "texture_set": "euro_pallet_side"},
    "pallet_foil": {"color": [0.45, 0.45, 0.43], "rough": 0.3},
    "cardboard": {"color": [0.35, 0.25, 0.14], "rough": 0.9},
    "bin_plastic_green": {"color": [0.03, 0.10, 0.05], "rough": 0.6},
    "bin_plastic_grey": {"color": [0.10, 0.10, 0.10], "rough": 0.6},
    "bin_plastic_yellow": {"color": [0.55, 0.40, 0.03], "rough": 0.6},
    "bin_plastic_blue": {"color": [0.03, 0.07, 0.20], "rough": 0.6},
    "skip_paint": {"color": [0.45, 0.32, 0.03], "rough": 0.7, "metal": 0.2},
    "skip_inside": {"color": [0.12, 0.09, 0.05], "rough": 0.9},
    "rubble": {"color": [0.22, 0.20, 0.17], "rough": 0.95},
    "cone_base": {"color": [0.02, 0.02, 0.02], "rough": 0.8},
    "cone_orange": {"color": [0.70, 0.15, 0.02], "rough": 0.6},
    "booth_panel": {"color": [0.45, 0.46, 0.45], "rough": 0.5, "metal": 0.3, "texture_set": "sandwich_ribbed"},
    "booth_glass": {"color": [0.03, 0.035, 0.04], "rough": 0.05},
    "barrier_housing": {"color": [0.55, 0.40, 0.03], "rough": 0.5, "metal": 0.3},
    # facade kit (streetscape.buildings_mesh)
    "downpipe": {"color": [0.30, 0.31, 0.31], "rough": 0.45, "metal": 0.7},
    "gutter": {"color": [0.30, 0.31, 0.31], "rough": 0.45, "metal": 0.7},
    "hall_wall_graphite": {"color": [0.08, 0.085, 0.09], "rough": 0.5, "metal": 0.3, "texture_set": "trapezoid_sheet"},
    "hall_wall_accent_blue": {"color": [0.06, 0.12, 0.20], "rough": 0.5, "metal": 0.3, "texture_set": "trapezoid_sheet"},
    "hall_wall_accent_red": {"color": [0.22, 0.05, 0.04], "rough": 0.5, "metal": 0.3, "texture_set": "trapezoid_sheet"},
    "hall_wall_accent_green": {"color": [0.05, 0.13, 0.09], "rough": 0.5, "metal": 0.3, "texture_set": "trapezoid_sheet"},
    "canopy_steel": {"color": [0.20, 0.21, 0.22], "rough": 0.45, "metal": 0.6},
    "canopy_glass": {"color": [0.25, 0.27, 0.27], "rough": 0.1},
    "roof_vent": {"color": [0.40, 0.41, 0.41], "rough": 0.5, "metal": 0.8},
    "panel_concrete": {"color": [0.30, 0.29, 0.27], "rough": 0.9, "texture_set": "large_panel_joints"},
    "balcony_slab": {"color": [0.30, 0.30, 0.28], "rough": 0.9},
    "balcony_panel": {"color": [0.35, 0.36, 0.36], "rough": 0.6, "metal": 0.3, "texture_set": "trapezoid_sheet"},
    "plaster_accent_terracotta": {"color": [0.42, 0.20, 0.12], "rough": 0.9, "texture_set": "plaster"},
    "plaster_accent_green": {"color": [0.26, 0.33, 0.24], "rough": 0.9, "texture_set": "plaster"},
    "plaster_accent_ochre": {"color": [0.52, 0.38, 0.16], "rough": 0.9, "texture_set": "plaster"},
    "plaster_accent_grey": {"color": [0.20, 0.21, 0.22], "rough": 0.9, "texture_set": "plaster"},
    "wood_planks": {"color": [0.22, 0.15, 0.09], "rough": 0.85, "texture_set": "wood_siding"},
    "wood_planks_green": {"color": [0.08, 0.14, 0.10], "rough": 0.85, "texture_set": "wood_siding"},
    "chimney_brick": {"color": [0.22, 0.09, 0.06], "rough": 0.9, "texture_set": "brick"},
    # behaton (I-shaped interlocking blocks) in truck yards (streetscape.paved)
    "yard_behaton": {"color": [0.23, 0.228, 0.22], "rough": 0.85, "surface": "paving_stones", "texture_set": "behaton_i_grey"},
    # decals on roads (markings layer, depth offset like the markings)
    "decal_oil": {"color": [0.02, 0.02, 0.02], "rough": 0.35, "decal": True, "texture_set": "oil_stain_alpha"},
    "decal_tyre": {"color": [0.018, 0.018, 0.017], "rough": 0.55, "decal": True, "texture_set": "tyre_scrub_alpha"},
    "marking_yard": {"color": [0.46, 0.46, 0.45], "rough": 0.7, "surface": "paint", "decal": True},   # worn yard paint on light pavers; 0.36 (r7) dropped line/paver contrast 1.54 -> 1.14 (review r7 part 2), back to 0.46
    "drain_grate": {"color": [0.035, 0.033, 0.03], "rough": 0.6, "decal": True, "procedural": "grate"},  # cast iron
    "decal_patch": {"color": [0.062, 0.062, 0.06], "rough": 0.85, "decal": True, "texture_set": "asphalt_patch"},
    # bridges (roads.meshing bridge_style overrides; CC0 photos of the Andersa viaducts, docs/REFERENCES.md)
    # hero viaduct asset (ADR 0067, streetscape.hero_bridge): strip atlas on a CC0 scan (colour = atlas mean, so the
    # calibrated-set tint is 1), railing infill + galvanised steel, light crushed stone of the centre island
    "viaduct_concrete": {"color": _set_mean("viaduct_concrete", [0.369, 0.324, 0.276]), "rough": 0.85,
                         "surface": "concrete", "texture_set": "viaduct_concrete", "set_tile": True},
    "viaduct_steel": {"color": [1.0, 1.0, 1.0], "rough": 0.9, "metal": 0.0, "texture": "viaduct_steel",
                      "alpha_cutoff": 0.5},
    "island_gravel": {"color": [0.30, 0.285, 0.26], "rough": 0.95, "surface": "gravel",
                      "texture_set": "gravel_compacted"},
    "bridge_fascia_red": {"color": [0.30, 0.05, 0.04], "rough": 0.7},
    "bridge_fascia_green": {"color": [0.07, 0.17, 0.10], "rough": 0.7},
    "pier_yellow": {"color": [0.46, 0.40, 0.17], "rough": 0.85},
    # transparent noise screens (PMMA / laminated glass, viaduct decks): clear sheet with a faint green edge tint, sky
    # reflection, road-spray film on the lowest ~0.9 m (Kamion/World Car Glass; UV0 v = 1 at the foot -> -0.25 at the
    # top, roads.meshing). Review r6 W-N2: the flat 0.55/0.60/0.60 alpha 0.22 sheet read as solid mint. WORKING_VALUE
    "noise_glass": {"color": [0.030, 0.042, 0.040], "rough": 0.04, "alpha": 0.10, "blend": True, "shader": "car_glass",
                    "dust": 0.75},
    # authored plantings (streetscape.plantings, review r6 W-N12): red berberis hedge, island bed soil / bark mulch.
    # Linear albedo WORKING_VALUE from the CC0 Bieżeństwa photo (hedge vs asphalt luminance ratio, overcast).
    # Clipped hedges = opaque dark core (interior shade + stems, hedge_foliage set) + alpha leaf shell + loose shoot
    # cards (streetscape.hedge_textures, colours in the texture, sRGB; ADR 0049 addendum). Core albedo ~0.4 x leaf.
    "hedge_berberis": {"color": [0.085, 0.034, 0.024], "rough": 0.85, "surface": "grass", "texture_set": "hedge_foliage"},
    "hedge_privet": {"color": [0.020, 0.030, 0.012], "rough": 0.85, "surface": "grass", "texture_set": "hedge_foliage"},
    "hedge_hornbeam": {"color": [0.026, 0.036, 0.014], "rough": 0.85, "surface": "grass", "texture_set": "hedge_foliage"},
    "hedge_thuja": {"color": [0.016, 0.028, 0.012], "rough": 0.85, "surface": "grass", "texture_set": "hedge_foliage"},
    **{f"hedge_{kind}_{sp}": {"color": [1.0, 1.0, 1.0], "rough": 0.9 if sp == "privet" else 0.97,
                              "texture": f"hedge_{kind}_{sp}", "alpha_cutoff": 0.5}
       for kind in ("shell", "sprig") for sp in ("berberis", "privet", "hornbeam", "thuja")},
    "bed_soil": {"color": [0.17, 0.13, 0.095], "rough": 0.9, "surface": "grass", "texture_set": "soil_bed"},
    # roundabout centre under the viaduct: loose grey-beige river stones / coarse gravel on a slope (Mapillary CC BY-SA
    # 201270605169291 / 2818555625124739, 2020-08, D42, reference only; ADR 0060). Set gravel_compacted (no pebble set
    # yet), lighter than a road shoulder. WORKING_VALUE.
    "bed_stones": {"color": [0.22, 0.21, 0.195], "rough": 0.95, "surface": "gravel", "texture_set": "gravel_compacted"},
    # sign gantry (streetscape.life_props.sign_gantry)
    "gantry_steel": {"color": [0.42, 0.43, 0.43], "rough": 0.55, "metal": 0.9},
    # landmarks
    "chimney_concrete": {"color": [0.40, 0.40, 0.38], "rough": 0.9},
    "chimney_red": {"color": [0.35, 0.05, 0.04], "rough": 0.85},
    "chimney_white": {"color": [0.62, 0.62, 0.60], "rough": 0.85},
    # collision
    "collision_vehicle": {"color": [1, 0, 1], "rough": 1.0, "surface": "steel", "collision": True},
    "collision_building": {"color": [1, 0, 1], "rough": 1.0, "surface": "concrete", "collision": True},
    "collision_fence": {"color": [1, 0, 1], "rough": 1.0, "surface": "steel", "collision": True},
    "collision_steel": {"color": [1, 0, 1], "rough": 1.0, "surface": "steel", "collision": True},
    # v3.1 facade palette additions (buildings_mesh.BLOCK_WALLS / OFFICE_WALLS, WORKING_VALUE colours)
    "plaster_yellow": {"color": [0.58, 0.50, 0.28], "rough": 0.9, "texture_set": "plaster"},
    "plaster_peach": {"color": [0.58, 0.42, 0.32], "rough": 0.9, "texture_set": "plaster"},
    "plaster_sage": {"color": [0.40, 0.45, 0.36], "rough": 0.9, "texture_set": "plaster"},
    "plaster_white": {"color": [0.60, 0.60, 0.58], "rough": 0.9, "texture_set": "plaster"},
    "plaster_band_grey": {"color": [0.26, 0.27, 0.27], "rough": 0.9, "texture_set": "plaster"},
    # retaining walls of the raised ramps (roads.profile.mark_walled_ramps): block-faced concrete
    "ramp_wall_blocks": {"color": [0.34, 0.33, 0.31], "rough": 0.9, "texture_set": "concrete_blocks_split"},
}

# LOD1 far facade materials <wall>__far_<kind> (buildings_mesh.lod1_wall): the wall colour + a window grid the
# shader draws from TEXCOORD_1 (one unit = one window bay x one storey; extras.window_grid in those units).
# Keep in sync with buildings_mesh.FAR_GRID / BLOCK_WALLS / OFFICE_WALLS (test_far_facade_materials).
FAR_GRID = {"block": {"pitch_m": 3.0, "win_w": 0.50, "sill": 0.32, "head": 0.84},
            "office": {"pitch_m": 3.0, "win_w": 0.50, "sill": 0.26, "head": 0.71},
            "ribbon": {"pitch_m": 3.0, "win_w": 1.00, "sill": 0.26, "head": 0.71}}
_FAR_WALLS = {"block": ["plaster_cream", "plaster_grey", "plaster_pastel_blue", "plaster_light", "plaster_yellow",
                        "plaster_peach", "plaster_sage", "panel_concrete", "plaster_accent_terracotta",
                        "plaster_accent_green", "plaster_accent_ochre", "plaster_accent_grey"],
              "office": ["plaster_light", "plaster_grey", "plaster_beige", "plaster_white", "brick_red"]}
_FAR_WALLS["ribbon"] = _FAR_WALLS["office"]
for _k, _ws in _FAR_WALLS.items():
    for _w in _ws:
        if _w in M:
            M[f"{_w}__far_{_k}"] = {"color": M[_w]["color"], "rough": M[_w]["rough"], "base": _w,
                                    "window_grid": dict(FAR_GRID[_k], uv="TEXCOORD_1"),
                                    "glass_color": [0.03, 0.035, 0.04]}

# Sky occlusion (ADR 0060, review r7 N-2 "no dark accents"): the engine lights the world with the sky SH and a sky
# reflection probe and has no screen-space AO, so (a) faces looking down (deck soffits, eaves, canopy and balcony
# undersides, the head of window reveals) were lit by a ground that is in fact shaded by the same structure, and
# (b) glazing mirrored the bright horizon where a real window sees the street, trees and the buildings opposite.
# [x, y] = Kamion/World Surface / PBR _SkyOcc: x scales the ambient of down-facing faces by 1 - x * max(-n.y, 0),
# y scales near-horizontal reflections (R.y < 0.45) by up to 1 - y. WORKING_VALUE, judged against the CC0 Bieżeństwa
# photo (soffit / fascia ~20 % luma at overcast vs ~30 % before). Not on cars, ground, vegetation, decals or
# collision (cars belong to the vehicle look work; ground faces up).
SKY_OCC_GLASS = [0.0, 0.9]   # r8 after4: 0.6 left glazing at ~40 % luma (target 0.03-0.06 lin.)
SKY_OCC_STRUCT = [0.5, 0.0]
_NO_SKY_OCC = ("car_", "collision_", "decal_", "marking", "hedge_", "lamp_glass", "signal_", "tyre", "rim",
               "trailer_", "tractor_", "vehicle_", "wire", "bed_soil", "noise_glass")
_GLASSY = ("glass", "door_glass", "booth_glass", "shelter_glass", "canopy_glass", "skylight")


def _sky_occ(k, v):
    if k.startswith(_NO_SKY_OCC) or v.get("collision") or v.get("decal") or "surface" in v and v["surface"] in (
            "grass", "asphalt", "paving_stones", "gravel", "sett"):
        return None
    if k in _GLASSY or "window_grid" in v:
        return SKY_OCC_GLASS if k in _GLASSY else [SKY_OCC_STRUCT[0], SKY_OCC_GLASS[1]]
    return SKY_OCC_STRUCT


for _k, _v in M.items():
    _so = _sky_occ(_k, _v)
    if _so is not None:
        _v.setdefault("sky_occ", _so)

