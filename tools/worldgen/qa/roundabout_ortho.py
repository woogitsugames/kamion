"""Kerb geometry of a roundabout measured on the GUGiK orthophoto WMS (ADR 0274; open data, numbers only - no pixel
is stored in git).

  probe:  uv run --project tools/worldgen python tools/worldgen/qa/roundabout_ortho.py probe <region> <ring_osm_way> <out.json>
          -> sheet date of the orthophoto at the ring centre, whether the roundabout is on it at all, and - only then -
             kerb-return radii between the arms and the splitter islands; always: carriageway width of every arm
             every 5 m along its graph axis (5-75 m from the split node).
  mask:   measure_mask(asphalt, res_m, center_px, r_axis_m, arm_bearings_rad) on any boolean raster (north up) - the
          same code measures a rasterised generator outline in tests/gis/test_roundabout_0274.py, so the generated
          roundabout and the photographed one are read with one ruler.

Method. One GetMap crop (WMS StandardResolution, layer Raster, EPSG:2180) of +-HALF m at RES m/px about the centre of
the ring (least-squares circle through the ring edges of roads.graph.json). Asphalt = grey pixels (saturation and
brightness near the median of the ring axis circle, not green; bright unsaturated paint counts as carriageway).
  * roundabout present: the disc r < ISLAND_PROBE_R about the centre is NOT asphalt (centre island) and the ring
    axis circle is. A plain crossroads has asphalt in the middle.
  * outer kerb: first non-asphalt pixel on rays from the centre (0.5 deg), beyond the ring axis. Sectors between
    two arms: the lowest part is the ring's outer kerb (r_out), each flank where the kerb leaves that circle is a
    kerb return - radius = least-squares circle through the flank points 0.4-8 m outside r_out.
  * splitter island of an arm: non-asphalt run across the arm axis (+-ISLAND_LAT m) between two asphalt lanes, at
    stations every 0.5 m outward from r_out; length = extent of stations with a run >= 0.6 m, width = its maximum.
  * arm widths: asphalt run through the axis on perpendicular profiles (median over +-2 m along the axis).
Reading accuracy: +-0.3 m at an asphalt edge (as tools/worldgen/qa/ortho_xsec.py, ADR 0272), radii +-15 %
(tests on synthetic rasters). Tree shadows, cars and light block paving next to the carriageway give wrong edges.
The date of the sheet comes from the index service SkorowidzeWgAktualnosci (GetFeatureInfo), not from the image.
"""
import io, json, math, re, sys, time, urllib.request
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
WMS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution"
INDEX = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/SkorowidzeWgAktualnosci"
UA = {"User-Agent": "osm-research-client/1.0"}
HALF, RES = 100.0, 0.1
ISLAND_PROBE_R = 2.5        # m: a centre island of any roundabout this size covers this disc
RAY_STEP_DEG, RAY_MAX_M = 0.5, 45.0
FLANK_M = (0.4, 8.0)        # kerb-return points this far outside the outer ring kerb enter the circle fit
ISLAND_LAT = 7.0


def _get(url, tries=4):
    for k in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()
        except Exception:
            time.sleep(2 ** (k + 1))
    raise SystemExit("WMS failed: " + url.split("?")[0])


def sheets(cx, cy):
    """Orthophoto sheets covering the point (index layers of the last three years): godlo, date, pixel size."""
    out = []
    for year in (2026, 2025, 2024):
        lay = f"SkorowidzeOrtofotomapy{year}"
        u = (f"{INDEX}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetFeatureInfo&LAYERS={lay}&QUERY_LAYERS={lay}&CRS=EPSG:2180"
             f"&BBOX={cy - 10},{cx - 10},{cy + 10},{cx + 10}&WIDTH=101&HEIGHT=101&I=50&J=50&INFO_FORMAT=text/html"
             f"&FEATURE_COUNT=10")
        t = _get(u).decode("utf-8", "replace")
        for m in re.finditer(r'godlo:"([^"]+)",\s*aktualnosc:"([^"]+)",\s*wielkoscPiksela:"([^"]+)"', t):
            row = {"index_layer": lay, "godlo": m.group(1), "date": m.group(2), "pixel_m": float(m.group(3))}
            if row not in out:
                out.append(row)
    return out


