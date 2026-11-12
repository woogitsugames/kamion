"""Mosaic of GUGiK WMS HighResolution cells (0.08 m) around the DK8 / Putry decks + local E,N helpers (ADR 0133)."""
from PIL import Image, ImageDraw
import sys
R = 'C:/Users/matma/Documents/Claude/kamion/Data/raw/refs/gugik-ortho-hr/bialystok-industrial-c/'
X0B, Y0B = 776971, 595199
OX, OY = 777995.0, 596223.0
IX = range(0, 6); IY = (7, 8)
MX0 = X0B; MYT = Y0B + 9 * 128

def mosaic():
    W = Image.new('RGB', (1600 * len(IX), 1600 * len(IY)), (40, 40, 40))
    for i in IX:
        for j in IY:
            try:
                W.paste(Image.open(R + f'c_{i:02d}_{j:02d}.jpg'), ((i - IX[0]) * 1600, (IY[-1] - j) * 1600))
            except FileNotFoundError:
                pass
    return W

def px(e, n):
    return ((e + OX - MX0) / 0.08, (MYT - (n + OY)) / 0.08)

def en(u, v):
    return (u * 0.08 + MX0 - OX, MYT - v * 0.08 - OY)
