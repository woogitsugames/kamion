"""ADR 0213 tuning loop only: write water material values straight into the imported M_water.mat of the given regions
(the final values go to build_world WATER_MATERIALS + a full import). usage: setmat.py <json> <region...>"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
v = json.loads(sys.argv[1])
props = {"color": "_BaseColor", "shallow": "_ShallowColor", "bank_tint": "_BankTint"}
floats = {"reflect": "_Reflect", "reflect_low": "_ReflectLow", "flow_mps": "_FlowSpeed", "flow_cycle_s": "_FlowCycle",
          "ripple_m": "_RippleScale", "ripple_slope": "_RippleStrength", "smoothness": "_Smoothness", "bank_horizon": "_BankHorizon"}
for reg in sys.argv[2:]:
    p = ROOT / f"game/Assets/_Generated/World/{reg}/Materials/M_water.mat"
    s = p.read_text(encoding="utf-8")
    for k, pr in props.items():
        if k in v:
            c = v[k]
            line = f"    - {pr}: {{r: {c[0]}, g: {c[1]}, b: {c[2]}, a: 1}}"
            if re.search(rf"^    - {pr}:.*$", s, re.M):
                s = re.sub(rf"^    - {pr}:.*$", line, s, flags=re.M)
            else:
                s = s.replace("    m_Colors:\n", "    m_Colors:\n" + line + "\n")
    for k, pr in floats.items():
        if k in v:
            line = f"    - {pr}: {v[k]}"
            if re.search(rf"^    - {pr}:.*$", s, re.M):
                s = re.sub(rf"^    - {pr}:.*$", line, s, flags=re.M)
            else:
                s = s.replace("    m_Floats:\n", "    m_Floats:\n" + line + "\n")
    p.write_text(s, encoding="utf-8")
    print(reg, "ok")