def crop(cx, cy, half=HALF, res=RES):
    from PIL import Image
    px = int(round(2 * half / res))
    u = (f"{WMS}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=Raster&STYLES=&CRS=EPSG:2180"
         f"&BBOX={cy - half},{cx - half},{cy + half},{cx + half}&WIDTH={px}&HEIGHT={px}&FORMAT=image/png")
    return np.asarray(Image.open(io.BytesIO(_get(u))).convert("RGB"), float)


def asphalt_mask(A, ref_px):
    """Boolean carriageway raster; `ref_px` = (rows, cols) of pixels known to be asphalt (ring axis circle)."""
    v = A.mean(axis=2)
    mx, mn = A.max(axis=2), A.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1)
    green = A[:, :, 1] - 0.5 * (A[:, :, 0] + A[:, :, 2])
    a_v, a_sat = float(np.median(v[ref_px])), float(np.median(sat[ref_px]))
    ok = (sat < a_sat + 0.07) & (np.abs(v - a_v) < 38) & (green < 6)
    return ok | ((v > a_v + 25) & (sat < 0.12)), {"asphalt_brightness": round(a_v, 1), "asphalt_saturation": round(a_sat, 3)}


def fit_circle(P):
    A = np.column_stack([2 * P, np.ones(len(P))])
    sol = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
    c = sol[:2]
    return c, float(math.sqrt(max(sol[2] + c @ c, 0.0)))


def _sample(mask, res, cpx, e, n):
    """mask value at metres east / north of the centre pixel (rows grow south)."""
    col = np.clip(np.round(cpx[0] + np.asarray(e) / res).astype(int), 0, mask.shape[1] - 1)
    row = np.clip(np.round(cpx[1] - np.asarray(n) / res).astype(int), 0, mask.shape[0] - 1)
    return mask[row, col]


def _run_through(ok, k0, tol=3):
    """index range [a, b] of the True run through index k0 (up to `tol` False samples bridged)."""
    ends = []
    for sgn in (-1, +1):
        k, last, miss = k0, k0, 0
        while 0 < k < len(ok) - 1 and miss <= tol:
            k += sgn
            if ok[k]:
                last, miss = k, 0
            else:
                miss += 1
        ends.append(last)
    return ends[0], ends[1]


