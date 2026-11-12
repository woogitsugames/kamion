"""One bounded interactive PNG preview, never a full image batch."""
import argparse
import ctypes
from pathlib import Path
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('phase', choices=('before', 'after', 'before-side', 'after-side', 'early-after1', 'after2', 'after2-side'))
parser.add_argument('variant', choices=('Low-clear', 'Low-overcast', 'High-clear', 'High-overcast'))
parser.add_argument('camera', choices=tuple(f'furniture-shelter-{stop}-{view}'
    for stop in ('anders-1000', 'factory') for view in ('front', 'corner', 'reverse')))
args = parser.parse_args()
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.GetCurrentProcess.restype = ctypes.c_void_p
kernel.SetPriorityClass.argtypes = (ctypes.c_void_p, ctypes.c_ulong)
assert kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x40), 'Could not set IDLE priority'
ev = Path(__file__).resolve().parent
source = ev / args.phase / args.variant / (args.camera+'.png')
out = ev / ('preview-'+args.phase) / (args.variant+'-'+args.camera+'.jpg')
out.parent.mkdir(exist_ok=True)
with Image.open(source) as image:
    assert image.width * image.height <= 3_000_000, 'Interactive input exceeds 3 MP'
    with image.convert('RGB') as rgb:
        rgb.thumbnail((960, 960))
        rgb.save(out, quality=94)
print(out)
