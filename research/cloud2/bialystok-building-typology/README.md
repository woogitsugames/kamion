# R4 — typologia zabudowy Białegostoku: trasa C i Dojlidy (pakiet cloud2)

**Dokończenie 2026-11-15:** obejrzałem 24 pliki Commons (16 Dojlidy, 8 trasa C; 23 × CC0 + 1 × CC BY-SA 3.0) w 960 px i opisałem elewacje. Razem teraz **40 obejrzanych kadrów**: 16 z 2026-11-14 i 24 nowe. 3 z nich (R4-140 Dojlidy-las, R4-144 Andersa zimą, R4-150 estakada) nie pokazują elewacji, więc kadrów z elewacjami jest **37**, w tym **15 w Dojlidach**. Manifest: **150 wierszy**; nowe to R4-127…R4-150, wiersze R4-001…126 się nie zmieniły. Samokontrola nowych: seed 20261115, próba 5, wynik **4 PASS / 1 FIX**. Recenzja: `REVIEW.md`. Zdjęcia w repo: `files/commons/` (24, ≤ 1600 px) i `files/jpg1600/` (16 kadrów z 2026-11-14) + `INDEX.csv`.

**Stan pierwotny —** Data: 2026-11-14 · gałąź `research/cloud2-bialystok-building-typology` · wierszy manifestu: **126** · obejrzanych kadrów: **16 (wszystkie trasa C; Dojlidy 0)** · samokontrola: **26 PASS / 0 FAIL** (seed 20261114).

*(Nieaktualne od 2026-11-15 — patrz „Kadry Commons i opisy elewacji”.)* **Stan 2026-11-14: NIEDOKOŃCZONE — praca przerwana poleceniem lidera (limit sesji).** Cel 30 kadrów (12 + 12) nie jest spełniony, a opisy elewacji z kadrów (kolory po termomodernizacji, balkony, rytm okien) nie powstały. Gotowe są: statystyki, wysokości z NMPT−NMT i cytaty do hal.

## Metoda
1. OSM Overpass dla dwóch prostokątów (kafel regionu + ulice z zadania), statystyka tagów i wymiarów obrysu — `tools/overpass.py`, `tools/stats.py`.
2. Te same statystyki z `Data/Regions/*/buildings.geojson` (BDOT10k funkcja i kondygnacje, LoD1 2024, LoD2 2017) — tylko w granicach kafli.
3. Wysokości próbki 56 budynków OSM z WCS GUGiK: mediana NMPT w obrysie zwężonym o 1 m minus p10 NMT w pierścieniu 1–4 m — `tools/nmpt_heights.py`, `data/nmpt_sample.csv`.
4. Kadry uliczne: Panoramax (7) i KartaView (9), każdy obejrzany w 960 px, azymut z API.
5. Cytaty z dokumentacji producentów (hale) i Wikipedii (systemy wielkiej płyty).

## Wyniki

### Kondygnacje i wymiary (BDOT10k + LoD1 w kaflach; OSM tylko pomocniczo)
OSM jest za ubogi na źródło typologii: `building=yes` ma 2224 z 2734 budynków (trasa C) i 756 z 962 (Dojlidy); `building:levels` 261 i 124; `roof:shape` 2 i 4; `height` 9 i 0.

