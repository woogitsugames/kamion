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


def _hero_thuja_shell_tint():
    """ADR0070 r7: hero-only alias; all global route hedge colours stay unchanged."""
    import json
    from pathlib import Path
    p = Path(__file__).resolve().parents[3] / "art-source/world/landmarks/fire_station_jrg2/atlas_layout.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))["atlas"]["thuja_shell_tint_linear"]
    except (OSError, KeyError, ValueError):
        return [1.76558, 1.55454, 2.45559]  # default shared leaf palette / procedural covered-shell mean


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
    # ADR 0091: reveals are painted white with the insulation (was 0.40 warm grey = the wall tone, so the opening
    # had no outline); plaster_grey 0.36 -> 0.62 and plaster_white 0.60 -> 0.76: at 0.36 the wall read 92-98 sRGB under
    # an overcast sky of 238 ("dark concrete", review s9: +25-35 levels asked = albedo x 1.7 at gamma 2.2); facade
    # greys are light paints of LRV ~60, whites ~75-85 (WORKING_VALUE until the owner's photos)
    "reveal_plaster": {"color": [0.60, 0.59, 0.56], "rough": 0.85},
    "plaster_light": {"color": [0.52, 0.50, 0.46], "rough": 0.9, "texture_set": "plaster"},
    "plaster_grey": {"color": [0.62, 0.62, 0.61], "rough": 0.9, "texture_set": "plaster"},
    "plaster_beige": {"color": [0.50, 0.44, 0.34], "rough": 0.9, "texture_set": "plaster"},
    "plaster_cream": {"color": [0.55, 0.48, 0.33], "rough": 0.9, "texture_set": "plaster"},
    "plaster_pastel_blue": {"color": [0.36, 0.42, 0.47], "rough": 0.9, "texture_set": "plaster"},
    # set_tile (ADR 0067): the NF brick set is 1.506 m, at the shader default 4 m a course read as 20 cm (r10 r1 render)
    # ADR 0091: saturation -28 % (linear chroma about the luminance: [0.26, 0.10, 0.07] -> below; on screen -20 %), `macro` =
    # [size m, strength] of the macro tone drift (importer default for modulation sets 64 m / 0.06): lots of brick
    # from different firings differ every few metres
    "brick_red": {"color": [0.224, 0.109, 0.087], "rough": 0.9, "texture_set": "brick", "set_tile": True,
                  "macro": [48.0, 0.18]},
    # plinths (cokół): render in two tones, `splash_h` = splash / soil zone height (m) of Kamion/World PBR _SPLASH
    # (the plinth covers the zone the plaster_* walls had it in, so r10 showed no splash at all)
    # ADR 0094: one plinth tone again (plinth_grey stays defined but unused: every material is a draw per chunk on
    # both LODs - review s9 "draws Low +3...5 %"), 0.16 -> 0.20; the tone variation of a plinth now comes from the
    # splash zone that follows the terrain (buildings_mesh: plinth UV0.v = metres above the ground at the wall)
    "plinth_dark": {"color": [0.20, 0.20, 0.195], "rough": 0.9, "texture_set": "plaster", "splash_h": 0.5},
    "plinth_grey": {"color": [0.25, 0.25, 0.24], "rough": 0.9, "texture_set": "plaster", "splash_h": 0.5},
    # pitched roofs (ADR 0091): one modulation set `roof_tiles` (S-profile tile courses) for ceramic tile and pressed
    # metal tile sheet, set_tile = real course size
    "roof_tiles_red": {"color": [0.20, 0.075, 0.05], "rough": 0.75, "texture_set": "roof_tiles", "set_tile": True},
    "roof_tiles_brown": {"color": [0.11, 0.065, 0.045], "rough": 0.75, "texture_set": "roof_tiles", "set_tile": True},
    "roof_metal_graphite": {"color": [0.055, 0.057, 0.06], "rough": 0.5, "texture_set": "roof_tiles", "set_tile": True},

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
    # prefabricated concrete fence (ADR 0081): calibrated strip atlas, UV0 = atlas metres (facade_atlas.fence_uv);
    # posts and caps use the post strip of the same atlas (one draw)
    "concrete_fence": {"color": _set_mean("fence_concrete", [0.30, 0.29, 0.27]), "rough": 0.9,
                       "texture_set": "fence_concrete", "set_tile": True},
    # building cell atlas (ADR 0081): windows with interiors, doors, garage doors, balustrades, facade equipment
    "facade_atlas": {"color": _set_mean("facade_atlas", [0.30, 0.30, 0.29]), "rough": 0.5, "texture_set": "facade_atlas",
                     "set_tile": True, "sky_occ": [0.5, 0.9]},
    "concrete_wall": {"color": [0.30, 0.30, 0.28], "rough": 0.9},
    "barrier_post": {"color": [0.40, 0.41, 0.41], "rough": 0.55, "metal": 0.9},
    # ADR 0060 (r7 N-2, D42 Mapillary 2018-07 / 2024-07 at g3b_eye_s1482 / s1632, reference only): the absorbing
    # cassettes along Andersa / Putry are dark powder-coated (anthracite / moss-green class), read near-black under the
    # glass panes; 0.30 read as a light grey wall. WORKING_VALUE (no RAL plate seen).
    "noise_panel": {"color": [0.05, 0.06, 0.055], "rough": 0.6, "metal": 0.1, "texture_set": "noise_cassette"},
    # ADR 0069 noise barriers after Mapillary p38/p40 (2024, overcast): cassettes 36-40 sRGB next to a plinth of 105
    # sRGB on the same vertical face -> linear ratio 0.135 x concrete_plinth 0.30 = 0.04; 0.07 keeps the cassette
    # relief readable on Low overcast (0.17 + metal 0.3 read near-black in r5). Posts 98/108/100 sRGB (green-grey).
    # ADR0086: with the corrected linear upload, the old bug-tuned .068/.072/.070
    # rose from 28/29/28 to 57/59/56 in High overcast (route-putry-entry-signs).
    # Candidate linear albedo below targets the photo's 36–40 display levels;
    # screen appearance calibration only, not a physical measurement of the paint.
    # ADR0101 (r2): that compared absolute levels with a brighter summer photo; the measured quantity is the
    # cassette/plinth ratio on one face (p40: 0.34-0.38). Back to the measured 0.04 (hue of the old .068/.072/.070),
    # checked as a ratio to the plinth on 2 cameras (tools/worldgen/qa/tint_ratio.py).
    "noise_panel_dark": {"color": [0.039, 0.041, 0.040], "rough": 0.7, "metal": 0.05, "texture_set": "noise_cassette"},
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
    # r10 (ADR 0078): "paint" = [base-coat metal, flake tilt, pearl, base-coat roughness] for the _CARPAINT layer of
    # Kamion/World PBR (clear coat = "rough"). Types, WORKING_VALUE (no Polish register of paint types): silver, grey
    # and blue metallic (aluminium flake), black pearl (mica, blue-violet at grazing angles), white and red solid
    # (white is the no-surcharge base colour of most ranges; the vans' whites are solid fleet paint).
    # r10b: dark paints lifted (black 0.018 -> 0.035, blue 0.03 / 0.05 / 0.12 -> 0.045 / 0.085 / 0.21, grey 0.13 -> 0.16):
    # under the ADR 0080 overcast the old values rendered as black silhouettes (review 0080 P1 #2); the Mapillary
    # crops in artifacts/cars-r9/refs show black / dark grey bodies clearly above the tyres. WORKING_VALUE.
    "car_paint_silver": {"color": [0.42, 0.43, 0.44], "rough": 0.28, "metal": 0.6, "texture_set": "car_grime_clean",
                         "paint": [0.85, 0.30, 0.0, 0.50]},
    "car_paint_grey": {"color": [0.16, 0.165, 0.17], "rough": 0.26, "metal": 0.5, "texture_set": "car_grime_clean",
                       "paint": [0.75, 0.28, 0.0, 0.50]},
    "car_paint_black": {"color": [0.035, 0.035, 0.038], "rough": 0.2, "metal": 0.3, "texture_set": "car_grime_clean",
                        "paint": [0.55, 0.22, 0.8, 0.45], "pearl_tint": [1.6, 1.9, 3.2]},
    "car_paint_white": {"color": [0.68, 0.68, 0.66], "rough": 0.3, "texture_set": "car_grime_clean",
                        "paint": [0.0, 0.0, 0.0, 0.5]},
    "car_paint_white2": {"color": [0.62, 0.63, 0.62], "rough": 0.36, "texture_set": "car_grime_clean",
                         "paint": [0.0, 0.0, 0.0, 0.5]},
    "car_paint_blue": {"color": [0.045, 0.085, 0.21], "rough": 0.24, "metal": 0.4, "texture_set": "car_grime_clean",
                       "paint": [0.70, 0.30, 0.0, 0.48]},
    "car_paint_red": {"color": [0.32, 0.03, 0.025], "rough": 0.28, "metal": 0.2, "texture_set": "car_grime_clean",
                      "paint": [0.0, 0.0, 0.0, 0.5]},
    "car_paint_green": {"color": [0.035, 0.07, 0.045], "rough": 0.35, "metal": 0.4, "texture_set": "car_grime"},
    "car_paint_beige": {"color": [0.36, 0.32, 0.24], "rough": 0.4, "metal": 0.3, "texture_set": "car_grime"},
    "car_glass": {"color": [0.012, 0.014, 0.016], "rough": 0.65},     # opaque (LOD1 / LOD2): does not mirror the sky
    # LOD0 car glazing: dark tint, alpha blended (importer: "blend"), the dark interior shows through
    # v4 (REVIEW r6 W-N8): transmission 0.35 per face onto the dark interior (both faces drawn), thinner dust film
    "car_glass_tint": {"color": [0.010, 0.016, 0.016], "rough": 0.05, "alpha": 0.65, "blend": True, "shader": "car_glass",
                       "dust": 0.35, "privacy_alpha": 0.80, "reflect": 1.0, "lens_alpha": 0.10},
    # road film overlays of car LOD0 / LOD1 (ADR 0041 par. 8): alpha texture x per-level alpha, three dirt levels
    # v4: darker grey-brown, lower alpha (the salt-pale level 3 at alpha 1.0 read as beige paint on red / dark cars)
    "car_dirt_1": {"color": [0.15, 0.13, 0.10], "rough": 1.0, "alpha": 0.45, "blend": True, "texture": "car_dirt"},
    "car_dirt_2": {"color": [0.16, 0.14, 0.11], "rough": 1.0, "alpha": 0.62, "blend": True, "texture": "car_dirt"},
    "car_dirt_3": {"color": [0.18, 0.165, 0.135], "rough": 1.0, "alpha": 0.78, "blend": True, "texture": "car_dirt"},
    "car_lamp": {"color": [0.045, 0.047, 0.05], "rough": 0.12, "metal": 0.5},     # smoked lamp housing behind the lens
    # alloy under brake dust (v4: 0.115 rendered as a black disc on LOD1 at 12-45 m on Low, read as "no rim")
    # ADR0089 WORKING_VALUE: neutral brake dust/rubber, old luminance retained; dark dish stays rim_dark/car_trim.
    "rim_dusty": {"color": [0.25, 0.25, 0.25], "rough": 0.58, "metal": 0.45},
    "tyre_dusty": {"color": [0.046, 0.046, 0.046], "rough": 0.95},
    # r10 (ADR 0078): LOD0 car tyres with the tread / sidewall texture (modulation, mean ~0.78; colour raised to match)
    "car_tyre": {"color": [0.033, 0.033, 0.033], "rough": 0.85, "texture": "car_tyre"},
    "car_tyre_dusty": {"color": [0.060, 0.060, 0.060], "rough": 0.95, "texture": "car_tyre"},
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
    # r12 (ADR 0092): "rough" of a curtain is now applied by the importer (mean roughness of the set scaled to it; before
    # the set's 0.64 was used whatever stood here). Matt PVC-coated fabric 0.82, the silver (aluminised) tarp 0.72;
    # metallic 0 (WORKING_VALUE, judged on the dock renders: no horizon line on a tarp in the shade of the hall).
    # ADR0086: explicit working pigments preserve ADR0092/s9 accepted matte curtain appearance.
    # Previous values were tuned through Unity Color double-gamma; these are their linear GPU values.
    "trailer_curtain_grey": {"color": [0.03310477, 0.03630648, 0.03630648], "rough": 0.82, "texture_set": "curtain_folds"},
    "trailer_curtain_blue": {"color": [0.00232198, 0.00489631, 0.0173891], "rough": 0.82, "texture_set": "curtain_folds"},
    "trailer_curtain_white": {"color": [0.26327341, 0.27383842, 0.26327341], "rough": 0.82, "texture_set": "curtain_folds"},
    "trailer_curtain_red": {"color": [0.02721178, 0.00350102, 0.00270898], "rough": 0.82, "texture_set": "curtain_folds"},
    "trailer_curtain_green": {"color": [0.00350102, 0.00719441, 0.00489631], "rough": 0.82, "texture_set": "curtain_folds"},
    "trailer_curtain_silver": {"color": [0.10653922, 0.11280479, 0.11280479], "rough": 0.72, "texture_set": "curtain_folds"},
    "trailer_box_white": {"color": [0.31854678, 0.33034371, 0.31854678], "rough": 0.45, "texture_set": "box_panel"},
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
    "trailer_front_dark": {"color": [0.075, 0.08, 0.085], "rough": 0.5, "metal": 0.3},
    "trailer_alu": {"color": [0.45, 0.46, 0.46], "rough": 0.4, "metal": 0.9},
    "trailer_doors": {"color": [0.50, 0.51, 0.50], "rough": 0.45, "metal": 0.3},
    "trailer_chassis": {"color": [0.03, 0.03, 0.032], "rough": 0.6, "metal": 0.5},
    "trailer_strap": {"color": [0.10, 0.10, 0.10], "rough": 0.6, "metal": 0.4},
    "reefer_unit": {"color": [0.48, 0.49, 0.48], "rough": 0.5},
    "reefer_grille": {"color": [0.03, 0.03, 0.03], "rough": 0.6, "texture_set": "louvre_slats"},   # r12: slats (importer stripes)
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
    # ADR 0094: soffit boarding under the eaves and verges of houses (white-grey PVC / painted boards). sky_occ x = 0:
    # the ambient of a face that looks down is not halved (ADR 0060) - with the halving a white soffit read 72 sRGB
    # under an overcast sky next to a wall of 140, a graphite one 24 ("black sail", review s9 P1-4)
    "soffit_boards": {"color": [0.55, 0.54, 0.51], "rough": 0.85, "sky_occ": [0.0, 0.0]},
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
    "chimney_brick": {"color": [0.20, 0.092, 0.07], "rough": 0.9, "texture_set": "brick", "set_tile": True},
    # behaton (I-shaped interlocking blocks) in truck yards (streetscape.paved)
    "yard_behaton": {"color": [0.23, 0.228, 0.22], "rough": 0.85, "surface": "paving_stones", "texture_set": "behaton_i_grey"},
    # decals on roads (markings layer, depth offset like the markings)
    "decal_oil": {"color": [0.02, 0.02, 0.02], "rough": 0.35, "decal": True, "texture_set": "oil_stain_alpha"},
    "decal_tyre": {"color": [0.018, 0.018, 0.017], "rough": 0.55, "decal": True, "texture_set": "tyre_scrub_alpha"},
    "marking_yard": {"color": [0.46, 0.46, 0.45], "rough": 0.7, "surface": "paint", "decal": True},   # worn yard paint on light pavers; 0.36 (r7) dropped line/paver contrast 1.54 -> 1.14 (review r7 part 2), back to 0.46
    "drain_grate": {"color": [0.035, 0.033, 0.03], "rough": 0.6, "decal": True, "procedural": "grate"},  # cast iron
    "decal_patch": {"color": [0.062, 0.062, 0.06], "rough": 0.85, "decal": True, "texture_set": "asphalt_patch"},
    # authored yard wear (streetscape.yard_wear, ADR 0071 r11). Relaid paving = the yard's own block set in another
    # tone (new blocks lighter, re-sanded oily ones darker; world-planar, so the bond runs through the patch edge);
    # soil washed against kerbs and wall feet is drawn with decal_tyre bands (no material of its own).
    # Sealant = bitumen in the saw cuts of the induction loops at the gate. Worn dock apron: darker, soiled cast
    # concrete with the 16 m crack layer (`cracks` = strength). WORKING_VALUE colours.
    # +7 % / -10 % of yard_behaton 0.23: the first render at +24 % / -24 % read as a white sheet / a hole at overcast
    # (the grading of ADR 0080 stretches mid-tone differences); the orthophoto rectangle is barely lighter than the yard
    "decal_yard_patch_light": {"color": [0.248, 0.245, 0.236], "rough": 0.85, "decal": True, "texture_set": "behaton_i_grey"},
    "decal_yard_patch_dark": {"color": [0.207, 0.205, 0.198], "rough": 0.85, "decal": True, "texture_set": "behaton_i_grey"},
    "decal_sealant": {"color": [0.02, 0.02, 0.02], "rough": 0.4, "decal": True},
    "yard_concrete_worn": {"color": [0.235, 0.232, 0.223], "rough": 0.85, "surface": "concrete",
                           "texture_set": "concrete_cast_5m_joints", "cracks": 0.7},
    # bridges (roads.meshing bridge_style overrides; CC0 photos of the Andersa viaducts, docs/REFERENCES.md)
    # hero depot hall Kwadrat Park (ADR 0071, streetscape.hero_depot; colours read off CC0 photos by Rakoon, Commons:
    # light grey horizontally profiled sheet, vermilion window / louvre frames and portals, glass-block strip lights)
    # r11 (review 2026-11-10 A3 / A7): `weather` = splash zone above the ground (UV0.y = metres above the facade
    # ground) + run-off streaks under the coping and the strip-window sills (TEXCOORD_1 of make_depot.py), like the
    # generated hall walls. 0.62 -> 0.56: the wall, the sky and the apron were one light grey (WORKING_VALUE; the CC0
    # photo 20210904_101250 shows the sheet clearly darker than the overcast sky).
    # r12 (ADR 0092): `panel_m` = cladding module of the set [panel length, course height] m: the macro tone drift is
    # quantised to it (one tone per panel + a butt joint line) instead of a smooth noise
    # ADR0101 (r2): under the linear _Tint contract (0086) 0.56 doubled the GPU albedo and the sunlit gate facade
    # clipped (252 sRGB, ribs lost). 0.37/0.38/0.38 (WORKING_VALUE) is checked as hall/sky ratio on a lit and a
    # shaded camera (overcast 0.6-0.88 like the CC0 photos, clear without clip; tools/worldgen/qa/tint_ratio.py).
    "kp_wall": {"color": [0.37, 0.38, 0.38], "rough": 0.5, "metal": 0.1, "texture_set": "sandwich_ribbed", "weather": True,
                "panel_m": [6.0, 1.0]},
    "kp_accent": {"color": [0.50, 0.075, 0.035], "rough": 0.55, "metal": 0.2},
    "kp_glass_block": {"color": [0.27, 0.29, 0.30], "rough": 0.3},
    "kp_roof_white": {"color": [0.52, 0.52, 0.50], "rough": 0.8},
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
    # hero fire station asset (ADR 0070, streetscape.hero_building): atlas on CC0 scans (colour = atlas mean, so the
    # calibrated-set tint is 1), alpha-tested fence / gate / lettering
    "fire_station": {"color": _set_mean("fire_station", [0.30, 0.33, 0.39]), "rough": 0.8,
                     "surface": "concrete", "texture_set": "fire_station"},
    "fire_station_alpha": {"color": [1.0, 1.0, 1.0], "rough": 0.6, "texture": "fire_station_alpha",
                           "alpha_cutoff": 0.5},
    "fire_station_thuja_shell": {"color": _hero_thuja_shell_tint(), "rough": 0.97,
                                 "texture": "hedge_shell_thuja", "alpha_cutoff": 0.5},
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
    "plaster_white": {"color": [0.76, 0.76, 0.74], "rough": 0.9, "texture_set": "plaster"},
    "plaster_band_grey": {"color": [0.26, 0.27, 0.27], "rough": 0.9, "texture_set": "plaster"},
    # retaining walls of the raised ramps (roads.profile.mark_walled_ramps): block-faced concrete
    "ramp_wall_blocks": {"color": [0.34, 0.33, 0.31], "rough": 0.9, "texture_set": "concrete_blocks_split"},
    # far-field backdrop beyond the 2x2 km region border (ADR 0085, streetscape.far_field): one merged submesh per
    # cardinal sector with linear albedo in COLOR_0.rgb, window-mode flag in COLOR_0.a (1 = block/office grid,
    # 0.75 = ribbon windows, 0 = windowless wall/roof/plinth/chimney/pylon), and bay x storey coordinates in TEXCOORD_1.
    "far_field_buildings": {"color": [1.0, 1.0, 1.0], "rough": 0.88, "base": "plaster_white", "vertex_color": True,
                            "window_grid": {"pitch_m": 3.0, "win_w": 0.48, "sill": 0.30, "head": 0.82,
                                            "uv": "TEXCOORD_1"},
                            "glass_color": [0.032, 0.038, 0.046]},
}

