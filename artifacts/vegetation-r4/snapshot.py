"""Record provenance and detect test-driven canonical-data changes; no world writes."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("label")
args = parser.parse_args()
dest = HERE/("snapshot-"+args.label)
dest.mkdir(exist_ok=True)
files = list((ROOT/"Data/Regions/bialystok-industrial-c/generated").glob("*.json"))
files += list((ROOT/"Data/raw/derived/bialystok-industrial-c/world").glob("*.glb"))
hashes = {}
for path in sorted(files):
    with path.open("rb") as stream:
        hashes[str(path.relative_to(ROOT))] = hashlib.file_digest(stream, "sha256").hexdigest()
    if path.suffix == ".json":
        shutil.copyfile(path, dest/path.name)
source_sha = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
report = dict(source_sha=source_sha, source_note=(
    "Fresh R4 baseline after main merge; no frame reuse from previous rounds."
    if args.label == "baseline" else "Snapshot of generated outputs; inspect dirty state separately."), files=hashes)
tracked = subprocess.check_output(['git','ls-files','-z','--','tools/worldgen','game/Assets/_Project',
    'art-source/world/materials/_src','Data/Regions/bialystok-industrial-c'],cwd=ROOT).decode('utf-8').split('\0')
extensions = {'.py','.cs','.shader','.hlsl','.asset','.mat','.json','.yaml','.yml','.unity'}
report['source_files'] = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    for name in tracked if name and (ROOT/name).is_file() and Path(name).suffix in extensions}
instance_dest = dest/'instances'
instance_dest.mkdir(exist_ok=True)
report['instance_files'] = {}
for path in sorted((ROOT/'Data/raw/derived/bialystok-industrial-c/world').glob('instances_*.json')):
    shutil.copyfile(path,instance_dest/path.name)
    report['instance_files'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
(dest/"sha256.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
print("Snapshot", args.label, "files", len(files))
