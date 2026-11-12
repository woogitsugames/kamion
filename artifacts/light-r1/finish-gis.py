"""End-of-round GIS, called serially by review-matrices inside run-heavy's held slot.
Never acquire the same owner reentrantly here: the outer wrapper releases after exit.
"""
import json
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
owner = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()
if owner != 'gpt-light-r1':
    raise RuntimeError('End-of-round validation belongs to gpt-light-r1')
slot = Path('C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots')/(owner+'.slot')
if not slot.is_file():
    raise RuntimeError('Outer heavy slot is not held; refusing full GIS')
subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--',
                'game/Assets/_Project/Rendering', 'game/Assets/_Project/Tests/EditMode'], cwd=ROOT, check=True)
test = ROOT/'artifacts/tests/editmode-20261112-000534.xml'
result = ET.parse(test).getroot()
if result.attrib.get('failed') != '0' or result.attrib.get('passed') != '264':
    raise RuntimeError('Expected final EditMode 264/264 proof before GIS')
if not (OUT/'sbs-final-ready.json').is_file():
    raise RuntimeError('Final render completion marker is missing')
started = time.time()
with (OUT/'gis-final.log').open('w', encoding='utf-8') as log:
    code = subprocess.run([sys.executable, '-m', 'pytest', 'tests/gis', '-q'], cwd=ROOT,
                          stdout=log, stderr=subprocess.STDOUT).returncode
proof = dict(owner=owner, pool='heavy (outer run-heavy.ps1 slot, serial after analysis)',
             command='uv run --project tools/worldgen python -m pytest tests/gis -q',
             exit_code=code, elapsed_seconds=round(time.time()-started, 3),
             editmode=str(test), source_sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
(OUT/'gis-final-result.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
print((OUT/'gis-final.log').read_text(encoding='utf-8')[-4000:])
if code:
    raise SystemExit(code)