# ADR 0081 (r10 r2): Kamion/World PBR declares _Tint as a Color property, so Unity converts the value written by the
# importer from sRGB to linear a second time: every modulation material rendered at about colour ^ 2.2 (measured on
# the r1 renders: plaster_grey 0.36 -> 0.095, plaster_cream [0.55, 0.48, 0.33] -> [0.19, 0.15, 0.09]; an untextured
# material of 0.16 came out LIGHTER than the 0.36 wall above it). `tint_linear` makes the importer write the tint
# gamma-encoded so the shader multiplies by the linear colour of this table. Scoped to the building envelope (walls,
# roofs, doors) - the materials this task renders and reviews; the other modulation materials keep the look they
# were reviewed with until the lead switches the flag on globally (open point in the ADR).
_TINT_LINEAR = ("plaster_", "plinth_", "panel_concrete", "brick_red", "chimney_brick", "hall_wall_", "hall_plinth",
                "roof_tiles_", "roof_metal_", "wood_planks", "garage_door", "dock_door", "balcony_panel")
for _k, _v in M.items():
    if _k.startswith(_TINT_LINEAR) and "texture_set" in _v:
        _v["tint_linear"] = True
    # ADR 0091: the plaster scan is 2 m of wall; at the shader default (4 m) its trowel marks came out twice their size
    # and read as a coarse relief from the street (r11 r2 render) - same fix as brick in ADR 0081
    if _v.get("texture_set") == "plaster":
        _v["set_tile"] = True
        # ADR 0094: the walls' splash zone (0.6 m) was hidden behind the plinth (0.45-0.9 m); 1.2 m leaves a faint
        # soiled band above the plinth (-10 % at 0.6 m, 0 at 1.2 m) - the tone variation of a facade comes from here
        # and from the run-off streaks, not from the plaster tile (review s9 P1-2). WORKING_VALUE.
        if _k.startswith("plaster_"):
            _v["splash_h"] = 1.2

