"""Read-only attribution of stale foreign-domain report; never regenerates it."""
import hashlib
import json
import subprocess
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[1]
base = '49de5a4e'
region = Path('Data/Regions/bialystok-industrial-c')
report = region/'generated/fidelity_qa.json'
blob = lambda name: subprocess.check_output(['git','show',f'{base}:{name.as_posix()}'],cwd=root)
sha = lambda value: hashlib.sha256(value).hexdigest()
qa = json.loads((root/report).read_text(encoding='utf-8'))
entries = {}
for key, expected in qa['inputs_sha256'].items():
    path = Path(key) if '/' in key else region/key
    working = (root/path).read_bytes()
    baseline = blob(path)
    if sha(working) == expected:
        continue
    normalized_working = working.replace(b'\r\n', b'\n')
    normalized_baseline = baseline.replace(b'\r\n', b'\n')
    entries[key] = dict(report_sha256=expected, working_sha256=sha(working),
        baseline_lf_sha256=sha(normalized_baseline),
        baseline_crlf_sha256=sha(normalized_baseline.replace(b'\n',b'\r\n')),
        source_unchanged_normalized=normalized_working==normalized_baseline,
        report_matches_neither_baseline_line_ending=expected not in (
            sha(normalized_baseline),sha(normalized_baseline.replace(b'\n',b'\r\n'))))
result = dict(base=base, report_unchanged_from_base=(root/report).read_bytes().replace(b'\r\n',b'\n') == blob(report).replace(b'\r\n',b'\n'),
              stale_inputs=entries,
              note='Read-only attribution, not a passing fidelity test or permission to inherit the failure after integration.')
(here/'fidelity-stale-baseline-proof.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
