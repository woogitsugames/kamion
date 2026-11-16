"""Input hashes of the road fidelity report (ADR 0075, ADR 0245).

One definition for the writer (fidelity/run.py) and the staleness test (tests/gis/test_road_fidelity.py):
- every hash is CRLF-normalised (Windows checkouts and Linux CI agree);
- generator code = the road generator modules TRACKED by git (`git ls-files`), so an untracked work-in-progress
  file in a local checkout (s21: an empty `roads/tunnels.py` of an unmerged branch) does not leak into a committed
  report that no clean checkout can then reproduce;
- a module recorded with the hash of an empty file is equivalent to a missing module (an empty module adds no code).
No Data/raw is read here: the report's inputs are the region graph/overrides/route and the generator code.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ROADS_DIR = "tools/worldgen/roads"
REGION_FILES = ("roads.graph.json", "overrides.yaml", "route_start.json")
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


def sha_file(p: Path) -> str:
    # CRLF-normalised: Windows checkouts and Linux CI must agree (Mistral M1 review)
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def generator_modules(repo: Path = REPO) -> list[str] | None:
    """Repo-relative paths of the tracked road generator modules, sorted; None when git is not available."""
    try:
        r = subprocess.run(["git", "-C", str(repo), "ls-files", "--", f"{ROADS_DIR}/*.py"],
                           capture_output=True, text=True, check=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return sorted(p for p in r.stdout.splitlines() if p.count("/") == ROADS_DIR.count("/") + 1)


def compute(rdir: Path, repo: Path = REPO) -> dict[str, str]:
    inputs = {p: sha_file(rdir / p) for p in REGION_FILES}
    mods = generator_modules(repo)
    if mods is None:                       # no git (exported tree): every module on disk
        mods = sorted(f"{ROADS_DIR}/{p.name}" for p in (repo / ROADS_DIR).glob("*.py"))
    for m in mods:
        p = repo / m
        if p.exists():
            inputs[m] = sha_file(p)
    return inputs


def stale(recorded: dict[str, str], rdir: Path, repo: Path = REPO) -> list[str]:
    """Keys of `recorded` whose file changed, plus tracked generator modules the report does not know."""
    out = []
    mods = generator_modules(repo)
    for k, v in recorded.items():
        p = (rdir / k) if "/" not in k else (repo / k)
        untracked = mods is not None and k.startswith(ROADS_DIR + "/") and k not in mods
        if untracked or not p.exists():    # an untracked module is not part of the generator (same as compute)
            if v != EMPTY_SHA256:          # an empty module that is gone changed nothing
                out.append(k)
        elif sha_file(p) != v:
            out.append(k)
    if mods is not None:
        out += [m for m in mods if m not in recorded]
    return out
