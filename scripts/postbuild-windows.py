#!/usr/bin/env python3
"""Post-build step of the Windows player (ADR 0276): content hash of the player data + region launchers.

    python scripts/postbuild-windows.py artifacts/win/kamion-0.1.0-<sha>-regions --log artifacts/logs/build-win-<ts>.log --git-sha <sha>
    python scripts/postbuild-windows.py <build dir> --check        # recompute, compare with build-id.json (exit 1 on mismatch)

Called by scripts/build-windows.ps1 after a successful build; prints one JSON object (summary) on stdout.

Why: Kamion.exe is the Unity launcher stub - the same bytes in every build (INTEGRATION-2026-11-15-int-pc-s23 §8), so
Kamion.exe.sha256 does not identify a build. The content of the build is Kamion_Data/ (scenes, resources, managed code
under Mono, il2cpp metadata under IL2CPP).

Content hash (schema kamion/build-id/1):
  manifest = one line "<sha256 hex>  <path>\\n" per file under Kamion_Data/ (path relative to the build folder, POSIX
             separators, sorted by its UTF-8 bytes), without *.pdb and *_DoNotShip / *_ButDontShipItWithYourGame
             folders (the same files package-windows.py leaves out of the zip);
  contentSha256 = SHA-256 of the manifest text (UTF-8); contentHash = its first 12 hex digits.
Order (the hash never contains itself): the git sha is baked into Kamion_Data before the build (BuildInfoWriter,
Resources/build_info.json); after the build this script hashes Kamion_Data and writes build-id.json NEXT TO the exe
(outside Kamion_Data); the player reads it once at start (Game.Core.BuildInfo.ReadContentHash) and shows
"<ver> (<sha>) · dane <contentHash>" in the menu, the "Informacje" screen, the diagnostics overlay and the [BOOT] log.
Two builds of one commit normally get different hashes (build_info.json carries the build time) - the hash names one
build, it is not a reproducibility proof.

Launchers: Kamion-okno.cmd (menu in a 1600x900 window) and Kamion-<region>.cmd for every region whose Low scene is in
the build (read from the "[BUILD] Windows x64 -> ... scenes=[...]" line of the build log, i.e. after the expansion of
sets / aliases / ranges by RegionBuildList and after -RegionsAllowMissing). Each starts the player windowed with
-scene <region id> (GameBootstrap: region id or alias -> the region scene of the active tier).
Standard library only (Python >= 3.10).
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = "kamion/build-id/1"
DATA_DIR = "Kamion_Data"            # Unity: <ProductName>_Data next to Kamion.exe
EXE_NAME = "Kamion.exe"
BUILD_ID = "build-id.json"          # Game.Core.BuildInfo.BuildIdFileName - ships with the player
MANIFEST = "Kamion_Data.sha256"     # full manifest, build metadata (not shipped: the zip has SHA256SUMS.txt)
SHORT = 12                          # Game.Core.BuildInfo.ContentHashLength
WINDOW_ARGS = "-screen-fullscreen 0 -screen-width 1600 -screen-height 900"   # ProjectSettings default is fullscreen (ADR 0261)
WINDOW_LAUNCHER = "Kamion-okno.cmd"
EXCLUDED_DIR_GLOBS = ("*_DoNotShip", "*_ButDontShipItWithYourGame")
EXCLUDED_FILE_GLOBS = ("*.pdb",)
REGION_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")   # catalog ids; anything else never reaches a .cmd line
SCENES_RE = re.compile(r"\[BUILD\] Windows x64 .*? scenes=\[(?P<scenes>[^\]]*)\]")
REGION_SCENE_RE = re.compile(r"^Assets/_Generated/World/(?P<id>[^/]+)/(?P<scene>WorldC|World_[^/]+)\.unity$")


class PostBuildError(Exception):
    pass


def _excluded(rel_parts: tuple[str, ...]) -> bool:
    if any(fnmatch.fnmatchcase(p, g) for p in rel_parts[:-1] for g in EXCLUDED_DIR_GLOBS):
        return True
    return any(fnmatch.fnmatchcase(rel_parts[-1].lower(), g) for g in EXCLUDED_FILE_GLOBS)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def data_manifest(build_dir: Path) -> list[tuple[str, str, int]]:
    """(path, sha256, bytes) of every hashed file under Kamion_Data/, sorted by the UTF-8 bytes of the path."""
    data = build_dir / DATA_DIR
    if not data.is_dir():
        raise PostBuildError(f"{DATA_DIR}/ missing in {build_dir}")
    out = []
    for p in data.rglob("*"):
        if p.is_symlink() or not p.is_file():
            continue
        rel = p.relative_to(build_dir)
        if _excluded(rel.parts):
            continue
        out.append((rel.as_posix(), _sha256(p), p.stat().st_size))
    out.sort(key=lambda e: e[0].encode("utf-8"))
    if not out:
        raise PostBuildError(f"{DATA_DIR}/ in {build_dir} has no files")
    return out


def manifest_text(entries: list[tuple[str, str, int]]) -> str:
    return "".join(f"{sha}  {path}\n" for path, sha, _ in entries)


def content_sha256(entries: list[tuple[str, str, int]]) -> str:
    return hashlib.sha256(manifest_text(entries).encode("utf-8")).hexdigest()


def build_id(entries: list[tuple[str, str, int]], git_sha: str | None) -> dict:
    full = content_sha256(entries)
    return {
        "schema": SCHEMA,
        "gitSha": git_sha or "",
        "contentHash": full[:SHORT],
        "contentSha256": full,
        "contentFiles": len(entries),
        "contentBytes": sum(e[2] for e in entries),
        "scope": f"{DATA_DIR}/ (sha256 manifest, sorted; *.pdb and *_DoNotShip excluded)",
    }


def read_build_id(build_dir: Path) -> dict | None:
    p = build_dir / BUILD_ID
    if not p.is_file():
        return None
    try:
        doc = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        raise PostBuildError(f"{BUILD_ID} unreadable: {e}")
    if doc.get("schema") != SCHEMA or not re.fullmatch(r"[0-9a-f]{%d}" % SHORT, str(doc.get("contentHash", ""))):
        raise PostBuildError(f"{BUILD_ID}: schema {doc.get('schema')!r} / contentHash {doc.get('contentHash')!r} not {SCHEMA}")
    return doc


def write_build_id(build_dir: Path, entries: list[tuple[str, str, int]], git_sha: str | None) -> dict:
    doc = build_id(entries, git_sha)
    (build_dir / BUILD_ID).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    (build_dir / MANIFEST).write_text(manifest_text(entries), encoding="utf-8", newline="\n")
    return doc


# ---------------------------------------------------------------- regions / launchers

def regions_from_log(log_text: str) -> list[str]:
    """Region ids whose Low scene is in the build, in build order (last '[BUILD] Windows x64' line of the log)."""
    found = SCENES_RE.findall(log_text)
    if not found:
        raise PostBuildError("no '[BUILD] Windows x64 ... scenes=[...]' line in the build log")
    ids: list[str] = []
    for scene in (s.strip() for s in found[-1].split(",")):
        m = REGION_SCENE_RE.match(scene)
        if not m:
            continue
        rid, name = m.group("id"), m.group("scene")
        if name.endswith("_High") or (name != "WorldC" and name != f"World_{rid}"):
            continue
        if rid not in ids:
            ids.append(rid)
    return ids


def launcher_text(extra_args: str = "") -> str:
    tail = f" {extra_args}" if extra_args else ""
    return f'@echo off\r\nstart "" "%~dp0{EXE_NAME}" {WINDOW_ARGS}{tail} %*\r\n'


def launcher_name(region_id: str) -> str:
    return f"Kamion-{region_id}.cmd"


def write_launchers(build_dir: Path, regions: list[str]) -> tuple[list[str], list[str]]:
    """Kamion-okno.cmd + Kamion-<id>.cmd per region. Returns (written names, skipped ids)."""
    written, skipped = [], []
    (build_dir / WINDOW_LAUNCHER).write_bytes(launcher_text().encode("ascii"))
    written.append(WINDOW_LAUNCHER)
    for rid in regions:
        if not REGION_ID_RE.match(rid) or launcher_name(rid) == WINDOW_LAUNCHER:
            skipped.append(rid)
            continue
        (build_dir / launcher_name(rid)).write_bytes(launcher_text(f"-scene {rid}").encode("ascii"))
        written.append(launcher_name(rid))
    return written, skipped


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("build_dir", type=Path)
    ap.add_argument("--log", type=Path, help="Unity build log (region launchers); without it only Kamion-okno.cmd")
    ap.add_argument("--git-sha", help="git sha of the build (written to build-id.json)")
    ap.add_argument("--check", action="store_true", help="recompute and compare with build-id.json; write nothing")
    a = ap.parse_args(argv)
    try:
        b = a.build_dir.resolve()
        entries = data_manifest(b)
        if a.check:
            doc = read_build_id(b)
            if doc is None:
                raise PostBuildError(f"{BUILD_ID} missing in {b}")
            now = build_id(entries, doc.get("gitSha"))
            ok = now["contentSha256"] == doc.get("contentSha256")
            print(json.dumps({"ok": ok, "contentHash": now["contentHash"], "recorded": doc.get("contentHash")}))
            return 0 if ok else 1
        doc = write_build_id(b, entries, a.git_sha)
        regions = regions_from_log(a.log.read_text(encoding="utf-8", errors="replace")) if a.log else []
        written, skipped = write_launchers(b, regions)
        print(json.dumps({**doc, "regionIds": regions, "launchers": written, "skippedRegionIds": skipped}))
        return 0
    except (PostBuildError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
