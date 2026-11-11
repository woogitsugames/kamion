"""Read-only proof that the three independently built baseline worlds agree."""
import hashlib
import json
from pathlib import Path

MAIN = Path('C:/Users/matma/Documents/Claude/kamion')
OUT = Path(__file__).parent / 'baseline-world-proof.json'
results = {}
for name in ('gpt-tint-gamma', 'gpt-vegetation-r2', 'gpt-light-r12'):
    root = MAIN / '.claude/worktrees' / name
    manifest = json.loads((root / 'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
    rows = [r for chunk in manifest['chunks'] for r in (chunk, chunk['low'], chunk['instances'])]
    mismatch = [row['file'] for row in rows if hashlib.sha256((root / row['file']).read_bytes()).hexdigest() != row['sha256']]
    signature = hashlib.sha256(json.dumps(sorted((row['file'], row['sha256']) for row in rows)).encode()).hexdigest()
    results[name] = {'files': len(rows), 'mismatches': mismatch, 'world_signature': signature}
results['same_world'] = len({v['world_signature'] for v in results.values()}) == 1
OUT.write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))
assert results['same_world'] and not any(v['mismatches'] for k, v in results.items() if k != 'same_world')
