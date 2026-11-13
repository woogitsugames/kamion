# M52 — P2 surfaces 2 (znaki poziome P-*, nawierzchnie Białegostoku)

Paczka badawcza M52. Gałąź: `research/mistral/p2-surfaces-2`. Kontynuacja / uzupełnienie
`research/gptpro/p2-surfaces/` (M51/P2-001…P2-094) — **bez dublowania** tamtych ustaleń.

## Zakres (6 zadań)

1. Wymiary znaków poziomych **z rysunków** załącznika nr 2 do rozporządzenia w sprawie
   szczegółowych warunków technicznych dla znaków i sygnałów drogowych
   (jednolity tekst: Dz.U. 2019 poz. 2311; PDF z eli.gov.pl, część c2):
   P-2a/b, P-3a/b, P-4, P-5, P-6 (szerokości linii, odstęp linii podwójnych, kreska/przerwa),
   P-12, P-13, P-14, P-21a/b, P-23, P-25. Dla każdej wartości: **numer rysunku + strona Dz.U.**
   Źródła wtórne (blogi, tioman.pl) odrzucone jako niepotwierdzające.
2. Zdjęcia kafla startowego **Jaroszówka** (~53,152 N 23,168 E) z poziomu jezdni — ≥10 kadrów,
   data + azymut.
3. Zdjęcia + wymiary: **azyle** (wyspy dzielące), **płytki dotykowe** (układ rzędów),
   **ścieki przykrawężnikowe i wpusty** — Białystok.
4. **Kolor dróg i pasów rowerowych** na trasie startowej (Andersa, Al. Tysiąclecia, Sokólska,
   Wileńska): gdzie czerwony asfalt, gdzie pas malowany na szarym asfalcie — pozycje + zdjęcia.
5. **Rynek Kościuszki**: rodzaj nawierzchni (kostka granitowa? wymiary, układ) — z dokumentu
   (projekt rewitalizacji, BIP) albo ESTIMATED ze zdjęcia z metodą.
6. Aktualny katalog standardów/wytycznych **ZDM/ZDiT Białystok** (nowszy niż
   „Wytyczne do projektowania" z 13.07.2018, BIP resource 99308) — link, data, zmiany.

## Status prac (aktualizowany)

- [x] Gałąź utworzona z `origin/main` (b571433).
- [x] PDF Dz.U. 2019 poz. 2311 część c2 (załącznik 2, 381 stron) pobrany z eli.gov.pl.
- [x] Ekstrakcja tekstu wektorowego (381 stron) i obrazów rastrowych (rysunki).
- [ ] OCR etykiet wymiarów na rysunkach (P-2…P-25) — w toku.
- [ ] Zdjęcia Panoramax/KartaView/Commons — do zrobienia.
- [ ] Zadanie 5 (Rynek Kościuszki) — do zrobienia.
- [ ] Zadanie 6 (ZDM/ZDiT) — do zrobienia.
- [ ] manifest.csv, audit_20_percent.json — na końcu.

## Ważna korekta względem starej paczki (P2)

**P-11 to PRZEJAZD DLA ROWERZYSTÓW** (szerokość 1,8 m jednokierunkowy / 3,0 m dwukierunkowy),
NIE „przebieg przejścia/azyl". Potwierdzone tekstem rozporządzenia (Dz.U. 2019 poz. 2311,
zał. 2, rozdz. 2 — str. Dz.U. 569) i rysunkiem.

## Zasady

- Zakaz Google Maps / Street View / Earth / 3D Tiles.
- Źródła zdjęć: ELI/Dz.U., BIP Białystok, GDDKiA, Panoramax, KartaView, Commons, Openverse.
  Mapillary: brak tokenu → UNVERIFIED.
- Licencje komercyjne; NC/ND = „tylko referencja"; CC BY-SA = „referencja, nie tekstura".
- Każda liczba: źródło albo UNVERIFIED/ESTIMATED z metodą.
- Pozycje WGS84; sezon i pora_dnia dla zdjęć. JPG ≤1600 px. PDF urzędowe ≤5 MB.
- Samokontrola 20% z jawnym seedem (README + audit_20_percent.json).
- Zdjęcia/podzbiory binarne: `files/` (w `.gitignore`), paczka `mistral-p2-surfaces-2-files.zip`
  dostarczona poza gitem (patrz opis PR).

## Plikia

- `README.md` — ten plik (tabela wyników finalna niżej).
- `manifest.csv` — pozycje M52-001… (kolumny jak w `research/gptpro/p2-surfaces/manifest.csv`).
- `sources.md` — pełne źródła z linkami, licencjami i datami dostępu.
- `audit_20_percent.json` — samokontrola 20% (seed jawny).

## Tabela znaków poziomych (uzupełniana)

| Znak | Rysunek | Str. Dz.U. | Wymiary | Status |
|------|---------|-----------|---------|--------|
| P-2a | — | — | — | W TOKU |
| P-2b | — | — | — | W TOKU |
| P-3a | — | — | — | W TOKU |
| P-3b | 2.2.1.9 | 539 | — | W TOKU |
| P-4 | 2.2.1.10 | 539 | — | W TOKU |
| P-5 | 2.2.1.11 | 540 | — | W TOKU |
| P-6 | 2.2.1.12 | 541 | — | W TOKU |
| P-12 | 4.2.3.1 | 571 | — | W TOKU |
| P-13 | 4.2.4.1 | 572 | — | W TOKU |
| P-14 | 4.2.5.1 | 573 | — | W TOKU |
| P-21a | 5.2.7.1 | 588 | — | W TOKU |
| P-23 | 5.2.9.1 | 596 | — | W TOKU |
| P-25 | 4.2.6.1 | 574 | — | W TOKU |
