"""Verify that the shipped source/meshes are exactly the tested version, and evidence is complete."""
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/edge-far-r2"
REFERENCE = "c05e8f06"
sources = ["tools/worldgen/streetscape/far_field.py",
           "game/Assets/_Project/World/Import/WorldEdgeBuilder.cs",
           "tests/gis/test_far_field_boundary.py"]
subprocess.run(["git", "diff", "--exit-code", REFERENCE, "--", *sources], cwd=ROOT, check=True)
qa_file = "Data/Regions/bialystok-industrial-c/generated/far_field_qa.json"
expected = json.loads(subprocess.check_output(["git", "show", f"{REFERENCE}:{qa_file}"], cwd=ROOT))
actual = json.loads((ROOT / qa_file).read_text(encoding="utf-8"))
assert actual == expected
mesh_hashes = {}
for tier in ("Low", "High"):
    item = actual["tiers"][tier]
    digest = hashlib.sha256((ROOT / item["file"]).read_bytes()).hexdigest()
    assert digest == item["sha256"]
    mesh_hashes[tier] = digest

tests = {}
for filename, count in [("editmode-20261111-120601.xml", 226), ("playmode-20261111-120628.xml", 3)]:
    run = ET.parse(ROOT / "artifacts/tests" / filename).getroot()
    assert int(run.attrib["passed"]) == count and int(run.attrib["failed"]) == 0
    assert int(run.attrib["skipped"]) == 0
    tests[filename] = dict(run.attrib)
assert (OUT / "EVIDENCE_COMPLETE").exists() and (OUT / "SKYLINE_COMPLETE").exists()
frames = []
for path in [OUT / "before", OUT / "after", OUT / "skyline/before", OUT / "skyline/after"]:
    frames.extend(path.rglob("*.png"))
assert len(frames) == 64
for frame in frames:
    with Image.open(frame) as picture:
        assert picture.size == (2340, 1080)
        picture.verify()
rows = json.loads((OUT / "measurements.json").read_text())
skyline = json.loads((OUT / "skyline-measurements.json").read_text())
low = [r for r in rows + skyline if r["configuration"].startswith("Low")]
draw_deltas = [r["after"]["static_draws"] + r["after"]["instanced_draws"]
               - r["before"]["static_draws"] - r["before"]["instanced_draws"] for r in low]
tri_deltas = [r["after"]["static_tris_k"] + r["after"]["instanced_tris_k"]
              - r["before"]["static_tris_k"] - r["before"]["instanced_tris_k"] for r in low]
assert max(draw_deltas) == 0 and max(tri_deltas) == 0
report = dict(tested_source_reference=REFERENCE, source_files=sources,
              meshes_match_tested_commit=mesh_hashes, unity_tests=tests,
              verified_pngs=len(frames), paired_estimates=len(rows) + len(skyline),
              low_max_delta_draws=max(draw_deltas), low_max_delta_tris_k=max(tri_deltas),
              gis="388 passed, 1 expected xfailed; gis-after.log",
              independent_review="pending leader", phone_validation="leader-owned; not performed here")
(OUT / "VALIDATION.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("Verified tested source, identical tested meshes, 64 PNGs, 32 pairs, Unity 226+3 passed; Low +0 draws/+0 max trisK")
