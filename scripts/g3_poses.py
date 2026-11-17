#!/usr/bin/env python
"""Gate 3 photo-pair poses for the Windows player (D73) and the phone (ADR 0246, BACKLOG B-111). Stdlib only.

The poses are NOT authored here: every pose is copied from the photo-pair cameras the editor side-by-side uses
(Data/Regions/<region>/sbs_cameras.json, ADR 0103/0160/0172; rendered by scripts/sbs-gate3.ps1 through visual-qa -Gate3)
and joined with the photo metadata of sbs_references.json (photo size -> output aspect, attribution, comparison photo).
Output: ONE pose file, written to the data folder and byte-identical to the copy the game loads from Resources.

CLI:
  python scripts/g3_poses.py export [--region bialystok-industrial-c]   -> writes both copies, prints a summary
  python scripts/g3_poses.py check  [--region ...]                      -> exit 1 when a copy is stale or missing
  python scripts/g3_poses.py list   [--region ...] [--only <filter>]    -> "index id ref_photo comparison_photo w h" per pose
Windows player (scripts/g3-poses.ps1 -Exe; pure functions, tested by tests/gate3/test_g3_poses.py without Unity/Windows):
  python scripts/g3_poses.py winargs --run <id> --lighting <l> --tier High --out-dir <dir> --log <Player.log> [...]
        -> JSON array: the Kamion.exe command line of ONE capture run (one process renders every selected pose)
  python scripts/g3_poses.py verify --dir <dir> --log <Player.log> --run <id> --lighting <l> [--only <filter>]
        -> JSON verdict (missing / unexpected / duplicate PNG, manifest, [G3POSE] lines, exceptions); exit 0 ok, 6 not
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCHEMA = "kamion/g3-poses/1"
DEFAULT_REGION = "bialystok-industrial-c"
# Output width of the phone frames: the same width scripts/sbs-gate3.ps1 renders the editor pairs at ($width = 1280),
# height from the photo aspect exactly as there ([int]($width * height / width)).
OUT_WIDTH = 1280
RESOURCE_REL = "game/Assets/_Project/Gameplay/Resources/g3_poses.json"


def data_paths(region: str) -> dict[str, Path]:
    d = REPO / "Data" / "Regions" / region
    return {
        "cameras": d / "sbs_cameras.json",
        "references": d / "sbs_references.json",
        "data_out": d / "g3_poses.json",
        "resource_out": REPO / RESOURCE_REL,
    }


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p: Path) -> str:
    return p.resolve().relative_to(REPO).as_posix()


def out_height(width: int, ref_w: int, ref_h: int) -> int:
    # PowerShell [int] rounds half to even; Python round() does the same.
    return int(round(width * ref_h / ref_w))


def build(region: str) -> dict:
    p = data_paths(region)
    cams_doc = json.loads(p["cameras"].read_text(encoding="utf-8"))
    refs_doc = json.loads(p["references"].read_text(encoding="utf-8"))
    cams = cams_doc["cameras"]
    refs = {r["camera"]: r for r in refs_doc["references"]}
    poses = []
    errors = []
    seen = set()
    for i, c in enumerate(cams):
        cid = c["id"]
        if cid in seen:
            errors.append(f"duplicate camera id {cid}")
        seen.add(cid)
        r = refs.get(cid)
        if r is None:
            errors.append(f"camera {cid} has no entry in {rel(p['references'])}")
            continue
        if c.get("segment") != r.get("segment"):
            errors.append(f"camera {cid}: segment {c.get('segment')} != reference {r.get('segment')}")
        w, h = int(r["width"]), int(r["height"])
        poses.append({
            "index": len(poses) + 1,
            "id": cid,
            "segment": c["segment"],
            "kind": c["kind"],
            "seat": c.get("seat", ""),
            "pos": c["pos"],
            "look_at": c["look_at"],
            "fov_deg": c["fov_deg"],
            "pose_confidence": c.get("pose_confidence", ""),
            "out_width": OUT_WIDTH,
            "out_height": out_height(OUT_WIDTH, w, h),
            "source": {
                "cameras_file": rel(p["cameras"]),
                "cameras_index": i,
                "references_file": rel(p["references"]),
                "pose_reason": c.get("pose_reason", ""),
                "note": c.get("note", ""),
            },
            "reference": {
                "photo": r.get("photo", ""),
                "comparison_photo": r.get("comparison_photo", ""),
                "source_id": str(r.get("source_id", "")),
                "page_url": r.get("page_url", ""),
                "author": r.get("author", ""),
                "license": r.get("license", ""),
                "captured_at": r.get("captured_at", ""),
                "width": w,
                "height": h,
            },
        })
    extra = sorted(set(refs) - seen)
    if extra:
        errors.append(f"references without a camera: {', '.join(extra)}")
    if errors:
        raise SystemExit("g3_poses: " + "; ".join(errors))
    return {
        "schema": SCHEMA,
        "region": region,
        "frame": cams_doc.get("frame", ""),
        "generated_by": "python scripts/g3_poses.py export --region " + region,
        "adr": "docs/adr/0246-zrzuty-a16-poz-par-zdjeciowych-g3.md",
        "inputs": {
            rel(p["cameras"]): sha256(p["cameras"]),
            rel(p["references"]): sha256(p["references"]),
        },
        "count": len(poses),
        "count_note": "every camera of sbs_cameras.json (kind photo_match); the 42 pairs of the s16b review "
                      "(docs/reports/visual/REVIEW-2026-11-13-s16b-final.md, 27 R / 15 P / 0 N)",
        "out_width_source": "scripts/sbs-gate3.ps1 ($width = 1280, height from the photo aspect)",
        "poses": poses,
    }


def render(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def cmd_export(a) -> int:
    p = data_paths(a.region)
    text = render(build(a.region))
    for k in ("data_out", "resource_out"):
        p[k].parent.mkdir(parents=True, exist_ok=True)
        p[k].write_text(text, encoding="utf-8", newline="\n")
    doc = json.loads(text)
    seg = {}
    for x in doc["poses"]:
        seg[x["segment"]] = seg.get(x["segment"], 0) + 1
    print(f"g3_poses: {doc['count']} poses ({', '.join(f'{k} {v}' for k, v in sorted(seg.items()))}) -> "
          f"{rel(p['data_out'])}, {rel(p['resource_out'])}")
    return 0


def cmd_check(a) -> int:
    p = data_paths(a.region)
    want = render(build(a.region))
    bad = []
    for k in ("data_out", "resource_out"):
        if not p[k].exists():
            bad.append(f"{rel(p[k])} missing")
        elif p[k].read_text(encoding="utf-8") != want:
            bad.append(f"{rel(p[k])} stale")
    if bad:
        print("g3_poses check FAIL: " + "; ".join(bad) + f" - run: python scripts/g3_poses.py export --region {a.region}")
        return 1
    print(f"g3_poses check OK ({json.loads(want)['count']} poses)")
    return 0


def is_index(t: str) -> bool:
    return 0 < len(t) <= 3 and t.isascii() and t.isdigit()


def matches(pose: dict, only: str) -> bool:
    """Same rule as Game.Gameplay.G3PoseSet.Matches: comma tokens; a number of at most 3 digits is the 1-based index,
    "a-b" of such numbers an index range, otherwise (also a longer number, e.g. a photo key) a case-insensitive
    substring of the id ('_' and '-' are equal)."""
    if not only or not only.strip():
        return True
    norm = pose["id"].replace("_", "-").lower()
    for t in (x.strip() for x in only.split(",")):
        if not t:
            continue
        if is_index(t):
            if int(t) == pose["index"]:
                return True
            continue
        a, dash, b = t.partition("-")
        if dash and is_index(a) and is_index(b):
            if min(int(a), int(b)) <= pose["index"] <= max(int(a), int(b)):
                return True
            continue
        if t.replace("_", "-").lower() in norm:
            return True
    return False


# ---------------------------------------------------------------- Windows player (D73, ADR 0246 "Windows")

MANIFEST_NAME = "manifest.json"                 # Game.Gameplay.G3PoseCapture.ManifestName
CAPTURE_SCHEMA = "kamion/g3-poses-capture/1"    # G3PoseRunner.Manifest.schema
WIN_SCENE = "WorldC"
# Window of the capture run: the frames are rendered off-screen at --width, so the window size does not change them;
# 1600x900 windowed is the launcher size of scripts/build-windows.ps1 (ADR 0261).
WIN_SCREEN = (1600, 900)
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
# Lines of a Unity Player.log that make a run suspicious (same idea as build-windows.ps1 -Run).
LOG_BAD = re.compile(r"\b\w*Exception\b|Crash!!!|Shader error|\bFatal error\b", re.IGNORECASE)
LIGHTING_REFUSED = ("dusk",)   # review P2-4: lamps follow the player camera, not the pose camera (ADR 0246 Konsekwencje)


def sanitize_token(s: str, max_len: int) -> str:
    """Game.Gameplay.G3PoseArgs.SanitizeToken: keeps [A-Za-z0-9._-], at most max_len characters, no leading dot."""
    out = [c for c in (s or "") if c.isascii() and (c.isalnum() or c in "-_.")]
    return "".join(out[:max_len]).lstrip(".")


def frame_name(pose: dict, lighting: str) -> str:
    """Game.Gameplay.G3PoseCapture.FileName: '07_sbs-g3-a-1406533339711789_overcast.png'."""
    pid = sanitize_token(pose.get("id") or "pose", 96) or "pose"
    light = sanitize_token(lighting or "", 32)
    return f"{int(pose.get('index', 0)):02d}_{pid}" + (f"_{light}" if light else "") + ".png"


def select(doc: dict, only: str) -> list[dict]:
    return [x for x in doc["poses"] if matches(x, only)]


def win_player_args(*, run_id: str, lighting: str, tier: str, out_dir: str, log_file: str, only: str = "",
                    width: int = OUT_WIDTH, fps: int = 0, screen: tuple[int, int] = WIN_SCREEN, scene: str = WIN_SCENE,
                    extra: list[str] | None = None) -> list[str]:
    """Command line of one Windows capture run (everything after Kamion.exe). The game reads "-key value" pairs
    (Game.Platform.DefaultPlatformServices.GetLaunchArgument); -screen-* and -logFile are Unity player arguments."""
    if not run_id or sanitize_token(run_id, 64) != run_id:
        raise ValueError(f"run id '{run_id}' must be [A-Za-z0-9._-], at most 64 characters, no leading dot")
    if not lighting or sanitize_token(lighting, 32) != lighting:
        raise ValueError(f"lighting '{lighting}' is not a preset token")
    if lighting in LIGHTING_REFUSED:
        raise ValueError(f"lighting '{lighting}' is not supported by the pose capture (lamps follow the player camera)")
    if not out_dir or not log_file:
        raise ValueError("out_dir and log_file are required")
    if not (64 <= int(width) <= 4096):
        raise ValueError(f"width {width} outside [64, 4096] (G3PoseArgs.MinWidth/MaxWidth)")
    args = ["-screen-fullscreen", "0", "-screen-width", str(int(screen[0])), "-screen-height", str(int(screen[1])),
            "-logFile", str(log_file),
            "-scene", scene, "-tier", tier,
            "-g3pose", "1", "-g3pose_run", run_id, "-g3pose_width", str(int(width)), "-lighting", lighting,
            "-g3pose_dir", str(out_dir), "-g3pose_quit", "1"]
    if fps and int(fps) > 0:
        args += ["-fps", str(int(fps))]
    only = re.sub(r"\s", "", only or "")
    if only:
        args += ["-g3pose_only", only]
    for kv in extra or []:
        k, eq, v = kv.partition("=")
        k = k.strip().lstrip("-")
        if not k or not eq:
            raise ValueError(f"extra argument '{kv}' is not key=value")
        args += ["-" + k, v]
    return args


def quote_windows(args: list[str]) -> str:
    """One command-line string for Start-Process (quotes arguments with whitespace; no argument may hold a quote)."""
    for a in args:
        if '"' in a:
            raise ValueError(f"argument with a double quote: {a}")
    return " ".join(f'"{a}"' if (a == "" or re.search(r"\s", a)) else a for a in args)


def parse_player_log(text: str, run_id: str) -> dict:
    """[G3POSE] lines and suspicious lines of a Player.log (or logcat). Nothing here decides pass/fail alone."""
    lines = (text or "").splitlines()
    done = None
    for ln in lines:
        m = re.search(r"\[G3POSE\] DONE run=" + re.escape(run_id) + r" captured=(\d+) failed=(\d+) timeout=(\d+) dir=(.*)$", ln)
        if m:
            done = {"captured": int(m.group(1)), "failed": int(m.group(2)), "timeout": int(m.group(3)), "dir": m.group(4).strip()}
    pick = lambda pat: [ln.strip() for ln in lines if re.search(pat, ln)]
    first = lambda pat: next(iter(pick(pat)), None)
    fails = pick(r"\[G3POSE\] FAIL ")
    return {
        "done": done,
        "refused": first(r"\[G3POSE\] REFUSED"),
        "begin": first(r"\[G3POSE\] BEGIN "),
        "captureLine": first(r"\[G3POSE\] build="),
        "bootLine": first(r"\[BOOT\] Kamion "),
        "shots": len(pick(r"\[G3POSE\] SHOT ")),
        "failLines": fails,
        "unknownLighting": bool(pick(r"lighting=\S+: no such preset")),
        # A [G3POSE] FAIL line may quote an exception type: it is already counted as a failed frame, not twice.
        "suspiciousLines": [ln.strip() for ln in lines if LOG_BAD.search(ln) and "[G3POSE] FAIL" not in ln][:40],
    }


def verify_capture(out_dir: Path, poses: list[dict], lighting: str, log_text: str, run_id: str, timed_out: bool = False,
                   exit_code: int | None = None) -> dict:
    """Verdict of one Windows capture run: every planned frame present, a real PNG, no two frames identical, manifest
    consistent, DONE marker clean, no exception in the log. ok=False => scripts/g3-poses.ps1 exits 6."""
    out_dir = Path(out_dir)
    expected = [frame_name(p, lighting) for p in poses]
    found = sorted(f.name for f in out_dir.glob("*.png")) if out_dir.is_dir() else []
    problems: list[str] = []
    missing = [n for n in expected if n not in found]
    unexpected = [n for n in found if n not in expected]
    bad_png, dups, seen = [], [], {}
    for n in found:
        data = (out_dir / n).read_bytes()
        if not data.startswith(PNG_MAGIC) or len(data) < 64:
            bad_png.append(n)
            continue
        h = hashlib.md5(data).hexdigest()
        if h in seen:
            dups.append(f"{n} == {seen[h]}")
        else:
            seen[h] = n
    log = parse_player_log(log_text, run_id)
    manifest = None
    mpath = out_dir / MANIFEST_NAME
    if mpath.is_file():
        try:
            manifest = json.loads(mpath.read_text(encoding="utf-8-sig"))
        except (ValueError, OSError) as e:
            problems.append(f"{MANIFEST_NAME} unreadable: {e}")
    else:
        problems.append(f"{MANIFEST_NAME} missing")
    settle_timeouts = 0
    if manifest is not None:
        if manifest.get("schema") != CAPTURE_SCHEMA:
            problems.append(f"manifest schema {manifest.get('schema')!r} != {CAPTURE_SCHEMA}")
        if manifest.get("run") != run_id:
            problems.append(f"manifest run {manifest.get('run')!r} != {run_id!r} (stale folder?)")
        shots = manifest.get("shots") or []
        ok_files = sorted(s.get("file") for s in shots if s.get("status") in ("OK", "TIMEOUT") and s.get("file"))
        if ok_files != sorted(n for n in found if n not in bad_png):
            problems.append(f"manifest lists {len(ok_files)} frame(s), folder holds {len(found) - len(bad_png)} PNG")
        if int(manifest.get("failed") or 0) > 0:
            problems.append(f"manifest failed={manifest.get('failed')}: {'; '.join(manifest.get('errors') or [])[:300]}")
        settle_timeouts = int(manifest.get("timeout") or 0)
    if timed_out:
        problems.append("TIMEOUT: the player was killed before the DONE marker")
    if log["refused"]:
        problems.append(log["refused"])
    if log["done"] is None:
        problems.append("no [G3POSE] DONE line for this run in the player log")
    else:
        d = log["done"]
        if d["failed"] > 0:
            problems.append(f"DONE failed={d['failed']}")
        if d["captured"] != len(expected):
            problems.append(f"DONE captured={d['captured']}, planned {len(expected)}")
    if missing:
        problems.append(f"{len(missing)} PNG missing: {', '.join(missing[:5])}{' ...' if len(missing) > 5 else ''}")
    if unexpected:
        problems.append(f"{len(unexpected)} unexpected PNG: {', '.join(unexpected[:5])}")
    if bad_png:
        problems.append(f"not a PNG: {', '.join(bad_png[:5])}")
    if dups:
        problems.append(f"duplicate frames (not evidence of distinct poses): {'; '.join(dups[:5])}")
    if log["failLines"]:
        problems.append(f"{len(log['failLines'])} [G3POSE] FAIL line(s)")
    if log["suspiciousLines"]:
        problems.append(f"{len(log['suspiciousLines'])} exception/crash line(s) in the player log: {log['suspiciousLines'][0][:200]}")
    if exit_code not in (None, 0) and not timed_out:
        problems.append(f"player exit code {exit_code}")
    return {
        "ok": not problems, "problems": problems, "planned": len(expected), "pngs": len(found),
        "missing": missing, "unexpected": unexpected, "badPng": bad_png, "duplicateFrames": dups,
        "settleTimeouts": settle_timeouts, "manifest": manifest is not None, "log": log,
    }


def cmd_winargs(a) -> int:
    try:
        args = win_player_args(run_id=a.run, lighting=a.lighting, tier=a.tier, out_dir=a.out_dir, log_file=a.log,
                               only=a.only, width=a.width, fps=a.fps, screen=(a.screen_width, a.screen_height),
                               extra=[x for x in (a.extra or "").split(",") if x])
        line = quote_windows(args)
    except ValueError as e:
        print(f"g3_poses winargs: {e}", file=sys.stderr)
        return 2
    print(json.dumps({"args": args, "line": line}))
    return 0


def cmd_verify(a) -> int:
    doc = json.loads(data_paths(a.region)["data_out"].read_text(encoding="utf-8"))
    log = Path(a.log)
    text = log.read_text(encoding="utf-8-sig", errors="replace") if log.is_file() else ""
    v = verify_capture(Path(a.dir), select(doc, a.only), a.lighting, text, a.run, timed_out=a.timed_out,
                       exit_code=a.exit_code)
    if not log.is_file():
        v["ok"] = False
        v["problems"].insert(0, f"player log missing: {log}")
    print(json.dumps(v))
    return 0 if v["ok"] else 6


def cmd_list(a) -> int:
    p = data_paths(a.region)
    doc = json.loads(p["data_out"].read_text(encoding="utf-8"))
    for x in doc["poses"]:
        if matches(x, a.only):
            r = x["reference"]
            print(f"{x['index']}\t{x['id']}\t{r['photo']}\t{r['comparison_photo']}\t{x['out_width']}\t{x['out_height']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("export", "check", "list", "winargs", "verify"):
        s = sub.add_parser(name)
        s.add_argument("--region", default=DEFAULT_REGION)
        if name in ("list", "winargs", "verify"):
            s.add_argument("--only", default="")
        if name in ("winargs", "verify"):
            s.add_argument("--run", required=True)
            s.add_argument("--lighting", required=True)
            s.add_argument("--log", required=True)
        if name == "winargs":
            s.add_argument("--tier", default="High")
            s.add_argument("--out-dir", required=True)
            s.add_argument("--width", type=int, default=OUT_WIDTH)
            s.add_argument("--fps", type=int, default=0)
            s.add_argument("--screen-width", type=int, default=WIN_SCREEN[0])
            s.add_argument("--screen-height", type=int, default=WIN_SCREEN[1])
            s.add_argument("--extra", default="", help="key=value[,key=value] extra game arguments")
        if name == "verify":
            s.add_argument("--dir", required=True)
            s.add_argument("--timed-out", action="store_true")
            s.add_argument("--exit-code", type=int, default=None)
    a = ap.parse_args(argv)
    return {"export": cmd_export, "check": cmd_check, "list": cmd_list, "winargs": cmd_winargs, "verify": cmd_verify}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