def measure_mask(mask, res, cpx, r_axis, arm_bearings):
    """Kerb returns, outer ring radius and splitter islands of a roundabout on a boolean asphalt raster.
    `cpx` = (col, row) of the ring centre, bearings in radians (0 = east, counter-clockwise)."""
    rr = np.arange(0.0, ISLAND_PROBE_R, res)
    tt = np.radians(np.arange(0, 360, 5.0))
    centre = _sample(mask, res, cpx, rr[:, None] * np.cos(tt), rr[:, None] * np.sin(tt))
    t_ring = np.radians(np.arange(0, 360, 1.0))
    ring = _sample(mask, res, cpx, r_axis * np.cos(t_ring), r_axis * np.sin(t_ring))
    out = {"centre_disc_asphalt_share": round(float(centre.mean()), 3), "ring_axis_asphalt_share": round(float(ring.mean()), 3)}
    out["roundabout_visible"] = bool(centre.mean() < 0.4 and ring.mean() > 0.7)
    if not out["roundabout_visible"]:
        return out
    th = np.radians(np.arange(0.0, 360.0, RAY_STEP_DEG))
    d = np.arange(r_axis, RAY_MAX_M, res / 2)
    on = _sample(mask, res, cpx, d[None, :] * np.cos(th)[:, None], d[None, :] * np.sin(th)[:, None])
    first_off = np.where(on.all(axis=1), len(d) - 1, np.argmin(on, axis=1))
    kerb = d[first_off]
    bear = np.sort(np.mod(np.asarray(arm_bearings, float), 2 * math.pi))
    sectors = []
    for i in range(len(bear)):
        b0, b1 = bear[i], bear[(i + 1) % len(bear)]
        if b1 <= b0:
            b1 += 2 * math.pi
        sel = np.where((np.mod(th - b0, 2 * math.pi) < (b1 - b0)))[0]
        sel = sel[np.argsort(np.mod(th[sel] - b0, 2 * math.pi))]
        k = kerb[sel]
        r_out = float(np.percentile(k, 5))
        P = np.column_stack([k * np.cos(th[sel]), k * np.sin(th[sel])])
        low = int(np.argmin(k))
        rec = {"from_arm_deg": round(math.degrees(b0) % 360, 1), "to_arm_deg": round(math.degrees(b1) % 360, 1),
               "r_out_m": round(r_out, 2),
               "ring_kerb_arc_deg": round(float(((k < r_out + 0.3).sum()) * RAY_STEP_DEG), 1)}
        for name, idx in (("return_after_from_arm", np.arange(0, low)), ("return_before_to_arm", np.arange(low, len(k)))):
            pick = idx[(k[idx] > r_out + FLANK_M[0]) & (k[idx] < r_out + FLANK_M[1])]
            if len(pick) >= 6:
                c, R = fit_circle(P[pick])
                rec[name] = {"radius_m": round(R, 1), "points": int(len(pick)),
                             "rms_m": round(float(np.sqrt(np.mean((np.hypot(*(P[pick] - c).T) - R) ** 2))), 2)}
            else:
                rec[name] = None
        sectors.append(rec)
    out["sectors"] = sectors
    out["r_out_m"] = round(float(np.median([s["r_out_m"] for s in sectors])), 2)
    lat = np.arange(-ISLAND_LAT, ISLAND_LAT + 1e-9, res)
    k0 = len(lat) // 2
    arms = []
    for b in bear:
        u, nrm = np.array([math.cos(b), math.sin(b)]), np.array([-math.sin(b), math.cos(b)])
        st, wid = np.arange(out["r_out_m"], RAY_MAX_M - 1.0, 0.5), []
        for s in st:
            ok = _sample(mask, res, cpx, s * u[0] + lat * nrm[0], s * u[1] + lat * nrm[1])
            # the island is the widest False run that has asphalt on both sides within the profile
            best, k = 0.0, 0
            while k < len(ok):
                if not ok[k]:
                    j = k
                    while j < len(ok) and not ok[j]:
                        j += 1
                    if k > 0 and j < len(ok) and abs(lat[(k + j) // 2]) < 4.0:
                        best = max(best, (j - k) * res)
                    k = j
                else:
                    k += 1
            wid.append(best)
        wid = np.array(wid)
        has = wid >= 0.6
        if has.any():
            i0 = int(np.argmax(has))
            i1 = i0
            while i1 + 1 < len(has) and (has[i1 + 1] or (i1 + 2 < len(has) and has[i1 + 2])):
                i1 += 1
            arms.append({"bearing_deg": round(math.degrees(b), 1), "splitter_nose_from_ring_kerb_m": round(float(st[i0] - out["r_out_m"]), 1),
                         "splitter_len_m": round(float(st[i1] - st[i0] + 0.5), 1), "splitter_max_w_m": round(float(wid[i0:i1 + 1].max()), 1)})
        else:
            arms.append({"bearing_deg": round(math.degrees(b), 1), "splitter_len_m": 0.0})
    out["arms"] = arms
    return out


def arm_widths(mask, res, cpx, axis, d0=5.0, d1=75.0, step=5.0):
    """Asphalt width across an arm: `axis` = polyline (m east / north of the centre) from the split node outward;
    stations d m from the split node along it. Rows of (d, left, right, width); left = left of the outward direction."""
    axis = np.asarray(axis, float)
    seg = np.hypot(*np.diff(axis, axis=0).T)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    lat = np.arange(-14.0, 14.0 + 1e-9, res)
    al = np.arange(-2.0, 2.0 + 1e-9, 0.5)
    rows = []
    for dd in np.arange(d0, min(d1, cum[-1] - 2.0) + 1e-9, step):
        i = int(min(np.searchsorted(cum, dd, side="right") - 1, len(seg) - 1))
        u = (axis[i + 1] - axis[i]) / seg[i]
        p = axis[i] + u * (dd - cum[i])
        nrm = np.array([-u[1], u[0]])
        ok = np.median([_sample(mask, res, cpx, p[0] + a * u[0] + lat * nrm[0], p[1] + a * u[1] + lat * nrm[1])
                        for a in al], axis=0) > 0.5
        k0 = len(lat) // 2
        if not ok[k0 - 5:k0 + 6].any():
            rows.append({"d_m": float(dd), "asphalt_w_m": None})
            continue
        k0 = k0 if ok[k0] else int(k0 - 5 + np.argmax(ok[k0 - 5:k0 + 6]))
        a, b = _run_through(ok, k0)
        rows.append({"d_m": float(dd), "left_m": round(float(lat[b]), 2), "right_m": round(float(lat[a]), 2),
                     "asphalt_w_m": round(float(lat[b] - lat[a]), 2)})
    return rows


def ring_of(region, way):
    """(centre E/N EPSG:2180, axis radius, [(arm osm way, bearing rad, axis polyline)]) from roads.graph.json."""
    g = json.loads((REPO / "Data/Regions" / region / "roads.graph.json").read_text(encoding="utf-8"))
    ring = [e for e in g["edges"] if e["osm_way"] == way]
    if not ring:
        raise SystemExit(f"way {way} not in {region}")
    c, r = fit_circle(np.vstack([np.array(e["geometry"], float) for e in ring]))
    ring_nodes = {n for e in ring for n in (e["from"], e["to"])}
    feed = [e for e in g["edges"] if e["osm_way"] != way and ((e["from"] in ring_nodes) != (e["to"] in ring_nodes))]
    split = {(e["to"] if e["from"] in ring_nodes else e["from"]) for e in feed}
    arms = []
    for e in g["edges"]:
        if e in feed or e in ring or not ((e["from"] in split) != (e["to"] in split)):
            continue
        P = np.array(e["geometry"], float)
        P = P if e["from"] in split else P[::-1]
        far = P[min(len(P) - 1, 1)] if np.hypot(*(P[-1] - P[0])) < 5 else P[0] + (P[-1] - P[0]) / np.hypot(*(P[-1] - P[0])) * 5
        v = far - c
        arms.append({"osm_way": e["osm_way"], "bearing": float(math.atan2(v[1], v[0])), "axis": P - c,
                     "split_node_from_centre_m": round(float(np.hypot(*(P[0] - c))), 1)})
    return c, r, arms


def probe(region, way, out):
    c, r, arms = ring_of(region, int(way))
    A = crop(float(c[0]), float(c[1]))
    cpx = (A.shape[1] / 2 - 0.5, A.shape[0] / 2 - 0.5)
    t = np.radians(np.arange(0, 360, 1.0))
    ref = (np.clip(np.round(cpx[1] - r * np.sin(t) / RES).astype(int), 0, A.shape[0] - 1),
           np.clip(np.round(cpx[0] + r * np.cos(t) / RES).astype(int), 0, A.shape[1] - 1))
    mask, ref_stats = asphalt_mask(A, ref)
    res = {"tool": "tools/worldgen/qa/roundabout_ortho.py", "region": region, "ring_osm_way": int(way),
           "source": {"service": WMS, "layer": "Raster", "crs": "EPSG:2180", "crop_half_m": HALF, "res_m": RES,
                      "license": "GUGiK orthophoto, open data (docs/LICENSES.md); no pixel stored",
                      "sheets_at_centre": sheets(float(c[0]), float(c[1]))},
           "ring_axis": {"centre_epsg2180": [round(float(c[0]), 2), round(float(c[1]), 2)], "r_axis_m": round(r, 2)},
           "reference": ref_stats}
    res.update(measure_mask(mask, RES, cpx, r, [a["bearing"] for a in arms]))
    for a in arms:
        rows = arm_widths(mask, RES, cpx, a.pop("axis"))
        w = [q["asphalt_w_m"] for q in rows if q["asphalt_w_m"]]
        a["bearing_deg"] = round(math.degrees(a.pop("bearing")) % 360, 1)
        a["asphalt_w_median_m"] = round(float(np.median(w)), 2) if w else None
        a["stations"] = rows
    res["arm_carriageways"] = arms
    Path(out).write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("arm_carriageways", "sectors")}, ensure_ascii=False))
    for a in arms:
        print(a["osm_way"], a["bearing_deg"], a["asphalt_w_median_m"], [q["asphalt_w_m"] for q in a["stations"]])


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "probe":
        probe(*sys.argv[2:])
    else:
        raise SystemExit(__doc__)
