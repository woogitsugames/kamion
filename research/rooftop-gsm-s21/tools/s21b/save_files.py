"""Zapis JPG ≤ 1600 px (q82) do files/: python3 -I save_files.py dl_dir files_dir"""
import sys, os
from PIL import Image
D, F = sys.argv[1], sys.argv[2]
JOBS = [
    ('kv_1326673605.jpg', 'kv_1326673605.jpg', None),
    ('kv_1326673605.jpg', 'kv_1326673605_wyc3x.jpg', (3220, 1000, 3900, 1300)),
    ('r605.jpg', 'kv_1326673605_pomiar.jpg', None),
    ('kv_1326673581.jpg', 'kv_1326673581.jpg', None),
    ('r581.jpg', 'kv_1326673581_pomiar.jpg', None),
    ('kv_993062010.jpg', 'kv_993062010.jpg', None),
    ('kv_993062010.jpg', 'kv_993062010_wyc3x.jpg', (3072, 936, 3648, 1320)),
    ('kv_993061738.jpg', 'kv_993061738.jpg', None),
    ('r738.jpg', 'kv_993061738_wyc4x.jpg', None),
    ('kv_1326672625.jpg', 'kv_1326672625.jpg', None),
    ('kv_1326672621.jpg', 'kv_1326672621.jpg', None),
    ('kv_2634225507.jpg', 'kv_2634225507.jpg', None),
    ('kv_2634225487.jpg', 'kv_2634225487.jpg', None),
    ('kv_5062497.jpg', 'kv_5062497.jpg', None),
    ('kv_1326673557.jpg', 'kv_1326673557.jpg', None),
    ('kv_993061478.jpg', 'kv_993061478.jpg', None),
]
for src, dst, box in JOBS:
    im = Image.open(os.path.join(D, src)).convert('RGB')
    if box:
        im = im.crop(box)
        im = im.resize((im.width * 3, im.height * 3), Image.LANCZOS)
    im.thumbnail((1600, 1600), Image.LANCZOS)
    im.save(os.path.join(F, dst), quality=82)
    print(dst, im.size, os.path.getsize(os.path.join(F, dst)))
