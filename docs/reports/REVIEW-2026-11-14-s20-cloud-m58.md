# Przegląd M58 cloud (C58, Dojlidy/Krywlany: słupki z łańcuchem, pas 09R/27L, ogrodzenie lotniska) — s20, 2026-11-14

**Werdykt: SCAL z erratą.** Paczka jest rzetelna i liczby, które przejmie gra, się bronią. Wysokość i rozstaw słupków, układ pasów i łańcuchów, cały układ oznakowania pasa 09R/27L oraz werdykt „z drogi NIE widać” sprawdziłem sam: na obrazach, na karcie AIP i w ortofoto. Jedyna istotna luka paczki to brak cytatu U-12b z zał. 4 Dz.U. 2019 poz. 2311. Zamknąłem ją w recenzji, bo zał. 4 jest w tym samym pliku ELI, z którego korzystała M66 (`text/I/D20192311-c2.pdf`). Gotowy blok errat jest w §4.

- PR #68, gałąź `origin/research/cloud-p15-dojlidy-details` @ `b24001bff`. Diff `origin/main...` ma 7 plików, wszystkie w `research/cloud/p15-dojlidy-details/` (+531 linii). Poza katalogiem nic się nie zmieniło.
- Manifest ma 80 wierszy, id są unikalne. Statusy: 42 SOURCED, 36 ESTIMATED, 2 UNVERIFIED. Kolumny bloku M58 są kompletne, doszły do nich `plik`, `url_pliku`, `sha256` i `sha1_commons`.
- Nic nie scalono, nic nie scommitowano, PR bez komentarza. Ten raport nie jest scommitowany.

## 1. Kryteria M58 punkt po punkcie

| # | Wymóg (MISTRAL-TASKS-9 §M58) | Wynik | Dowód recenzenta |
|---|---|---|---|
| 1 | Słupki P11-063: wysokość, przekrój, pasy, rozstaw, zwis, kolor łańcucha, przebieg, długość, końce | **TAK** | Rozstaw zmierzyłem sam na ortofoto 0,05 m (§3): 1,9 / 2,04 / 1,93 m. Na P11-063 i P11-076 (wycinki) sprawdziłem pasy i łańcuchy |
| 1 | Podstawa Dz.U. 2019 poz. 2311 zał. 4 (U-12b), cytat + strona | **NIE w paczce → zamknięte w recenzji** | Zał. 4 jest w `api.sejm.gov.pl/eli/acts/DU/2019/2311/text/I/D20192311-c2.pdf` (sha256 `8abcce24…5c4`, ten sam plik co w M66), s. 843 (zał. 4 s. 38). Cytat w §4 |
| 1 | Pozycje końców (ortofoto/OSM), `barrier=chain` | **TAK** | C58-012/013 po przeliczeniu na EPSG:2180 dają N [780013,35; 590461,80] i S [780018,27; 590448,70], długość **13,99 m**. OSM `chain` = 0 (nie liczyłem ponownie) |
| 1 | Inne takie wygrodzenia w regionie | **TAK** | Dywizjonu 303 (P11-076: obejrzany, łańcuchy takie jak przy Mickiewicza) oraz zjazd do bramy E (P11-022: obejrzany, 4 słupki bez łańcucha i 3 z łańcuchem — zgodne) |
| 2 | Oznakowanie pasa z AIP i ortofoto 2023–2025 | **TAK** | Kartę AIP wyrenderowałem sam (pymupdf, 200 dpi): 1350 × 30, CONC/ASPH, TORA 1350, LDA 900/640, TRUE 092/272, AIRAC AMDT VFR 06/26, 11 JUN 2026 — wszystko zgodne. Obejrzałem wycinki 0,05 m progu 09R, progu 27L i oznacznika 27L oraz przegląd 0,4 m |
| 2 | Widoczność z drogi (geometria + kadry), werdykt | **TAK, „NIE”** | Na P11-080 i P11-076 widać ogrodzenie, łąkę, samoloty i las, pasa się nie da wskazać. Zgadza się to z własną kamerą `krywlany_runway` z ADR 0196 („z 1,7 m oznakowania nie widać”). Ul. Kuronia bez kadru, wynik tylko z geometrii |
| 2 | Ogrodzenie lotniska z kadrów | **TAK (wysokość ESTIMATED)** | P11-080 obejrzany: zielony panel 3D, zielone słupki, 2 druty kolczaste na przedłużeniach słupków, czerwona tabliczka. Wysokość ma za skalę założony moduł 2,5 m, co paczka uczciwie oznacza jako WORKING_VALUE |
| 3 | Inne wygrodzenia (U-5a, U-12a, szlabany), 1–3 przykłady | **CZĘŚCIOWO** | Są szlabany (3), żółte U-12a i tablice prowadzące. U-5a „nie znaleziono” (C58-080). Akceptowalne |
| — | Każdy kadr obejrzany, zdanie „co widać”, przypisanie ≤ 25 m | **TAK** | 10 opisów porównałem z obrazem, wszystkie się zgadzają (§2) |
| — | Kierunek z API albo UNVERIFIED | **TAK** | Commons nie podaje azymutu. 3 kadry mają ESTIMATED z geometrii, reszta UNVERIFIED |
| — | Samokontrola ≥ 20 %, seed | **TAK** | `random.Random(20261114).sample(ids, 16)` daje tę samą listę co `audit_20_percent.json` ✓. Wynik 10 PASS i 6 poprawek |
| — | Licencje, zakaz Google | **TAK** | 17 plików CC0 (Rakoon), 1 CC BY-SA 4.0 jako referencja. GUGiK i PAŻP to dane urzędowe. Google, Bing i Mapillary nie były używane |
| — | Zdjęcia poza gitem, fetch.py | **TAK z zastrzeżeniem** | `python -I fetch.py --skip-large` u mnie: 20/33 OK (wszystkie GUGiK i PAŻP mają zgodne sha256, 4 oryginały Commons zgodne z sha1 z API). 13 plików Commons dostało HTTP 429 w dwóch próbach (logi zakończone o 19:39 i 20:10) — to limit Commons, nie błąd skryptu |

