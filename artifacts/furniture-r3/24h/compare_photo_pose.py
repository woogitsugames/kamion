"""One bounded interactive photo/render comparison, with explicit pose uncertainty."""
import argparse
import ctypes
import json
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw, ImageOps

parser = argparse.ArgumentParser()
parser.add_argument('tier', choices=('Low', 'High'))
parser.add_argument('mode', choices=('raw', 'fit'))
parser.add_argument('vfov', type=int, choices=(45, 55, 65))
args = parser.parse_args()
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.GetCurrentProcess.restype = ctypes.c_void_p
kernel.SetPriorityClass.argtypes = (ctypes.c_void_p, ctypes.c_ulong)
assert kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x40), 'Could not set IDLE priority'
ev = Path(__file__).resolve().parent
photo = '1911352299378570'
camera = f'furniture-photo-{photo}-' + ('fit-' if args.mode == 'fit' else '') + f'v{args.vfov}'
definitions = json.loads((ev / 'photo-cameras.json').read_text())['cameras']
assert camera in {item['id'] for item in definitions}
render = ev / 'photo-after3' / (args.tier+'-overcast') / (camera+'.png')
reference = ev.parents[1] / 'furniture-r2/24h/bus-reference-preview' / (photo+'.jpg')
crop = ev / 'reference/shelter-2024-crop.jpg'
with Image.open(render) as source:
    assert source.size == (1280, 960), 'Unexpected render dimensions; normalized crop would be wrong'
evidence = json.loads((ev / 'photo-camera-evidence.json').read_text())
sheet = Image.new('RGB', (960, 930), '#202020')
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 14)
draw.text((8, 6), f'Zdjecie | render: {args.tier}, VFOV {args.vfov}, {args.mode}', font=font, fill='white')
draw.text((8, 27), 'WORKING_VALUE: hipoteza pozy, bez niezaleznej kalibracji wymiarow i koloru.', font=font, fill='#ffdd77')

def paste(path, position, size, roi=None):
    with Image.open(path) as source:
        assert source.width * source.height <= 3_000_000, 'Interactive input exceeds 3 MP'
        with source.convert('RGB') as rgb:
            image = rgb.crop(roi) if roi else rgb.copy()
            try:
                fitted = ImageOps.contain(image, size, Image.Resampling.LANCZOS)
                sheet.paste(fitted, position)
                fitted.close()
            finally:
                image.close()

paste(reference, (0, 57), (480, 360))
paste(render, (480, 57), (480, 360))
draw.text((8, 425), 'Ten sam znormalizowany wycinek obrazu; render powiekszony wylacznie do podgladu.', font=font, fill='white')
paste(crop, (10, 451), (450, 430))
# Reference crop: 450x430 at (1180,880) in the 2048x1536 original.
sx, sy = 1280/2048, 960/1536
roi = tuple(round(value) for value in (1180*sx, 880*sy, 1630*sx, 1310*sy))
paste(render, (500, 451), (450, 430), roi)
draw.text((8, 886), 'Mapillary 1911352299378570, kino, 2024-07-26, CC BY-SA 4.0.', font=font, fill='white')
if args.mode == 'fit':
    fit = next(item for item in evidence['one_object_fits_working'] if item['vfov_deg'] == args.vfov)
    text = f"Dopasowanie jednego obiektu: przesuniecie boczne {fit['lateral_shift_m']:.2f} m; nie jest dowodem metrycznym."
else:
    text = 'Surowa hipoteza GPS/kompasu; rozbieznosc z obiektem na zdjeciu pozostaje jawna.'
draw.text((8, 907), text, font=font, fill='#ffdd77')
out = ev / 'photo-compare' / f'{args.tier}-{args.mode}-v{args.vfov}.jpg'
out.parent.mkdir(exist_ok=True)
sheet.save(out, quality=94)
sheet.close()
print(out)