# ADR 0081 (r10 r2): run-off streaks under the attic coping also on the render / panel walls of flat-roofed blocks
# and offices (LOD0 only; the wall-top TEXCOORD_1 comes from buildings_mesh, the importer enables _RUNOFF)
for _k, _v in M.items():
    if (_k.startswith("plaster_") or _k == "panel_concrete") and "texture_set" in _v:
        _v["runoff"] = True

# LOD1 far facade materials <wall>__far_<kind> (buildings_mesh.lod1_wall): the wall colour + a window grid the
# shader draws from TEXCOORD_1 (one unit = one window bay x one storey; extras.window_grid in those units).
# Keep in sync with buildings_mesh.FAR_GRID / BLOCK_WALLS / OFFICE_WALLS (test_far_facade_materials).
SKY_OCC_STRUCT_X = 0.5
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
            # ADR 0081: the window zone is drawn from the storey rows of the facade_far set (modulation: wall colour x
            # neutral map, UV0 = row atlas metres, streetscape.facade_atlas.FAR_*), not from a shader grid
            M[f"{_w}__far_{_k}"] = {"color": M[_w]["color"], "rough": M[_w]["rough"], "base": _w,
                                    "texture_set": "facade_far", "set_tile": True, "tint_linear": True,
                                    "sky_occ": [SKY_OCC_STRUCT_X, 0.9]}

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