| Typ | Obszar | n | Kondygnacje (BDOT10k) | Wysokość LoD1 p10/p50/p90 [m] | Rzut p50 [m] | Dach LoD2 2017 (kody z danych) |
|---|---|---|---|---|---|---|
| blok | C | 50 | 4: 25; 2: 7; 3: 7; 6: 3; 16: 3; 5: 2; 12: 2; 13: 1 | 8,9 / 14,9 / 39,6 | 47,7 × 15,7 | 1130: 23; brak: 17; 1030: 6; 1000: 4 |
| blok | Dojlidy | 12 | 4: 5; 3: 4; 2: 2; 5: 1 | 7,3 / 11,9 / 17,8 | 42,2 × 14,9 | 1130: 4; 1030: 4; brak: 4 |
| dom | C | 269 | 2: 229; 1: 38; 3: 2 | 4,6 / 7,7 / 10,8 | 12,6 × 8,6 | 1130: 168; 1010: 38; 1030: 19; 1000: 3 |
| dom | Dojlidy | 172 | 2: 152; 1: 13; 3: 5; 4: 2 | 6,5 / 7,9 / 9,7 | 12,5 × 8,8 | 1130: 94; 1030: 20; 1000: 14; 1040: 6 |
| hala | C | 52 | brak w BDOT | 3,6 / 6,6 / 15,5 | 49,2 × 18,0 (p90 109,9 × 55,1) | 1130: 20; 1030: 9; 1000: 8 |
| hala | Dojlidy | 38 | brak w BDOT | 3,7 / 5,4 / 13,1 | 55,4 × 19,6 (p90 156,6 × 96,8) | brak: 23; 1030: 6 |
| biuro/usługi | C | 102 | 1: 63; 2: 23; 3: 6; 4: 3; 5: 2; 11: 1 | 3,2 / 6,4 / 14,5 | 30,9 × 12,9 | 1130: 37; 1000: 24; 1030: 14 |
| biuro/usługi | Dojlidy | 60 | 1: 36; 3: 8; 2: 7; 4: 2; 5: 2 | 3,6 / 5,3 / 13,1 | 30,8 × 15,9 | 1130: 18; 1030: 14; 1000: 7 |

Znaczenia kodów dachu nie potwierdzałem w źródle; generator w repo traktuje 1000 jako płaski, 1010 jednospadowy, 1030 dwuspadowy, 1040 czterospadowy (`tools/worldgen/streetscape/roofs.py`).

Duże hale z próbki NMPT (Dojlidy): 12,2–13,0 m przy rzucie 135–155 × 83–98 m, jedna 18,9 m przy 166 × 98 m; hala magazynowa przy Andersa 10,7 m przy 154 × 147 m.

### Wysokości z NMPT−NMT (ESTIMATED, 56 budynków)
- Zgodność z LoD1 2024 dla 20 budynków: mediana różnicy +0,015 m, mediana wartości bezwzględnej 0,195 m. Percentyl 95 leży medianowo 0,73 m nad LoD1 (kalenice, attyki, nadbudówki).
- Bloki z kondygnacjami w OSM: 15,0 m (Białostoczek 27, liczba kondygnacji nieznana), 12,8 m / 4 = 3,2 m; 34,5 m / 12 = 2,87 m; 18,3 m / 6 = 3,05 m; 12,9 m / 4 = 3,22 m (dach wliczony).
- Domy: 7,1–10,3 m dla 2 kondygnacji, 3,6–7,2 m dla 1.

### Liczby dla generatora
| Parametr | Wartość | Status |
|---|---|---|
| OWT-67 kondygnacja brutto | 270 cm | SOURCED |
| OWT-75 kondygnacja | 280 cm | SOURCED |
| OW-T siatka | 540 × 480, 540 × 540, 270 × 480 cm | SOURCED |
| W-70 rozstawy ścian / kondygnacja | 240, 360, 480, 600 cm / 280 cm | SOURCED dla systemu; użycie w Białymstoku UNVERIFIED |
| Płyta warstwowa: moduł / długość | 1150 mm (1000, 1050) / do 15 m | SOURCED |
| Blacha trapezowa T35 | profil 34 mm, krycie 1035 mm, do 12 m | SOURCED |
| Brama segmentowa: otwór | szer. 1700–8000, wys. 2000–8000 mm; sekcja 545 mm | SOURCED |
| Brama „typowa” 4,0 × 4,5 m | — | WORKING_VALUE |
| Śluza doku | 3000–3400 × 3000–4400 mm, głębokość 600 mm | SOURCED |
| Wysokość doku | 1,1 m | SOURCED (1,2 m z zadania: UNVERIFIED) |