## 2. Co obejrzałem sam (14 obrazów)

- **Kadry Commons/P11 (lokalne kopie 1600 px z `research/_incoming/mistral-p11-dojlidy-photos-v2/` albo oryginały z fetch.py):**
  - P11-063 w całości oraz wycinek słupków 2× (1600 px).
  - P11-076 = 20200726_082324 w całości oraz wycinek dolnej części z oryginału 4608 px.
  - 20230814_174527 (rondo Wünschego), P11-080, P11-022, P11-077.
- **Ortofoto i dokumenty:**
  - Ortofoto Mickiewicza × Kuronia: wycinek 3× i drugi wycinek 5× z pliku 0,05 m.
  - Pas 0,4 m (przegląd), próg 09R, próg 27L, oznacznik 27L i brama E.
  - Karta AIP VFR AD 4 EPBK 2-1 (render 200 dpi).
- **Zgodność z opisami:** wszystkie opisy się zgadzają. Ważne szczegóły:
  - **Łańcuchy:** w każdym przęśle łańcuch jest jednobarwny, kolor zmienia się co przęsło, a górny i dolny są w przeciwnej fazie (P11-063, P11-076). Paczka opisuje to poprawnie.
  - **Proporcja przęsło/wysokość** na obu kadrach wychodzi ok. 1,65–1,7. Na P11-063 kolejne słupki stoją przy x = 630 / 750 / 858 / 966 px, a ich wysokość to 72 → 64 px. To zgadza się z modelem otworkowym paczki (1,712), a nie z 2,0 z ADR 0183.
  - **Linia osiowa przy 09R:** na wycinku progu kreska przecina pas poprzeczny i biegnie przez groty (C58-040 „skrajne kreski przecinają pasy poprzeczne”). Zdanie w README §0 „między progami tylko linia osiowa” jest więc nieprecyzyjne (errata 3).
  - **Metoda B wysokości (cień):** cień słupka pada pod azymutem ~324°, a rząd biegnie pod ~340°. Różnica to tylko ~16°, więc cień słupka leży prawie wzdłuż cieni łańcuchów. Odczyt jest możliwy, ale metoda nie jest tak niezależna, jak twierdzi paczka (errata 4). Mój zgrubny odczyt cienia daje ~1,0–1,2 m.
  - **Położenie rzędu:** 5 słupków z wycinka 5× przeliczyłem na EPSG:2180 (E = 779930 + 0,05·kol., N = 590520 − 0,05·wiersz): od [780014,20; 590459,92] do [780016,90; 590452,60]. Od linii M58 (C58-012→013) odchylają się o 0,01–0,13 m. Od linii override 0183 (po przesunięciu r2) dzielą je 1,5–2,4 m, a od pierwotnej linii 0183 z ortofoto 2024 1,1–2,0 m. Słupki stoją między tymi dwiema liniami.