# ADR 0097 (zabudowa r5; additive block - the table above is shared with ADR 0086 / 0098, so the building changes of
# this round are applied here, in place, after it):
# - review 0094 P2-e "szczyt 251/241/210 (R przy klipie)" in High clear: plaster_cream albedo -8 % (the review's own
#   alternative to an exposure change, which belongs to the lighting work, ADR 0098). In place: the LOD1 far
#   materials share the colour list.
# - review 0094 P1-a / P2-g "rozbryzgu nie widać": the plinth 0.20 -> 0.24 (dark mineral plaster; the shader's splash
#   multiplier is fixed, so a lighter base is what makes 8-10 sRGB levels of splash) and its splash zone 0.5 -> 0.8 m.
#   WORKING_VALUE both.
M["plaster_cream"]["color"][:] = [round(c * 0.92, 4) for c in M["plaster_cream"]["color"]]
M["plinth_dark"]["color"][:] = [0.24, 0.24, 0.235]
M["plinth_dark"]["splash_h"] = 0.8
# ADR 0102: additive, furniture-only atlas bindings; existing shared pigments and the linear tint contract stay intact.
for _kind, _base in (("galv", "steel_galv"), ("grey", "steel_painted_grey"),
                     ("concrete", "concrete_pole"), ("bollard", "steel_painted")):
    M[f"furniture_{_kind}"] = {**M[_base], "texture": f"furniture_{_kind}"}
