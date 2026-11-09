"""Track A5 — render the swappable-parameter variants (trim colour x4, hub badge x4) and assemble sheets.

    python tools/blender/truck/interior/variants.py --out docs/reports/visual/truck-A5 [--samples 256]

Needs `blender` and `uv` in PATH. Intermediate 800x450 renders go to <out>/_var (deleted afterwards).
"""
import argparse
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build_interior.py")
SHEET = os.path.join(HERE, "sheet.py")


def blender(out, cams, extra, samples):
    cmd = ["blender", "-b", "--factory-startup", "--python", BUILD, "--", "--out", out, "--cams", cams,
           "--light", "overcast", "--samples", str(samples), "--res", "800x450"] + extra
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--samples", type=int, default=256)
    a = p.parse_args()
    out = os.path.abspath(a.out)
    tmp = os.path.join(out, "_var")
    os.makedirs(tmp, exist_ok=True)
    trims = [("grafit", "grafit"), ("piasek", "piasek"), ("koniak", "koniak (wybrany, domyślny)"), ("lupek", "łupek")]
    for t, _ in trims:
        blender(tmp, "pasazer,fotel", ["--trim", t, "--suffix", f"_{t}"], a.samples)
    badges = [("none", "bez znaku (neutralny)"), ("trakt", "TRAKT (wybrany, domyślny)"), ("bielik", "BIELIK"), ("narew", "NAREW")]
    for b, _ in badges:
        blender(tmp, "piasta", ["--badge", b, "--suffix", f"_{b}"], a.samples)
    uv = ["uv", "run", "--no-project", "--with", "pillow", "python", SHEET]
    for cam, title in (("pasazer", "Kolor wstawek (trim): deska, drzwi, środki foteli — widok z fotela pasażera"),
                       ("fotel", "Kolor wstawek (trim): środkowe panele fotela")):
        args = []
        for t, lab in trims:
            args += [os.path.join(tmp, f"{cam}_overcast_{t}.jpg"), lab]
        subprocess.run(uv + [os.path.join(out, f"wariant_trim_{cam}.jpg"), title] + args, check=True)
    args = []
    for b, lab in badges:
        args += [os.path.join(tmp, f"piasta_overcast_{b}.jpg"), lab]
    subprocess.run(uv + [os.path.join(out, "wariant_znak_piasta.jpg"),
                         "Znak na piaście kierownicy (jedyny element zależny od marki)"] + args, check=True)
    shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
