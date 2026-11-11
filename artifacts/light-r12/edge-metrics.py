"""Fixed original-pixel edges and cab numeral; report measured tradeoffs, no no-loss claim."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).parent
BASE = ROOT / 'before/High-clear'
TEST = ROOT / 'noise/legibility-zero'
ROIS = {
    'road_paint': ('driver-andersa-to-putry', (1330, 760, 1540, 900)),
    'window_edge': ('r10_block_3', (1480, 375, 1550, 405)),
    'cab_numeral': ('cab-dash', (980, 580, 1020, 645)),
}

def stats(im, edge):
    a = np.asarray(im.convert('L'), float)
    out = {'p95_minus_p05_srgb': float(np.percentile(a, 95)-np.percentile(a, 5)),
           'mean_abs_gradient': float((np.abs(np.diff(a, axis=0)).mean()+np.abs(np.diff(a, axis=1)).mean())*.5)}
    if edge:
        widths=[]
        for row in a:
            e = int(np.argmax(np.abs(np.diff(row))))
            if e < 8 or e >= len(row)-9:
                continue
            profile = row[e-8:e+9]
            lo, hi = float(np.median(profile[:3])), float(np.median(profile[-3:]))
            if abs(hi-lo) < 15:
                continue
            s = np.maximum.accumulate(np.clip((profile-lo)/(hi-lo), 0, 1))
            widths.append(float(np.interp(.9, s, np.arange(17))-np.interp(.1, s, np.arange(17))))
        out['edge_10_90_width_original_px_median'] = float(np.median(widths)) if widths else None
        out['valid_rows'] = len(widths)
    return out

sheet = Image.new('RGB', (960, 780), '#202020')
draw = ImageDraw.Draw(sheet)
result = {}
for y,(label,(camera,rect)) in enumerate(ROIS.items()):
    result[label]={'camera':camera,'rect_original_px':rect}
    for x,(name,directory) in enumerate([('before',BASE),('candidate_rcas0',TEST)]):
        crop=Image.open(directory/(camera+'.png')).convert('RGB').crop(rect)
        # The compound window frame contains several edges: report its contrast/gradient,
        # not a misleading single-step width. Paint has one clean boundary per row.
        result[label][name]=stats(crop,label=='road_paint')
        crop.thumbnail((460, 220))
        # Small diagnostic ROIs enlarged to show the actual sampled edge/letter pixels.
        crop=crop.resize((min(460,crop.width*3),min(220,crop.height*3)),Image.Resampling.NEAREST)
        sheet.paste(crop,(x*480,y*260+25))
        draw.text((x*480+4,y*260+4),label+' / '+name,fill='white')
(ROOT/'noise/edge-metrics.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
sheet.save(ROOT/'noise/edge-crops.jpg',quality=96)
print(json.dumps(result,indent=2))
