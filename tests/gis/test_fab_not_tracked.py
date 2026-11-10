"""D45: Fab Standard License files must never be tracked by git (public repo)."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> set[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return set(out.splitlines())


def test_no_fab_files_tracked():
    tracked = _tracked()
    assert not [p for p in tracked if p.startswith("Data/raw/fab/")]
    for manifest in (ROOT / "Data/SourceManifests").glob("fab-*.json"):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for item in data["items"]:
            assert item["file"] not in tracked, item["file"]
            assert item["sha256"] and item["license"]


def test_fab_items_listed_in_licenses():
    lic = (ROOT / "docs/LICENSES.md").read_text(encoding="utf-8")
    for manifest in (ROOT / "Data/SourceManifests").glob("fab-*.json"):
        for item in json.loads(manifest.read_text(encoding="utf-8"))["items"]:
            assert item["listing_url"] in lic, item["id"]


def test_fab_derivative_paths_and_hashes_not_tracked():
    """Also detect renamed archives/products, not just their expected directory."""
    import hashlib
    from zipfile import ZipFile, BadZipFile

    tracked = _tracked()
    forbidden = ('Data/raw/fab/', 'art-source/world/megascans/_generated/', 'game/Assets/_Generated/')
    assert not [p for p in tracked if p.startswith(forbidden)]
    hashes = set()
    source_archives = []
    for manifest in (ROOT / 'Data/SourceManifests').glob('fab-*.json'):
        for item in json.loads(manifest.read_text(encoding='utf-8'))['items']:
            hashes.add(item['sha256'])
            if item.get('acquisition_record_sha256'):
                hashes.add(item['acquisition_record_sha256'])
            archive = ROOT / item['file']
            if archive.exists():
                source_archives.append(archive)
    generated = ROOT / 'art-source/world/megascans/_generated'
    # No dependence on local proprietary files on CI/public clones.
    for manifest in generated.glob('*manifest.json'):
        def walk(value):
            if isinstance(value, dict):
                if isinstance(value.get('sha256'), str): hashes.add(value['sha256'])
                for v in value.values(): walk(v)
            elif isinstance(value, list):
                for v in value: walk(v)
            elif isinstance(value, str) and value.startswith('art-source/world/megascans/_generated/'):
                path = ROOT / value
                if path.is_file(): hashes.add(hashlib.sha256(path.read_bytes()).hexdigest())
        walk(json.loads(manifest.read_text(encoding='utf-8')))
    # Hash tracked worktree content including staged additions; pointer files do
    # not conceal an accidentally checked-out source in local LFS storage.
    tracked_hashes = {}
    by_size = {}
    for name in sorted(tracked):
        path = ROOT / name
        if path.is_file():
            by_size.setdefault(path.stat().st_size, []).append(name)
            tracked_hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert not [p for p, h in tracked_hashes.items() if h in hashes]
    # Detect even renamed raw ZIP members. Only decompress members whose size
    # occurs in tracked files, keeping the guard cheap for large local libraries.
    known = set(tracked_hashes.values())
    for archive in source_archives:
        try:
            with ZipFile(archive) as z:
                for info in z.infolist():
                    if not info.is_dir() and info.file_size in by_size:
                        digest = hashlib.sha256(z.read(info)).hexdigest()
                        assert digest not in known, f'Fab ZIP member tracked: {info.filename}'
        except BadZipFile:
            raise AssertionError(f'Invalid local Fab ZIP: {archive.name}')