### Kadry (16, trasa C)
Z poziomu kierowcy na Andersa i Maczka elewacje są w większości zasłonięte: ekrany akustyczne (betonowy cokół, panele ryflowane jasnoszare lub ciemne szarozielone, przezroczysta góra na zielonych słupkach), estakady na piaskowożółtych podporach, las. Widoczne budynki: jeden dom z białą elewacją i stromym ciemnym dachem dwuspadowym, jeden budynek około 4-kondygnacyjny o beżowożółtej elewacji z płaskim dachem, niskie pawilony handlowe w bieli i błękicie. Żadnego kadru nie przypisałem do way OSM.

### Kadry Commons i opisy elewacji (2026-11-15; 24 obejrzane, ESTIMATED z obrazu)
Liczbę kondygnacji liczyłem z rzędów okien, kolory podaję słownie. Pełne opisy są w `data/commons_viewed.json` i w kolumnie `opis_co_widać`. Pozycje to współrzędne aparatu (EXIF/Commons), nie budynku. Kierunek kadru: UNVERIFIED.

| Typ | Kadry | Co widać (wspólne cechy) |
|---|---|---|
| **Hale magazynowe/produkcyjne, Dojlidy (strefa przy Kuronia)** | R4-127, 128, 129, 130, 131, 134 | długie bryły z **płaskim dachem**, okładzina z paneli: **biała / jasnoszara** (większość), **czerwona** (1 hala); szare cokoły; niższe przybudówki biurowe grafitowe lub szaro-białe z pasem okien; ogrodzenia panelowe z **czerwonymi słupkami**; 2 hale w budowie (prefabrykowany szkielet betonowy, stalowe kratownice, dźwig) |
| Biurowce, Dojlidy | R4-132, 133, 141 | 3–5 kondygnacji, płaski dach; elewacje: jasnobeżowa z ciemnografitową attyką i cokołem, szare panele z pasami okien, biały tynk z regularnymi oknami; ogrodzenia z czerwonej cegły z metalowymi przęsłami, tuje |
| Mniejsze budynki usługowe, Dojlidy | R4-135, 136, 142 | starsza hala parterowa szaroniebieska z żółtymi pasami i żółtą attyką; budynek 2-kondygnacyjny w **szachownicę** jasnoszaro-średnioszaro-czerwoną; parterowy budynek z łukowym zwieńczeniem w beżu i brązie |
| Domy jednorodzinne, Dojlidy | R4-137, 138, 139 | parter + poddasze lub 2 kondygnacje; tynk beżowy/szary, cegła silikatowa, klinkier pomarańczowo-czerwony; dachy dwuspadowe/czterospadowe z blachy lub dachówki czerwonobrązowej, grafitowe; PV na dachu; ogrodzenia z siatki, desek, kutych prętów; ulice z szarej kostki, chodniki z czerwonej kostki |
| Biurowce/usługi, trasa C | R4-145, 148 | Andersa 38A: 2 kondygnacje, jasnoszary tynk, ciemny pas attyki, klimatyzatory; budynek 8–9 kondygnacji w jasnozielonym/oliwkowym kolorze z regularną siatką okien |
| Bloki, trasa C | R4-146, 147 | 5 kondygnacji, biała elewacja z poziomymi pasami balkonów; nowe bloki 5–7 kondygnacji przy Tysiąclecia PP z białymi/jasnoszarymi elewacjami i szklanymi balustradami |
| Hala duża, trasa C | R4-143 | długi zakład z ciemnoniebieską okładziną i jasnymi pasami, płaski dach (z daleka) |
| Dom, okolica trasy C (ul. — UNVERIFIED; współrzędne 53.1566, 23.1859) | R4-149 | 2 kondygnacje, różowo-beżowy tynk, dach czterospadowy z czerwonobrązowej blachy, balkony z kutą balustradą, ogrodzenie z czerwonej cegły |