## 3. Liczby sprawdzone u źródła (9)

| # | Liczba / cytat | Źródło | Wynik |
|---|---|---|---|
| 1 | RWY 09R/27L 1350 × 30, CONC/ASPH, TORA 1350, LDA 900 / 640, TRUE 092/272 | karta AIP (render) | ✓ |
| 2 | 09L/27R 840 × 160 GRASS | karta AIP | ✓ (ADR 0196 podaje 860 m z OSM; AIP mówi 840) |
| 3 | „Zwężenie RWY 09L/27R do 80 m.” | SUP 02/26 (pdftotext) | ✓ |
| 4 | Rozstaw słupków 2,0 m (2,04/1,91/1,96) | ortofoto 0,05 m, mój pomiar 5× | ✓ 1,90 / 2,04 / 1,93 m |
| 5 | Długość odcinka ~14 m, końce C58-012/013 | przeliczenie WGS84 → EPSG:2180 (pyproj) | ✓ 13,99 m |
| 6 | Grot/pas progu 27L: 5 grotów, pas poprzeczny, dalej linia osiowa | wycinek 0,05 m | ✓ |
| 7 | „27” + „L” przy końcu E, „L” w osi, żółta linia płyty dochodzi do „L” | wycinek 0,05 m | ✓ |
| 8 | OSM: way 958211700 `aeroway=runway, ref=09R/27L, length=1350, width=30, surface=asphalt`; way 483199984 `barrier=fence, fence_type=metal` | OSM API 0.6 (ways.json), 2026-11-14 | ✓ |

| 9 | Położenie rzędu (C58-012/013) | 5 słupków z ortofoto 0,05 m przeliczonych na EPSG:2180 | ✓ 0,01–0,13 m od linii M58 |

Dodatkowo w Dz.U. 2019 poz. 2311 przeczytałem U-12b (s. 843) i U-12c (s. 847): tekst z pymupdf, strona PDF 317 = s. 843. Paczka ich nie cytuje, ale zmieniają wnioski dla gry (§5).

## 4. Errata (blok do wklejenia autorowi lub do naniesienia przy scaleniu — nie blokuje)

