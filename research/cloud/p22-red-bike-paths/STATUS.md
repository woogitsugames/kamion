# STATUS — M65 (cloud p22-red-bike-paths)

Stan: **GOTOWE do przeglądu** (2026-11-14). Manifest 239 wierszy, fetch.py 133 pliki (68 794 874 B, sha256 OK), samokontrola 48 wierszy (38 PASS / 10 POPRAWIONO).

- [x] Overpass → `overpass-result.json`; `inventory.json` (C 71, Dojlidy 22), `crossings.json` (54 jezdnie + 38 wjazdów)
- [x] ortofotomapa GUGiK 5 cm: 27 wycinków zbiorczych (17 opisanych), 64 przekroje, 32 przejazdy, 12 wjazdów — obejrzane; `data/observations.py`
- [x] Panoramax 7 + KartaView 8 kadrów (C) — obejrzane; `data/frame_notes.py`
- [x] manifest.csv, README.md, sources.md, fetch.py, audit_20_percent.json
- [ ] **LUKA:** Wikimedia Commons HTTP 429 przez całą sesję → P11-001, P11-056 i kadry uliczne Dojlid nieobejrzane (README §9)

NASTĘPNY KROK (gdy Commons odblokowane): pobrać `https://upload.wikimedia.org/wikipedia/commons/8/88/20240623_142113_June_2024_in_Bia%C5%82ystok.jpg` (P11-001) i plik P11-056, obejrzeć, dopisać do `data/commons_frames.json` (pola jak w `data/street_frames.json`, `src: commons`) + opis w `data/frame_notes.py`, potem `python3 -I tools/build_manifest.py && python3 -I tools/build_readme.py`.
