"""Keep A/B generated products outside git, including any optional licensed geometry."""
import shutil
import sys
from pathlib import Path

action, phase = sys.argv[1:]
root = Path.cwd()
snap = root / 'Data/raw/derived/bialystok-industrial-c' / f'furniture-r1-{phase}'
paths = {'world': 'Data/raw/derived/bialystok-industrial-c/world',
         'region': 'Data/Regions/bialystok-industrial-c/generated',
         'props': 'art-source/world/props', 'signs': 'art-source/world/signs', 'textures': 'art-source/world/textures'}
for key, rel in paths.items():
    src, dst = (root / rel, snap / key) if action == 'save' else (snap / key, root / rel)
    if not src.is_dir():
        raise RuntimeError(f'Missing product source: {src}')
    # Merge copies are sufficient: exports overwrite all chunk/prototype files; unreferenced textures are harmless.
    shutil.copytree(src, dst, dirs_exist_ok=True)
print(action, phase, 'OK')
