#!/usr/bin/env bash
# ADR 0141 pairs, 960 px wide: SBS cameras = photo | before | after; control cameras = before over after.
# Usage: make-pairs.sh <Tier-Lighting> [before-name] [after-name]
set -e
cd "$(dirname "$0")"
L=${1:-Low-clear}; B=${2:-baseline}; A=${3:-after}; P=${4:-pairs}
mkdir -p $P/$L
python - "$L" "$B" "$A" "$P" <<'PY'
import json, subprocess, sys, os, glob
L, B, A, P = sys.argv[1:5]
refs = {r['camera']: r for r in json.load(open('../../Data/Regions/bialystok-industrial-c/sbs_references.json', encoding='utf-8'))['references']}
lab = lambda t: ['-gravity', 'NorthWest', '-fill', 'white', '-undercolor', '#000000a0', '-pointsize', '14', '-annotate', '+4+4', t]
n = 0
for a in sorted(glob.glob(f'{A}/{L}/*.png')):
    cam = os.path.basename(a)[:-4]; b = f'{B}/{L}/{cam}.png'
    if not os.path.exists(b) or cam.startswith(('cab-', 'truck-', 'chase')): continue
    out = f"{P}/{L}/{cam}.jpg"
    if cam in refs:
        r = refs[cam]; photo = '../../' + (r.get('comparison_photo') or r['photo'])
        if not os.path.exists(photo): photo = 'C:/Users/matma/Documents/Claude/kamion/' + (r.get('comparison_photo') or r['photo'])
        if not os.path.exists(photo): photo = '../../' + r['photo']
        h = int(320 * r['height'] / r['width'])
        cmd = ['magick', '(', photo, '-resize', f'320x{h}!', *lab(f"photo {r['captured_at']} {r['author']} CC BY-SA 4.0"), ')',
               '(', b, '-resize', f'320x{h}!', *lab('before'), ')', '(', a, '-resize', f'320x{h}!', *lab(f'after ADR 0141 {L}'), ')', '+append', '-quality', '90', out]
    else:
        cmd = ['magick', '(', b, '-resize', '960x', *lab('before'), ')', '(', a, '-resize', '960x', *lab(f'after ADR 0141 {L}'), ')', '-append', '-quality', '88', out]
    subprocess.run(cmd, check=True); n += 1
print(n, 'pairs')
PY