M["furniture_footing"] = {**M["concrete_base"], "texture": "furniture_concrete"}



# ADR 0107 (zabudowa r6; additive block, same rule as the ADR 0097 block above):
# - review 0097 P1-e "spody i boki płyt balkonowych 38-40 sRGB przy ścianie 100-150": the slab was raw concrete 0.30
#   with the ambient of its underside halved (SKY_OCC_STRUCT). Balcony slabs of the insulated blocks are rendered and
#   painted with the facade (light grey / off-white underside on the CC0 Putry photos, refs/cm121537425): albedo 0.52,
#   and no halving of the down-facing ambient (like soffit_boards, ADR 0094) - the ground SH term is already the dark
#   side of the ambient. WORKING_VALUE, target: underside >= 55-60 % of the wall luminance at overcast.
M["balcony_slab"]["color"][:] = [0.52, 0.515, 0.50]
M["balcony_slab"]["sky_occ"] = [0.0, 0.0]
# - review 0097 P2-n "dachówka: regularne pasy, jednolity ton": the 1.4 m roof_tiles set repeats its 7 x 4 tiles; a
#   macro tone drift of 7 m / 0.16 (importer `macro` = [size m, strength], as on brick_red: lots, weathering, moss on
#   the north slope) breaks the repeat over a slope. Tile roofs only - a pressed metal sheet is one tone. WORKING_VALUE.
for _k in ("roof_tiles_red", "roof_tiles_brown"):
    M[_k]["macro"] = [7.0, 0.16]


