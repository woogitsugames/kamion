"""License audit of git-tracked binary assets against docs/LICENSES.md.

CLAUDE.md rule 8: every asset must have an entry in docs/LICENSES.md; no
Fab/Megascans files in git; no Google Maps/Street View/Earth/3D Tiles.

Zasób (reguła, używana też w raporcie i testach):
  plik śledzony przez git (`git ls-files`) o rozszerzeniu binarnego zasobu:
  tekstura/obraz/HDRI/zdjęcie (png jpg jpeg webp tga tif tiff exr hdr psd bmp),
  audio (wav ogg mp3 aiff aif), model 3D (glb fbx obj blend), font (ttf otf woff woff2).
  POMIJANE jako generowane kodem: każda ścieżka, której którykolwiek segment
  katalogu (nazwa między „/”) to „generated” albo „_Generated” (bez względu na
  wielkość liter) — tam są wyłącznie wyniki generatorów (Data/**/generated/**,
  game/Assets/_Generated/**, game/Assets/_Project/Audio/Generated/**).
  Pliki .meta i *_meta.json nie są zasobami (nie mają rozszerzenia zasobu).

Pokrycie: wpis w docs/LICENSES.md = dowolny token w backtickach wyglądający na
ścieżkę lub wzorzec (zawiera „/”, „*” lub „?”), dopasowany do ścieżki pliku
albo do dowolnego jej sufiksu zaczynającego się na granicy katalogu (wzorce typu
`Environment/DrivingLab/Textures/T_*.png` są względem game/Assets/_Project).
Wzorce występujące wyłącznie w sekcji z nagłówkiem „UNVERIFIED” nie pokrywają —
liczą się jako „unverified” (do uzupełnienia przez lidera).

Uruchomienie:
  uv run --project tools/licenses python tools/licenses/audit.py [--json artifacts/licenses-audit.json] [-v]
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LICENSES = REPO / "docs" / "LICENSES.md"

CATEGORY_EXTENSIONS = {
    "texture/photo/hdri": {".png", ".jpg", ".jpeg", ".webp", ".tga", ".tif", ".tiff", ".exr", ".hdr", ".psd", ".bmp"},
    "audio": {".wav", ".ogg", ".mp3", ".aiff", ".aif"},
    "model": {".glb", ".fbx", ".obj", ".blend"},
    "font": {".ttf", ".otf", ".woff", ".woff2"},
}
ASSET_EXTENSIONS = {ext for exts in CATEGORY_EXTENSIONS.values() for ext in exts}

GENERATED_SEGMENTS = {"generated", "_generated"}

FAB_NAME_TOKENS = (re.compile(r"\bfab\b", re.IGNORECASE), re.compile(r"megascans", re.IGNORECASE), re.compile(r"quixel", re.IGNORECASE))
GOOGLE_NAME_TOKENS = (
    re.compile(r"google", re.IGNORECASE),
    re.compile(r"street[ _-]?view", re.IGNORECASE),
    re.compile(r"\bgmaps\b", re.IGNORECASE),
    re.compile(r"3d[ _-]?tiles", re.IGNORECASE),
)
FAB_CONTENT_TOKENS = (b"quixel", b"megascans")
GOOGLE_CONTENT_TOKENS = (b"google maps", b"street view", b"google earth", b"3d tiles")

LFS_POINTER_MAGIC = b"version https://git-lfs.github.com/spec/v1"

BACKTICK = re.compile(r"`([^`\n]+)`")
HEADING = re.compile(r"^#{1,6}\s")


@dataclass
class Pattern:
    raw: str
    unverified_only: bool


@dataclass
class Asset:
    path: str
    category: str
    covered_by: list[str] = field(default_factory=list)
    unverified_by: list[str] = field(default_factory=list)
    suspicious: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.suspicious:
            return "suspicious"
        if self.covered_by:
            return "covered"
        return "unverified"


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True).stdout
    return [p.decode("utf-8") for p in out.split(b"\0") if p]


def category_of(path: str) -> str | None:
    ext = Path(path).suffix.lower()
    for cat, exts in CATEGORY_EXTENSIONS.items():
        if ext in exts:
            return cat
    return None


def is_code_generated(path: str) -> bool:
    return any(seg.lower() in GENERATED_SEGMENTS for seg in path.split("/")[:-1])


def list_assets() -> list[Asset]:
    assets = []
    for path in tracked_files():
        cat = category_of(path)
        if cat is None or is_code_generated(path):
            continue
        assets.append(Asset(path=path, category=cat))
    return assets


def load_patterns() -> list[Pattern]:
    patterns: list[Pattern] = []
    seen: set[tuple[str, bool]] = set()
    unverified_section = False
    for line in LICENSES.read_text(encoding="utf-8").splitlines():
        if HEADING.match(line):
            if "UNVERIFIED" in line.upper():
                unverified_section = True
            elif line.lstrip("#").strip() and "UNVERIFIED" not in line.upper():
                # nowy nagłówek główny (##) bez UNVERIFIED zamyka sekcję UNVERIFIED
                if line.startswith("## ") and not line.startswith("### "):
                    unverified_section = False
            continue
        for m in BACKTICK.finditer(line):
            tok = m.group(1).strip().rstrip(".,;)")
            if not tok or "/" not in tok and "*" not in tok and "?" not in tok and Path(tok).suffix.lower() not in ASSET_EXTENSIONS:
                continue
            if tok.startswith("http") or tok.startswith("<"):
                continue
            key = (tok, unverified_section)
            if key in seen:
                continue
            seen.add(key)
            patterns.append(Pattern(raw=tok, unverified_only=unverified_section))
    return patterns


def expand_braces(pattern: str) -> list[str]:
    """Rozwiń nawiasy klamrowe: `art-source/world/vegetation/{leaves,bark}_*.png` → 2 wzorce."""
    m = re.search(r"\{([^{}]+)\}", pattern)
    if not m:
        return [pattern]
    out = []
    for alt in m.group(1).split(","):
        out.extend(expand_braces(pattern[: m.start()] + alt + pattern[m.end():]))
    return out


def _suffixes(path: str) -> list[str]:
    parts = path.split("/")
    return ["/".join(parts[i:]) for i in range(1, len(parts))]


def pattern_matches(pattern: str, path: str) -> bool:
    if pattern.endswith("/"):  # wzorzec katalogu: `art-source/world/materials/_renders/`
        return path.startswith(pattern) or any(s.startswith(pattern) for s in _suffixes(path))
    for pat in expand_braces(pattern):
        if fnmatch.fnmatchcase(path, pat):
            return True
    return any(fnmatch.fnmatchcase(s, pat) for s in _suffixes(path) for pat in expand_braces(pattern))


def _is_lfs_pointer(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            return fh.read(len(LFS_POINTER_MAGIC)) == LFS_POINTER_MAGIC
    except OSError:
        return False


def scan_content(asset: Asset) -> None:
    """Metadane binarne: GLB/FBX mogą zawierać nazwy producenta w nagłówku/JSON."""
    if Path(asset.path).suffix.lower() not in {".glb", ".fbx", ".obj"}:
        return
    p = REPO / asset.path
    if not p.is_file() or _is_lfs_pointer(p):
        return
    blob = p.read_bytes().lower()
    for tok in FAB_CONTENT_TOKENS:
        if tok in blob:
            asset.suspicious.append(f"content:{tok.decode()}")
    for tok in GOOGLE_CONTENT_TOKENS:
        if tok in blob:
            asset.suspicious.append(f"content:{tok.decode()}")


def scan_names(assets: list[Asset]) -> None:
    for a in assets:
        name = a.path.lower()
        for tok in FAB_NAME_TOKENS:
            if tok.search(name):
                a.suspicious.append(f"name:{tok.pattern}")
        for tok in GOOGLE_NAME_TOKENS:
            if tok.search(name):
                a.suspicious.append(f"name:{tok.pattern}")


def audit() -> dict:
    assets = list_assets()
    patterns = load_patterns()
    for a in assets:
        for pat in patterns:
            if pattern_matches(pat.raw, a.path):
                (a.unverified_by if pat.unverified_only else a.covered_by).append(pat.raw)
    scan_names(assets)
    for a in assets:
        scan_content(a)
    by_status = {"covered": [], "unverified": [], "suspicious": []}
    for a in assets:
        by_status[a.status].append(a.path)
    by_category: dict[str, int] = {}
    for a in assets:
        by_category[a.category] = by_category.get(a.category, 0) + 1
    return {
        "total": len(assets),
        "by_category": by_category,
        "covered": sorted(by_status["covered"]),
        "unverified": sorted(by_status["unverified"]),
        "suspicious": sorted(by_status["suspicious"]),
        "assets": [
            {
                "path": a.path,
                "category": a.category,
                "status": a.status,
                "covered_by": a.covered_by,
                "unverified_by": a.unverified_by,
                "suspicious": a.suspicious,
            }
            for a in assets
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit tracked assets vs docs/LICENSES.md")
    ap.add_argument("--json", type=Path, default=None, help="write full JSON report here")
    ap.add_argument("-v", "--verbose", action="store_true", help="list unverified/suspicious files")
    args = ap.parse_args()

    rep = audit()
    print(f"assets total:   {rep['total']}  {rep['by_category']}")
    print(f"covered:        {len(rep['covered'])}")
    print(f"unverified:     {len(rep['unverified'])}")
    print(f"suspicious:     {len(rep['suspicious'])}")
    if args.verbose:
        for label in ("unverified", "suspicious"):
            if rep[label]:
                print(f"\n== {label} ==")
                for p in rep[label]:
                    print(" ", p)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nJSON report: {args.json}")
    return 1 if rep["suspicious"] else 0


if __name__ == "__main__":
    sys.exit(main())
