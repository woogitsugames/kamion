"""Pobiera akty prawne użyte w pakiecie R1 (ELI API Sejmu) do files/ i weryfikuje sha256.
Użycie: python -I fetch.py   (exit 1 przy niezgodności lub błędzie pobierania)
Lista plików = unikalne url_pliku z manifest.csv + akty pomocnicze (2020/862, 2021/438, 2022/2372)."""
import csv, hashlib, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = HERE / "files"
EXTRA = {
    "https://api.sejm.gov.pl/eli/acts/DU/2020/862/text/O/D20200862.pdf": "df34e362b0bb07ec23d94272e0c8ad3e6d8e91aa1fcce4bcb361a7bb82c6d013",
    "https://api.sejm.gov.pl/eli/acts/DU/2021/438/text/O/D20210438.pdf": "f44940be53436dc661c619887b59ffeb580c6fd9f6848505e85be4be462d88d1",
    "https://api.sejm.gov.pl/eli/acts/DU/2022/2372/text/O/D20222372.pdf": "bd29ae2368f592cba38cabdde53cacd3a63b0b42170953ff9ad4c4fbba7dfc3e",
}


def main():
    want = dict(EXTRA)
    with open(HERE / "manifest.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["url_pliku"].startswith("http") and r["sha256"]:
                want[r["url_pliku"]] = r["sha256"]
    FILES.mkdir(exist_ok=True)
    bad = 0
    for url, sha in sorted(want.items()):
        dst = FILES / url.rsplit("/", 1)[1]
        if not (dst.exists() and hashlib.sha256(dst.read_bytes()).hexdigest() == sha):
            for attempt in range(4):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "research-fetch/1.0"})
                    dst.write_bytes(urllib.request.urlopen(req, timeout=300).read())
                    break
                except Exception as e:  # noqa: BLE001
                    print("retry", url, e); time.sleep(2 ** attempt)
        got = hashlib.sha256(dst.read_bytes()).hexdigest() if dst.exists() else "-"
        ok = got == sha
        bad += not ok
        print("OK " if ok else "BAD", dst.name, got)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
