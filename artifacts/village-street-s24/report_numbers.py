"""Summary numbers of docs/reports/village-street-0349/*.json for the ADR (run from the repo root)."""
import json
import statistics
from pathlib import Path

for f in sorted(Path("docs/reports/village-street-0349").glob("*.json")):
    r = json.loads(f.read_text(encoding="utf-8"))
    yes = [e for e in r["edges"] if e["left"]["sidewalk_w"] or e["right"]["sidewalk_w"]]
    no = [e for e in r["edges"] if e not in yes]

    def stats(eds):
        rows = [s for e in eds for s in e["stations"] if s["valid"]]
        if not rows:
            return "no valid stations"
        le = [s["left_m"] for s in rows]
        ri = [s["right_m"] for s in rows]
        tot = sorted(a + b for a, b in zip(le, ri))
        q = lambda v, p: round(sorted(v)[int(p * (len(v) - 1))], 2)   # noqa: E731
        return (f"{len(rows)} st, length {round(sum(e['length_m'] for e in eds))} m, left med {statistics.median(le):.2f} "
                f"(q10-q90 {q(le, .1)}-{q(le, .9)}), right med {statistics.median(ri):.2f} ({q(ri, .1)}-{q(ri, .9)}), "
                f"total med {statistics.median(tot):.2f} ({q(tot, .1)}-{q(tot, .9)}), "
                f"carriageway {sorted({e['carriageway_m'] for e in eds})}")
    print(r["region"], "| sidewalk edges", len(yes), ":", stats(yes) if yes else "-")
    print(" " * len(r["region"]), "| other edges   ", len(no), ":", stats(no) if no else "-")
