# STATUS — M58 (cloud p15-dojlidy-details)

## 2026-11-14 ~17:50 UTC — WIP 1
- Zrobione: OSM (API 0.6 map bbox 23.155,53.094,23.212,53.114; brak barrier=chain w OSM), AIP VFR EPBK (AD 4 EPBK 2-1, AIRAC AMDT VFR 06/26: RWY 09R/27L 1350×30, LDA 900/640), ortofoto GUGiK 0,05 m (arkusz N-34-107-C-b-3-4, 2025-04-18) — pomiar oznakowania pasa, NMT 1 m (WCS), 31 kadrów Commons obejrzanych (960 px) + 13 w wycinkach 3840 px.
- Blokada: upload.wikimedia.org zwraca 429 (retry-after 600) — oryginały do sha256 pobierane w tle; kadry oglądane przez commons thumb.php.
- Dz.U. 2019 poz. 2311: API Sejmu podaje ten sam plik dla c1 i c2 (525 s., zał. 1) — zał. 4 (U-12b) niedostępny → UNVERIFIED.
- NASTĘPNY KROK: wygenerować manifest.csv (skrypt w scratch), README.md, sources.md, fetch.py, audit_20_percent.json; potem PR.
