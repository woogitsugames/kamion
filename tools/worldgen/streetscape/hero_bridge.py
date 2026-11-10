"""Hero viaducts: authored override `kind: hero_bridge` (ADR 0067).

A generic bridge (roads.meshing: flat soffit, painted band, railing, round piers by rule) is replaced by an authored
Blender asset that follows the generated road exactly:

  1. `plan()`   after the roads, profiles and the conformed terrain exist: writes the *spec* of every hero bridge
                (deck edge rails per station from the same formulas as the generic deck, ground heights, pier lines
                that avoid the carriageways underneath, segment cuts, all structural dimensions) to
                `Data/Regions/<id>/generated/landmarks/<asset>.spec.json` (git) and checks that the asset
                (`art-source/world/landmarks/<asset>/<asset>.glb` + `_meta.json`) was built from exactly this spec
                (sha256). A stale or missing asset is rebuilt with Blender when Blender is available
                (`KAMION_BLENDER` or `blender` on PATH); otherwise the bridge keeps its generic geometry and the
                override is reported as stale (manifest `overrides_stale`, streetscape QA `hero_bridges`).
  2. `apply()`  drops the generic soffit / fascia / railing of the hero chains (their ribbons are rebuilt with a
                shallow deck edge), skips their generic supports, adds one point instance per asset segment
                (prototype `landmark_<asset>_<k>`, LOD0/1/2 in the asset GLB), pier / abutment collision boxes and
                the triangle counts for the frame estimate.

The road surface, kerbs, caps, guard rails, retaining walls of the ramps and the road collision stay generated, so the
physics and the route corridor are unchanged. Every dimension without a source is a WORKING_VALUE in DEFAULTS
(read off the Mapillary reference frames of ADR 0065 by eye; pattern only, no pixels used).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np

from roads import meshing as M
from roads import standards as S

REPO = Path(__file__).resolve().parents[3]
KIND = "hero_bridge"
SCHEMA = "truck-sim-pl/hero-bridge-spec/1"
BLENDER_SCRIPT = REPO / "tools" / "blender" / "world" / "landmarks" / "make_viaduct.py"

# Structural dimensions in metres. All WORKING_VALUE unless noted: no drawings of the object are available, the
# values are proportions read off Mapillary frames 2818555625124739 / 504348097385466 (richlv, CC BY-SA 4.0,
# reference only) against the generated deck width (11.3 m per carriageway).
DEFAULTS = {
    "station_step_m": 4.0,
    "edge_depth_m": 0.50,        # generated deck edge face kept under the cornice (replaces 1.4 m)
    "cornice_h_m": 0.57,         # red precast cornice plate (top 2 cm above the cap)
    "cornice_proud_m": 0.03,
    "edge_beam_h_m": 0.14,       # grey drip beam under the cornice
    "cant_root_m": 3.40,         # lateral offset of the cantilever root from the deck centre
    "cant_root_drop_m": 0.92,    # below the cap top line
    "box_bottom_half_m": 2.00,   # half width of the box girder bottom flange
    "girder_depth_m": 1.55,      # below the cap top line (1.32 m below the carriageway edge; generic: 1.20 m)
    "span_target_m": 25.0,
    "pier_shift_max_m": 10.0,
    "col_offset_m": 1.30,        # two columns per deck, lateral offset from the deck centre
    "col_len_m": 0.80,           # along the bridge
    "col_wid_m": 1.00,           # across
    "col_chamfer_m": 0.12,
    "bearing_gap_m": 0.22,       # plinth + elastomeric bearing between column head and girder
    "abutment_t_m": 1.00,
    "rail_h_m": S.BRIDGE_PARAPET_H,
    "rail_inset_m": 0.15,
    "rail_post_m": 2.0,
    "pipe_d_m": 0.20,            # deck drainage collector under the low cantilever
    "pipe_offset_m": 4.35,
    "segment_target_m": 50.0,
    "lod_ends_m": [90.0, 300.0, 20000.0],   # at lodBias 1 (InstanceImporter.Policy / build_world.instance_ends)
}


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _r(v, n=3):
    return round(float(v), n)


def _chains(net, ways):
    out = []
    for c in net.chains:
        if c.meta.get("absorbed") or c.bridge is None or not c.bridge.any():
            continue
        if {str(e).split(":")[0].lstrip("w") for e, _ in c.edges} & ways:
            out.append(c)
    return sorted(out, key=lambda c: c.id)


def _run(c):
    """Longest contiguous elevated run of the chain inside its trimmed length: (s_a, s_b)."""
    s = c.line.s
    idx = np.where(c.bridge)[0]
    runs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
    run = max(runs, key=len)
    return max(float(s[run[0]]), c.t_a), min(float(s[run[-1]]), c.length - c.t_b)


def _walled(c, s):
    wl = c.meta.get("walled")
    return bool(wl is not None and c.interp(wl.astype(float), s) > 0.5)


def _open_range(c, sa, sb):
    """(s0, s1) of the part of the run that stands on piers (not on retaining walls), 0.25 m resolution."""
    ss = np.arange(sa, sb + 1e-6, 0.25)
    op = np.array([not _walled(c, x) for x in ss])
    if not op.any():
        return None
    i = np.where(op)[0]
    return float(ss[i[0]]), float(ss[i[-1]])


def _station(c, s):
    """Deck edge rails at station s: the cap outer top points (as roads.meshing.build_bridge_extras) and the
    carriageway edges."""
    p = np.asarray(c.line.point(s), float)
    t, n = c.line.frame(s)
    h = float(c.hw_at(s))
    out = {"s": _r(s), "c": [_r(p[0]), _r(p[1]), _r(c.zc(s))], "t": [_r(t[0], 5), _r(t[1], 5)]}
    for side, sgn in (("l", 1.0), ("r", -1.0)):
        prof = M.side_profile(*M.side_params(c, side.upper(), s))
        zg = float(c.crossfall_z(s, sgn * h))
        q = p + np.asarray(n) * sgn * (h + prof[-1][2])
        g = p + np.asarray(n) * sgn * h
        out[side] = [_r(q[0]), _r(q[1]), _r(zg + prof[-1][1])]
        out[side + "g"] = [_r(g[0]), _r(g[1]), _r(zg)]
    out["open"] = not _walled(c, s)
    return out


def build_spec(w, o, zground, blocked) -> dict | None:
    """Spec of one hero bridge. zground(e, n) -> conformed terrain height; blocked(q) -> True where a column may not
    stand (carriageway or paved surface underneath)."""
    prm = {**DEFAULTS, **(o.get("set") or {})}
    ways = {str(x) for x in o["target"]["osm_way"]}
    chains = _chains(w.net, ways)
    if not chains:
        return None
    lead = chains[0]
    la, lb = _run(lead)
    lop = _open_range(lead, la, lb)
    if lop is None:
        return None
    # pier lines on the lead deck, mirrored onto the other decks by projection (one transverse line of columns)
    span = lop[1] - lop[0]
    nsp = max(1, int(round(span / prm["span_target_m"])))
    runs = {c.id: _run(c) for c in chains}
    opens = {c.id: _open_range(c, *runs[c.id]) for c in chains}

    def cols_at(c, s):
        st = _station(c, s)
        mid = (np.array(st["l"][:2]) + np.array(st["r"][:2])) / 2
        nn = np.array(st["l"][:2]) - np.array(st["r"][:2])
        nn /= np.linalg.norm(nn)
        return [mid + nn * f * prm["col_offset_m"] for f in (-1.0, 1.0)]

    def on(c, p):
        s, _ = c.line.project(np.asarray(p, float))
        return float(s)

    shifts = [0.0]
    k = 2.0
    while k <= prm["pier_shift_max_m"] + 1e-6:
        shifts += [k, -k]
        k += 2.0
    lines, skipped = [], 0
    for i in range(1, nsp):
        s0 = lop[0] + span * i / nsp
        for sh in shifts:
            sl = s0 + sh
            if not (lop[0] + 6.0 < sl < lop[1] - 6.0):
                continue
            pl_ = np.asarray(lead.line.point(sl), float)
            per = {}
            ok = True
            for c in chains:
                sc = sl if c is lead else on(c, pl_)
                oc = opens[c.id]
                if oc is None or not (oc[0] + 3.0 < sc < oc[1] - 3.0):
                    per[c.id] = None          # this deck is on its ramp walls here
                    continue
                cc = cols_at(c, sc)
                if any(blocked(q) for q in cc):
                    ok = False
                    break
                per[c.id] = (sc, cc)
            if ok and any(v is not None for v in per.values()):
                if lines and abs(sl - lines[-1]["s_lead"]) < 8.0:
                    continue
                lines.append({"s_lead": sl, "per": per})
                break
        else:
            skipped += 1
    # segment cuts on the lead deck: run ends, both abutments, then every pier line that keeps segments near the
    # target length
    cuts = [la, lop[0]]
    for ln in lines:
        if ln["s_lead"] - cuts[-1] >= prm["segment_target_m"] - 6.0 and lop[1] - ln["s_lead"] >= 20.0:
            cuts.append(ln["s_lead"])
    cuts += [lop[1], lb]
    cuts = sorted(set(round(x, 3) for x in cuts))
    cuts = [x for i, x in enumerate(cuts) if i == 0 or x - cuts[i - 1] > 1.0]
    decks = []
    for c in chains:
        sa, sb = runs[c.id]
        oc = opens[c.id]
        rev = False
        if c is lead:
            cc = list(cuts)
        else:
            cc = [on(c, lead.line.point(x)) for x in cuts[1:-1]]
            rev = len(cc) > 1 and cc[0] > cc[-1]          # chain runs against the lead (opposite carriageway)
            cc = sorted(cc)
            cc = [sa] + [x for x in cc if sa + 1.0 < x < sb - 1.0] + [sb]
        keys = set(round(x, 3) for x in cc)
        if oc:
            keys |= {round(oc[0], 3), round(oc[1], 3)}
        piers = []
        for ln in lines:
            v = ln["per"].get(c.id)
            if v is None:
                continue
            sc, colsxy = v
            keys.add(round(sc, 3))
            st = _station(c, sc)
            piers.append({"s": _r(sc), "cols": [[_r(q[0]), _r(q[1]), _r(zground(q[0], q[1]))] for q in colsxy],
                          "top": _r((st["l"][2] + st["r"][2]) / 2 - prm["girder_depth_m"])})
        n = max(1, int(math.ceil((sb - sa) / prm["station_step_m"])))
        keys |= {round(x, 3) for x in np.linspace(sa, sb, n + 1)}
        ks = sorted(keys)
        ks = [x for i, x in enumerate(ks) if i == 0 or x - ks[i - 1] > 0.6 or x in set(round(y, 3) for y in cc)
              or (oc and x in (round(oc[0], 3), round(oc[1], 3)))]
        sts = []
        for x in ks:
            st = _station(c, x)
            for side in ("l", "r"):
                st["z" + side] = _r(zground(st[side][0], st[side][1]))
            st["zc"] = _r(zground(st["c"][0], st["c"][1]))
            sts.append(st)
        decks.append({"chain": c.id, "s_run": [_r(sa), _r(sb)], "s_open": [_r(oc[0]), _r(oc[1])] if oc else None,
                      "cuts": [_r(x) for x in cc], "reversed": bool(rev), "stations": sts,
                      "piers": sorted(piers, key=lambda p_: p_["s"])})
    mid = np.asarray(lead.line.point(0.5 * (lop[0] + lop[1])), float)
    spec = {
        "schema": SCHEMA, "id": o["id"], "asset": o["asset"],
        "frame": "local E, N (EPSG:2180 minus region origin), U absolute EVRF2007; metres",
        "region": w.region.get("id") or w.region.get("name"),
        "osm_ways": sorted(ways),
        "params": {k: prm[k] for k in sorted(prm)},
        "centre": [_r(mid[0]), _r(mid[1]), _r(lead.zc(0.5 * (lop[0] + lop[1])))],
        "decks": decks,
        "pier_lines": len(lines), "pier_lines_skipped": skipped,
        "confidence": {"axis_and_levels": "generated road (OSM axis, NMT, PTB2022 clearance): medium",
                       "structure": "WORKING_VALUE (Mapillary reference frames, by eye): low"},
    }
    return spec


def asset_paths(asset: str):
    d = REPO / "art-source" / "world" / "landmarks" / asset
    return d, d / f"{asset}.glb", d / f"{asset}_meta.json"


def spec_path(region_id: str, asset: str) -> Path:
    return REPO / "Data" / "Regions" / region_id / "generated" / "landmarks" / f"{asset}.spec.json"


def _asset_meta(asset, sha):
    _, glb, meta = asset_paths(asset)
    if not (glb.exists() and meta.exists()):
        return None, "missing"
    m = json.loads(meta.read_text(encoding="utf-8"))
    if m.get("spec_sha256") != sha:
        return None, "stale"
    if m.get("glb_sha256") != hashlib.sha256(glb.read_bytes()).hexdigest():
        return None, "glb_changed"
    return m, "ok"


def _blender():
    exe = os.environ.get("KAMION_BLENDER") or shutil.which("blender")
    return exe if exe and Path(exe).exists() else None


def rebuild_asset(spec_file: Path, log) -> bool:
    exe = _blender()
    if exe is None or os.environ.get("KAMION_NO_BLENDER"):
        return False
    log(f"hero bridge: asset stale -> blender {BLENDER_SCRIPT.name}")
    r = subprocess.run([exe, "-b", "--factory-startup", "-P", str(BLENDER_SCRIPT), "--", "--spec", str(spec_file)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        log("hero bridge: blender failed:", (r.stdout + r.stderr)[-600:])
        return False
    return True


def plan(w, region_id, overrides, zground, blocked, log=lambda *a: None) -> list:
    """[{override, spec, meta, chains}] of the hero bridges whose asset matches the current spec."""
    out = []
    rep = w.stats.setdefault("hero_bridges", {"applied": [], "stale": []})
    for o in overrides:
        if o.get("kind") != KIND:
            continue
        spec = build_spec(w, o, zground, blocked)
        if spec is None:
            rep["stale"].append({"id": o["id"], "why": "no elevated chain on the target ways"})
            w.net.overrides_stale.append(o["id"])
            continue
        sp = spec_path(region_id, o["asset"])
        sp.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(spec, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
        if not sp.exists() or sp.read_text(encoding="utf-8") != text:
            sp.write_text(text, encoding="utf-8", newline="\n")
        sha = _sha(spec)
        meta, why = _asset_meta(o["asset"], sha)
        if meta is None and why != "glb_changed" and rebuild_asset(sp, log):
            meta, why = _asset_meta(o["asset"], sha)
        if meta is None:
            rep["stale"].append({"id": o["id"], "why": f"asset {why}: run blender -b --factory-startup -P "
                                                       f"tools/blender/world/landmarks/make_viaduct.py -- --spec {sp.relative_to(REPO).as_posix()}"})
            w.net.overrides_stale.append(o["id"])
            log("hero bridge", o["id"], "STALE:", why, "- generic geometry kept")
            continue
        ways = set(spec["osm_ways"])
        out.append({"override": o, "spec": spec, "meta": meta, "sha": sha, "chains": _chains(w.net, ways)})
    return out


def chain_ids(heroes) -> set:
    return {c.id for h in heroes for c in h["chains"]}


def apply(w, heroes, instances: list, log=lambda *a: None) -> dict:
    """Swap the generic bridge dressing for the asset. Returns {prototype: {tris_lod0, tris_lod1, tris_lod2}}."""
    rep = w.stats.setdefault("hero_bridges", {"applied": [], "stale": []})
    tris = {}
    for h in heroes:
        o, spec, meta = h["override"], h["spec"], h["meta"]
        prm = spec["params"]
        removed = {"soffit": 0, "fascia": 0, "parapet": 0}
        for c in h["chains"]:
            # 1. rebuild the chain's ribbons with the shallow deck edge and without the generic dressing
            before = len(w.buf.parts)
            for p in w.buf.parts:
                if p.src.startswith(c.id + ":") and p.src.rsplit(":", 1)[-1] in removed:
                    removed[p.src.rsplit(":", 1)[-1]] += len(p.T)
            w.buf.parts = [p for p in w.buf.parts if not (p.src == c.id or p.src.startswith(c.id + ":"))]
            c.meta["hero"] = o["id"]
            br = c.bridge
            for side in ("L", "R"):
                d = c.side[side]["depth"]
                d[br] = np.minimum(d[br], prm["edge_depth_m"])
            M.build_ribbon(w.buf, w.net, c)
            M.build_ribbon(w.buf, w.net, c, coarse=True)
            log(f"hero bridge {o['id']}: chain {c.id} parts {before} -> {len(w.buf.parts)}")
        # 2. collision: columns and abutment walls (the deck surface is the generated road collision)
        nbox = 0
        for dk in spec["decks"]:
            sts = dk["stations"]
            for pr in dk["piers"]:
                st = min(sts, key=lambda s_: abs(s_["s"] - pr["s"]))
                for q in pr["cols"]:
                    M.box(w.buf, "collision", "collision_building", np.array(q[:2]), np.array(st["t"]),
                          prm["col_len_m"] / 2, prm["col_wid_m"] / 2, q[2] - 0.5, pr["top"], f"hero:{o['id']}:pier")
                    nbox += 1
            if dk["s_open"]:
                for sa_ in dk["s_open"]:
                    st = min(sts, key=lambda s_: abs(s_["s"] - sa_))
                    mid = (np.array(st["l"][:2]) + np.array(st["r"][:2])) / 2
                    hw = np.linalg.norm(np.array(st["l"][:2]) - np.array(st["r"][:2])) / 2
                    top = (st["l"][2] + st["r"][2]) / 2 - prm["girder_depth_m"]
                    inward = 1.0 if abs(sa_ - dk["s_open"][0]) < 1e-6 else -1.0     # wall sits behind the bearing line
                    ctr = mid - np.array(st["t"]) * inward * prm["abutment_t_m"] / 2
                    M.box(w.buf, "collision", "collision_building", ctr, np.array(st["t"]), prm["abutment_t_m"] / 2,
                          hw, min(st["zc"], st["zl"], st["zr"]) - 0.5, top, f"hero:{o['id']}:abutment")
                    nbox += 1
        # 3. instances: one per asset segment
        for seg in meta["segments"]:
            a = seg["anchor"]
            instances.append({"p": seg["name"], "e": _r(a[0]), "n": _r(a[1]), "z": _r(a[2]), "yaw": 0.0,
                              "src": f"override:{o['id']}"})
            tris[seg["name"]] = {"tris_lod0": seg["tris"][0], "tris_lod1": seg["tris"][1], "tris_lod2": seg["tris"][2]}
        w.net.overrides_applied.append({"id": o["id"], "targets": [f"w{x}" for x in spec["osm_ways"]]})
        rep["applied"].append({
            "id": o["id"], "asset": o["asset"], "spec_sha256": h["sha"], "glb_sha256": meta["glb_sha256"],
            "chains": [c.id for c in h["chains"]], "segments": len(meta["segments"]),
            "pier_lines": spec["pier_lines"], "pier_lines_skipped": spec["pier_lines_skipped"],
            "collision_boxes": nbox, "generic_tris_removed": removed,
            "tris": {f"lod{k}": int(sum(s_["tris"][k] for s_ in meta["segments"])) for k in range(3)},
            "materials": meta["materials"], "confidence": spec["confidence"]})
    return tris
