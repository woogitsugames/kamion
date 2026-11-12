#!/usr/bin/env bash
# (2024 photo | control render) for the ADR 0126 control cameras that name a photo; plain resize of the others.
# Usage: make-pairs-2024.sh <dir-name> [Tier-Lighting]
set -e
cd "$(dirname "$0")"
A=${1:-after}; T=${2:-Low-overcast}
mkdir -p pairs-2024
python - "$A" "$T" <<'PY'
import json, subprocess, sys, os
a, t = sys.argv[1], sys.argv[2]
cams = json.load(open('../../Data/Regions/bialystok-industrial-c/g3b_frontage_cameras.json', encoding='utf-8'))['cameras']
for c in cams:
    r = f"{a}/control-{t}/{c['id']}.png"
    if not os.path.exists(r):
        continue
    out = f"pairs-2024/{c['id']}-{t}.jpg"
    if c.get('photo'):
        lab = ['-gravity', 'NorthWest', '-fill', 'white', '-undercolor', '#000000a0', '-pointsize', '15', '-annotate', '+4+4']
        subprocess.run(['magick', '(', os.path.join('../..', c['photo']), '-resize', '480x360!', *lab, 'photo 2024 (Mapillary, CC BY-SA 4.0)', ')',
                        '(', r, '-resize', '480x360!', *lab, f'render {t} (ADR 0126)', ')', '+append', '-quality', '88', out], check=True)
    else:
        subprocess.run(['magick', r, '-resize', '960x', '-quality', '88', out], check=True)
    print(out)
PY
