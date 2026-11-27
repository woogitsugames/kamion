"""Measure and break down far_field triangle/submesh budgets across wave 12 (b116028eb),
pre-wave-13 merge (e5e39f1dd^1), wave 13 (e5e39f1dd), and current HEAD (fields4 + hvfar).

Read-only: reads git objects (`git show`) and existing `far_field_gis_cache.json` /
`border` height data without writing to `Data/Regions/*/generated` or `Data/raw/derived`.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))


def list_qa_paths(rev: str) -> list[str]:
    out = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", rev, "Data/Regions"],
        cwd=REPO, text=True,
    )
    return sorted(p for p in out.splitlines() if p.endswith("/generated/far_field_qa.json"))


def load_git_json(rev: str, path: str) -> dict:
    return json.loads(subprocess.check_output(["git", "show", f"{rev}:{path}"], cwd=REPO, text=True))


def summarise_qa(q: dict) -> dict:
    out = {}
    for tier in ("Low", "High"):
        t = q["tiers"][tier]
        bld = sum(s["by_material"].get("far_field_buildings", 0) for s in t["sectors"].values())
        for_ = sum(s["by_material"].get("forest_edge_mixed_far_atlas", 0) for s in t["sectors"].values())
        sky = t["skyline"]["triangles"]
        subs = [s["submeshes"] for s in t["sectors"].values()]
        out[tier] = {
            "total": t["total_triangles"],
            "bld": bld,
            "for": for_,
            "sky": sky,
            "subs_max": max(subs),
            "subs_sum": sum(subs) + (1 if sky > 0 else 0),
        }
    return out


def run_git_comparison(out_json: Path | None = None) -> dict:
    paths = list_qa_paths("e5e39f1dd")
    revs = ("b116028eb", "e5e39f1dd^1", "e5e39f1dd", "HEAD")
    rows = []
    for p in paths:
        reg = p.split("/")[2]
        snap = {r: summarise_qa(load_git_json(r, p)) for r in revs}
        w12, pre13, w13, head = (snap[r] for r in revs)
        dh = w13["High"]["total"] - w12["High"]["total"]
        dl = w13["Low"]["total"] - w12["Low"]["total"]
        pct_12_13 = dh / w12["High"]["total"] * 100.0
        pct_pre13 = (w13["High"]["total"] - pre13["High"]["total"]) / pre13["High"]["total"] * 100.0
        rows.append({
            "region": reg,
            "low_w12": w12["Low"]["total"],
            "low_pre13": pre13["Low"]["total"],
            "low_w13": w13["Low"]["total"],
            "low_delta": dl,
            "high_w12": w12["High"]["total"],
            "high_pre13": pre13["High"]["total"],
            "high_w13": w13["High"]["total"],
            "high_delta_w12": dh,
            "high_pct_w12": pct_12_13,
            "high_delta_pre13": w13["High"]["total"] - pre13["High"]["total"],
            "high_pct_pre13": pct_pre13,
            "d_bld_high": w13["High"]["bld"] - w12["High"]["bld"],
            "d_for_high": w13["High"]["for"] - w12["High"]["for"],
            "d_sky_high": w13["High"]["sky"] - w12["High"]["sky"],
            "w12": w12,
            "pre13": pre13,
            "w13": w13,
            "head": head,
        })
    pcts = sorted(r["high_pct_w12"] for r in rows)
    low_over_30k = [r["region"] for r in rows if r["low_w13"] > 30_000]
    sky_low_over = [r["region"] for r in rows if r["w13"]["Low"]["sky"] > 3_000]
    sky_high_over = [r["region"] for r in rows if r["w13"]["High"]["sky"] > 8_000]
    sub_over = [r["region"] for r in rows if r["w13"]["High"]["subs_max"] > 2 or r["w13"]["Low"]["subs_max"] > 2]
    summary = {
        "n_regions": len(rows),
        "w12_to_w13_high_pct": {
            "min": round(pcts[0], 2),
            "p25": round(pcts[len(pcts) // 4], 2),
            "median": round(pcts[len(pcts) // 2], 2),
            "p75": round(pcts[(3 * len(pcts)) // 4], 2),
            "max": round(pcts[-1], 2),
        },
        "low_delta_nonzero": [r["region"] for r in rows if r["low_delta"] != 0],
        "d_bld_high_nonzero": [r["region"] for r in rows if r["d_bld_high"] != 0],
        "d_sky_high_nonzero": [r["region"] for r in rows if r["d_sky_high"] != 0],
        "low_over_30k": low_over_30k,
        "sky_low_over_3k": sky_low_over,
        "sky_high_over_8k": sky_high_over,
        "submeshes_over_2": sub_over,
        "rows": rows,
    }
    if out_json is not None:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def measure_region_breakdown(
    region_id: str,
    *,
    emergent_step: tuple[float, float] | None = None,
    enable_emergent: bool = True,
    enable_end_trees: bool = True,
    impostor_max_d: float | None = None,
    enable_skirt: bool = True,
) -> dict:
    """Run far_field in-memory on read-only GIS cache for `region_id` and track triangles per category."""
    import shapely
    from roads import pipeline
    from streetscape import far_field as FF
    from streetscape import forest_hlod as FH

    reg = pipeline.load_region(region_id)
    ox, oy = float(reg["origin"]["x"]), float(reg["origin"]["y"])
    half = float(reg["bbox"]["width_m"]) / 2.0
    out_root = REPO / "Data" / "raw" / "derived" / region_id / "world"

    elev = FF.BorderElevation.from_region(region_id, half=half, out_root=out_root)
    cache_path = out_root / "far_field_gis_cache.json"
    gis = json.loads(cache_path.read_text(encoding="utf-8"))
    building_exclusion = FF.region_building_exclusion(region_id, ox, oy, half)
    stream_exclusion, _ = FF.streaming_building_exclusion(ox, oy)
    building_exclusion = shapely.union_all([building_exclusion, stream_exclusion])
    shapely.prepare(building_exclusion)
    render_buildings = [
        b for b in gis["buildings"]
        if FF.building_rectangle_outside_region(b["rect"], half, building_exclusion)
    ]
    plan = FF.power_plan(gis, half, region_id)
    ring_chm = FF.RingChm.for_region(region_id, ox, oy, FF.RING_MAX_M)
    landmark_stacks = FF.region_landmark_stacks(region_id, ox, oy)

    # Save and patch constants if testing reduction variants
    orig_em = FF.FAR_EMERGENT_STEP_M
    orig_imp_d = FF.FAR_IMPOSTOR_MAX_D_M
    orig_skirt_d = FF.FAR_SKIRT_MAX_D_M
    orig_add_imp = FF.SectorBuilder.add_tree_impostor1
    orig_add_curt = FF.SectorBuilder.add_curtain1
    orig_add_tri0 = FF.SectorBuilder.add_tri0
    orig_add_quad0 = FF.SectorBuilder.add_quad0

    current_cat = ["unknown"]
    cat_counts: dict[str, dict[str, int]] = {}
    current_tier = ["High"]

    def rec(cat: str, tris: int):
        t = current_tier[0]
        cat_counts.setdefault(t, {})[cat] = cat_counts.setdefault(t, {}).get(cat, 0) + int(tris)

    def wrapped_curtain(self, pts_xy, z_bot, z_top, face_sign=1.0, u_scale=48.0,
                        mat="forest_edge_mixed", u_shift=0.0, half=1024.0,
                        v_bot=0.0, v_top=None):
        before = sum(len(x) for x in self.t1)
        orig_add_curt(self, pts_xy, z_bot, z_top, face_sign, u_scale, mat, u_shift, half, v_bot, v_top)
        added = sum(len(x) for x in self.t1) - before
        subcat = "las_podszyt" if v_bot > 0.5 else "las_kurtyny_glowne_i_zebra"
        rec(subcat, added)

    def wrapped_impostor(self, e, n, z_bot, h_m, tree_name, yaw=0.0, half=1024.0):
        import inspect
        loc = inspect.currentframe().f_back.f_locals
        if "hf_" in loc and "fwd" in loc:
            subcat = "las_impostory_konce_biegu"
            if not enable_end_trees:
                return
        elif "back" in loc and "s_cur" in loc and "ek" in loc:
            subcat = "las_impostory_nad_okapem"
            if not enable_emergent:
                return
        else:
            subcat = "las_impostory_skraj"
        before = sum(len(x) for x in self.t1)
        orig_add_imp(self, e, n, z_bot, h_m, tree_name, yaw, half)
        added = sum(len(x) for x in self.t1) - before
        rec(subcat, added)

    def _cat0(self):
        return f"{current_cat[0]}_skyline" if self.uv1_flag else current_cat[0]

    def wrapped_tri0(self, a, b, c, col_rgba, uv1=None, normal=None):
        before = sum(len(x) for x in self.t0)
        orig_add_tri0(self, a, b, c, col_rgba, uv1, normal)
        added = sum(len(x) for x in self.t0) - before
        rec(_cat0(self), added)

    def wrapped_quad0(self, a, b, c, d, col_rgba, uv1=None, normal=None):
        before = sum(len(x) for x in self.t0)
        orig_add_quad0(self, a, b, c, d, col_rgba, uv1, normal)
        added = sum(len(x) for x in self.t0) - before
        rec(_cat0(self), added)

    try:
        if emergent_step is not None:
            FF.FAR_EMERGENT_STEP_M = emergent_step
        if impostor_max_d is not None:
            FF.FAR_IMPOSTOR_MAX_D_M = impostor_max_d
        if not enable_skirt:
            FF.FAR_SKIRT_MAX_D_M = -1.0
        FF.SectorBuilder.add_curtain1 = wrapped_curtain
        FF.SectorBuilder.add_tree_impostor1 = wrapped_impostor
        FF.SectorBuilder.add_tri0 = wrapped_tri0
        FF.SectorBuilder.add_quad0 = wrapped_quad0

        totals = {}
        for tier in ("High", "Low"):
            current_tier[0] = tier
            sectors = {name: FF.SectorBuilder(name) for name in FF.SECTORS}
            skyline = FF.SectorBuilder(FF.SKYLINE, uv1_flag=FF.SKYLINE_FLAG_CLAMP)
            chm_arg = ring_chm if tier == "High" else FF.RingChm(ring_chm.entries)

            current_cat[0] = "las_kopce_podkoronowe"
            for f in gis["forests"] + FF._corridor_treelines(half, region_id):
                FF._add_forest_stand(sectors, f["coords"], f.get("mix", "mixed"), elev, half, tier,
                                     ring_chm=chm_arg, region_id=region_id)

            current_cat[0] = "zabudowa_sektory"
            for b in render_buildings:
                FF._add_building(sectors, b, elev, half, tier, exclusion=building_exclusion, skyline=skyline)

            current_cat[0] = "kominy_sektory"
            for ch in gis["chimneys"]:
                if any(math.hypot(ch["e"] - st["e"], ch["n"] - st["n"]) < FF.SKYLINE_PROXY_MERGE_M for st in landmark_stacks):
                    continue
                FF._add_chimney(sectors, ch, elev, half, tier, skyline=skyline)
            current_cat[0] = "skyline_proxy"
            for st in landmark_stacks:
                FF._add_landmark_stack_proxy(skyline, st, elev, tier)

            hv_pylons, hv_spans = FF._select_far_hv(plan, half, tier)
            current_cat[0] = "wn_wieze_i_maszty"
            for py in hv_pylons:
                FF._add_pylon(sectors, py, elev, half, tier, yaw=float(py["yaw"]))
            for py in plan["masts"]:
                FF._add_pylon(sectors, py, elev, half, tier, yaw=float(py.get("yaw", 0.4)), arms=False)
            current_cat[0] = "wn_przewody"
            for a, b in hv_spans:
                FF._add_span(sectors, a, b, elev, half, tier)

            if tier == "High":
                mv_poles, mv_spans = FF._select_far_mv(plan, half)
                current_cat[0] = "sn_slupy"
                for s in mv_poles:
                    FF._add_pole(sectors, s, elev, half)
                current_cat[0] = "sn_przewody"
                for a, b in mv_spans:
                    FF._add_span(sectors, a, b, elev, half, tier, mv=True)

            # Also extract exact submesh totals + skyline split from SectorBuilder
            sec_bld, sec_for = 0, 0
            for name in FF.SECTORS:
                for p in sectors[name].primitives(half):
                    if p["mat"] == "far_field_buildings":
                        sec_bld += len(p["T"])
                    else:
                        sec_for += len(p["T"])
            sky_tris = sum(len(p["T"]) for p in skyline.primitives(half))
            totals[tier] = {
                "total": sec_bld + sec_for + sky_tris,
                "far_field_buildings": sec_bld,
                "forest_edge_mixed_far_atlas": sec_for,
                "skyline": sky_tris,
                "by_category": cat_counts.get(tier, {}),
            }
        return {"region": region_id, "tiers": totals}
    finally:
        FF.FAR_EMERGENT_STEP_M = orig_em
        FF.FAR_IMPOSTOR_MAX_D_M = orig_imp_d
        FF.FAR_SKIRT_MAX_D_M = orig_skirt_d
        FF.SectorBuilder.add_tree_impostor1 = orig_add_imp
        FF.SectorBuilder.add_curtain1 = orig_add_curt
        FF.SectorBuilder.add_tri0 = orig_add_tri0
        FF.SectorBuilder.add_quad0 = orig_add_quad0


def measure_forest_variants(region_id: str) -> dict:
    """Measure forest-only triangle counts on High tier across reduction variants using cached GIS (read-only)."""
    from roads import pipeline
    from streetscape import far_field as FF

    reg = pipeline.load_region(region_id)
    ox, oy = float(reg["origin"]["x"]), float(reg["origin"]["y"])
    half = float(reg["bbox"]["width_m"]) / 2.0
    out_root = REPO / "Data" / "raw" / "derived" / region_id / "world"
    elev = FF.BorderElevation.from_region(region_id, half=half, out_root=out_root)
    gis = json.loads((out_root / "far_field_gis_cache.json").read_text(encoding="utf-8"))
    ring_chm = FF.RingChm.for_region(region_id, ox, oy, FF.RING_MAX_M)
    forests = gis["forests"] + FF._corridor_treelines(half, region_id)

    orig_em = FF.FAR_EMERGENT_STEP_M
    orig_imp_d = FF.FAR_IMPOSTOR_MAX_D_M
    orig_add_imp = FF.SectorBuilder.add_tree_impostor1
    orig_add_curt = FF.SectorBuilder.add_curtain1
    orig_add_tri0 = FF.SectorBuilder.add_tri0

    def run_variant(
        *,
        emergent_step=orig_em,
        enable_emergent=True,
        enable_end_trees=True,
        end_max_q=3,
        end_min_run_m=8.0,
        emergent_max_d=None,
        impostor_max_d=orig_imp_d,
    ) -> dict:
        import inspect
        counts = {
            "las_kurtyny_glowne_i_zebra": 0,
            "las_podszyt": 0,
            "las_impostory_skraj": 0,
            "las_impostory_nad_okapem": 0,
            "las_impostory_konce_biegu": 0,
            "las_kopce_podkoronowe": 0,
        }

        def wrapped_curtain(self, pts_xy, z_bot, z_top, face_sign=1.0, u_scale=48.0,
                            mat="forest_edge_mixed", u_shift=0.0, half=1024.0,
                            v_bot=0.0, v_top=None):
            before = sum(len(x) for x in self.t1)
            orig_add_curt(self, pts_xy, z_bot, z_top, face_sign, u_scale, mat, u_shift, half, v_bot, v_top)
            counts["las_podszyt" if v_bot > 0.5 else "las_kurtyny_glowne_i_zebra"] += sum(len(x) for x in self.t1) - before

        def wrapped_impostor(self, e, n, z_bot, h_m, tree_name, yaw=0.0, half=1024.0):
            loc = inspect.currentframe().f_back.f_locals
            if "hf_" in loc and "fwd" in loc:
                if not enable_end_trees:
                    return
                if loc.get("q", 0) >= end_max_q:
                    return
                if loc.get("total_s", 0.0) < end_min_run_m:
                    return
                subcat = "las_impostory_konce_biegu"
            elif "back" in loc and "s_cur" in loc and "ek" in loc:
                if not enable_emergent:
                    return
                if emergent_max_d is not None and loc.get("dt_pt", 0.0) > emergent_max_d:
                    return
                subcat = "las_impostory_nad_okapem"
            else:
                subcat = "las_impostory_skraj"
            before = sum(len(x) for x in self.t1)
            orig_add_imp(self, e, n, z_bot, h_m, tree_name, yaw, half)
            counts[subcat] += sum(len(x) for x in self.t1) - before

        def wrapped_tri0(self, a, b, c, col_rgba, uv1=None, normal=None):
            before = sum(len(x) for x in self.t0)
            orig_add_tri0(self, a, b, c, col_rgba, uv1, normal)
            counts["las_kopce_podkoronowe"] += sum(len(x) for x in self.t0) - before

        try:
            FF.FAR_EMERGENT_STEP_M = emergent_step
            FF.FAR_IMPOSTOR_MAX_D_M = impostor_max_d
            FF.SectorBuilder.add_curtain1 = wrapped_curtain
            FF.SectorBuilder.add_tree_impostor1 = wrapped_impostor
            FF.SectorBuilder.add_tri0 = wrapped_tri0
            sectors = {name: FF.SectorBuilder(name) for name in FF.SECTORS}
            for f in forests:
                FF._add_forest_stand(sectors, f["coords"], f.get("mix", "mixed"), elev, half, "High",
                                     ring_chm=ring_chm, region_id=region_id)
            atlas_tris = (
                counts["las_kurtyny_glowne_i_zebra"]
                + counts["las_podszyt"]
                + counts["las_impostory_skraj"]
                + counts["las_impostory_nad_okapem"]
                + counts["las_impostory_konce_biegu"]
            )
            return {"forest_atlas_tris": atlas_tris, "by_category": counts}
        finally:
            FF.FAR_EMERGENT_STEP_M = orig_em
            FF.FAR_IMPOSTOR_MAX_D_M = orig_imp_d
            FF.SectorBuilder.add_tree_impostor1 = orig_add_imp
            FF.SectorBuilder.add_curtain1 = orig_add_curt
            FF.SectorBuilder.add_tri0 = orig_add_tri0

    specs = (
        ("A_head_fields4", {}),
        ("W12_baseline_no_r4_trees", {"enable_emergent": False, "enable_end_trees": False}),
        ("B1_no_end_trees", {"enable_end_trees": False}),
        ("B2_end_1tree_min24m_no_em_far", {"end_max_q": 1, "end_min_run_m": 24.0, "emergent_max_d": 1000.0}),
        ("B3_emergent_80_130_end_1tree_min24m", {"emergent_step": (80.0, 130.0), "end_max_q": 1, "end_min_run_m": 24.0}),
        ("B4_impostors_max_1050m", {"impostor_max_d": 1050.0}),
    )
    return {label: run_variant(**kw) for label, kw in specs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("git", "region", "variants"), default="git")
    ap.add_argument("--region", default="knyszyn-w")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    t0 = time.time()
    if args.mode == "git":
        res = run_git_comparison(args.out)
        print(f"54 tiles summary w12->w13 High %: {res['w12_to_w13_high_pct']}")
        print(f"low_delta_nonzero={res['low_delta_nonzero']}")
        print(f"d_bld_high_nonzero={res['d_bld_high_nonzero']}")
        print(f"d_sky_high_nonzero={res['d_sky_high_nonzero']}")
        print(f"low_over_30k={res['low_over_30k']}")
        print(f"sky_low_over_3k={res['sky_low_over_3k']} sky_high_over_8k={res['sky_high_over_8k']}")
    elif args.mode == "region":
        res = measure_region_breakdown(args.region)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.mode == "variants":
        out = measure_forest_variants(args.region)
        if args.out is not None:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")
        base = out["W12_baseline_no_r4_trees"]["forest_atlas_tris"]
        for label, d in out.items():
            at = d["forest_atlas_tris"]
            diff = at - base
            print(f"{label:36s}: atlas={at:6d} (vs w12: {diff:+6d}, {diff/base*100:+6.2f}%)  em={d['by_category']['las_impostory_nad_okapem']:5d}  end={d['by_category']['las_impostory_konce_biegu']:5d}  edge={d['by_category']['las_impostory_skraj']:5d}")
    print(f"Elapsed: {time.time() - t0:.2f} s")


if __name__ == "__main__":
    main()
