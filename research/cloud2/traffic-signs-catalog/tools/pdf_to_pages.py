"""pdftotext -layout z markerami stron "=== PDF p.N ===". Użycie: python -I pdf_to_pages.py <in.pdf> <out.txt>"""
import subprocess, sys
raw = subprocess.run(["pdftotext", "-layout", sys.argv[1], "-"], capture_output=True, text=True, check=True).stdout
with open(sys.argv[2], "w", encoding="utf-8") as f:
    for i, p in enumerate(raw.split("\f")):
        f.write("\n=== PDF p.%d ===\n" % (i + 1))
        f.write("\n".join(l.rstrip() for l in p.splitlines() if l.strip()))
