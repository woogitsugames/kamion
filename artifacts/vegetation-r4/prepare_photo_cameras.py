"""Snapshot existing photo matches; no source fetches or shared SBS-file edits."""
import hashlib
import json
import shutil
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAIN = Path("C:/Users/matma/Documents/Claude/kamion")
REGION = ROOT / "Data/Regions/bialystok-industrial-c"
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
cameras = {c["id"]: c for c in read(REGION/"sbs_cameras.json")["cameras"]}
# All current class B poses are included; positional and seasonal uncertainty stays explicit.
groups = defaultdict(list)
selected = []
(HERE/"references").mkdir(exist_ok=True)
for r in read(REGION/"sbs_references.json")["references"]:
    sid = r["source_id"]
    if r.get("pose_confidence") != "B":
        continue
    source = MAIN/r.get("comparison_photo", r["photo"])
    if not source.exists():
        raise FileNotFoundError(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    expected = r.get("comparison_sha256", r.get("sha256"))
    if expected and digest != expected:
        raise ValueError("Reference changed: "+sid)
    dest = HERE/"references"/(r["camera"]+source.suffix)
    shutil.copyfile(source, dest)
    row = dict(r)
    row.update(local_photo=str(dest.relative_to(ROOT)), verified_comparison_sha256=digest,
               calibration_status="UNVERIFIED: reviewed poses still have metre-scale positional uncertainty")
    selected.append(row)
    groups[f'{r["width"]}x{r["height"]}'].append(cameras[r["camera"]])
for aspect, rows in groups.items():
    (HERE/("photo-cameras-"+aspect+".json")).write_text(
        json.dumps({"schema":"kamion/sbs-cameras/1", "frame":"E,N,absolute U", "cameras":rows}, indent=2)+"\n")
(HERE/"photo-references.json").write_text(json.dumps({"references":selected}, indent=2)+"\n", encoding="utf-8")
print("Selected", len(selected), "class B matches; lighting/season may differ; groups", {k:len(v) for k,v in groups.items()})