Wnioski dla generatora:
- W strefie przemysłowej Dojlid dominują **białe i jasnoszare hale z płaskim dachem**; czerwona okładzina to wyjątek (1 z 6 hal).
- Ogrodzenia mają charakterystyczne czerwone słupki.
- Biurowce mają 3–5 kondygnacji, ciemną attykę i pasy okien.
- Domy: tynk w jasnych beżach i szarościach, dachy czerwonobrązowe lub grafitowe.

## Co już było w repo / co nowe
| Temat | W repo | Nowe tutaj |
|---|---|---|
| Systemy wielkiej płyty per osiedle (OWT-67/75) | `research/mistral/p3-buildings-2` | dosłowne cytaty modułów z oldid |
| Wysokości LoD1 per budynek, kolory elewacji Białostoczka | `mistral/p3-buildings-2`, `gptpro/p3` | niezależna kontrola NMPT−NMT (56 budynków) |
| Typologia Dojlid z BDOT/LoD1 | `mistral/p12-dojlidy-landmarks` | tabela kondygnacji/rzutów per typ dla obu kafli |
| Zdjęcia Dojlid (Commons) | `mistral/p11-dojlidy-photos` | 16 obejrzanych plików z opisem elewacji (2026-11-15). Część tytułów może się pokrywać z p11 — nie sprawdzałem tego kadr po kadrze |
| Okładziny, bramy, doki hal | brak | 19 wierszy z cytatami producentów |
| Statystyka tagów OSM | brak | pełna, z zapytaniem i datą |

## Luki
- Dojlidy: 16 kadrów Commons obejrzanych 2026-11-15, 15 z elewacją. Wszystkie są jednego autora (Commons), więc to wąskie spojrzenie; Panoramax i KartaView nie mają tam zdjęć.
- Bloki wielkiej płyty z bliska: tylko 2 kadry (R4-146, 147), oba bez widocznych klatek i loggii z bliska. Świetliki dachowe hal nie są widoczne z poziomu ulicy (UNVERIFIED).
- Brak przypisania kadrów do way OSM.
- Filtr „użyte w repo” w `commons_scan.py` jest niepełny (dopasowanie po tytule); `commons_pick.py` sprawdza znacznik czasu, ale wynik nie został zapisany.
- Samokontrola wysokości nie powtarzała wywołań WCS (porównanie z CSV i LoD1). Dwa obiekty szpitalne (R4-070, R4-071) różnią się od LoD1 o około −2 m: jeden obrys OSM obejmuje bryły o różnej wysokości.
- Rozkład 4/5/10/11 kondygnacji dla bloków: w kaflu C dominuje 4 (25 z 50), 5 ma tylko 2 budynki; osiedla 5- i 11-kondygnacyjne Białostoczka leżą głównie poza kaflem, więc tabela ich nie reprezentuje.
- W-70, Wk-70, system szczeciński w Białymstoku: bez źródła. Wymiar „typowej” bramy i doku 1,2 m: bez źródła.
- Kody typów dachu LoD2 bez cytatu ze słownika.

## Jak używać w grze
Liczbę kondygnacji i wysokość brać z BDOT10k + LoD1 (OSM się nie nadaje). Elewacje hal dzielić co 1,15 m (płyta) lub 1,035 m (arkusz blachy), bramy rysować z poziomymi sekcjami co 0,545 m, doki na 1,1 m z kołnierzem 3,4 × 3,4 m. Przy trasie C większy wpływ na obraz z kabiny mają ekrany akustyczne i estakady niż elewacje.

## Pliki
`manifest.csv`, `sources.md`, `fetch.py` (16 plików, 17,8 MB, sha256 zgodne), `audit_20_percent.json`, `STATUS.md`, `data/` (Overpass, statystyki, próbka NMPT, listy Panoramax/KartaView/Commons), `tools/`.
