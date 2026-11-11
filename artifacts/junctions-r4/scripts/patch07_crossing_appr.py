"""ADR 0095 patch 7: P-2a only on the approach end of a one-way carriageway; authored crossings; n100 paint."""
import io


def rd(p):
    return io.open(p, encoding="utf-8").read()


def wr(p, s):
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def rep(s, old, new):
    assert s.count(old) == 1, (s.count(old), old[:90])
    return s.replace(old, new)


p = "tools/worldgen/roads/markings.py"
s = rd(p)
s = rep(s, '''        for end, sj in (("a", s0), ("b", s1)):
            info = arm_info.get((c.id, end))
''', '''        for end, sj in (("a", s0), ("b", s1)):
            info = arm_info.get((c.id, end))
            # ADR 0095: a one-way carriageway approaches a junction only at its downstream end; the solid P-2a was
            # also painted for 20 m behind the junction (Andersa after the side street at n10015785253)
            d_end = int(c.dirn[0 if end == "a" else -1])
            if (d_end > 0 and end == "a") or (d_end < 0 and end == "b"):
                continue
''')
wr(p, s)

p = "tools/worldgen/roads/authored_paint.py"
s = rd(p)
s = rep(s, '''  kind: paint_clear    polygon_en: [[E, N], ...]    generated paint inside is removed (authored paint stays)
''', '''  kind: painted_crossing  line_en: [[E, N], [E, N]] (the walking line across the carriageway, kerb to kerb)
                       crossing: P-10 (bars 0.5 / 0.5 m) | P-11 (two rows of squares)   width_m (default 4.0 / 2.0 clear)
  kind: paint_clear    polygon_en: [[E, N], ...]    generated paint inside is removed (authored paint stays)
''')
s = rep(s, '''        if kind not in ("painted_line", "painted_arrow"):
            continue''', '''        if kind not in ("painted_line", "painted_arrow", "painted_crossing"):
            continue''')
s = rep(s, '''        else:
            at = np.asarray(o.get("at_en") or [], float)''', '''        elif kind == "painted_crossing":
            L = np.asarray(o.get("line_en") or [], float)
            if L.shape != (2, 2) or float(np.hypot(*(L[1] - L[0]))) < 1.0:
                stale.append(o["id"])
                rep.append({"id": o["id"], "built": False, "note": "line_en needs two points >= 1 m apart"})
                continue
            t = (L[1] - L[0]) / float(np.hypot(*(L[1] - L[0])))
            nrm = np.array([-t[1], t[0]])
            length = float(np.hypot(*(L[1] - L[0])))
            name = str(o.get("crossing", "P-10"))
            shapes = []
            if name == "P-11":
                clear = float(o.get("width_m", S.P11_CLEAR))
                x = S.P11_GAP / 2
                while x + S.P11_SQUARE <= length + 1e-6:
                    for sg in (-1.0, 1.0):
                        c0 = L[0] + t * (x + S.P11_SQUARE / 2) + nrm * sg * (clear + S.P11_SQUARE) / 2
                        h = S.P11_SQUARE / 2
                        shapes.append(Polygon([c0 - t * h - nrm * h, c0 + t * h - nrm * h, c0 + t * h + nrm * h, c0 - t * h + nrm * h]))
                    x += S.P11_SQUARE + S.P11_GAP
            else:
                wd = float(o.get("width_m", S.P10_WIDTH)) / 2
                x = S.P10_GAP / 2
                while x + S.P10_STRIPE <= length + 1e-6:
                    c0 = L[0] + t * (x + S.P10_STRIPE / 2)
                    h = S.P10_STRIPE / 2
                    shapes.append(Polygon([c0 - t * h - nrm * wd, c0 + t * h - nrm * wd, c0 + t * h + nrm * wd, c0 - t * h + nrm * wd]))
                    x += S.P10_STRIPE + S.P10_GAP
            for g in shapes:
                a_, b_ = _drape_polygon(buf, top, g, f"{AUTHORED_PREFIX}{name}@{o['id']}", 2.0)
                n += a_
                lost += b_
        else:
            at = np.asarray(o.get("at_en") or [], float)''')
wr(p, s)

p = "Data/Regions/bialystok-industrial-c/overrides.yaml"
s = rd(p).rstrip("\n") + """
  - id: n10015785253-edge-line-clear
    kind: paint_clear
    polygon_en: [[-238.0, -225.2], [-206.9, -245.1], [-207.6, -246.1], [-238.7, -226.2]]
    reason: >-
      The generated broken lane line 2|3 carried across this junction plate; on the orthophoto it is one solid line
      (next override).
    confidence: high
    verify: owner drive
  - id: n10015785253-edge-line
    kind: painted_line
    line: P-7b
    polyline_en: [[-238.35, -225.7], [-207.25, -245.6]]
    reason: >-
      Solid 0.24 m line along the right edge of the two through lanes of Andersa across the side-street junction
      (trace/n100_o.jpg: from E -237 N -226 to E -207 N -245).
    confidence: high
    verify: owner drive
  - id: n10015785253-crossing-west
    kind: painted_crossing
    crossing: P-10
    line_en: [[-222.7, -224.45], [-218.5, -227.6]]
    reason: >-
      Zebra across the slip lane from the side street onto Andersa (OSM node 10015785254; the slip way is absorbed
      into the junction plate, so the generator had no chain to put it on). Red cycle crossing beside it: not built.
    confidence: medium
    verify: owner drive
  - id: n10015785253-crossing-east
    kind: painted_crossing
    crossing: P-10
    line_en: [[-216.0, -230.2], [-211.75, -233.45]]
    reason: Zebra across the slip lane from Andersa into the side street (OSM node 3867825902). Red cycle crossing not built.
    confidence: medium
    verify: owner drive
"""
wr(p, s)
print("ok")