```
M58-ERRATA (cloud p15), recenzja s20 2026-11-14:
1. C58-017/C58-018 + README §1.1 kolumna „przepis” + §5 luka 1: zał. 4 JEST dostępny:
   https://api.sejm.gov.pl/eli/acts/DU/2019/2311/text/I/D20192311-c2.pdf (s. 526–906; sha256 8abcce24766fe743b5bbcd3d64771e70c1a6709c1db72fdf72adfebbfdc5d5c4),
   zał. 4 pkt 5.4, s. 843 Dz.U. (strona PDF 317). Cytat: „Wysokość tych ogrodzeń powinna wynosić 1,10 m. Rozstaw słupków
   powinien wynosić 1,5 m lub 2,0 m, a strzałka ugięcia łańcucha – do 0,10 m.” Barwy (zalecenie): słupki – pasy
   biało-czerwone po 25 cm, pierwszy dolny biały; łańcuch – szary lub biało-czerwony w odcinkach po 25 cm.
   C58-018 → SOURCED: wys. 1,10 m; rozstaw 1,5/2,0 m; zwis ≤ 0,10 m. Tabela 1.1: przepis vs odczyt = 1,10 vs 1,17/1,19;
   2,0 vs 2,0; zwis 0,10 vs 0,17–0,25 (odczyt przekracza zalecenie); łańcuch: przepis 25-cm odcinki, w terenie całe
   przęsła jednobarwne (odstępstwo od zalecenia, nie błąd odczytu).
2. C58-080: U-12c zdefiniowany na s. 847 („Wysokość słupków powinna wynosić od 0,6 do 0,8 m. Barwa słupków blokujących
   powinna być biało-czerwona.”) – kod U-12c przestaje być „roboczy”; 4 słupki bez łańcucha z P11-022 to kandydat U-12c
   (wysokość nie mierzona – UNVERIFIED).
3. README §0 pkt 2: „między progami tylko linia osiowa (5 kresek)” → „linia osiowa 5 kresek s = 420–680,5 m; skrajne
   przecinają pasy poprzeczne obu progów (przy 09R kreska biegnie przez środkowy grot)” – jak w C58-040.
4. C58-003 uwagi: dopisać „azymut cienia ~324°, oś rzędu ~340° – cień słupka leży blisko cieni łańcuchów; metoda B nie
   jest w pełni niezależna (koniec cienia słupka odczytany wśród cieni łańcuchów)”.
5. sha256 4 oryginałów Commons (pobrane w recenzji, sha1 zgodne z API):
   20200726_082250 44428eb21a36be4f2544042da96b127c0e1b2de64788058ac6e6071c6d0422f7
   20200726_082324 92f705b1e66452b2b363b50acbdab5fa25654762a7fd31cdb68d400c60cf7520
   20200726_083613 87e73c809088385ddfaac5a32a8316b9935ae06b54f9befba84e66e197da93de
   20230814_174527 67c9d313e080edb98041eb0f2a5172a1e04cc7eb7bb5909815f56f4828a06851
   Pozostałe 13: nadal HTTP 429 (Retry-After 600) – lider uruchamia fetch.py później; sha1 z API wystarcza do weryfikacji.
```

## 5. Co M58 daje grze (konkretnie)

### 5.1 ADR 0183 — słupki z łańcuchem (scalone): wymiary są dziś oparte na złym typie urządzenia

ADR 0183 i `tools/worldgen/streetscape/chain_bollards.py` uzasadniają `POST_H_M = 0.80` przepisem dla **U-12c** (słupki blokujące, 0,6–0,8 m). Na P11-063 stoi jednak **U-12b**, czyli ogrodzenie łańcuchowe, a dla niego Dz.U. podaje 1,10 m. Pomiar M58 potwierdza przepis.

