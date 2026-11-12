"""Choose inspected heading; preserve the first camera definition."""
import copy
import json
from pathlib import Path

root = Path(__file__).resolve().parent
path = root / "cameras.json"
before = json.loads(path.read_text(encoding="utf-8-sig"))
(root / "cameras-gps280.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
scouts = json.loads((root / "cameras-pose-scout.json").read_text(encoding="utf-8"))
selected = copy.deepcopy(next(c for c in scouts["cameras"] if c["id"] == "dk8-ref7204-h295"))
selected["id"] = "dk8-ref7204"
selected["note"] = "Commons camera GPS and 38 mm focal; heading 295 degrees visually selected, pitch 1.7 and eye 1.65 m WORKING_VALUE. Pose UNVERIFIED, screen/deck differences remain."
before["cameras"] = [selected if c["id"] == selected["id"] else c for c in before["cameras"]]
path.write_text(json.dumps(before, indent=2), encoding="utf-8")
