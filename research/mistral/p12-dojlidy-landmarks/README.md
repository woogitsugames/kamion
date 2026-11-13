# P12 — Dojlidy/Krywlany: obiekty charakterystyczne, typologia zabudowy i generatory ruchu (D60)

**Kamion — badanie rozpoznawalności kafla Dojlidy/Krywlany (D60).** Stan badania: 13 listopada 2026 r. Gałąź: `research/mistral-p12-dojlidy-landmarks`, wyjście z najnowszego `origin/main` (8a7296af). Materiał po polsku.

⚠️ **WERSJA ROBOCZA — commit okresowy.** Tabela landmarków, typologia, wyposażenie dróg i generatory są uzupełniane; ostateczną wersją jest ostatni commit tej gałęzi.

## Zakres i bbox (ustalenie własne — `Data/Regions/bialystok-dojlidy/region.yaml` nie istnieje)

Kafel badawczy **dokładnie 2000×2000 m**, osiowo w EPSG:2180, tak by objąć **lotnisko Białystok-Krywlany z płaszczyzną apron, hangarami i startem (RWY 12/30, trawa)** oraz **rdzeń strefy przemysłowej Dojlidy (KAN, Masterpress, BPN-T, Rosti, Bravilor)** wraz z korytarzem tranzytu ciężarowego **Ciołkowskiego–Dywizjonu 303–Kuronia**:

| Parametr | Wartość |
|---|---|
| BBOX EPSG:2180 (xmin, ymin, xmax, ymax) | **[778660, 589590, 780660, 591590]** |
| Środek (WGS84) | 53.107162, 23.179805 |
| Rogi WGS84 | SW 53.098717, 23.164035 · SE 53.097669, 23.193834 · NW 53.116653, 23.165771 · NE 53.115605, 23.195582 |
| BBOX WGS84 (przybliżenie osiowe) | 53.0984–53.1166 N, 23.1640–23.1956 E |

Zamiana współrzędnych: transformacja Transverse Mercator EPSG:2180 (GRS80, k0=0.9993, λ0=19°E) zaimplementowana w narzędziach badania i skalibrowana na istniejący kafel `bialystok-industrial-c` (bbox [776971,595199,779019,597247] ↔ środek 53.158550, 23.159877 — zgodność co do 1 m).

**Co świadomie mieści się poza kaflem** (odległość od wschodniej krawędzi): browar Dojlidy (~650 m), BIAFORM z kominami (~240–1100 m), BIAWAR (~560 m), BISON (~210 m), a poza zachodnią: wieś Krywlany i zachodni skrawek trawy lotniska (~370 m). Te obiekty są w katalogu jako **landmarky widoczne z dróg kafla** (z jawnym zaznaczeniem `poza kaflem`), bo bramka rozpoznawalności D51 działa z jezdni, nie od linii działki.

## Metoda i źródła (skrót; pełny rejestr w sources.md)

- **OSM** (ODbL): wyciąg API `/api/0.6/map` bbox 23.160–23.198, 53.0955–53.118 (kafel + bufor ~300 m); 23 271 węzłów, 4 179 dróg/obiektów. Przetworzono do compact JSON w `data/`.
- **GUGiK LoD1 2024** (CC BY 4.0): `measuredHeight` dla 1 189 budynków w kaflu (median 6,81 m, p90 9,72 m, max 24,44 m — budynek sądu).
- **GUGiK BDOT10k 2021** (schemat 2021, powiat 2061, stan 2024-09): funkcje budynków + kondygnacje dla 1 256 budynków kafla.
- **GUGiK ortofoto** (WMS StandardResolution, otwarte dane): kadry dowodowe 1600×1600 px (0,25 m/px, 400×400 m) do `files/` (poza git).
- Zdjęcia uliczne: Panoramax (CC BY-SA 4.0) — **brak pokrycia kafla** (0 kadrów w bbox); KartaView — API publiczne niedostępne (próba 404); Mapillary — brak tokenu (UNVERIFIED); Wikimedia Commons/Openverse — w trakcie.
- Zakazane źródła (Google Maps/Street View/Earth/3D Tiles) **nie były używane**.

## Stan prac (commit okresowy)

- [x] bbox + gałąź + dane OSM/LoD1/BDOT10k do `data/`
- [ ] tabela 25–40 landmarków z pozycjami, wysokościami, kolorami/materiałami, widocznością z dróg i zdjęciami z licencjami
- [ ] typologia zabudowy przy drogach (hale, domy, bloki, ogródki) z odsetkami z próby
- [ ] wyposażenie dróg: przystanki/wiaty, latarnie, bariery, ekrany akustyczne, ogrodzenia zakładów, drogowskazy E-*
- [ ] generatory ruchu ciężarówek z bramami
- [ ] manifest.csv, sources.md, audit_20_percent.json (samokontrola 20 %, jawny seed)
