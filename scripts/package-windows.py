#!/usr/bin/env python3
"""Pack a Windows player folder (scripts/build-windows.ps1 output) into a distributable zip (ADR 0271).

    uv run --no-project python scripts/package-windows.py artifacts/win/kamion-0.1.0-<sha>-regions
    uv run --no-project python scripts/package-windows.py <build dir> --dry-run          # list what would ship
    uv run --no-project python scripts/package-windows.py <build dir> --release          # also fail on licence blockers

Output (default artifacts/dist/):
    kamion-<ver>-<sha>[-low][-dev][-dirty]-win64.zip      top folder of the same name inside
    kamion-<ver>-<sha>...-win64.zip.sha256                "<sha256>  <zip name>" (sha256sum format)
    kamion-<ver>-<sha>...-win64.json                      file list, sizes, excluded paths, warnings

The zip is reproducible for identical input: sorted entries, fixed timestamp, fixed permissions.
Stdlib only (Python >= 3.10). Exit codes: 0 ok, 2 bad input (missing exe/data, dev or dirty build without the
allow flag), 3 --release and a licence blocker is still open.

What does NOT ship (Unity names its debug output so that it says so itself; see docs/12_DYSTRYBUCJA_PC.md §2):
  *_BurstDebugInformation_DoNotShip/, *_BackUpThisFolder_ButDontShipItWithYourGame/, *.pdb, plus the build
  metadata written by build-windows.ps1 / BuildCommands (build.json, Kamion.exe.sha256, Kamion.content.json,
  Kamion.top.txt, Kamion.variants.txt), the developer launcher Kamion-knyszyn.cmd and every other root launcher
  (*.cmd with "-scene <x>", build-windows.ps1) whose scene / region is not in this build (see build_scenes()).
What is added: THIRD_PARTY_NOTICES.txt (generated from the in-game "Informacje" text, so both stay one source),
README.txt (requirements D74, how to start, where logs are), SHA256SUMS.txt, collect-logs.ps1 + Zbierz-logi.cmd.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXE_NAME = "Kamion.exe"            # BuildCommands.WindowsExeName
DATA_DIR = "Kamion_Data"           # Unity: <ProjectName>_Data next to the exe
ABOUT_RESOURCES = REPO / "game/Assets/_Project/UI/Resources"
ATTRIBUTIONS = ABOUT_RESOURCES / "About/attributions.txt"
README_TEMPLATE = REPO / "dist/windows/README.txt.in"
COLLECT_LOGS = REPO / "scripts/collect-logs.ps1"
PROJECT_SETTINGS = REPO / "game/ProjectSettings/ProjectSettings.asset"
EDITOR_BUILD_SETTINGS = REPO / "game/ProjectSettings/EditorBuildSettings.asset"
REGION_CATALOG = REPO / "game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json"   # RegionBuildList.CatalogAssetPath
WORLD_ROOT = "Assets/_Generated/World/"     # RegionScenes.GeneratedRoot: scenes of region <id> live in WORLD_ROOT + <id>/
CITY_PREFIX = "bialystok-"                  # RegionCatalog.CityPrefix

# Directory names (any depth) that never ship.
EXCLUDED_DIR_GLOBS = ("*_BurstDebugInformation_DoNotShip", "*_BackUpThisFolder_ButDontShipItWithYourGame", "*_DoNotShip")
# File names (any depth) that never ship.
EXCLUDED_FILE_GLOBS = ("*.pdb",)
# Build metadata in the player root (build-windows.ps1 / BuildCommands.WriteContentReport): useful for us, not players.
EXCLUDED_ROOT_FILES = ("build.json", "Kamion.exe.sha256", "Kamion.content.json", "Kamion.top.txt",
                       "Kamion.variants.txt")
# Developer shortcuts (ADR 0271 §2): never ship, whatever the build holds.
DEV_LAUNCHERS = ("Kamion-knyszyn.cmd",)
# Root launchers that jump into a scene (build-windows.ps1: "... -scene knyszyn-w %*") ship only when that scene is in the build.
LAUNCHER_SCENE_RE = re.compile(r"(?:^|\s)-scene\s+\"?([^\s\"%]+)", re.I)
# BuildCommands.BuildWindows logs the final scene list: "[BUILD] Windows x64 → <exe> (...) scenes=[a, b, c]".
BUILD_LOG_SCENES_RE = re.compile(r"\[BUILD\] Windows x64 .*? scenes=\[([^\]]*)\]")
# Present only in Development builds (Unity manual, Windows standalone binaries: WinPixEventRuntime.dll).
DEV_MARKERS = ("WinPixEventRuntime.dll",)

# Fixed zip timestamp (DOS epoch is 1980; 2000-01-01 avoids tools that treat 1980 as "no date").
ZIP_DATE = (2000, 1, 1, 0, 0, 0)
FOLDER_RE = re.compile(r"^kamion-(?P<ver>\d+\.\d+\.\d+[0-9A-Za-z.+]*)-(?P<sha>[0-9a-f]{7,40})(?P<flags>(?:-[a-z]+)*)$")


@dataclass
class Plan:
    build_dir: Path
    version: str
    sha: str
    dirty: bool
    low: bool
    dev: bool
    files: list[Path] = field(default_factory=list)       # relative to build_dir, shipped
    excluded: list[str] = field(default_factory=list)     # relative posix paths (dirs end with '/')
    warnings: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        flags = "".join(s for s, on in (("-low", self.low), ("-dev", self.dev), ("-dirty", self.dirty)) if on)
        return f"kamion-{self.version}-{self.sha}{flags}-win64"


class PackageError(Exception):
    def __init__(self, msg: str, code: int = 2):
        super().__init__(msg)
        self.code = code


def is_excluded_dir(name: str) -> bool:
    return any(fnmatch.fnmatchcase(name, g) for g in EXCLUDED_DIR_GLOBS)


def is_excluded_file(rel: Path) -> bool:
    if any(fnmatch.fnmatchcase(rel.name.lower(), g) for g in EXCLUDED_FILE_GLOBS):
        return True
    return len(rel.parts) == 1 and rel.name in EXCLUDED_ROOT_FILES


# ---------------------------------------------------------------- scenes in the build (region launchers)

def _catalog(path: Path = REGION_CATALOG) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def resolve_region_id(cat: dict, token: str) -> str | None:
    """RegionCatalog.ResolveId: exact id, alias, or id without "bialystok-"; None when unknown."""
    t = (token or "").strip().lower()
    ids = [r["id"] for r in cat.get("regions", [])]
    if not t:
        return None
    if t in ids:
        return t
    for a in cat.get("aliases", []):
        if a.get("alias", "").lower() == t:
            return a.get("region")
    return CITY_PREFIX + t if CITY_PREFIX + t in ids else None


def resolve_regions(cat: dict, spec: str, errors: list[str]) -> list[str]:
    """RegionCatalog.Resolve (ids, aliases, sets, "all", ranges "a..b" and "a ... b"), in order, no duplicates."""
    ids = [r["id"] for r in cat.get("regions", [])]
    out: list[str] = []

    def add(i):
        if i not in out:
            out.append(i)

    def add_range(a, b, tok):
        if a not in ids or b not in ids:
            errors.append(f"range {tok!r}: unknown end")
            return
        x, y = ids.index(a), ids.index(b)
        for k in (range(x, y + 1) if x <= y else range(x, y - 1, -1)):
            add(ids[k])

    pending = None
    for t in (x for x in re.split(r"[,;\s\u00a0]+", spec or "") if x):
        if t in ("...", "…"):
            pending = out[-1] if out else None
            if pending is None:
                errors.append(f"{t!r} without a region before it")
            continue
        d = t.find("..")
        if 0 < d and d + 2 < len(t):
            add_range(resolve_region_id(cat, t[:d]), resolve_region_id(cat, t[d + 2:].lstrip(".")), t)
            pending = None
            continue
        if t.lower() == "all":
            for i in ids:
                add(i)
            pending = None
            continue
        st = next((x for x in cat.get("sets", []) if x.get("name", "").lower() == t.lower()), None)
        if st is not None:
            for r in st.get("regions", []):
                i = resolve_region_id(cat, r)
                add(i) if i else errors.append(f"set {st['name']}: unknown region {r!r}")
            pending = None
            continue
        one = resolve_region_id(cat, t)
        if one is None:
            errors.append(f"unknown region {t!r}")
        elif pending is not None:
            add_range(pending, one, f"{pending}...{one}")
        else:
            add(one)
        pending = None
    if pending is not None:
        errors.append("'...' without a region after it")
    return out


def _base_scenes(path: Path = EDITOR_BUILD_SETTINGS) -> list[str]:
    """Enabled scenes of EditorBuildSettings.asset (the list every build starts from, BuildCommands.ComposeBuildScenes)."""
    scenes, enabled = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*-?\s*enabled:\s*(\d)", line)
        if m:
            enabled = m.group(1) == "1"
            continue
        m = re.match(r"\s*path:\s*(\S+\.unity)\s*$", line)
        if m and enabled:
            scenes.append(m.group(1))
    return scenes


def build_scenes(build_dir: Path, info: dict, warnings: list[str]) -> list[str] | None:
    """Scene paths in this player build, None when they cannot be told (then every scene launcher stays out).

    1. the "[BUILD] Windows x64 ... scenes=[...]" line of the build log named in build.json "log" (the real list, also
       with -RegionsAllowMissing); 2. else build.json "regions" / "regionsFile" resolved with the region catalog on top of
       EditorBuildSettings (as RegionBuildList does; a region skipped by -RegionsAllowMissing is not visible here).
    """
    log = info.get("log")
    if log:
        try:
            hits = BUILD_LOG_SCENES_RE.findall(Path(log).read_text(encoding="utf-8-sig", errors="replace"))
            if hits:
                return [x.strip() for x in hits[-1].split(",") if x.strip()]
        except OSError:
            pass
    if not info:
        warnings.append("no build.json: scenes of the build unknown, scene launchers (-scene) left out")
        return None
    try:
        spec = info.get("regions") or ""
        rf = info.get("regionsFile") or ""
        if rf:
            p = Path(rf) if Path(rf).is_absolute() else REPO / rf
            doc = json.loads(p.read_text(encoding="utf-8-sig"))
            spec = ",".join(x for x in (spec, ",".join(doc.get("regions", []))) if x)
        errors: list[str] = []
        regions = resolve_regions(_catalog(), spec, errors) if spec.strip() else []
        if errors:
            warnings.append("regions of build.json not resolvable (" + "; ".join(errors) + "): scene launchers left out")
            return None
        scenes = _base_scenes()
    except (OSError, ValueError, KeyError) as e:
        warnings.append(f"scenes of the build unknown ({e}): scene launchers (-scene) left out")
        return None
    high = info.get("worldHigh") is not False
    for r in regions:
        name = "WorldC" if r == "bialystok-industrial-c" else "World_" + r      # RegionScenes.SceneNameFor
        for n in (name, name + "_High") if high else (name,):
            path = f"{WORLD_ROOT}{r}/{n}.unity"
            if path not in scenes:
                scenes.append(path)
    if regions:
        warnings.append("region scenes taken from build.json regions/regionsFile (build log not found): "
                        "a region skipped by -RegionsAllowMissing would not be noticed")
    return scenes


def launcher_ships(rel: Path, build_dir: Path, scenes: list[str] | None) -> bool:
    """A root *.cmd with "-scene <x>" ships only if <x> (region id / alias / scene name, as GameBootstrap.LaunchSceneFor)
    is in the build; Kamion-okno.cmd and other launchers without -scene always ship."""
    try:
        m = LAUNCHER_SCENE_RE.search((build_dir / rel).read_text(encoding="ascii", errors="replace"))
    except OSError:
        return False
    if not m:
        return True
    if scenes is None:
        return False
    token = m.group(1)
    try:
        rid = resolve_region_id(_catalog(), token)
    except (OSError, ValueError):
        rid = None
    if rid is not None:
        return any(s.startswith(f"{WORLD_ROOT}{rid}/") for s in scenes)
    return any(Path(s).stem.lower() == token.lower() for s in scenes)


def read_project_version() -> str | None:
    try:
        m = re.search(r"^\s*bundleVersion:\s*(\S+)\s*$", PROJECT_SETTINGS.read_text(encoding="utf-8"), re.M)
        return m.group(1) if m else None
    except OSError:
        return None


def read_build_json(build_dir: Path) -> dict:
    bj = build_dir / "build.json"
    if not bj.is_file():
        return {}
    try:
        return json.loads(bj.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        raise PackageError(f"build.json unreadable: {e}")


def identify(build_dir: Path, version: str | None, sha: str | None) -> tuple[str, str, bool, bool, bool]:
    """Version / sha / flags from build.json (build-windows.ps1), else the folder name, else arguments."""
    info = read_build_json(build_dir)
    m = FOLDER_RE.match(build_dir.name)
    flags = m.group("flags").split("-") if m else []
    ver = version or info.get("version") or (m.group("ver") if m else None) or read_project_version()
    raw_sha = sha or info.get("sha") or (m.group("sha") + ("-dirty" if "dirty" in flags else "") if m else None)
    if not ver or not raw_sha:
        raise PackageError("cannot tell version/sha: pass --version and --sha (or keep build.json / the folder name)")
    dirty = raw_sha.endswith("-dirty") or "dirty" in flags
    clean_sha = raw_sha.removesuffix("-dirty")
    if not re.fullmatch(r"[0-9a-f]{7,40}", clean_sha):
        raise PackageError(f"sha does not look like a git sha: {raw_sha!r}")
    if not re.fullmatch(r"\d+\.\d+\.\d+[0-9A-Za-z.+-]*", ver):
        raise PackageError(f"version is not semver-like: {ver!r}")
    low = bool(info.get("worldHigh") is False) or "low" in flags
    dev = bool(info.get("development")) or "dev" in flags
    return ver, clean_sha, dirty, low, dev


def plan_package(build_dir: Path, version: str | None = None, sha: str | None = None,
                 allow_dev: bool = False, allow_dirty: bool = False) -> Plan:
    build_dir = build_dir.resolve()
    if not build_dir.is_dir():
        raise PackageError(f"not a directory: {build_dir}")
    if not (build_dir / EXE_NAME).is_file():
        raise PackageError(f"{EXE_NAME} missing in {build_dir}")
    if not (build_dir / DATA_DIR).is_dir():
        raise PackageError(f"{DATA_DIR}/ missing in {build_dir}")
    if not (build_dir / "UnityPlayer.dll").is_file():
        raise PackageError(f"UnityPlayer.dll missing in {build_dir}")
    ver, s, dirty, low, dev = identify(build_dir, version, sha)
    plan = Plan(build_dir, ver, s, dirty, low, dev)
    scenes = build_scenes(build_dir, read_build_json(build_dir), plan.warnings)

    for p in sorted(build_dir.rglob("*")):
        rel = p.relative_to(build_dir)
        hit = next((i for i, part in enumerate(rel.parts) if is_excluded_dir(part)), None)
        if hit is not None:
            if hit == len(rel.parts) - 1 and p.is_dir():      # report the top excluded folder once
                plan.excluded.append(rel.as_posix() + "/")
            continue
        if p.is_symlink():
            plan.warnings.append(f"symlink skipped: {rel.as_posix()}")
            continue
        if p.is_dir():
            continue
        if is_excluded_file(rel):
            plan.excluded.append(rel.as_posix())
            continue
        if len(rel.parts) == 1 and rel.suffix.lower() == ".cmd" and (
                rel.name in DEV_LAUNCHERS or not launcher_ships(rel, build_dir, scenes)):
            plan.excluded.append(rel.as_posix())
            continue
        if len(rel.parts) == 1 and rel.name in DEV_MARKERS:
            plan.dev = True
        plan.files.append(rel)

    if plan.dev and not allow_dev:
        raise PackageError("Development build (WinPixEventRuntime.dll / -dev): pass --allow-dev to pack it for testers")
    if plan.dirty and not allow_dirty:
        raise PackageError("build from a dirty checkout (sha ends with -dirty): pass --allow-dirty or rebuild from a clean commit")
    if plan.dirty:
        plan.warnings.append("dirty checkout: the zip is not reproducible from the commit alone")
    return plan


# ---------------------------------------------------------------- notices / readme

def render_notices(attributions: Path = ATTRIBUTIONS, resources: Path = ABOUT_RESOURCES) -> str:
    """Plain-text THIRD_PARTY_NOTICES from the in-game "Informacje" document (same format as AttributionDocument)."""
    out = ["KAMION — informacje o licencjach i atrybucje (THIRD_PARTY_NOTICES)",
           "Ten sam tekst co ekran „Informacje” w menu gry.", ""]
    for line in attributions.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("#"):
            continue
        if line.startswith("@include "):
            inc = resources / (line[len("@include "):].strip() + ".txt")
            if not inc.is_file():
                raise PackageError(f"@include target missing: {inc}")
            out.extend(inc.read_text(encoding="utf-8-sig").rstrip("\n").splitlines())
            out.append("")
        elif line.startswith("== "):
            t = line[3:].strip()
            out += [t, "-" * len(t)]
        elif line.startswith("= "):
            t = line[2:].strip()
            out += ["", t.upper(), "=" * len(t)]
        else:
            out.append(line.rstrip())
    text = "\n".join(out).rstrip() + "\n"
    return re.sub(r"\n{3,}", "\n\n", text)


def licence_blockers(attributions: Path = ATTRIBUTIONS) -> list[str]:
    """Open P0 items still marked in the attribution source (docs/reports/LICENSES-AUDIT-S20.md)."""
    text = attributions.read_text(encoding="utf-8-sig")
    found = []
    if "R-P0-2" in text:
        found.append("R-P0-2: ODbL §4.6 offer of the derived OSM database (navigation data) has no address yet "
                     "(attributions.txt still carries the R-P0-2 note) — owner decision")
    if re.search(r"\[ADRES", text):
        found.append("placeholder [ADRES …] in the attribution text")
    return found


def render_readme(plan: Plan, template: Path = README_TEMPLATE, today: date | None = None) -> str:
    text = template.read_text(encoding="utf-8-sig")
    values = {"name": plan.name, "version": plan.version, "sha": plan.sha,
              "date": (today or date.today()).isoformat(),
              "flags": ", ".join(f for f, on in (("Low", plan.low), ("Development", plan.dev), ("dirty", plan.dirty)) if on) or "—"}
    for k, v in values.items():
        text = text.replace("{" + k + "}", v)
    if re.search(r"\{[a-z]+\}", text):
        raise PackageError(f"unfilled placeholder in {template}")
    return text.replace("\r\n", "\n").replace("\n", "\r\n")   # Notepad-friendly


# ---------------------------------------------------------------- zip

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _zinfo(arcname: str, size: int) -> zipfile.ZipInfo:
    zi = zipfile.ZipInfo(arcname, ZIP_DATE)
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.external_attr = 0o644 << 16
    zi.create_system = 0          # MS-DOS: same bytes on every OS
    zi.file_size = size
    return zi


def write_package(plan: Plan, out_dir: Path, extra: dict[str, bytes], compresslevel: int = 6) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{plan.name}.zip"
    tmp = zip_path.with_suffix(".zip.part")
    root = plan.name
    sums: list[tuple[str, str]] = []
    entries: list[dict] = []
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=compresslevel, allowZip64=True) as zf:
        items: list[tuple[str, Path | bytes]] = [(rel.as_posix(), plan.build_dir / rel) for rel in plan.files]
        items += list(extra.items())
        for arc, src in sorted(items, key=lambda t: t[0]):
            if isinstance(src, Path):
                size = src.stat().st_size
                zi = _zinfo(f"{root}/{arc}", size)
                h = hashlib.sha256()
                with src.open("rb") as fin, zf.open(zi, "w", force_zip64=size >= zipfile.ZIP64_LIMIT) as fout:
                    for chunk in iter(lambda: fin.read(1 << 20), b""):
                        h.update(chunk)
                        fout.write(chunk)
                digest = h.hexdigest()
            else:
                size = len(src)
                zf.writestr(_zinfo(f"{root}/{arc}", size), src)
                digest = hashlib.sha256(src).hexdigest()
            sums.append((digest, arc))
            entries.append({"path": arc, "bytes": size, "sha256": digest})
        listing = "".join(f"{d}  {a}\n" for d, a in sums).encode("ascii", "backslashreplace")
        zf.writestr(_zinfo(f"{root}/SHA256SUMS.txt", len(listing)), listing)
    shutil.move(tmp, zip_path)
    zip_sha = _sha256_file(zip_path)
    (out_dir / f"{zip_path.name}.sha256").write_text(f"{zip_sha}  {zip_path.name}\n", encoding="ascii", newline="\n")
    manifest = {
        "name": plan.name, "version": plan.version, "sha": plan.sha, "dirty": plan.dirty, "low": plan.low,
        "development": plan.dev, "zip": zip_path.name, "zipSha256": zip_sha, "zipBytes": zip_path.stat().st_size,
        "files": len(entries), "payloadBytes": sum(e["bytes"] for e in entries),
        "excluded": plan.excluded, "warnings": plan.warnings, "entries": entries,
    }
    (out_dir / f"{plan.name}.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def extras(plan: Plan) -> dict[str, bytes]:
    out = {
        "THIRD_PARTY_NOTICES.txt": render_notices().replace("\n", "\r\n").encode("utf-8-sig"),
        "README.txt": render_readme(plan).encode("utf-8-sig"),
    }
    if COLLECT_LOGS.is_file():
        out["collect-logs.ps1"] = COLLECT_LOGS.read_bytes()
        out["Zbierz-logi.cmd"] = ('@echo off\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0collect-logs.ps1" %*\r\n'
                                  'pause\r\n').encode("ascii")
    else:
        plan.warnings.append("scripts/collect-logs.ps1 missing - tester log collector not packed")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("build_dir", type=Path, help="folder with Kamion.exe (artifacts/win/kamion-<ver>-<sha>...)")
    ap.add_argument("--out-dir", type=Path, default=REPO / "artifacts/dist")
    ap.add_argument("--version", help="override version (default: build.json / folder name / ProjectSettings)")
    ap.add_argument("--sha", help="override git sha (default: build.json / folder name)")
    ap.add_argument("--allow-dev", action="store_true", help="pack a Development build (testers only)")
    ap.add_argument("--allow-dirty", action="store_true", help="pack a build from a dirty checkout (testers only)")
    ap.add_argument("--release", action="store_true", help="public release: fail on dev/dirty and on open licence blockers")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    ap.add_argument("--compresslevel", type=int, default=6)
    a = ap.parse_args(argv)
    try:
        if a.release and (a.allow_dev or a.allow_dirty):
            raise PackageError("--release cannot be combined with --allow-dev / --allow-dirty")
        plan = plan_package(a.build_dir, a.version, a.sha, a.allow_dev, a.allow_dirty)
        blockers = licence_blockers()
        for b in blockers:
            print(f"LICENCE BLOCKER: {b}", file=sys.stderr)
        if a.release and blockers:
            raise PackageError("public release blocked by open licence items (see docs/12_DYSTRYBUCJA_PC.md §5)", 3)
        if blockers:
            plan.warnings.append("internal/tester package only: " + "; ".join(blockers))
        ex = extras(plan)
        payload = sum((plan.build_dir / f).stat().st_size for f in plan.files)
        print(f"package  {plan.name}.zip  ({len(plan.files)} build files, {payload / 2**20:,.1f} MB before compression)")
        for e in plan.excluded:
            print(f"  exclude {e}")
        for k in sorted(ex):
            print(f"  add     {k}")
        for w in plan.warnings:
            print(f"  WARNING {w}")
        if a.dry_run:
            return 0
        m = write_package(plan, a.out_dir, ex, a.compresslevel)
        print(f"ZIP    {a.out_dir / m['zip']}  {m['zipBytes'] / 2**20:,.1f} MB, {m['files']} files")
        print(f"SHA256 {m['zipSha256']}")
        return 0
    except PackageError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
