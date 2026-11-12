"""Three headings from the same documented camera location; no source geometry edits."""
import copy
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parent
original = json.loads((root / "cameras.json").read_text(encoding="utf-8-sig"))
template = next(camera for camera in original["cameras"] if camera["id"] == "dk8-ref7204")
scouts = []
for heading in (295, 305, 315):
    camera = copy.deepcopy(template)
    camera["id"] = f"dk8-ref7204-h{heading}"
    camera["look_at"] = [camera["pos"][0] + 100 * math.sin(math.radians(heading)),
                         camera["pos"][1] + 100 * math.cos(math.radians(heading)),
                         camera["pos"][2] + 100 * math.tan(math.radians(1.7))]
    camera["note"] = f"Heading scout {heading} degrees WORKING_VALUE, same GPS and FOV; pose UNVERIFIED"
    scouts.append(camera)
(root / "cameras-pose-scout.json").write_text(json.dumps({**original, "cameras": scouts}, indent=2), encoding="utf-8")
print(",".join(camera["id"] for camera in scouts))
