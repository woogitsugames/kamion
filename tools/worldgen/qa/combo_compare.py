"""D94 / ADR 0306: before / after table of qa/combo_lane_check.py results (markdown on stdout).

    uv run --no-project python tools/worldgen/qa/combo_compare.py before.json [before_extra.json ...] -- after.json [...]

Later files override earlier ones per (tile, piece). Rows: every piece with any event before or after."""
import json
import sys


def load(paths):
    out = {}
    for p in paths:
        d = json.load(open(p, encoding="utf-8"))
        for rows in d["corridors"].values():
            for r in rows:
                if "tyre_points" in r:
                    out[(r["tile"], r["piece"])] = r
        for r in d["links"].values():
            out[(r["tile"], r["piece"])] = r
    return out


def cell(r):
    if r is None:
        return "—", "—"
    a = f"{r['opposite']} / {r['kerb']} / {r['off_hard']}"
    w = r.get("swing", r)
    return a, f"{w['opposite']} / {w['kerb']} / {w['off_hard']}"


def main(argv):
    i = argv.index("--")
    B, A = load(argv[:i]), load(argv[i + 1:])
    keys = sorted(set(B) | set(A))
    print("| kafel | odcinek | przed: środek pasa opp/kerb/off | przed: ze swingiem | po: środek pasa | po: ze swingiem |")
    print("|---|---|---|---|---|---|")
    tot = {k: [0, 0, 0, 0, 0, 0] for k in ("B", "A")}
    for k in keys:
        b, a = B.get(k), A.get(k)
        def ev(r):
            if r is None:
                return 0
            w = r.get("swing", r)
            return r["opposite"] + r["kerb"] + r["off_hard"] + w["opposite"] + w["kerb"] + w["off_hard"]
        for tag, r in (("B", b), ("A", a)):
            if r is not None:
                w = r.get("swing", r)
                for j, v in enumerate((r["opposite"], r["kerb"], r["off_hard"], w["opposite"], w["kerb"], w["off_hard"])):
                    tot[tag][j] += v
        if ev(b) + ev(a) == 0:
            continue
        print(f"| {k[0]} | {k[1]} | {' | '.join(cell(b))} | {' | '.join(cell(a))} |")
    for tag in ("B", "A"):
        t = tot[tag]
        print(f"\n{'PRZED' if tag == 'B' else 'PO'} suma: środek pasa opp {t[0]} kerb {t[1]} off {t[2]}; ze swingiem opp {t[3]} kerb {t[4]} off {t[5]}")


if __name__ == "__main__":
    main(sys.argv[1:])
