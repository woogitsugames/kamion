"""Compare every camera in SceneStats, preserving separate instancing estimates.

These are CPU estimates before batching, not measured GPU draws or device timings.
Missing cameras fail the comparison instead of silently shrinking its scope.
"""
import argparse
import json
import re
from pathlib import Path

STATIC = re.compile(r"^(.+?): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)")
INSTANCED = re.compile(r"^\s+(.+?) instanced \(props\+trees\): draws (\d+), instances (\d+), triangles (\d+)k")


def read(path):
    cameras = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = STATIC.match(line)
        if match:
            camera, objects, draws, shadows, tris = match.groups()
            if camera in cameras:
                raise ValueError(f"Duplicate camera {camera}: {path}")
            cameras[camera] = dict(objects=int(objects), draws=int(draws), shadows=int(shadows),
                                   triangles_k=int(tris))
            continue
        match = INSTANCED.match(line)
        if match:
            camera, draws, instances, tris = match.groups()
            cameras[camera].update(instanced_draws=int(draws), instances=int(instances),
                                   instanced_triangles_k=int(tris))
    if not cameras:
        raise ValueError(f"No cameras in {path}")
    for camera, counts in cameras.items():
        if "instanced_draws" not in counts:
            raise ValueError(f"Missing instancing estimates for {camera}: {path}")
    return cameras


def compare(before, after):
    a, b = read(before), read(after)
    if a.keys() != b.keys():
        raise ValueError(f"Different cameras: missing={sorted(a.keys()-b.keys())}, added={sorted(b.keys()-a.keys())}")
    result = {}
    for camera in a:
        delta = {key: b[camera][key] - value for key, value in a[camera].items()}
        tris_a = a[camera]["triangles_k"] + a[camera]["instanced_triangles_k"]
        tris_b = b[camera]["triangles_k"] + b[camera]["instanced_triangles_k"]
        result[camera] = dict(before=a[camera], after=b[camera], delta=delta,
                              total_draw_delta=delta["draws"] + delta["instanced_draws"],
                              total_triangle_delta_percent=100 * (tris_b-tris_a) / max(tris_a, 1))
    return {"scope": "all cameras in both stats files; CPU estimates, tris rounded to thousands",
            "before": str(before), "after": str(after), "camera_count": len(result), "cameras": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = compare(args.before, args.after)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