# ADR 0114 (zabudowa r7, house plots; additive block):
# - `plot_kit`: ONE alpha-clip atlas (streetscape.plot_kit, colours in the texture, sRGB) for every fence / gate /
#   garden plant of the single-family plots, so a chunk full of plots is one draw. Matt (rough 0.85, no metal): the
#   galvanised mesh of ADR 0107 (metal 0.9, albedo 0.40) clipped to white under the overcast sky (review 0107 P1-r7-b).
# - `plot_lawn`: the mown lawn inside a plot, a draped surface of the grass_verge set. Lighter and yellower than the
#   rough grass outside the fence (WORKING_VALUE, refs P13 / P19 / C04: a lawn reads ~1.3x the luminance of the
#   unmown verge next to it).
M["plot_kit"] = {"color": [1.0, 1.0, 1.0], "rough": 0.85, "texture": "plot_kit", "alpha_cutoff": 0.5}
M["plot_lawn"] = {"color": [0.150, 0.200, 0.060], "rough": 0.95, "surface": "grass", "texture_set": "grass_verge"}


# ADR0118 r1: asphalt-only overrides of the road material table (MATERIALS.update(M)).
# WORKING_VALUE: judged against local photo wheel/centre ratio 0.67, not measured physical albedo.
# No road generator/geometry change; fresh SMA deliberately has no old-road damage opt-in.
M["road_asphalt"] = {"color": [0.081, 0.08, 0.079], "rough": 0.9, "surface": "asphalt",
                     "texture_set": "asphalt_worn",
                     "asphalt_wear": {"tone": 0.90, "wheel_darkening": 0.45, "low_cracks": 1.0,
                                      "low_photo_detail": 0.75}}
