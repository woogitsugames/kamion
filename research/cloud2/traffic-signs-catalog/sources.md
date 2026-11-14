# Źródła — R1 traffic-signs-catalog

Wszystkie akty pobrano 2026-11-14 z API ELI Sejmu (`api.sejm.gov.pl/eli/acts/...`), to te same pliki „tekst ogłoszony” co w ISAP (`isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU…`). Status prawny: akty normatywne, nie podlegają prawu autorskiemu (art. 4 pkt 2 ustawy o prawie autorskim i prawach pokrewnych). Pliki leżą w `files/` (poza gitem), `fetch.py` pobiera je i sprawdza sha256.

| Klucz | Akt i tytuł | URL PDF | Strony | Do czego użyte |
|---|---|---|---|---|
| 2311 | Dz.U. 2019 poz. 2311: obwieszczenie Ministra Infrastruktury z 9 września 2019 r. w sprawie ogłoszenia jednolitego tekstu rozporządzenia Ministra Infrastruktury w sprawie **szczegółowych warunków technicznych dla znaków i sygnałów drogowych oraz urządzeń bezpieczeństwa ruchu drogowego i warunków ich umieszczania na drogach** (rozp. z 3.07.2003, Dz.U. 2003 nr 220 poz. 2181) | https://api.sejm.gov.pl/eli/acts/DU/2019/2311/text/O/D20192311-c1.pdf | 525 (cz. 1 = cały zał. 1) | wymiary, grupy wielkości, barwy CIE, odblask, folie, liternictwo, montaż, rysunki konstrukcyjne (rozdz. 9) |
| 2310 | Dz.U. 2019 poz. 2310: obwieszczenie MI i MSWiA z 31 października 2019 r. w sprawie ogłoszenia jednolitego tekstu rozporządzenia Ministrów Infrastruktury oraz Spraw Wewnętrznych i Administracji **w sprawie znaków i sygnałów drogowych** (rozp. z 31.07.2002, Dz.U. 2002 nr 170 poz. 1393) | https://api.sejm.gov.pl/eli/acts/DU/2019/2310/text/O/D20192310.pdf | 55 | znaczenie znaków (§), spis znaków z nazwami (zał., s. 29–40), barwne wzory (s. 41–50) |
| 2020/862 | Dz.U. 2020 poz. 862: obwieszczenie MI o sprostowaniu błędu (w 2311 skreśla rys. 5.2.6.11 i 5.2.6.12) | https://api.sejm.gov.pl/eli/acts/DU/2020/862/text/O/D20200862.pdf | 1 | sprawdzenie, czy dotyczy wymiarów: nie dotyczy |
| 2021/433 | Dz.U. 2021 poz. 433: rozp. MI i MSWiA z 8.03.2021 zmieniające rozp. w sprawie znaków i sygnałów (B-19, E-15) | https://api.sejm.gov.pl/eli/acts/DU/2021/433/text/O/D20210433.pdf | 2 | nowa nazwa B-19 |
| 2021/438 | Dz.U. 2021 poz. 438: rozp. MI z 8.03.2021 zmieniające 2311 (pkt 3.2.20 B-19, część 6 E-15) | https://api.sejm.gov.pl/eli/acts/DU/2021/438/text/O/D20210438.pdf | – | sprawdzenie zakresu zmian (nie zmienia wymiarów A–D, T) |
| 2021/2065 | Dz.U. 2021 poz. 2065: rozp. MI i MSWiA z 12.10.2021 zmieniające rozp. w sprawie znaków i sygnałów (D-23b, D-23c, D-34b, F-14d–f, T-1a, T-32, D-44/D-45) | https://api.sejm.gov.pl/eli/acts/DU/2021/2065/text/O/D20212065.pdf | 4 | nowe znaki i nazwy, wzory s. 3–4 |
| 2021/2066 | Dz.U. 2021 poz. 2066: rozp. MI z 12.10.2021 zmieniające 2311 (pkt 1.2.2, tab. 1.11, 5.1.1, 5.1.1a, 7.2.14, rys. 9.4.x, 9.6.18–20) | https://api.sejm.gov.pl/eli/acts/DU/2021/2066/text/O/D20212066.pdf | 26 | folie fluorescencyjne, odległości znaków poprzedzających D, rysunki nowych znaków |
| 2022/2372 | Dz.U. 2022 poz. 2372: rozp. MI i MSWiA z 14.10.2022 zmieniające rozp. w sprawie znaków i sygnałów (D-19/D-20, UNESCO, nowy rysunek D-39) | https://api.sejm.gov.pl/eli/acts/DU/2022/2372/text/O/D20222372.pdf | 2 | wzór D-39 |
| 2022/2377 | Dz.U. 2022 poz. 2377: rozp. MI z 14.10.2022 zmieniające 2311 (pkt 1.2.2, 1.3.2, 1.5.2, **tab. 1.11**, 5.2.48.1 D-42) | https://api.sejm.gov.pl/eli/acts/DU/2022/2377/text/O/D20222377.pdf | 18 | aktualna tabela wysokości 1.11, D-42/D-43 600 mm |
| 2026/132 | Dz.U. 2026 poz. 132: rozp. MI z 14.01.2026 zmieniające 2311 (pkt 1.4.1, 2.2.x, 3.2.x, 5.x, 6.x, F-23, F-24) | https://api.sejm.gov.pl/eli/acts/DU/2026/132/text/O/D20260132.pdf | 18 | brzmienie pkt 1.4.1 (liternictwo), rysunki F-23/F-24 |
| 2026/133 | Dz.U. 2026 poz. 133: rozp. MI i MSWiA z 14.01.2026 zmieniające rozp. w sprawie znaków i sygnałów (D-23b/c, E-1c, E-20a, F-23, F-24) | https://api.sejm.gov.pl/eli/acts/DU/2026/133/text/O/D20260133.pdf | 4 | nowe znaki F-23, F-24 i nazwy D-23b/c |

Lista zmian aktów sprawdzona w API ELI (`/eli/acts/DU/2002/1393` i `/eli/acts/DU/2003/2181`, pole `references`), stan na 2026-11-14 17:11 UTC: po t.j. 2019 nie ma nowszego tekstu jednolitego, a lista nowelizacji jest kompletna jak wyżej.

Nieużyte lub niedostępne:
- PN-EN 12899-1 (stałe pionowe znaki drogowe): norma PKN jest płatna i niedostępna otwarcie, więc jej nie użyto. Wiersz manifestu ma status UNVERIFIED.
- Wikimedia Commons (zdjęcia P11-005/063/129 do ponownego obejrzenia przy erracie C-1/C-2): API zwracało HTTP 429 (2026-11-14 ok. 18:55 UTC), więc niczego nie pobrano. Rozstrzygnięcie C-1/C-2 opiera się na akcie, a nie na zdjęciach.
- Google, Street View i Mapillary: nie używano.

Pliki pomocnicze (poza gitem, odtwarzane): `files/_derived/*_p.txt` (pdftotext z markerami stron, `tools/pdf_to_pages.py`), `files/_derived/list2310.json`, `fig9.json`, `audit_auto.json`, `files/_view/c1c2.png` (zestawienie stron 158, 159 i 399 do rozstrzygnięcia C-1/C-2).
