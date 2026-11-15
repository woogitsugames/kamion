"""Read ESRI ASCII grids (NMPT 0.5 m), mosaic and crop to bbox E0 E1 N0 N1 -> out.npy (row0 = north) + json."""
import sys, json
import numpy as np
E0, E1, N0, N1 = map(float, sys.argv[1:5])
out = sys.argv[5]
files = sys.argv[6:]
cs = None
res = None
for f in files:
    with open(f) as fh:
        hdr = {}
        for _ in range(6):
            k, v = fh.readline().split()
            hdr[k.lower()] = float(v)
        ncols, nrows = int(hdr['ncols']), int(hdr['nrows'])
        cs = hdr['cellsize']
        x0 = hdr['xllcorner'] if 'xllcorner' in hdr else hdr['xllcenter'] - hdr['cellsize'] / 2
        y0 = hdr['yllcorner'] if 'yllcorner' in hdr else hdr['yllcenter'] - hdr['cellsize'] / 2
        nod = hdr.get('nodata_value', -9999)
        # ASCII from GUGiK: x = E? check orientation by header print
        print(f, hdr, file=sys.stderr)
        ytop = y0 + nrows * cs
        if res is None:
            W = int(round((E1 - E0) / cs)); H = int(round((N1 - N0) / cs))
            res = np.full((H, W), np.nan, dtype=np.float32)
        r_start = int(np.floor((ytop - N1) / cs)); r_end = int(np.ceil((ytop - N0) / cs))
        c_start = int(np.floor((E0 - x0) / cs)); c_end = int(np.ceil((E1 - x0) / cs))
        rs, re_ = max(r_start, 0), min(r_end, nrows)
        cs_, ce = max(c_start, 0), min(c_end, ncols)
        if rs >= re_ or cs_ >= ce:
            print('no overlap', f, file=sys.stderr)
            continue
        for _ in range(rs):
            fh.readline()
        rows = []
        for _ in range(rs, re_):
            line = fh.readline()
            rows.append(np.array(line.split()[cs_:ce], dtype=np.float32))
        blk = np.vstack(rows)
        blk[blk == nod] = np.nan
        # target indices
        ty = int(round((N1 - (ytop - rs * cs)) / cs)); tx = int(round((x0 + cs_ * cs - E0) / cs))
        sub = res[ty:ty + blk.shape[0], tx:tx + blk.shape[1]]
        m = np.isnan(sub)
        sub[m] = blk[:sub.shape[0], :sub.shape[1]][m]
        print('placed', f, blk.shape, ty, tx, file=sys.stderr)
np.save(out + '.npy', res)
json.dump({'E0': E0, 'N1': N1, 'cell': cs}, open(out + '.json', 'w'))
print('nan share', float(np.isnan(res).mean()))
