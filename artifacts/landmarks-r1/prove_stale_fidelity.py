"""Read-only proof: stale road-report inputs were not edited by this round."""
from pathlib import Path
import hashlib
import json
import subprocess

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
REGION=ROOT/'Data/Regions/bialystok-industrial-c'
qa=json.loads((REGION/'generated/fidelity_qa.json').read_text(encoding='utf-8'))
rows=[]
for key,old in qa['inputs_sha256'].items():
    path=(REGION if '/' not in key else ROOT)/key
    current=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    if current != old:
        relative=path.relative_to(ROOT).as_posix()
        check=subprocess.run(['git','diff','--quiet','5f2aa277','--',relative],cwd=ROOT)
        rows.append(dict(path=relative,report_sha256=old,current_sha256=current,
                         unchanged_since_round_base=check.returncode==0))
result={'stale_inputs':rows,'all_unchanged_since_round_base':all(r['unchanged_since_round_base'] for r in rows),
        'action':'No road-source or fidelity-report edits; regeneration belongs to integration of the road domain.'}
assert rows and result['all_unchanged_since_round_base']
(OUT/'stale-fidelity-proof.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(len(rows),'stale inputs, all unchanged since round base')
