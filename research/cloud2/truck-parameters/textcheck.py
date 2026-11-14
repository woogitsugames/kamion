"""Wyszukiwanie dosłownego cytatu w pobranym dokumencie (pdftotext -layout i raw, per strona).
Zwraca numer strony PDF (1-based) albo None. Normalizacja: zbite białe znaki, ligatury fi/fl."""
import json, os, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = os.path.join(HERE, "files")
CACHE = os.path.join(FILES, "_pages")


def norm(s):
    s = s.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("­", "").replace("‑", "-")
    return re.sub(r"\s+", " ", s).strip()


def pages(fname):
    os.makedirs(CACHE, exist_ok=True)
    cp = os.path.join(CACHE, fname + ".json")
    src = os.path.join(FILES, fname)
    if os.path.exists(cp) and os.path.getmtime(cp) >= os.path.getmtime(src):
        return json.load(open(cp, encoding="utf-8"))
    out = []
    if fname.endswith(".xml"):
        t = open(src, encoding="utf-8").read()
        t = re.sub(r"<[^>]+>", " ", t)
        out = [[norm(t), norm(t)]]
    else:
        info = subprocess.run(["pdfinfo", src], capture_output=True, text=True).stdout
        n = int(re.search(r"Pages:\s+(\d+)", info).group(1))
        for p in range(1, n + 1):
            lay = subprocess.run(["pdftotext", "-q", "-layout", "-f", str(p), "-l", str(p), src, "-"],
                                 capture_output=True, text=True).stdout
            raw = subprocess.run(["pdftotext", "-q", "-f", str(p), "-l", str(p), src, "-"],
                                 capture_output=True, text=True).stdout
            out.append([norm(lay), norm(raw)])
    json.dump(out, open(cp, "w", encoding="utf-8"))
    return out


def find(fname, quote):
    """'…' w cytacie = pominięty fragment (np. kropki wypełniające w kartach producenta), maks. 200 znaków."""
    q = norm(quote)
    rx = re.compile(".{0,200}?".join(re.escape(norm(p)) for p in q.split("…")))
    for i, (lay, raw) in enumerate(pages(fname), 1):
        if rx.search(lay) or rx.search(raw):
            return i
    return None
