"""ADR 0095 patch 4: width profile along an edge (`width: [[t, w], ...]`) + kerb_merge overrides using it."""
import io


def rd(p):
    return io.open(p, encoding="utf-8").read()


def wr(p, s):
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def rep(s, old, new):
    assert s.count(old) == 1, (s.count(old), old[:90])
    return s.replace(old, new)


p = "tools/worldgen/roads/network.py"
s = rd(p)
s = rep(s, '''    center_offset_profile: list | None = None  # authored: [[t, offset], ...], t = 0..1 along the edge (ADR 0095)''',
        '''    center_offset_profile: list | None = None  # authored: [[t, offset], ...], t = 0..1 along the edge (ADR 0095)
    width_profile: list | None = None          # authored: [[t, width], ...] along the edge (ADR 0095); `width` = max''')
s = rep(s, '''            if "width" in st:
                # measured carriageway width (orthophoto): lanes keep their count, lane width follows
                sec.width = float(st["width"])''', '''            if "width" in st and isinstance(st["width"], (list, tuple)):
                # ADR 0095: measured width varying along the edge, [[t, w], ...] with t = 0..1 in the edge direction
                # (a ramp lane that widens beside a painted gore); lane layout keeps using the widest value
                sec.width_profile = sorted((float(t), float(v)) for t, v in st["width"])
                sec.width = max(v for _, v in sec.width_profile)
                sec.lane_w = round((sec.width - 2 * sec.edge_strip) / max(sec.lanes, 1), 3)
                sec.width_src = f"authored_override:{ov['id']} (profile)"
            elif "width" in st:
                # measured carriageway width (orthophoto): lanes keep their count, lane width follows
                sec.width = float(st["width"])''')
s = rep(s, '''    hw = np.array([sl[i].width / 2 for i in c.sec_idx])
''', '''    hw = np.array([sl[i].width / 2 for i in c.sec_idx])
    for i_sp, (a0, a1, eid, rv) in enumerate(c.raw_spans):
        pr = net.sections[eid].width_profile
        if pr:
            m = k == i_sp
            t = np.clip((s_raw[m] - a0) / max(a1 - a0, 1e-6), 0.0, 1.0)
            hw[m] = np.interp(1.0 - t if rv else t, [q[0] for q in pr], [q[1] for q in pr]) / 2
''')
wr(p, s)

p = "Data/Regions/bialystok-industrial-c/overrides.yaml"
s = rd(p)
a = s.index("  - id: dk8-viaduct-w-ramp-lane\n")
b = s.index("  - id: ", a + 10)
s = s[:a] + '''  - id: dk8-viaduct-w-ramp-lane
    target: {edge: "w240542867:1847044963-1832991672"}
    reason: >-
      Ramp from Rondo Putry beside the main carriageway (strip xsec/km_ramp_raw.png along the raw OSM way; also
      xsec/km_trunk0.png, xsec/km_trunk.png). OSM draws the last 40 m of the ramp into the axis of the main
      carriageway; the real lane stays beside it. Read at 0 / 20 / 40 / 60 / 80 / 95 / 110 / 125 m before the merge
      node: centre 5.0 / 3.05 / 0.65 / 0.25 / 0 m right, then 0.1 / 0.85 / 0.8 m left of the way (direction of
      travel; beside the separator the carriageway includes the P-21 band); width kerb to line / separator
      3.9 / 3.9 / 4.6 / 4.4 / 4.2 / 4.2 / 5.1 / 5.75 m (was 5.5 m everywhere). center_offset and width =
      [[t, m], ...] along the edge, t = 0 at its start on the viaduct side.
    confidence: medium
    verify: owner drive
    set:
      width: [[0.0, 5.75], [0.10, 5.75], [0.21, 5.1], [0.32, 4.2], [0.426, 4.2], [0.569, 4.4], [0.713, 4.6], [0.856, 3.9], [1.0, 3.9]]
      center_offset: [[0.0, 0.8], [0.10, 0.8], [0.21, 0.85], [0.32, 0.1], [0.426, 0.0], [0.569, -0.25], [0.713, -0.65], [0.856, -3.05], [1.0, -5.0]]
  - id: gore-dk8-ramp-split
    kind: paved_gore
    at_en: [-797.0, 76.8]
    radius_m: 20.0
    reason: >-
      Wedge between the ramp lane and the main carriageway in front of the separator nose (E -815...-782): one
      asphalt surface carrying the P-21 chevrons (xsec/km_trunk.png stations 76-106). The generic merge rule skips
      it because the two carriageways run closer than 4 m for more than 90 m.
    confidence: high
    verify: owner drive
''' + s[b:]
wr(p, s)
print("ok")
