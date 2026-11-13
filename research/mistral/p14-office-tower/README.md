# P14 — Wieżowiec przy Kwadrat Park (Andersa 38, Białystok): elewacje NE/NW/SE/SW, parter, dach

**Kamion — badanie referencyjne 11-kondygnacyjnego biurowca przy wjeździe do kompleksu Kwadrat Park, ul. gen. Władysława Andersa 38, Białystok** (obok stacji paliw Circle K). Stan: W TOKU (checkpoint 1). Gałąź: `research/mistral-p14-office-tower`, wyjście z najnowszego `origin/main` (54a50ad3).

## Obiekt (ustalone)

| Parametr | Wartość | Źródło |
|---|---|---|
| OSM | way/219260018 „Biazet / Biazet S.A.", building=office, levels=11, height=41 | OSM (ODbL), weryfikacja 2026-11-13 |
| BDOT10k | 2BE4B431-CA0F-1BF0-E053-CC2BA8C0D140, 11 kondygnacji, „siedziba firmy" | ADR 0180 (dane GUGiK w repo) |
| LoD1 2024 | 41,81 m (kondygnacja 3,69 m) | ADR 0180 (dane GUGiK w repo) |
| Centroid WGS84 | 53.153231, 23.168022 | OSM (średnia wierzchołków) |
| Centroid EPSG:2180 | x 778573,54 y 595663,57 | przeliczenie własne (TM/CS92, zweryfikowane 1:1 na kaflu P12) |
| Obrys | szczyty SW/NE ~16,1/16,4 m (normalne 208°/28°), ściany SE/NW ~37 m (normalne 118°/298°) | ADR 0180 + OSM |

Badanie w toku — pełne tabele ścian i dachu, manifest.csv, sources.md, audit_20_percent.json zostaną dodane w kolejnych commitach.
