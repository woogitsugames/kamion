"""Compare every camera, keeping ordinary scene and instanced submission counts separate."""
import argparse
import json
import re
from pathlib import Path


def read(path):
    rows = {}
    current = None
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = re.match(r"(\S+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)", line)
        if match:
            current = match[1]
            rows[current] = dict(scene_draws_est=int(match[3]), shadow_draws_est=int(match[4]),
                                 scene_tris_k_floor=int(match[5]))
        match = re.match(r"\s+(\S+) instanced .*draws (\d+), instances (\d+), triangles (\d+)k", line)
        if match:
            if match[1] not in rows:
                raise ValueError(f"Missing scene row: {match[1]}")
            rows[match[1]].update(instance_draws=int(match[2]), instances=int(match[3]),
                                  instance_tris_k_floor=int(match[4]))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--after", default="after")
    args = parser.parse_args()
    result = {"units": "SceneStats CPU estimate; instanced draws=submission batches. trisK are truncated thousands; GPU/SRP batches unverified", "conditions": {}}
    integrity = json.loads((args.root / "world-integrity.json").read_text())
    if integrity["failures"]:
        raise ValueError("World integrity failed: " + str(integrity["failures"]))
    failures = []
    lines = ["# Każda kamera — przed / po", "", "Tris w tysiącach, ucięte przez runner; batche instancji są zgłoszeniami CPU. Low limit +2% sprawdzony konserwatywnie z jednym przedziałem 1k dla nieznanej dokładnej delty siatek; niezmienność instancji osobno w world-integrity.json.", ""]
    for tier in ("Low", "High"):
        for light in ("clear", "overcast"):
            condition = f"{tier}-{light}"
            before = read(args.root / "before" / condition / "stats.txt")
            after = read(args.root / args.after / condition / "stats.txt")
            if before.keys() != after.keys():
                raise ValueError(f"Camera sets differ: {condition}")
            rows = []
            lines += [f"## {condition}", "", "| Kamera | Draws sceny | Batche instancji | Tris sceny k | Tris instancji k |", "|---|---:|---:|---:|---:|"]
            for camera in before:
                b, a = before[camera], after[camera]
                if b.keys() != a.keys() or "instance_draws" not in a:
                    raise ValueError(f"Incomplete counts: {condition} {camera}")
                delta = {k: a[k] - b[k] for k in b}
                baseline_k = b["scene_tris_k_floor"] + b["instance_tris_k_floor"]
                # Non-High instance data and meshes are identical (world-integrity.json),
                # so only the scene mesh count can grow. One 1k quantization interval
                # is a conservative upper bound on its unknown exact delta.
                upper_percent = 100 * max(0, delta["scene_tris_k_floor"] + 1) / baseline_k if baseline_k else None
                rows.append(dict(camera=camera, before=b, after=a, delta=delta,
                                 triangle_growth_upper_percent=upper_percent))
                columns = ["scene_draws_est", "instance_draws", "scene_tris_k_floor", "instance_tris_k_floor"]
                lines.append("| " + camera + " | " + " | ".join(f"{b[k]} → {a[k]}" for k in columns) + " |")
                if tier == "Low" and (delta["scene_draws_est"] + delta["instance_draws"] > 0
                                      or delta["shadow_draws_est"] > 0
                                      or delta["instance_draws"] != 0 or delta["instances"] != 0
                                      or delta["instance_tris_k_floor"] != 0
                                      or upper_percent is None or upper_percent > 2):
                    failures.append(f"{condition}/{camera}")
            result["conditions"][condition] = rows
            lines.append("")
    result["low_budget_failures"] = failures
    (args.root / "camera-counts.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (args.root / "CAMERAS.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"cameras": {c:len(r) for c,r in result["conditions"].items()}, "low_budget_failures": failures}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
