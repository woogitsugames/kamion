"""dbg_rails.py: runs pipeline.build + furniture.guardrails with a recording Lin; pickles every built run
(key, P, Z, tall) to artifacts/junctions-r5/rails.pkl and prints the runs near the given E,N,R triples (ADR 0117)."""
import sys, pickle
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import pipeline
from streetscape import paved as PV
from roads.meshing import MeshBuf
from streetscape import furniture as FU
w = pipeline.build("bialystok-industrial-c")
hf = w.hf
runs = []
orig = FU.guardrail
def rec(lin, P, Z, key, tall=None, term=(False, False)):
    runs.append({"key": key, "P": np.array(P), "Z": np.array(Z), "tall": None if tall is None else np.array(tall), "term": term})
    return orig(lin, P, Z, key, tall, term)
FU.guardrail = rec
def znat(e, n):
    return PV.bilinear(hf.z, hf, np.asarray(e, float), np.asarray(n, float))
rep = {}
lin = FU.Lin(MeshBuf(), lambda e, n: PV.bilinear(hf.z, hf, np.asarray(e, float), np.asarray(n, float)))
FU.guardrails(lin, w.net, znat, rep)
print(rep["guardrails_m"])
pickle.dump(runs, open("artifacts/junctions-r5/rails.pkl", "wb"))
for a in sys.argv[1:]:
    e, n, r = (float(v) for v in a.split(","))
    print("==", a)
    for q in runs:
        d = np.hypot(q["P"][:, 0] - e, q["P"][:, 1] - n)
        if d.min() < r:
            i = np.where(d < r)[0]
            print(f"  {q['key']:60s} n {len(q['P'])} term {q['term']} tall {None if q['tall'] is None else int(q['tall'].sum())} "
                  f"near idx {i[0]}-{i[-1]} from {np.round(q['P'][0],1)} to {np.round(q['P'][-1],1)} z {q['Z'][i[0]]:.2f}")
