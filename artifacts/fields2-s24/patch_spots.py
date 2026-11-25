from pathlib import Path
p = Path("artifacts/fields2-s24/find_spots.py")
s = p.read_text(encoding="utf-8")
a = "def ground(e, n, z0):"
i = s.index(a); j = s.index("def ploughed(L):")
new = (
"tj = json.loads((d / 'terrain.json').read_text(encoding='utf-8'))\n"
"hm = np.fromfile(tj['encoding']['file'], dtype='<u2').reshape(tj['samples'][1], tj['samples'][0])\n\n\n"
"def ground(e, n, z0=None):\n"
"    i_ = int(round(e + ox - tj['bbox'][0])); j_ = int(round(tj['bbox'][3] - (n + oy)))\n"
"    if not (0 <= i_ < hm.shape[1] and 0 <= j_ < hm.shape[0]):\n"
"        return z0\n"
"    return float(tj['encoding']['offset_m'] + hm[j_, i_] * tj['encoding']['scale_m_per_unit'])\n\n\n")
s = s[:i] + new + s[j:]
tail = "print(len(out), \"cameras\")"
k = s.index(tail)
extra = (
"# tile-wide: the roomiest strip of each furrowed use, a standing camera along its rows and an oblique one above\n"
"hw = r['bbox']['width_m'] / 2 - 120\n"
"gx, gy = np.meshgrid(np.arange(-hw, hw, 12.0), np.arange(-hw, hw, 12.0))\n"
"G = np.column_stack([gx.ravel(), gy.ravel()])\n"
"G = G[VG.shapely.contains_xy(arable.buffer(-25.0), G[:, 0], G[:, 1])]\n"
"if len(G):\n"
"    L = VG.field_layout(G[:, 0] + ox, G[:, 1] + oy)\n"
"    u = VG.field_use(L, True)\n"
"    pl = ploughed(L)\n"
"    room = np.minimum(np.minimum(L['across'], L['w'] - L['across']), L['block_edge'] - 20.0)\n"
"    for name, m in (('ploughed', (u == VG.FIELD_USES.index('disked')) & pl), ('disked', (u == VG.FIELD_USES.index('disked')) & ~pl),\n"
"                    ('stubble', u == VG.FIELD_USES.index('stubble')), ('maize', u == VG.FIELD_USES.index('maize'))):\n"
"        if not m.any():\n"
"            continue\n"
"        b = int(np.argmax(np.where(m, room, -1e9)))\n"
"        q = G[b]; th = float(L['th'][b]); al = np.array([-np.sin(th), np.cos(th)]); nr = np.array([np.cos(th), np.sin(th)])\n"
"        zg = ground(q[0], q[1])\n"
"        qs = q - al * 6.0\n"
"        out.append({'id': f'f2_rows_{name}', 'type': 'persp', 'kind': 'field_side', 'pos': [round(float(qs[0]), 2), round(float(qs[1]), 2), round(ground(qs[0], qs[1]) + 1.7, 2)],\n"
"                    'look_at': [round(float(q[0] + al[0] * 14), 2), round(float(q[1] + al[1] * 14), 2), round(zg, 2)], 'fov_deg': 60.0, 'note': f'standing in a {name} strip, along its rows'})\n"
"        qc = q - nr * 22.0 - al * 10.0\n"
"        out.append({'id': f'f2_cross_{name}', 'type': 'persp', 'kind': 'field_side', 'pos': [round(float(qc[0]), 2), round(float(qc[1]), 2), round(ground(qc[0], qc[1]) + 2.5, 2)],\n"
"                    'look_at': [round(float(q[0] + nr[0] * 10), 2), round(float(q[1] + nr[1] * 10), 2), round(zg, 2)], 'fov_deg': 60.0, 'note': f'cab height 2.5 m, looking across the strips towards a {name} strip 22 m away'})\n"
"        qo = q - nr * 45.0 - al * 45.0\n"
"        out.append({'id': f'f2_obl_{name}', 'type': 'persp', 'kind': 'field_side', 'pos': [round(float(qo[0]), 2), round(float(qo[1]), 2), round(zg + 38.0, 2)],\n"
"                    'look_at': [round(float(q[0]), 2), round(float(q[1]), 2), round(zg, 2)], 'fov_deg': 60.0, 'note': f'oblique 38 m above a {name} strip'})\n"
"    # a headland: arable point 4 m inside a block border\n"
"    hd = np.abs(L['block_edge'] - 4.0) < 1.5\n"
"    if hd.any():\n"
"        b = int(np.flatnonzero(hd)[len(np.flatnonzero(hd)) // 2])\n"
"        q = G[b]; zg = ground(q[0], q[1])\n"
"        out.append({'id': 'f2_obl_headland', 'type': 'persp', 'kind': 'field_side', 'pos': [round(float(q[0] - 30), 2), round(float(q[1] - 30), 2), round(zg + 30.0, 2)],\n"
"                    'look_at': [round(float(q[0]), 2), round(float(q[1]), 2), round(zg, 2)], 'fov_deg': 60.0, 'note': 'oblique 30 m above a block border (headland / field track)'})\n"
)
s = s[:k] + extra + s[k:]
p.write_text(s, encoding="utf-8", newline="\n")
