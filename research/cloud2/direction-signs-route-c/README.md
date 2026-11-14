# R2 — tablice kierunkowe (E-*) na trasie C, Białystok — WYNIK CZĘŚCIOWY

Data: 2026-11-14 · gałąź `research/cloud2-direction-signs-route-c` · **57 wierszy** manifestu (12 kadrów, 8 tablic/zespołów, 33 way OSM z `destination*`, 4 fakty OSM) · **12 obejrzanych kadrów** (960 px + wycinki 3×) · samokontrola 12/57: **11 PASS / 1 FAIL** (skorygowany), seed 20261114.

**Pakiet przerwany na polecenie lidera (limit sesji) po kroku 1 i części kroku 2.** Cel ≥ 20 kadrów NIE został osiągnięty (12). Krok 3 (normatyw Dz.U. 2019 poz. 2310) i pomiar wymiarów tablic NIE zostały wykonane. Patrz „Luki”.

## Metoda
- OSM: Overpass, zapytanie `osm/overpass_query.overpassql`, bbox 53.1480,23.1400–53.1700,23.1800, pobrane 2026-11-14T17:10:40Z (`osm/overpass_raw.json`).
- Kadry: Panoramax `GET /api/search?bbox=23.14,53.148,23.18,53.17&limit=1000` → 68 kadrów w bbox (`osm/panoramax_search_bbox.json`), 2 przejazdy z 2019 r. (autor „stanton”, CC BY-SA 4.0). Obejrzano 8 arkuszy stykowych (wszystkie 68 miniatur, tylko selekcja) i 12 kadrów w 960 px z wycinkami 3×. Opisy w manifeście dotyczą tylko tych 12.
- Kamery kontrolne: `sbs_cameras.json` (42) i `generated/control_cameras.json` (23 persp + 1 ortho) są w układzie lokalnym E,N,U względem origin regionu EPSG:2180 (777995, 596223) z `region.yaml`; przeliczone pyproj do WGS84, azymut = atan2(ΔE, ΔN) pos→look_at → `control_cameras_wgs84.json`.

## Wyniki
### OSM
- `traffic_sign=PL:E-*`: **0** (jedyny traffic_sign w bbox to PL:B-1). Relacje `destination_sign`: 0. `motorway_junction`: 0. `man_made=gantry`: 1 (node 11877183092, 53.167655, 23.147932). Wszystkie tablice z kadrów: **brak tagu**.
- 33 way z `destination*` (R2-021…R2-053) — treść tagów, nie odczyt tablic.
- Nazwy: „Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP”, „Rondo Pamięci Bieżeństwa 1915 roku” (ulicy „Bieżeńców” w wyniku nie ma).

### Tablice odczytane z kadrów (stan 2019-08-15; pozycja = pozycja kadru, tablica leży przed nim)
| id | kadr (lat, lon) | kurs jazdy | typ (wizualnie) | treść | montaż | tło |
|---|---|---|---|---|---|---|
| R2-013 | 53.159486, 23.144835 | 89° | E-1 schemat | 65 Bobrowniki PL BY / 19 Lublin na wprost; 8 E 67 Augustów / 19 Kuźnica PL BY w prawo; 3. wiersz zaklejony | bramownica kratowa | zielone |
| R2-014 | 53.159500, 23.145782 | 91° | 2× E-2 nad pasami | L: 65 Bobrowniki, 19 Lublin ↑; P: 8 E 67 Augustów, 19 Kuźnica ↗ + zaklejony wiersz | bramownica kratowa | zielone |
| R2-015 | 53.159476, 23.147838 | 99° | E-1 schemat-krzyż | jw. + pole żółte i zaklejony wiersz | bramownica kratowa | zielone |
| R2-016 | 53.159332, 23.149293 | 101° | 3× E-2 przed rondem Putry (wlot zach.) | ← Augustów/Kuźnica; ↑ Bobrowniki/Lublin nad ← Augustów/Kuźnica; mała → zaklejona | bramownica kratowa | zielone |
| R2-017 | 53.159413, 23.151885 | 356° | E-15 po obu stronach | „8” „19” czerwone nad „E 67” zielonym | słupek | czerwone/zielone |
| R2-018 | 53.161607, 23.152065 | 359° | E-14 | Korycin, Suchowola, Augustów, Suwałki, Kaunas; km UNVERIFIED | UNVERIFIED | UNVERIFIED |
| R2-019 | 53.159486, 23.144835 | 89° | 3× E-22 | 16km Uzdrowisko Supraśl; Sanktuarium Święta Woda; Sanktuarium Miłosierdzia Bożego | 2 słupki | brąz/biel |
| R2-020 | 53.159476, 23.147838 | 99° | 2× E-22 | Święta Woda ←; Miłosierdzia Bożego → | 2 słupki | białe |

