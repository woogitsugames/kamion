"""Compare renderer estimates and actual mirror configuration; not GPU/phone timing."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def scene_stats(path):
    text = path.read_text()
    regular = {m[0]: dict(draws=int(m[1]), shadow_draws=int(m[2]), tris_k=int(m[3]))
               for m in re.findall(r'^(cab-[^:]+):.*drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)', text, re.M)}
    for name, draws, triangles in re.findall(r'^  (cab-[^ ]+) instanced.*draws (\d+),.*triangles (\d+)k', text, re.M):
        regular[name].update(inst_draws=int(draws), inst_tris_k=int(triangles))
    if len(regular) != 9:
        raise ValueError(f"Expected nine camera stats: {path}, found {len(regular)}")
    return regular


result = {"scope": "Editor CPU-side visibility estimates before SRP batching; rounded thousands of triangles. Phone GPU/CPU time UNVERIFIED.", "configurations": {}}
failed = []
for tier in ("Low", "High"):
    for light in ("overcast", "clear"):
        key = f"{tier}-{light}"
        before = ROOT / "before" / key
        after = ROOT / "after" / key
        a, b = scene_stats(before / "stats.txt"), scene_stats(after / "stats.txt")
        delta = {name: {field: b[name][field] - value for field, value in values.items()} for name, values in a.items()}
        def configuration(folder):
            return [line for line in (folder / "native-mirrors/configuration.tsv").read_text().splitlines() if not line.startswith("#")]
        mirror_equal = configuration(before) == configuration(after)
        result["configurations"][key] = dict(before=a, after=b, delta=delta, mirror_configuration_identical=mirror_equal)
        if not mirror_equal:
            failed.append(key + ": mirror configuration changed")
        if tier == "Low" and any(value > 0 for values in delta.values() for value in values.values()):
            failed.append(key + ": Low visibility estimate increased")
result["failures"] = failed
result["result"] = "FAIL" if failed else "PASS"
(ROOT / "budget-comparison.json").write_text(json.dumps(result, indent=2))
print(result["result"], failed)
raise SystemExit(bool(failed))
