import sys, numpy as np, rasterio
from rasterio.windows import from_bounds
from PIL import Image
def crop(name, e0, n0, e1, n1, sc):
    with rasterio.open('Data/raw/derived/bialystok-dojlidy/ortho_0p25m.tif') as ds:
        a = ds.read([1, 2, 3], window=from_bounds(e0 + 780043, n0 + 590079, e1 + 780043, n1 + 590079, ds.transform))
    im = Image.fromarray(np.moveaxis(a, 0, 2)); im = im.resize((int(im.size[0] * sc), int(im.size[1] * sc)), Image.LANCZOS)
    im.save(name, quality=92); print(name, im.size)
crop(sys.argv[1], *map(float, sys.argv[2:7]))