Numery dróg na zielonych tablicach: krajowe w czerwonych polach, „E 67” w zielonym polu z białą ramką; owale „PL”, „BY” białe. Wymiary: **UNVERIFIED** (nie zmierzono).

### Kamera kontrolna → tablice
Kolumna `kamery_kontrolne` (R2-013…R2-020): test czysto geometryczny (≤ 350 m, w połowie FOV) względem pozycji KADRU, ESTIMATED. Nie uwzględnia przesłonięć ani strony lica: tablice R2-013…R2-016 są zwrócone licem na zachód (dla jadących na E), więc kamery patrzące na NW widzą co najwyżej ich tył. Realnie przydatne: **R2-017 (E-15 „8|19 / E 67”)** — w FOV `sbs-g3-b-182011943700132` (55 m), `route_putry_entry_signs` (62 m), `putry_above` (66 m), `g3b_rondo_putry_approach` (132 m), `route_putry_approach` (170 m). R2-018 (E-14): `sbs-g3-b-1801374876712141` (219 m). Kamera `dk8_dk19_exit` — żadna z odczytanych tablic w zasięgu.

### Rozbieżności
- `view:azimuth` Panoramax w kadrach R2-008…R2-012 (48–56°) nie zgadza się z obrazem ani z kursem toru (349–6°); w manifeście oba (kolumna `kurs_toru_deg`, ESTIMATED).
- OSM `destination` way 173956079 = „Augustów Kuźnica;Centrum”, ref 8;19 — zgodne z R2-014 (prawa tablica), przy czym wiersz „Centrum” był w 2019 r. zaklejony. way 23982185 „Lublin;Bobrowniki PL/BY” 19;65 — zgodne z lewą tablicą R2-014.

## Co już było w repo / co nowe
| Było | Nowe tutaj |
|---|---|
| `research/gptpro/3-s8-signs` (G3-C001…C011, G3-P001…P020): treść tablic przy rondzie Putry od strony Andersa i Tysiąclecia (m.in. bramownica Warszawa/Ełk/Augustów/Kuźnica, VMS 53.161139, 23.151859) — głównie Mapillary/Commons. Nie dublowano. | Zespół bramownic na wlocie zachodnim (Maczka → rondo) z Panoramax, E-15 i E-14 na wylocie N, E-22, tagi OSM z Overpass z dnia 2026-11-14, kamery kontrolne w WGS84 i test FOV |
| `research/mistral/p8-restrictions-3`: kadr 6ded8ec0 — B-26, B-33 „70”, tablice DK19/E67 | ten sam kadr (R2-008): odczyt E-15 „8”,„19”,„E 67” |
| `research/mistral/p1-route-photos-2`: kadry KartaView Andersa/Tysiąclecia (P1B-001 „drogowskazy DK19 Kuźnica/DK65 Ełk”) | — (KartaView tylko zebrano metadane, nie obejrzano) |

## Luki
1. **Trasa C właściwa (Andersa od ronda Bieżeństwa do ronda Putry, kierunek NW) — 0 obejrzanych kadrów w tym pakiecie.** Panoramax nie ma tam zdjęć; KartaView ma przejazdy 3686129 (2021-06-23), 2769366 (2019-08-25), 14055 (2016) — metadane 812 kadrów zebrane, obrazów nie obejrzano. Treść tych tablic jest w G3 (gptpro).
2. Al. Tysiąclecia kierunek S (dojazd do Putry z N: bramownice, VMS): kadry Panoramax 989ab5f4 widziane tylko na arkuszu stykowym — nieopisane.
3. Sokólska, Wysockiego, Kombatantów; rondo Bieżeństwa — brak kadrów; zapytanie Overpass o nazwy nie powiodło się (504).
4. Wymiary tablic i wysokość liter: UNVERIFIED. Normatyw (Dz.U. 2019 poz. 2310, E-*) — nie otwarto.
5. Stan 2019 (objazd, zaklejone wiersze „Centrum”); stan 2026 UNVERIFIED.
6. Commons: 643 pliki z geosearch zebrane, nie obejrzano. Pozycje tablic = pozycje kadrów (odległość do tablicy UNVERIFIED).

## Jak używać w grze
Układ treści i kolorystykę zespołu tablic przed rondem Putry brać z R2-013…R2-016 łącznie z G3; E-15 za rondem na N z R2-017. Kadry CC BY-SA = referencja, nie tekstura.
