"""Replace only the recaptured reference camera; retain both original pixels and stats."""
import hashlib
import json
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent
camera = "dk8-ref7204"
record = root / "baseline-camera-update.json"
assert not record.exists(), "Already applied; inspect the existing receipt before repeating"
assert (root / "pose-final-exit.txt").read_text().strip() == "0", "Capture not complete"


def selected(line):
    return line.startswith(camera + ":") or line.lstrip().startswith(camera + " instanced ")


rows = []
for condition in ("Low-overcast", "Low-clear", "High-overcast", "High-clear"):
    baseline, source = root / "before" / condition, root / "pose-final" / condition
    old = (baseline / "stats.txt").read_text(encoding="utf-8-sig").splitlines()
    new = (source / "stats.txt").read_text(encoding="utf-8-sig").splitlines()
    replacement = [line for line in new if selected(line)]
    assert len(replacement) == sum(selected(line) for line in old) == 2, condition
    assert old[0] == new[0], "Different rendering configuration"
    archive = root / "pose-initial-gps280" / condition
    archive.mkdir(parents=True, exist_ok=True)
    for name in (camera + ".png", "stats.txt"):
        shutil.copy2(baseline / name, archive / name)
    image = source / (camera + ".png")
    assert image.stat().st_size > 10000, "Missing image"
    updated = iter(replacement)
    (baseline / "stats.txt").write_text("\n".join(next(updated) if selected(line) else line for line in old) + "\n", encoding="utf-8")
    shutil.copy2(image, baseline / image.name)
    rows.append(dict(condition=condition, source=str(image.relative_to(root)),
                     sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                     replaced_stats_lines=replacement,
                     archived_original=str(archive.relative_to(root)),
                     baseline_png_count=len(list(baseline.glob("*.png")))))
assert all(row["baseline_png_count"] == 58 for row in rows)
record.write_text(json.dumps(dict(camera=camera, heading_before=280, heading_after=295,
                                  pose_confidence="UNVERIFIED", rows=rows), indent=2), encoding="utf-8")
print("Updated exactly one camera in all four inventories; original evidence archived")
