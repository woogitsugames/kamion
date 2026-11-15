"""Fetch NMT 1 m (GUGiK WCS, KRON86) for bbox E0 E1 N0 N1 in 500 m tiles -> nmt.npy (row 0 = north) + meta json."""
import sys, os, json, io, time, urllib.request
import numpy as np
from PIL import Image
E0, E1, N0, N1 = map(int, sys.argv[1:5])
out = sys.argv[5]
U = ('https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF?SERVICE=WCS&VERSION=2.0.1'
     '&REQUEST=GetCoverage&COVERAGEID=DTM_PL-KRON86-NH_TIFF&FORMAT=image/tiff&SUBSET=x({},{})&SUBSET=y({},{})'
     '&SUBSETTINGCRS=http://www.opengis.net/def/crs/EPSG/0/2180')
W, H = E1 - E0, N1 - N0
A = np.full((H, W), np.nan, dtype=np.float32)
for e in range(E0, E1, 500):
    for n in range(N0, N1, 500):
        e2, n2 = min(e + 500, E1), min(n + 500, N1)
        url = U.format(e, e2, n, n2)
        for i in range(5):
            try:
                d = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'research-client/1.0 (generic)'}), timeout=300).read()
                a = np.array(Image.open(io.BytesIO(d)), dtype=np.float32)
                break
            except Exception as ex:
                print('retry', ex, file=sys.stderr)
                time.sleep(10 * (i + 1))
        r0 = N1 - n2
        A[r0:r0 + a.shape[0], e - E0:e - E0 + a.shape[1]] = a
        print('tile', e, n, a.shape, float(np.nanmin(a)), float(np.nanmax(a)))
np.save(out + '.npy', A)
json.dump({'E0': E0, 'N1': N1, 'cell': 1.0, 'crs': 'EPSG:2180 / PL-KRON86-NH', 'src': U.format('E1', 'E2', 'N1', 'N2')}, open(out + '.json', 'w'))
