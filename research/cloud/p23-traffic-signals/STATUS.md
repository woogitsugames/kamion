# STATUS — M66 (p23-traffic-signals)

## 2026-11-14 krok 1 — przepisy + inwentarz OSM (WIP)
- Dz.U. 2019 poz. 2311 zał. 3 pobrany z API ELI Sejmu (`text/I/D20192311-c2.pdf`, 381 s. = s. 526–906 dziennika,
  sha256 8abcce24…d5c4); odczytane: ekran kontrastowy (def. s. 701, pkt 3.3.5.6 s. 715–716, rys. 10.28–10.32 s. 802–805),
  komory (pkt 3.3.2 s. 707–709), średnice soczewek (pkt 3.2.2–3.2.7 s. 702–704), tabela 7.1 (s. 757), przyciski (s. 712).
  Nowelizacje 2021/438, 2021/2066, 2022/2377, 2026/132 sprawdzone: w zał. 3 zmieniono tylko rys. 10.3 i pkt 3.3.5.2–3.3.5.3.
- OSM: 457 węzłów `highway=traffic_signals` w bbox 53.09,23.10–53.17,23.22 (Overpass mirror mail.ru, 2026-11-14T16:59Z) → 151 skupisk.
- Pokrycie zdjęciami: KartaView (30 kandydatów w 23 skupiskach), Panoramax (1 skupisko), Commons geosearch — w toku.

NASTĘPNY KROK: pobrać kandydatów KartaView/Commons, obejrzeć (960 px + wycinki 3×), zbudować manifest.csv.