| stała (`chain_bollards.py`) | dziś | przepis U-12b (s. 843) | pomiar M58 / mój | proponowane |
|---|---|---|---|---|
| `POST_H_M` | 0,80 | 1,10 (SOURCED) | 1,17 / 1,19 (ESTIMATED); proporcja na kadrach ~1,7 | **1,10** (przepis; mieści się w niepewności pomiaru) |
| `BAY_M` | 1,60 (= 2,0 × wys.) | 1,5 lub 2,0 | ortofoto 1,90–2,04 | **2,00** |
| `BANDS` | ułamki 0,22/0,43/0,68/0,89 | pasy 25 cm, dolny biały | 5 pasów, górny biały ~0,12 m | od ziemi W 0–0,25, R 0,25–0,50, W 0,50–0,75, R 0,75–1,00, W 1,00–1,10 m |
| `CHAIN_Z_M` | 0,94 / 0,46 × H | — | 1,10 / 0,56 m (0,94 / 0,48 × H) | ułamki zostają, przy H 1,10 m dają ≈ 1,03 / 0,51 m |
| `CHAIN_SAG_M` | 0,18 / 0,16 × H | ≤ 0,10 m (zalecenie) | 0,17–0,25 m | zostaje ≈ 0,20 / 0,18 m (zdjęcie > zalecenie) |
| `CHAIN_PAINT` | pół przęsła czerwone, pół białe | 25-cm odcinki (zalecenie) | **całe przęsło jednobarwne, kolor zmienia się co przęsło, górny i dolny w przeciwnej fazie** (C58-010; sprawdzone na P11-063 i P11-076) | wzór na dwa przęsła: (górny R, dolny W), (górny W, dolny R) |
| linia override `mickiewicza-kuronia-chain-posts-p11-063` | 11,2 m (8 słupków × 1,6) | — | 13,99 m, ≥ 8 słupków; N [780013,35; 590461,80], S [780018,27; 590448,70] (±2 m wg M58; moja kontrola 5 słupków: 0,01–0,13 m od tej linii) | `line_epsg2180` = linia M58, 7 przęseł × 2,0 = 14,0 m. Prawdziwe słupki stoją 1,5–2,4 m bliżej jezdni niż dzisiejszy override i 1,1–2,0 m dalej niż pierwotna linia 0183. Przesunięcie r2 (+3,5 m) jest więc za duże o ~2 m. Czy wygenerowany chodnik sięga do linii M58, musi sprawdzić 0183 (sonda chunku 3_2) |

Inne miejsca do rozstawienia (nowe wpisy `chain_bollards`):
- **Dywizjonu 303 przed wjazdem na lotnisko:** ≥ 20 słupków (≥ 38 m), przęsło 2,03 m, punkt startowy 53.105683, 23.167169 (C58-019…025). Końce odcinka są UNVERIFIED, nie stawiać bez nich.
- **Zjazd do bramy E** (P11-022): lewa strona to 4 słupki bez łańcucha z czarnym kapturkiem (`chain: false`), prawa to 3 słupki z jednym ciemnym łańcuchem. Drugiego wariantu łańcucha prototyp nie ma, to backlog.
Budżet: prototyp się nie zmienia. Rząd z 7 przęseł to te same +2–3 draw na prototyp i LOD, co w ADR 0183.

### 5.2 ADR 0196 — farba pasa 09R/27L (scalone)

Wpis `krywlany-runway-paint` w `Data/Regions/bialystok-dojlidy/overrides.yaml` porównałem z M58 (ortofoto 2025, 0,05 m). Wpis bazował na ortofoto 2024 0,25 m.
- **Przeliczenie stacji:** s_gry = s_M58 − 422,6. Kotwice to progi: M58 441,2 / 630,0 ↔ gra 18,4 / 207,4. Obie dają 422,6–422,8, więc układy się zgadzają.

| element | gra (0196) | M58 | działanie |
|---|---|---|---|
| groty (5 na próg), poprzeczki progów | s 5,5–15 / 211,4–221,4; poprzeczki 18,4 / 207,4 | 09R groty po W, 27L po E ✓ | bez zmian |
| strzałki od E | 10, końce grotów 278,3…796,2, co 57,7 | 10, s_M58 698,5–1257 → 275,9–834,4, co 57,5 | ✓ (±2,4 m) |
| linia osiowa | 4 kreski 54,7–258,4 | 5 kresek: brakuje **420–450,5 → gra 0,5–27,9** (przecina poprzeczkę 09R i biegnie przez środkowy grot, sprawdzone na wycinku) | **dodać kreskę `{s_m: [0.5, 27.9]}`** |
| „27 L” | nie rysowane (otwarte w 0196) | „27” s_M58 1268,5–1278 → **gra 845,9–855,4**; „L” 1283,5–1293 → **860,9–870,4**; wys. znaku 9,1–9,3 m, cyfra 3,0–3,3 m szer.; „2” i „7” obok siebie w poprzek osi, „L” w osi; podstawy znaków od strony końca E | dane gotowe do domknięcia otwartego punktu 0196 (kształt glifu nadal WORKING_VALUE) |
| szerokość poprzeczki progu | 1,0 | 1,25 | 1,25 |
| szerokość linii krawędziowych / rozstaw | 0,9; krawędzie zewnętrzne 29 m | 0,80–0,87; osie 29,1 m (krawędzie zewn. ≈ 29,95 m) | 0,85, `offset_m` 14,55 (oś linii) |
| trzon strzałki / linia osiowa | 0,45 (WORKING_VALUE) | ~0,35 | 0,35 |
| grot | 10 × 3,3 | 10 × 3,1, rozstaw 5,5 | 3,1 / 5,5 (drobne) |

