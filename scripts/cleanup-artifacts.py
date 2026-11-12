"""Housekeeping for artifacts/ (owner decision s16, 2026-11-12).

- APK: keep the 5 newest builds + every build named in HANDOVER.md (owner's test APKs); delete the rest
  (apk + .sha256 + .content.json siblings). Tracked files are never touched.
- Other artifacts: delete UNTRACKED files older than --days (default 3), except reports and evidence:
  *.md/*.txt/*.json/*.csv/*.xml/*.log and anything under live/, locks/, owner-feedback/, apk/, or a path
  containing 'pairs', 'gate3', 'sbs', 'REPORT'.  Paths used by active worktrees are not under artifacts/.

Usage: uv run --project tools/worldgen python scripts/cleanup-artifacts.py [--days 3] [--dry-run]
"""
import argparse
import os
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
STEM = re.compile(r"(kamion-0\.1\.0-[0-9a-f]+(?:-dirty)?)")
KEEP_EXT = {".md", ".txt", ".json", ".csv", ".xml", ".log", ".ps1", ".py"}
KEEP_TOP = {"live", "locks", "owner-feedback", "apk"}
KEEP_SUB = ("pairs", "gate3", "sbs", "REPORT")


def tracked() -> set[str]:
    out = subprocess.run(["git", "ls-files", "artifacts"], cwd=ROOT, capture_output=True, text=True, check=True)
    return {line.strip() for line in out.stdout.splitlines()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=float, default=3.0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    tr = tracked()
    rel = lambda p: p.relative_to(ROOT).as_posix()  # noqa: E731

    # APK
    keep = set(STEM.findall((ROOT / "HANDOVER.md").read_text(encoding="utf-8")))
    apks = sorted((ART / "apk").glob("*.apk"), key=lambda p: p.stat().st_mtime, reverse=True)
    keep |= {STEM.match(p.name).group(1) for p in apks[:5] if STEM.match(p.name)}
    apk_n = apk_b = 0
    for p in (ART / "apk").glob("*"):
        m = STEM.match(p.name)
        if not p.is_file() or not m or m.group(1) in keep or rel(p) in tr:
            continue
        apk_b += p.stat().st_size
        apk_n += 1
        if not a.dry_run:
            p.unlink()

    # other artifacts
    cutoff = time.time() - a.days * 86400
    n = b = 0
    for dirpath, _dirs, files in os.walk(ART):
        d = Path(dirpath)
        parts = d.relative_to(ART).parts
        if parts and parts[0] in KEEP_TOP:
            continue
        if any(k in d.as_posix() for k in KEEP_SUB):
            continue
        for f in files:
            p = d / f
            if p.suffix.lower() in KEEP_EXT or "REPORT" in f:
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            if st.st_mtime >= cutoff or rel(p) in tr:
                continue
            b += st.st_size
            n += 1
            if not a.dry_run:
                try:
                    p.unlink()
                except OSError:
                    pass
    print(f"apk: {apk_n} files {apk_b / 1e9:.2f} GB; other: {n} files {b / 1e9:.2f} GB; kept apk builds {len(keep)};"
          f" {'DRY RUN' if a.dry_run else 'deleted'}")


if __name__ == "__main__":
    main()
