#!/usr/bin/env bash
# before/after grids for the SBS cameras: (photo | baseline render) over (photo | after render), 960 px wide.
# Usage: make-pairs.sh <after-dir-name> [camera-id-filter]
set -e
cd "$(dirname "$0")"
A=${1:-after}; F=${2:-sbs-g3-b-}
REPO=../..
mkdir -p pairs-$A
python - "$A" "$F" <<'PY'
import json, subprocess, sys, os
a, flt = sys.argv[1], sys.argv[2]
refs = json.load(open('../../Data/Regions/bialystok-industrial-c/sbs_references.json', encoding='utf-8'))['references']
n = 0
for r in refs:
    cam = r['camera']
    if flt not in cam:
        continue
    photo = os.path.join('../..', r['photo'])
    b = f'baseline/renders/Low-overcast/{cam}.png'
    c = f'{a}/renders/Low-overcast/{cam}.png'
    if not (os.path.exists(photo) and os.path.exists(b) and os.path.exists(c)):
        continue
    h = int(480 * r['height'] / r['width'])
    lab = lambda t: ['-gravity', 'NorthWest', '-fill', 'white', '-undercolor', '#000000a0', '-pointsize', '15', '-annotate', '+4+4', t]
    cmd = ['magick', '(', '(', photo, '-resize', f'480x{h}!', *lab(f"photo {r['captured_at']} {r['author']} CC BY-SA 4.0"), ')',
           '(', b, '-resize', f'480x{h}!', *lab('before (main)'), ')', '+append', ')',
           '(', '(', photo, '-resize', f'480x{h}!', ')', '(', c, '-resize', f'480x{h}!', *lab('after (ADR 0127)'), ')', '+append', ')',
           '-append', '-quality', '88', f'pairs-{a}/{cam}.jpg']
    subprocess.run(cmd, check=True)
    n += 1
print(n, 'pairs')
PY
