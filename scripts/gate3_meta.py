#!/usr/bin/env python
"""Gate 3 metadata helpers (APK identity, duplicate-frame check). Stdlib only; used by gate3-run.ps1 and gate3_evidence.py.

CLI:
  python scripts/gate3_meta.py apk  --apk <file.apk> [--repo <dir>]   -> JSON {apkFile, apkSha256, gitSha, dirty, high, dev, headSha, warnings}
  python scripts/gate3_meta.py dups --dir <cam dir>                    -> JSON {frames, duplicates: [[file, ...], ...]}; exit 1 when duplicates exist
  python scripts/gate3_meta.py pick --dir <artifacts/apk> --high 0|1 [--dev 0|1]   -> path of the newest matching APK (empty + exit 1 if none)

The build-android.ps1 name is  kamion-<version>-<sha10>[-dirty][-high][-dev].apk  (sha = HEAD at BUILD time).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

APK_RE = re.compile(r"^kamion-(?P<ver>[^-]+)-(?P<sha>[0-9a-f]{7,40})(?P<dirty>-dirty)?(?P<high>-high)?(?P<dev>-dev)?\.apk$")


def parse_apk_name(name: str) -> dict | None:
    m = APK_RE.match(Path(name).name)
    if not m:
        return None
    return {"version": m["ver"], "sha": m["sha"], "dirty": bool(m["dirty"]), "high": bool(m["high"]), "dev": bool(m["dev"])}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def head_sha(repo: str | Path | None) -> str:
    if not repo:
        return ""
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return ""


def apk_meta(apk: str | Path, repo: str | Path | None = None, head: str | None = None) -> dict:
    """Identity of the APK that is (to be) installed. gitSha comes from the file NAME (the build's HEAD), never from the current HEAD."""
    apk = Path(apk)
    info = parse_apk_name(apk.name)
    warnings: list[str] = []
    out = {"apkFile": apk.name, "apkPath": str(apk), "apkSha256": None, "gitSha": None, "dirty": None, "high": None, "dev": None, "headSha": None, "warnings": warnings}
    if apk.exists():
        side = Path(str(apk) + ".sha256")
        out["apkSha256"] = sha256_file(apk)
        if side.exists():
            declared = side.read_text(encoding="utf-8", errors="ignore").split()[:1]
            if declared and declared[0].lower() != out["apkSha256"]:
                warnings.append(f"{side.name} declares {declared[0][:12]}... but the file hashes to {out['apkSha256'][:12]}...")
    else:
        warnings.append(f"APK not found: {apk}")
    if info is None:
        warnings.append(f"APK name '{apk.name}' does not match kamion-<ver>-<sha>[-dirty][-high][-dev].apk: git sha unknown")
        return out
    out.update(gitSha=info["sha"], dirty=info["dirty"], high=info["high"], dev=info["dev"])
    if info["dirty"]:
        warnings.append("APK is -dirty (built from uncommitted changes): not valid gate evidence")
    head = head if head is not None else head_sha(repo)
    out["headSha"] = head or None
    if head and not head.startswith(info["sha"]):
        warnings.append(f"APK built from {info['sha']} but repo HEAD is {head[:10]}: the measurement is NOT of HEAD")
    return out


def pick_apk(apk_dir: Path, high: bool, dev: bool = False) -> Path | None:
    cands = []
    for p in apk_dir.glob("*.apk"):
        i = parse_apk_name(p.name)
        if i and i["high"] == high and i["dev"] == dev:
            cands.append(p)
    return max(cands, key=lambda p: p.stat().st_mtime) if cands else None


def duplicate_frames(cam_dir: Path) -> list[list[str]]:
    """Groups of frame files with identical bytes (md5). Two cameras with the same frame = one of them was not captured."""
    groups: dict[str, list[str]] = {}
    for p in sorted(cam_dir.glob("*.png")):
        groups.setdefault(hashlib.md5(p.read_bytes()).hexdigest(), []).append(p.name)
    return [v for v in groups.values() if len(v) > 1]


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("apk")
    a.add_argument("--apk", required=True)
    a.add_argument("--repo")
    d = sub.add_parser("dups")
    d.add_argument("--dir", required=True)
    k = sub.add_parser("pick")
    k.add_argument("--dir", required=True)
    k.add_argument("--high", default="0")
    k.add_argument("--dev", default="0")
    n = ap.parse_args()
    if n.cmd == "apk":
        print(json.dumps(apk_meta(n.apk, n.repo), indent=1))
        return 0
    if n.cmd == "dups":
        dd = duplicate_frames(Path(n.dir))
        print(json.dumps({"frames": len(list(Path(n.dir).glob("*.png"))), "duplicates": dd}))
        return 1 if dd else 0
    p = pick_apk(Path(n.dir), n.high == "1", n.dev == "1")
    print(p or "")
    return 0 if p else 1


if __name__ == "__main__":
    sys.exit(main())
