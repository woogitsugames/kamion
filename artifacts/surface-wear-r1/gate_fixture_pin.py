"""Pin current first gate import for the next isolated source/material experiment."""
import hashlib,json
from bus_world_proof import ROOT,OUT
def main():
    files=json.loads((OUT/'bus-only-canonical-fixture.json').read_text())['files']
    files=[dict(file=r['file'],bytes=(ROOT/r['file']).stat().st_size,
                sha256=hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()) for r in files]
    raw=json.loads((OUT/'gate-world-proof.json').read_text())['files']
    for row in raw:assert hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest()==row['sha256']
    report=dict(state='Gate-first canonical import+Install, paint.425/.085; strength.9, broadINACTIVE. Actual gateAFTER8 complete. No visibilityPASS.',files=files,raw=raw)
    (OUT/'gate-first-fixture.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Pinned',len(files),'cachedGenerated and',len(raw),'current raw files')
if __name__=='__main__':main()
