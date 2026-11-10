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
