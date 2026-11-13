#!/usr/bin/env python3
"""P12: GUGiK LoD1-2024 CityGML (2061.zip) -> data/lod1-wysokosci.json.
Źródło: https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD1/2024/20/2061.zip (CC BY 4.0).
Wyciąga buildingId, measuredHeight, roofType i footprint dla budynków w kafel+150 m."""
import zipfile, json, re, sys
import xml.etree.ElementTree as ET
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from epsg2180 import tm_inverse

X0, Y0, X1, Y1 = 778660, 589590, 780660, 591590
PAD = 150
NSB = '{http://www.opengis.net/citygml/building/2.0}'
NS_G = '{http://www.opengis.net/citygml/generics/2.0}'
NS_GML = '{http://www.opengis.net/gml}'

def main(zippath):
    z = zipfile.ZipFile(zippath)
    out = []
    for name in z.namelist():
        data = z.read(name)
        m = re.search(rb'<gml:lowerCorner>([^<]+)</gml:lowerCorner>s*<gml:upperCorner>([^<]+)</gml:upperCorner>', data)
        if m:
            lc = [float(v) for v in m.group(1).split()]
            uc = [float(v) for v in m.group(2).split()]
            if lc[0] > X1 + PAD or uc[0] < X0 - PAD or lc[1] > Y1 + PAD or uc[1] < Y0 - PAD:
                continue
        root = ET.fromstring(data)
        for b in root.iter(NSB + 'Building'):
            bid = None
            for sa in b.iter(NS_G + 'stringAttribute'):
                if sa.get('name') == 'buildingId':
                    v = sa.find(NS_G + 'value')
                    if v is not None: bid = v.text
            h = b.find(NSB + 'measuredHeight')
            mh = h.text if h is not None else None
            rt = b.find(NSB + 'roofType')
            coords = None
            for pl in b.iter(NS_GML + 'posList'):
                if pl.text:
                    t = pl.text.split()
                    if len(t) >= 6 and float(t[2]) < 1e6:
                        coords = t; break
            if not coords: continue
            xs = [float(coords[i]) for i in range(0, len(coords), 3)]
            ys = [float(coords[i]) for i in range(1, len(coords), 3)]
            if min(xs) > X1 + PAD or max(xs) < X0 - PAD or min(ys) > Y1 + PAD or max(ys) < Y0 - PAD: continue
            cx = sum(xs) / len(xs); cy = sum(ys) / len(ys)
            la, lo = tm_inverse(cx, cy)
            out.append({'buildingId': bid, 'h': mh, 'roofType': rt.text if rt is not None else None,
                        'cx': round(cx, 1), 'cy': round(cy, 1), 'lat': round(la, 6), 'lon': round(lo, 6)})
    json.dump(out, open('data/lod1-wysokosci.json', 'w'))
    print('LoD1 budynków:', len(out))

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'lod1.zip')