# WORKING_VALUE: a 25 mm bituminous saw-cut seal, fresh darker fill and aged lighter aggregate.
# UV0 is normalised by yard_wear before chunking; base/normal textures still use world metres.
M["decal_patch"]["asphalt_patch_seam"] = {"width_m": 0.025, "darkening": 0.65,
                                         "fresh_tone": 0.88, "aged_tone": 1.08}
M["decal_patch"]["asphalt_wear"] = {"low_photo_detail": 0.75}
# Restore authored wheel wear (0099 halved it in C#). Keep all coefficients visible here.
# Glyphs share the transverse encoding: their readability is an explicit visual control, not a claimed fix.
from roads.standards import MARKING_LIFT as _ASPHALT_PAINT_LIFT
M["marking_white"] = {"color": [0.55, 0.55, 0.54], "rough": 0.65, "surface": "paint",
                      "texture_set": "asphalt_worn", "decal": True, "depth_offset_m": _ASPHALT_PAINT_LIFT,
                      "paint": {"wheel_wear": 0.85, "age_wear": 0.25, "dirt": 0.38, "line_w_m": 0.12,
                                "fresh_surface_from_road": True, "asphalt_underlay": True,
                                "fresh_wheel_scale": 0.0, "fresh_age_scale": 0.0,
                                "fresh_dirt_scale": 1.0, "fresh_underlay_scale": 0.9375},
                      "asphalt_wear": {"tone": 0.90, "wheel_darkening": 0.45, "low_cracks": 1.0,
                                       "low_photo_detail": 0.75, "wheel_polish": 0.6, "drip_band": 0.22}}
