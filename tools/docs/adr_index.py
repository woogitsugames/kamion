#!/usr/bin/env python3
"""Generuje docs/adr/README.md (indeks ADR) i drukuje audyt na stdout.

Uruchomienie z katalogu glownego repo:
    python3 tools/docs/adr_index.py           # zapisuje docs/adr/README.md + audyt
    python3 tools/docs/adr_index.py --check   # tylko audyt, bez zapisu

Bez zaleznosci ( sama biblioteka standardowa ). Indeks: numer, tytul, status,
data, link. Audyt: duplikaty numerow, luki w numeracji, ADR bez statusu,
odwolania "ADR NNNN" (md/py/cs/ps1) wskazujace nieistniejace ADR-y.
"""

import os
import re
import sys
from collections import defaultdict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ADR_DIR = os.path.join(REPO_ROOT, "docs", "adr")
OUT_FILE = os.path.join(ADR_DIR, "README.md")

REF_EXTENSIONS = (".md", ".py", ".cs", ".ps1")
REF_RE = re.compile(r"\bADR[ \-]?(\d{4})\b")
DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")
H1_RE = re.compile(r"^#\s+(.*)$")
STATUS_RE = re.compile(r"\b(?:status|stan)\b(?:\s+\S+)?\s*[:：]\s*(.+?)\s*$", re.IGNORECASE)
TITLE_PREFIX_RE = re.compile(r"^ADR\s?-?\s*\d{4}\s*[—–:\-]?\s*", re.IGNORECASE)


def parse_adr(path):
    number = None
    m = re.match(r"^(\d{4})-", os.path.basename(path))
    if m:
        number = m.group(1)
    title = ""
    status = None
    date = None
    with open(path, encoding="utf-8-sig") as f:
        head = [next(f, "") for _ in range(15)]
    for line in head:
        if not title:
            h = H1_RE.match(line.strip())
            if h:
                title = TITLE_PREFIX_RE.sub("", h.group(1)).strip()
        if status is None:
            s = STATUS_RE.search(line)
            if s:
                status = s.group(1)
        if date is None:
            d = DATE_RE.search(line)
            if d:
                date = d.group(1)
    if not title:
        title = os.path.basename(path)
    return {
        "number": number,
        "file": os.path.basename(path),
        "title": title,
        "status": status,
        "date": date or "—",
    }


def collect_adres():
    adrs = []
    for name in sorted(os.listdir(ADR_DIR)):
        if name.endswith(".md") and name != "README.md":
            adrs.append(parse_adr(os.path.join(ADR_DIR, name)))
    return adrs


def audit(adrs):
    numbers = [a["number"] for a in adrs if a["number"]]
    dupes = sorted({n for n in numbers if numbers.count(n) > 1})
    existing = set(numbers)
    lo, hi = min(existing), max(existing)
    gaps = [f"{n:04d}" for n in range(int(lo), int(hi) + 1) if f"{n:04d}" not in existing]
    no_status = [a for a in adrs if a["status"] is None]

    dangling = defaultdict(set)
    for dirpath, _dirnames, filenames in os.walk(REPO_ROOT):
        if ".git" in dirpath.split(os.sep):
            continue
        for fn in filenames:
            if not fn.lower().endswith(REF_EXTENSIONS):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, REPO_ROOT)
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except OSError:
                continue
            for m in REF_RE.finditer(text):
                n = m.group(1)
                if n not in existing:
                    dangling[n].add(rel)
    return dupes, gaps, no_status, dict(dangling)


def esc(text, limit=110):
    text = text.replace("|", "\\|").replace("\n", " ")
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


def render_readme(adrs):
    lines = [
        "# Indeks ADR",
        "",
        "Automatycznie generowany przez `tools/docs/adr_index.py` — nie edytuj ręcznie.",
        "Ponowne wygenerowanie: `python3 tools/docs/adr_index.py` (z katalogu głównego repo).",
        "",
        f"Liczba ADR: **{len(adrs)}** (numery {adrs[0]['number']}–{adrs[-1]['number']}, z lukami — patrz raport audytu).",
        "",
        "| Numer | Tytuł | Status | Data | Link |",
        "|---|---|---|---|---|",
    ]
    for a in adrs:
        status = a["status"] if a["status"] else "⚠ brak statusu"
        lines.append(
            "| {n} | {t} | {s} | {d} | [{f}]({f}) |".format(
                n=a["number"] or "????",
                t=esc(a["title"]),
                s=esc(status),
                d=a["date"],
                f=a["file"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def main():
    check_only = "--check" in sys.argv
    adrs = collect_adres()
    dupes, gaps, no_status, dangling = audit(adrs)

    print(f"ADR: {len(adrs)} plików")
    print(f"Duplikaty numerów: {dupes if dupes else 'brak'}")
    print(f"Luki w numeracji ({len(gaps)}): {', '.join(gaps) if gaps else 'brak'}")
    print(f"ADR bez statusu ({len(no_status)}):")
    for a in no_status:
        print(f"  - {a['file']}")
    print(f"Odwołania ADR NNNN do nieistniejących ADR ({len(dangling)}):")
    for n in sorted(dangling):
        for rel in sorted(dangling[n]):
            print(f"  - ADR {n}: {rel}")

    if not check_only:
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            f.write(render_readme(adrs))
        print(f"Zapisano: {os.path.relpath(OUT_FILE, REPO_ROOT)}")


if __name__ == "__main__":
    main()
