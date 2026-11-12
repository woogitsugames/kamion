"""Prepare a reviewable patch without executing or changing production code.

Standard-library-only, low-impact text/AST work while the heavy checks wait.
Apply only after source-mesh identification and a verified Red test result.
"""
import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = 'tools/worldgen/streetscape/far_field.py'
SHADER = 'game/Assets/_Project/Rendering/Shaders/WorldSurface.shader'
original = {p:(ROOT/p).read_text(encoding='utf-8-sig') for p in (SOURCE,SHADER)}
changed = dict(original)


def replace(path, old, new):
    if changed[path].count(old) != 1:
        raise RuntimeError(f'Patch anchor must be unique: {path}: {old[:90]}')
    changed[path] = changed[path].replace(old,new)


replace(SOURCE, '\ndef _add_building(sectors:', '''
def _hall_appearance_class(b: dict) -> str:
    """WORKING_VALUE surface typology from declared use, never measured height.

    Function is GIS data; cladding, colours and glazing below are estimates.
    A large hall-shaped footprint alone does not establish an industrial use.
    """
    function = str(b.get("func") or "").casefold()
    if any(word in function for word in ("elektrociepł", "elektrown", "ciepłown", "kotłown")):
        return "energy"
    if any(word in function for word in (
            "przemysł", "produkc", "magazyn", "składow", "warsztat", "fabryk", "spalarn",
            "industrial", "warehouse", "manufactur", "factory", "storage", "workshop")):
        return "industrial"
    return "other"


def _add_building(sectors:''')
replace(SOURCE, '''        is_power_plant = "elektrociepł" in b.get("func", "").lower() or h_raw >= 22.0
        wall_rgb = (0.24, 0.10, 0.07) if is_power_plant else _hpick(bid, PALETTE_HALL, "wall")
        acc_rgb = _hpick(bid, PALETTE_HALL_ACCENT, "acc")
        use_fascia = tier == "High" or d_raw < 700.0
        z_fascia = (z_top - max(1.1 * s_h, h_eff * 0.16)) if use_fascia else z_top
        has_clerestory = _hfloat(bid, "clere") < 0.55
''', '''        appearance = _hall_appearance_class(b)
        industrial = appearance == "industrial"
        panel_hall = industrial and h_raw >= 12.0  # WORKING_VALUE appearance, not a measured facade
        wall_rgb = (0.24, 0.10, 0.07) if appearance == "energy" else _hpick(bid, PALETTE_HALL, "wall")
        # Unknown branding is not a reason for a bright 16%-height coloured stripe.
        acc_rgb = tuple(c * 0.72 for c in wall_rgb) if industrial else _hpick(bid, PALETTE_HALL_ACCENT, "acc")
        use_fascia = tier == "High" or d_raw < 700.0
        fascia_h = min(max(0.35 * s_h, 0.10), h_eff * 0.04) if industrial else max(1.1 * s_h, h_eff * 0.16)
        z_fascia = z_top - fascia_h if use_fascia else z_top
        has_clerestory = panel_hall or _hfloat(bid, "clere") < 0.55
''')
replace(SOURCE, '''                uv1 = [[0.0, -1.2], [float(bays), -1.2], [float(bays), 1.0], [0.0, 1.0]]
                sec.add_quad0([a[0], a[1], z_bot], [c[0], c[1], z_bot], [c[0], c[1], z_fascia], [a[0], a[1], z_fascia],
                              (*wall_rgb, 0.75), uv1=uv1)
            else:
                sec.add_quad0([a[0], a[1], z_bot], [c[0], c[1], z_bot], [c[0], c[1], z_fascia], [a[0], a[1], z_fascia],
                              (*wall_rgb, 0.0))
''', '''                # Only the top row is positive: do not invent a storey count.
                # The 4 m source-height module gives an estimated ~1.8 m upper
                # glazing band. Preserve the legacy contract for other halls.
                bottom_v = 1.0 - (z_fascia - z_bot) / max(4.0 * s_h, 0.1) if panel_hall else -1.2
                uv1 = [[0.0, bottom_v], [float(bays), bottom_v], [float(bays), 1.0], [0.0, 1.0]]
                sec.add_quad0([a[0], a[1], z_bot], [c[0], c[1], z_bot], [c[0], c[1], z_fascia], [a[0], a[1], z_fascia],
                              (*wall_rgb, 0.65 if panel_hall else 0.75), uv1=uv1)
            else:
                panel_uv = None
                if panel_hall:
                    # Explicit opaque-cladding payload: 1.2 m wide / 3 m high
                    # source modules, carried in the already-existing UV1.
                    columns = L_raw / 1.2
                    rows = (z_fascia - z_bot) / max(3.0 * s_h, 0.1)
                    panel_uv = [[0.0, 0.0], [columns, 0.0], [columns, rows], [0.0, rows]]
                sec.add_quad0([a[0], a[1], z_bot], [c[0], c[1], z_bot], [c[0], c[1], z_fascia], [a[0], a[1], z_fascia],
                              (*wall_rgb, 0.25 if panel_hall else 0.0), uv1=panel_uv)
''')
replace(SOURCE, '''  - Submesh 1 (`forest_edge_mixed`, Kamion/Vegetation _HLOD_EDGE):''', '''    Industrial cladding (ADR 0121 r5) reserves alpha 0.25 for opaque panels and 0.65 for panels with an upper ribbon;
    these WORKING_VALUE appearance markers use the existing UV1 and do not change measured height or footprint.
  - Submesh 1 (`forest_edge_mixed`, Kamion/Vegetation _HLOD_EDGE):''')