# WORKING_VALUE: 0.85 legacy opacity × 1.15 = 0.9775, only for roads.decals traffic-stop stains.
# Private-yard/gate/bus oil retains UV1.x=0 and the previous material response.
M["decal_oil"]["traffic_opacity_scale"] = 1.15

# ADR0118 r2: material-only road aliases; geometry belongs to roads/ (Claude).
# WORKING_VALUE: mineral film on kerbs, dry footway joints without oily-looking pools.
# Reuse existing Mask.B and macro on kerbs, existing _GRIME fetch on the footway.
# Yard paving / behaton and Kwadrat materials retain their original defaults.
M["curb_concrete"] = {"color": [0.28, 0.278, 0.27], "rough": 0.85, "surface": "concrete_kerb",
                      "texture_set": "kerb_concrete_1m",
                      "kerb_wear": {"joint_dirt": 0.35, "mineral_film": 0.16, "film_threshold": 0.55}}
M["sidewalk_paving"] = {"color": [0.26, 0.255, 0.245], "rough": 0.85, "surface": "paving_stones",
                        "texture_set": "paving_20x10_grey",
                        "ground_grime": {"damp_darkening": 0.18, "damp_threshold": 0.65,
                                         "joint_dirt": 0.45, "damp_gloss": 0.15}}
