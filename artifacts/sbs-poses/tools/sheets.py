"""ADR 0130: photo | probe contact sheets (<=960 px wide) for visual pose choice."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P

def tile(im, label, w=480):
    h = round(w * im.height / im.width)
    t = im.convert('RGB').resize((w, h))
    d = ImageDraw.Draw(t)
    for f in (0.25, 0.5, 0.75):
        d.line((w * f, 0, w * f, h), fill='#707070'); d.line((0, h * f, w, h * f), fill='#707070')
    d.rectangle((0, 0, w, 14), fill='#000000'); d.text((3, 1), label, fill='#ffdd55')
    return t

def sheet(base_key, items, out):
    """items: list of (label, image path)."""
    R = P.refs(); ref = R['sbs-g3-b-' + base_key] if ('sbs-g3-b-' + base_key) in R else R[base_key]
    photo = Image.open(P.ROOT / ref['comparison_photo'])
    tiles = [tile(photo, f"PHOTO {ref['source_id']} {ref['author']} {ref['captured_at']} {ref['license']}")]
    tiles += [tile(Image.open(p), l) for l, p in items if Path(p).exists()]
    th = tiles[0].height
    rows = (len(tiles) + 1) // 2
    s = Image.new('RGB', (960, rows * (th + 2)), '#202020')
    for i, t in enumerate(tiles):
        s.paste(t.resize((480, th)), ((i % 2) * 480, (i // 2) * (th + 2)))
    s.save(out, quality=88)

if __name__ == '__main__':
    rnd, sub = sys.argv[1], sys.argv[2]  # e.g. r1 Low-overcast
    base = Path(__file__).resolve().parents[1] / rnd
    plan = json.loads((base / 'plan.json').read_text(encoding='utf-8'))
    groups = {}
    for p in plan:
        groups.setdefault(p['base'].split('-')[-1], []).append(p)
    for key, ps in groups.items():
        items = []
        for p in ps:
            for d in (base / 'renders').glob(sub + '-*'):
                f = d / (p['probe'] + '.png')
                if f.exists():
                    lab = f"{p['probe'][-3:]} f{p['fwd_m']:+} r{p['right_m']:+} eye{p['eye_m']} hd{p['heading_delta_deg']:+} h{p['horizon_y_fraction']}"
                    items.append((lab, f))
        prod = P.ROOT / 'artifacts/sbs-poses/before' / sub / ('sbs-g3-b-' + key + '.png')
        if prod.exists(): items.insert(0, ('PRODUCTION (before)', prod))
        sheet(key, items, base / f'sheet-{key[:6]}-{sub}.jpg')
        print('sheet', key, len(items))
