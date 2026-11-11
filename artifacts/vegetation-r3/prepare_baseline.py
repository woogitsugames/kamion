"""Reuse identical control renders and snapshot their imported-world metadata."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[1]
prior = here.parent / "vegetation-r1"
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
proof = read(prior / "evidence-summary.json")
for name, digest in proof["files"].items():
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
        raise RuntimeError("Source drift; cannot reuse baseline: " + name)
subprocess.run(["git", "diff", "--exit-code", "85fc9d8a", "HEAD", "--",
                "tools/worldgen", "art-source/world", "game/Assets/_Project"], cwd=root, check=True)
snapshot = read(prior / "snapshot-candidate-b-pretests/sha256.json")
glbs = {k: v for k, v in snapshot["files"].items() if k.endswith(".glb")}
for name, digest in glbs.items():
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
        raise RuntimeError("World mesh drift; cannot reuse baseline: " + name)
for tier in ("Low", "High"):
    for weather in ("clear", "overcast"):
        name = tier + "-" + weather
        shutil.copytree(prior / "after" / name, here / "before" / name, dirs_exist_ok=True)
# Preserve the metadata that produced the imported B world, separately from
# the canonical on-disk metadata restored before merge. Windows snapshot paths
# use backslashes; normalise only for matching, not for filesystem access.
metadata_dir = here / "snapshot-baseline/imported-world"
metadata_dir.mkdir(parents=True, exist_ok=True)
metadata_count = 0
for name in snapshot["files"]:
    if name.replace("\\", "/").startswith("Data/Regions/bialystok-industrial-c/generated/") and name.endswith(".json"):
        shutil.copyfile(prior / "snapshot-candidate-b-pretests" / Path(name).name, metadata_dir / Path(name).name)
        metadata_count += 1
result = dict(prior_round="gpt-vegetation-r1", prior_candidate="B", prior_source_commit="51bd2559",
              merge_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
              reused_control_frames=268, exact_source_hashes=proof["files"], verified_raw_glbs=len(glbs),
              imported_metadata_files=metadata_count,
              note="World sources/assets unchanged by merge. SBS metadata changed; photo cameras will be captured afresh. No fresh rendering claim for reused controls. Imported B metadata is preserved separately; canonical files are not restored by this helper.")
(here / "baseline-provenance.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
print("Reused 268 controls after exact source and", len(glbs), "GLB hash checks; saved", metadata_count, "imported metadata files.")
