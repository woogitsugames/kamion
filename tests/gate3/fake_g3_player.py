#!/usr/bin/env python3
"""Stand-in for Kamion.exe in tests/gate3/test_g3_poses.py (ADR 0246, Windows mode of scripts/g3-poses.ps1).

NOT the game: it only imitates what Game.Gameplay.G3PoseRunner leaves behind (PNG names, manifest.json, [G3POSE] lines in
-logFile) so the script's launch / wait / collect / verdict path can be exercised without Unity and without Windows.
Behaviour from the environment: G3_FAKE_REPO (repo root), G3_FAKE_MODE = ok | missing | exception | refused | hang | noquit.
"""
import json
import os
import struct
import sys
import time
import zlib
from pathlib import Path


def arg(argv, key, default=None):
    flag = "-" + key
    for i in range(len(argv) - 1):
        if argv[i].lower() == flag.lower():
            return argv[i + 1]
    return default


def png(seed: int) -> bytes:
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes([(seed * 7 + x + y) % 256 for x in range(8)]) for y in range(8))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def main(argv):
    repo = Path(os.environ["G3_FAKE_REPO"])
    mode = os.environ.get("G3_FAKE_MODE", "ok")
    sys.path.insert(0, str(repo / "scripts"))
    import g3_poses as gp
    log = Path(arg(argv, "logFile"))
    run, light, out = arg(argv, "g3pose_run"), arg(argv, "lighting", ""), Path(arg(argv, "g3pose_dir"))
    lines = [f"[BOOT] Kamion fake-player tier={arg(argv, 'tier')} scene={arg(argv, 'scene')}"]

    def flush():
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")

    flush()
    if mode == "hang":
        time.sleep(600)
        return 0
    if mode == "refused":
        lines += ["[G3POSE] REFUSED: not a Development build (build with -Development)",
                  f"[G3POSE] DONE run={run} captured=0 failed=0 timeout=0 dir=-"]
        flush()
        return 2
    doc = json.loads((repo / gp.RESOURCE_REL).read_text(encoding="utf-8"))
    poses = gp.select(doc, arg(argv, "g3pose_only", ""))
    out.mkdir(parents=True, exist_ok=True)
    lines += [f"[G3POSE] BEGIN run={run} poses={len(poses)} total={doc['count']} tier={arg(argv, 'tier')} lighting={light} width={arg(argv, 'g3pose_width')} dir={out}",
              "[G3POSE] build=fake device='fake' gpu='fake' renderScale=1 msaa=4 screen=1600x900"]
    shots = []
    for i, p in enumerate(poses):
        if mode == "missing" and i == len(poses) - 1:
            lines.append(f"[G3POSE] FAIL {i + 1}/{len(poses)} id={p['id']} reason=IOException: disk full")
            shots.append({"index": p["index"], "id": p["id"], "status": "FAIL", "reason": "IOException: disk full"})
            continue
        name = gp.frame_name(p, light)
        (out / name).write_bytes(png(p["index"]))
        shots.append({"index": p["index"], "id": p["id"], "file": name, "status": "OK", "width": p["out_width"], "height": p["out_height"]})
        lines.append(f"[G3POSE] SHOT {i + 1}/{len(poses)} id={p['id']} file={name} size={p['out_width']}x{p['out_height']} settled=yes")
    captured = sum(1 for s in shots if s["status"] == "OK")
    failed = len(shots) - captured
    if mode == "exception":
        lines.append("NullReferenceException: Object reference not set to an instance of an object")
    (out / gp.MANIFEST_NAME).write_text(json.dumps({"schema": gp.CAPTURE_SCHEMA, "run": run, "lighting": light, "selected": len(poses),
                                                    "total": doc["count"], "captured": captured, "failed": failed, "timeout": 0,
                                                    "errors": [], "shots": shots}), encoding="utf-8")
    lines.append(f"[G3POSE] DONE run={run} captured={captured} failed={failed} timeout=0 dir={out}")
    flush()
    if mode == "noquit":
        time.sleep(600)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
