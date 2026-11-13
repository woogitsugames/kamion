"""Check 3 (M37): terrain / height problems visible to the driver.

The raw NMT heightmap (Data/raw/.../heightmap_2049.r16) is NOT in git (LFS/raw, gitignored), so this check
works from the generator's own committed QA aggregates plus building ground heights:

  road_profile_deviation  chain whose generated profile deviates from NMT by profile_rms_vs_nmt_m > 0.50 m
                          (road buried in / floating above the terrain; NMT's own error is 0.09 m);
  road_grade_exceeded     chain whose max_grade exceeds its class grade_limit (niweleta too steep);
  terrain_wall            exposed terrain "skirt"/steep face higher than terrain_wall_max_m, surfaced from the
                          existing terrain_walls_qa.json (the mesh-level detection itself stays there - not
                          duplicated, only reported as driver-visible findings).

WORKING_VALUE thresholds are in common.PARAMS. Building ground_z vs terrain is NOT checkable from git data
(the NMT heightmap is in Data/raw, gitignored); noted as a limitation in the report.
"""

from __future__ import annotations

from .common import PROFILE_RMS_MAX_M, TERRAIN_WALL_MAX_M, Finding, World


def check(w: World) -> list[Finding]:
    findings: list[Finding] = []
    edge_by_id = {e["id"]: e for e in w.edges}

    for ch in w.chains_qa:
        cid = ch.get("id", "")
        edge = edge_by_id.get(cid[2:] if cid.startswith("c:") else cid)
        if edge and len(edge["coords"]) >= 2:
            mid = edge["coords"][len(edge["coords"]) // 2]
            e, n = mid
        else:
            e = n = 0.0
        rms = ch.get("profile_rms_vs_nmt_m")
        if rms is not None and float(rms) > PROFILE_RMS_MAX_M:
            findings.append(Finding("road_profile_deviation", e, n, cid,
                                    f"profile RMS vs NMT {float(rms):.2f} m > {PROFILE_RMS_MAX_M:.2f} m "
                                    f"(road buried / floating); highway={ch.get('highway')}",
                                    severity="warn", extra={"profile_rms_vs_nmt_m": float(rms)}))
        g, lim = ch.get("max_grade"), ch.get("grade_limit")
        if g is not None and lim is not None and float(g) > float(lim) + 1e-9:
            findings.append(Finding("road_grade_exceeded", e, n, cid,
                                    f"max_grade {float(g) * 100:.1f} % > class limit {float(lim) * 100:.1f} %",
                                    severity="error", extra={"max_grade": float(g), "grade_limit": float(lim)}))

    tw = w.terrain_walls or {}
    # Integration r6: the generator's own wall threshold (terrain_walls_qa.json thresh_m = 0.15 m) - with the
    # 0.50 m WORKING_VALUE the 4 known walls of ADR 0146 Open (0.317-0.345 m) were never reported.
    wall_max = float(tw.get("thresh_m", TERRAIN_WALL_MAX_M))
    for item in tw.get("worst", []):
        h = float(item.get("h", 0.0))
        if h > wall_max:
            findings.append(Finding("terrain_wall", float(item["e"]), float(item["n"]), str(item.get("src", "")),
                                    f"terrain wall {h:.2f} m high (kind={item.get('kind')}, mat={item.get('mat')}) "
                                    f"> {wall_max:.2f} m", severity="warn",
                                    extra={"h_m": h, "kind": item.get("kind"), "mat": item.get("mat")}))
    vs = tw.get("verge_strips") or {}
    if isinstance(vs.get("max_m"), (int, float)) and float(vs["max_m"]) > TERRAIN_WALL_MAX_M and vs.get("worst"):
        wv = vs["worst"]
        if isinstance(wv, list) and len(wv) >= 4:   # [kind, id, e, n] (r6: was >= 5, so never reported)
            findings.append(Finding("terrain_wall", float(wv[2]), float(wv[3]), str(wv[1]),
                                    f"verge strip {wv[0]} max {float(vs['max_m']):.2f} m > {TERRAIN_WALL_MAX_M:.2f} m",
                                    severity="info", extra={"h_m": float(vs["max_m"]), "kind": str(wv[0])}))

    # Building ground_z vs terrain cannot be checked here: the NMT heightmap lives in Data/raw (not in git).
    # When Data/raw is available, sample terrain.json's grid under each building centroid and compare.
    return findings