replace(SOURCE, '''    src_manifest = {
''', '''    appearance_policy = {
        "schema": "far-field-appearance/1",
        "status": "WORKING_VALUE",
        "not_measured": ["wall_colour", "cladding_modules", "glazing_band", "roof_fascia"],
        "classification": "declared function; height alone does not imply an energy plant",
        "industrial_panel_min_height_m": 12.0,
        "panel_alpha": 0.25,
        "panel_ribbon_alpha": 0.65,
        "source_hall_counts": {
            kind: sum(1 for b in gis["buildings"] if b["typ"] == "hall" and _hall_appearance_class(b) == kind)
            for kind in ("industrial", "energy", "other")
        },
        "source_panel_hall_count": sum(1 for b in gis["buildings"] if b["typ"] == "hall"
                                       and b["h"] >= 12.0 and _hall_appearance_class(b) == "industrial"),
    }
    src_manifest = {
''')
replace(SOURCE, '''        "adr": "0085-far-field-backdrop",
''', '''        "adr": "0085-far-field-backdrop",
        "appearance_policy": appearance_policy,
''')
replace(SOURCE, '''        "feature_counts": src_manifest["feature_counts"],
''', '''        "feature_counts": src_manifest["feature_counts"],
        "appearance_policy": appearance_policy,
''')
replace(SHADER, '''                    float2 g = i.uv1;
                    float2 bay = floor(g);
''', '''                    float2 g = i.uv1;
                    // ADR 0121 r5: explicit far-field industrial payload only.
                    // Legacy alpha 0 / 0.75 / 1 never enters this branch. No
                    // added channel, varying, texture, keyword or render pass.
                    half panelPlain = step(0.20h, i.masks.a) * step(i.masks.a, 0.30h);
                    half panelRibbon = step(0.60h, i.masks.a) * step(i.masks.a, 0.70h);
                    if (panelPlain + panelRibbon > 0.5h)
                    {
                        float2 panelUV = lerp(g, g * float2(10.0 / 3.0, 4.0 / 3.0), panelRibbon);
                        float2 panelFW = max(fwidth(panelUV), 1e-4);
                        float2 panelF = frac(panelUV);
                        float2 distanceToJoint = min(panelF, 1.0 - panelF);
                        float2 joint = saturate((0.012 - distanceToJoint) / panelFW + 0.5);
                        // At subpixel pitch use mean joint coverage, not a
                        // moire grid or a progressively darker whole facade.
                        joint = lerp(joint, float2(0.024, 0.024), saturate((panelFW - 0.5) * 2.0));
                        half jointCoverage = joint.x + joint.y - joint.x * joint.y;
                        float panelHash = frac(sin(dot(floor(panelUV), float2(12.9898, 78.233))) * 43758.5453);
                        half panelVariation = (panelHash - 0.5) * 0.045 * saturate(1.0 - max(panelFW.x, panelFW.y));
                        albedo *= 1.0h - 0.10h * jointCoverage + panelVariation;
                    }
                    float2 bay = floor(g);
''')

ast.parse(changed[SOURCE])
patch = ''.join(''.join(difflib.unified_diff(original[p].splitlines(keepends=True),
                                           changed[p].splitlines(keepends=True),
                                           fromfile='a/'+p,tofile='b/'+p)) for p in (SOURCE,SHADER))
(HERE/'candidate.patch').write_text(patch,encoding='utf-8',newline='\n')
(HERE/'far_field_candidate.py').write_text(changed[SOURCE],encoding='utf-8',newline='\n')
(HERE/'WorldSurface_candidate.shader').write_text(changed[SHADER],encoding='utf-8',newline='\n')
receipt = dict(production_edited=False, validation='Python AST only; shader not compiled, no rendered gain claim',
               source_files={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in (SOURCE,SHADER)},
               candidate_files={p:hashlib.sha256(changed[p].encode()).hexdigest() for p in (SOURCE,SHADER)},
               patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),
               gate='Apply only after baseline geometry identification and verified Red of the unchanged source')
(HERE/'candidate-preparation.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(dict(production_edited=False, patch_lines=len(patch.splitlines()))))
