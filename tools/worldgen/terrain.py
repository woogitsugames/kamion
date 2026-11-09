"""Terrain heightmap from GUGiK NMT (ARC/INFO ASCII GRID, 1 m, PL-1992 + PL-EVRF2007-NH).

The NMT sheets use `xllcenter/yllcenter` at integer metres, so grid nodes coincide with integer
EPSG:2180 coordinates. The tile bbox has integer corners, so the heightmap is an exact *sample*
of the source grid (no interpolation) with (W+1) x (H+1) nodes: node (i, j) is at
x = xmin + i, y = ymax - j (row 0 = north edge, image order).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

NODATA = -9999.0


def read_asc(path: Path) -> tuple[dict, np.ndarray]:
    text = path.read_bytes()
    hdr, pos = {}, 0
    for _ in range(6):
        end = text.index(b"\n", pos)
        k, v = text[pos:end].split()
        hdr[k.decode().lower()] = float(v)
        pos = end + 1
    data = np.array(text[pos:].split(), dtype=np.float32)
    nrows, ncols = int(hdr["nrows"]), int(hdr["ncols"])
    data = data.reshape(nrows, ncols)
    if "xllcorner" in hdr:  # convert to centre convention
        hdr["xllcenter"] = hdr.pop("xllcorner") + hdr["cellsize"] / 2
        hdr["yllcenter"] = hdr.pop("yllcorner") + hdr["cellsize"] / 2
    return hdr, data


def mosaic_nodes(sheets: list[Path], bbox, step: float = 1.0) -> np.ndarray:
    """Return heights at integer nodes of bbox (row 0 = north). NaN where no data."""
    x0, y0, x1, y1 = bbox
    w = int(round((x1 - x0) / step)) + 1
    h = int(round((y1 - y0) / step)) + 1
    out = np.full((h, w), np.nan, dtype=np.float64)
    for p in sorted(sheets):
        hdr, d = read_asc(p)
        cs = hdr["cellsize"]
        if abs(cs - step) > 1e-9:
            raise ValueError(f"{p.name}: cellsize {cs} != {step}")
        nrows, ncols = d.shape
        sx0 = hdr["xllcenter"]
        sy_top = hdr["yllcenter"] + (nrows - 1) * cs
        # overlap in node indices
        ox = np.arange(w) * step + x0                     # tile node x
        oy = y1 - np.arange(h) * step                     # tile node y (north->south)
        ci = np.rint((ox - sx0) / cs).astype(int)
        rj = np.rint((sy_top - oy) / cs).astype(int)
        okx = (ci >= 0) & (ci < ncols) & (np.abs(sx0 + ci * cs - ox) < 1e-6)
        oky = (rj >= 0) & (rj < nrows) & (np.abs(sy_top - rj * cs - oy) < 1e-6)
        if not okx.any() or not oky.any():
            continue
        sub = d[np.ix_(rj[oky], ci[okx])].astype(np.float64)
        sub[sub <= NODATA + 1] = np.nan
        tgt = out[np.ix_(np.where(oky)[0], np.where(okx)[0])]
        fill = np.isnan(tgt) & ~np.isnan(sub)
        # where both sheets have data they must agree (overlapping sheet margins)
        both = ~np.isnan(tgt) & ~np.isnan(sub)
        if both.any():
            diff = np.nanmax(np.abs(tgt[both] - sub[both]))
            if diff > 0.05:
                print(f"[terrain] WARNING {p.name}: overlap disagreement up to {diff:.3f} m")
        tgt[fill] = sub[fill]
        out[np.ix_(np.where(oky)[0], np.where(okx)[0])] = tgt
    return out


def encode_u16(z: np.ndarray) -> tuple[np.ndarray, dict]:
    """Quantise heights to uint16: z = offset + value * scale. Offset/scale rounded for readability."""
    zmin, zmax = float(np.nanmin(z)), float(np.nanmax(z))
    offset = float(np.floor(zmin) - 1.0)
    span = float(np.ceil(zmax) + 1.0) - offset
    scale = span / 65535.0
    q = np.rint((z - offset) / scale)
    q = np.clip(np.nan_to_num(q, nan=0), 0, 65535).astype("<u2")
    return q, {"offset_m": offset, "scale_m_per_unit": scale, "span_m": span,
               "quantisation_step_mm": round(scale * 1000, 4)}


def hillshade(z: np.ndarray, cell=1.0, az_deg=315.0, alt_deg=45.0, zf=1.0) -> np.ndarray:
    gy, gx = np.gradient(np.nan_to_num(z, nan=np.nanmean(z)) * zf, cell)
    slope = np.pi / 2 - np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = np.radians(az_deg), np.radians(alt_deg)
    hs = np.sin(alt) * np.sin(slope) + np.cos(alt) * np.cos(slope) * np.cos(az - aspect)
    return np.clip(hs, 0, 1)


def sample(z: np.ndarray, bbox, x: float, y: float) -> float:
    """Bilinear sample of node grid at EPSG:2180 point."""
    x0, _, _, y1 = bbox
    fx, fy = x - x0, y1 - y
    i, j = int(np.floor(fx)), int(np.floor(fy))
    if i < 0 or j < 0 or i + 1 >= z.shape[1] or j + 1 >= z.shape[0]:
        return float("nan")
    tx, ty = fx - i, fy - j
    a = z[j, i] * (1 - tx) + z[j, i + 1] * tx
    b = z[j + 1, i] * (1 - tx) + z[j + 1, i + 1] * tx
    return float(a * (1 - ty) + b * ty)
