"""ADR 0211: append the place cameras added after the r1 build_world started to generated/control_cameras.json
(same rule as build_world: NMT at the spot + eye_m)."""
import json, math, pickle, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np
from roads import pipeline
R = "bialystok-kleeberga"
w = pickle.load(open(REPO / "artifacts/tunnel-0211/dev_dump.pkl", "rb"))["w"]
gen = pipeline.REGIONS / R / "generated" / "control_cameras.json"
doc = json.loads(gen.read_text(encoding="utf-8"))
have = {c["id"] for c in doc["cameras"]}
r = lambda v: round(float(v), 2)
for e in json.loads((pipeline.REGIONS / R / "control_cameras_place.authored.json").read_text(encoding="utf-8"))["cameras"]:
    if e["id"] in have:
        continue
    p = np.array(e["pos_en"], float); hd = math.radians(e["heading_deg"]); d = np.array([math.sin(hd), math.cos(hd)])
    eye = float(w.hf.sample(np.array([p[0]]), np.array([p[1]]))[0]) + float(e.get("eye_m", 1.7))
    tgt = p + 100.0 * d; zt = eye + 100.0 * math.tan(math.radians(float(e.get("pitch_deg", 0.0))))
    doc["cameras"].append({"id": e["id"], "type": "persp", "fov_deg": float(e.get("fov_deg", 60.0)),
                           "pos": [r(p[0]), r(p[1]), r(eye)], "look_at": [r(tgt[0]), r(tgt[1]), r(zt)],
                           "note": f"place camera: {e['note']}"})
    print("added", e["id"], r(eye))
gen.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