- **Wały w NMT:** M58 (C58-056) mówi, że NMT z pomiaru 2018 ma podłużne nasypy 2–3 m ok. 70 m na N i 50–65 m na S od osi pasa, a na ortofoto 2025 ich nie ma.
  - Teren gry pochodzi z `gugik-nmt-2025-bialystok-dojlidy` (arkusze N-34-107-C-b-3-2/-4). Nie sprawdzałem, z którego roku jest tam pomiar.
  - **Działanie:** sprawdzić przekrój terenu gry w poprzek pasa (np. w E −600). Jeśli wały są w siatce, spłaszczyć je override'em terenu. Bez tego kamera `krywlany_runway` (oko 1,7 m, depresja 0,3–1,0°) ma fałszywą przesłonę.

### 5.3 Ogrodzenie lotniska

Ogrodzenie lotniska (OSM way 483199984 N, 483199985 W, 542255310 S/E) jest dziś zwykłym `panel_fence`. Kolor losuje `FENCE_COLOURS[_h(key) % 3]`, bo w `overrides.yaml` Dojlid nie ma wpisu `fence_style` dla tych dróg.
- Dodać `kind: fence_style` → `fence_green` dla trzech dróg (C58-061/062, P11-080).
- Wysokość: `FENCE_H` 2,03 m ≈ wierzch słupka ~2,0 m (ESTIMATED). Bez zmian.
- **Drut kolczasty** (2 rzędy, ~0,10 i ~0,26 m nad panelem, na pionowych przedłużeniach słupków) to nowy element ogrodzenia. Backlog, nie przy tym scaleniu.
- Brama E: stalowa, ramowa, ciemnozielona, 4 pola z zastrzałami, ~9,9 m. Środek E 780254,8 / N 589883,2 (C58-069), wysokość UNVERIFIED.

## 6. Dla lidera

- **Scalić PR #68.** Diff dotyczy tylko `research/cloud/p15-dojlidy-details/`. Errata 1–5 z §4 nanieść przy scaleniu albo zlecić autorowi. Najważniejsza jest errata 1, bo dodaje przepis U-12b.
- `fetch.py`: uruchomić lokalnie później, bo Commons odpowiada 429. Wszystkie pliki GUGiK i PAŻP są już zweryfikowane.
- **Zadanie dla gry (follow-up 0183, world-builder):** `POST_H_M` 1,10, `BAY_M` 2,00, `BANDS` po 25 cm, `CHAIN_PAINT` przęsłami, linia Mickiewicza = linia M58 (14,0 m). Trzeba też zaktualizować `tests/gis/test_chain_bollards_0183.py`: l. 85 `assert 0.6 <= CB.POST_H_M <= 0.8  # U-12c` i l. 86 `BAY_M == 2.0 * POST_H_M` kodują błędne założenie.
- **Zadanie dla gry (follow-up 0196):**
  - kreska osiowa s 0,5–27,9;
  - „27 L” w s 845,9–870,4;
  - poprzeczka 1,25, linie 0,85, trzon 0,35;
  - `fence_style` zielony dla 3 dróg ogrodzenia;
  - kontrola wałów w NMT.
