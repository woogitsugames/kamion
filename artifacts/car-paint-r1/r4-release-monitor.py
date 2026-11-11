"""Persist release invalidation; never launches or resumes Unity."""
from pathlib import Path
import json
import sys
import time

locks=Path('C:/Users/matma/Documents/Claude/kamion/artifacts/locks')
art=Path(__file__).resolve().parent
stop=Path(sys.argv[1])
token=sys.argv[2]
while not stop.exists():
    present=[n for n in ('PHONE_RUN','GPT_UNITY_HOLD') if (locks/n).exists()]
    if present:
        (art/'r4-release-invalidated.json').write_text(json.dumps(dict(root_release=token,markers=present,
            observed_unix=time.time(),note='Persistent invalidation: disappearance is not a fresh release.'))+'\n')
        break
    time.sleep(.1)
