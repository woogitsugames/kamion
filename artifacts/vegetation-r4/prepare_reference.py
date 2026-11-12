"""Copy the supplied real CC0 photo as evidence only; no image transformation."""
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image

here = Path(__file__).resolve().parent
root = here.parents[1]
main = Path('C:/Users/matma/Documents/Claude/kamion')
sources = list((main/'Data/photos/nowe').glob('*20201102_152339*'))
if len(sources) != 1:
    raise SystemExit('Expected the single Rakoon roundabout photograph from REFERENCES.md')
source = sources[0]
dest = here/'references/rakoon-rondo-20201102.jpg'
dest.parent.mkdir(exist_ok=True)
shutil.copyfile(source,dest)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
if sha(source) != sha(dest):
    raise SystemExit('Photo copy mismatch')
with Image.open(dest) as photo:
    dimensions = photo.size
result = dict(author='Rakoon',captured_at='2020-11-02',license='CC0',
              real_photograph=True,ai_reference=False,source_filename=source.name,
              supplied_source=str(source),local_photo=str(dest.relative_to(root)),
              sha256=sha(dest),width=dimensions[0],height=dimensions[1],
              attribution_source='docs/REFERENCES.md: Real photos (Wikimedia Commons)',
              attribution_document_sha256=sha(root/'docs/REFERENCES.md'),
              use='Appearance of clipped berberis only. Existing control camera pose is UNVERIFIED relative to this photo; do not infer surveyed dimensions or exact alignment. Never a game texture in this experiment.')
(here/'berberis-reference.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
