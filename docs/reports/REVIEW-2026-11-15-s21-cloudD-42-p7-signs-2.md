# Przegląd PR #42 — Mistral M45 P7 signs-2 (oznakowanie ronda Putry, Andersa, Tysiąclecia) — s21 cloud D, 2026-11-15

**Werdykt: ZAMKNIJ.** Powody:
- PR stoi od 2026-11-13 bez FIX, a decyzja lidera z s17 brzmi „nie scalamy” (HANDOVER s17–s20).
- Ponowny ogląd 10 z 10 kadrów potwierdza i rozszerza błędy z s17. **3 z 10 wierszy opisuje bramownicę, której na kadrze nie ma** (P7-005, 007, 008). **P7-006 to tył tablic** dla przeciwnej jezdni, a nie „nowa bramownica NB”. Dwie czytelne tablice mają status UNVERIFIED (P7-003, P7-010).
- Brak zdjęć z lat 2025–2026, czyli głównego celu zadania.
- Audyt sprawdza tylko formalności i nie ogląda obrazów.
- Wartościowa treść jest już w grze przez paczkę GPT G3 (ADR 0162, `overrides.yaml`). Trasę C obejmuje teraz R2 (#62).

- Gałąź `origin/research/mistral-p7-signs-2` @ `602dfc25a`. Baza `8c65107f7` jest 930 commitów za `origin/main`. `git diff --stat origin/main...` daje 7 plików, wszystkie w `research/mistral/p7-signs-2/` ✓.
- Wcześniejszy przegląd: `REVIEW-2026-11-13-s17-mistral-r8-p7.md` („PRZYJĄĆ CZĘŚCIOWO, NIE SCALAĆ”).

## 1. Kompletność (RESEARCH-PACK-03 / M45: stan 2025–26, oś czasu bramownic, DK19/DK65/DK8 N/S19/S8)
| Wymóg | Wynik |
|---|---|
| Stan bramownic 2025–2026 | **NIE.** 0 kadrów z lat 2025–26. Najnowszy to P7-004 z 2024-05-30 |
| Oś czasu bramownic Andersa | **CZĘŚCIOWO.** `timeline_andersa.md` ma fałszywą tezę „reorganizacji 2022→2024”, obaloną w s17 |
| Nowe korytarze DK19, DK65, DK8 N, S19, S8 | **PRAWIE NIE.** Jest tylko P7-004 (DK8 N, tablica odległościowa E-14). DK19, DK65 i S19 bez danych |
| Manifest w schemacie G3 | TAK (43 kolumny G3 + 3) |
| Samokontrola 20 % z obejrzeniem obrazów | **NIE.** 2 z 10 wierszy, testy wyłącznie formalne: sha256, słownik statusów, licencja, ≤ 1600 px |
| Licencje, Google, token Mapillary | TAK (§2). Google nieużyty, tokenu brak (s17) |
| Tylko własny katalog | TAK |

## 2. Obejrzane obrazy (10 z 10 kadrów, każdy osobno ≤ 960 px, plus 4 wycinki)
Panoramax pobrany przez API `search?ids=` (sd 2048 px), Commons jako miniatura 1920 px; P7-010 dodatkowo w 3840 px.

| Kadr | Licencja (API dziś) | Teza #42 | Co widać | Ocena |
|---|---|---|---|---|
| P7-001 (Panoramax 8176a172, az 194) | CC-BY-SA-4.0, stanton ✓ | bramownica N, teksty nieczytelne | bramownica kratowa z 3 panelami przed estakadą. Na wycinku: prawy panel „8 E67 Warszawa / 65 Ełk”, środkowy mały z żółtą tarczą, lewy rozmyty | ✓ konstrukcja; teksty częściowo czytelne |
| P7-002 (74817897, az 184) | CC-BY-SA-4.0 ✓ | ta sama bramownica z 290 m | bramownica w oddali, tablice usługowe po prawej | ✓ |
| P7-003 (d0fe5072, az 187) | CC-BY-SA-4.0 ✓ | teksty UNVERIFIED | znak zmiennej treści (VMS) „CENTRUM PRZEZ: / TYSIĄCLECIA P.P. … 7 MIN / ŚWIĘTOKRZYSKA … 7 MIN”, czytelny już przy 960 px | ✗ treść dało się odczytać (tak samo w s17) |
| P7-004 (Commons, Rakoon) | CC0 ✓ | „8 E 67 \| Korycin 35 \| Suchowola 49 \| Augustów 87 \| Suwałki 126 \| Kaunas 243” | dokładnie to; tablica na kratownicy, las w tle | ✓ (typ to E-14, nie E-1, jak w s17) |
| P7-005 (844e35c7, az 113) | CC-BY-SA-4.0 ✓ | PUTRY_W_GANTRY potwierdzona | maszty sygnalizacji z F-10 (niebieskie strzałki pasów), estakada po lewej, A-7 i C-12 po obu stronach; **bramownicy z tablicami nie ma** | ✗ |
| P7-006 (7196532e, az 54) | CC-BY-SA-4.0 ✓ | nowa bramownica NB „kier. węzeł S8/S19” | bramownica nad **lewą (przeciwną) jezdnią**. Wycinek pokazuje szare tyły paneli, ekran akustyczny po prawej | ✗ tablice obsługują jezdnię południową |
| P7-007 (35224dcb, az 121) | CC-BY-SA-4.0 ✓ | „bramownica obecna z sygnalizacją” | maszt sygnalizacji z wysięgnikiem, estakada, autobus; **bramownicy nie ma** | ✗ |
| P7-008 (6fc62548, az 100) | CC-BY-SA-4.0 ✓ | „bramownica obecna” | kamera **pod estakadą A**: pomosty, ochrowe słupy, dom w tle; **bramownicy nie ma** | ✗ |
| P7-009 (13bb273f, az 268) | CC-BY-SA-4.0 ✓ | konstrukcja z tablicami, treść UNVERIFIED | kratownica nad jezdnią z jedną tablicą ze schematem ronda; na wycinku „8 E67 Warszawa / 65 Ełk” u góry | ✓ obecność; treść częściowo czytelna |
| P7-010 (Commons, Rakoon) | CC0 ✓ | E-1, treść UNVERIFIED (3 sprzeczne odczyty) | wycinek z 3840 px: **„8 E67 Augustów / 19 Kuźnica PL BY” (prosto), „8 E67 Warszawa / 65 Ełk” (lewo), „65 Bobrowniki PL BY / 19 Lublin” (prawo)**, schemat skrzyżowania | ✗ czytelna (zgodnie z s17). To ta sama tablica co G3-C006 |

Wynik: **zgodne 4/10** (001, 002, 004, 009), **błędne tezy 4/10** (005, 006, 007, 008), **zaniżony odczyt 2/10** (003, 010). Marki na kadrach (salony, dealerzy) są tylko w tle. W manifeście padają nazwy usług z P7-002 („MITSUBISHI MOTORS, BOSCH SERVICE”) w kolumnie `uwagi`, ale nie trafiają do pól dla gry. Na scalenie to nie wpływa, bo PR i tak do zamknięcia.

## 3. Liczby sprawdzone u źródła (9)
- Azymuty `view:azimuth` z API Panoramax: 001 = 194, 002 = 184, 003 = 187, 009 = 268. Wartości z EXIF/API: 005 = 113, 006 = 54, 007 = 121, 008 = 100. Wszystkie **8/8 zgodne** z `kierunek_deg`.
- Daty 8/8 zgodne (np. 005: 2019-08-15 15:32:17 UTC, w manifeście 17:32:16 czasu lokalnego).
- Odległości P7-004 (35 / 49 / 87 / 126 / 243 km) zgadzają się z obrazem ✓.
- Liczby SOURCED: 1/10 wierszy tekstu (P7-004). Pozostałe UNVERIFIED, choć 2 z nich dało się odczytać (§2).

## 4. Wnioski dla gry
- **Nic nowego do `Data/Regions/bialystok-industrial-c/overrides.yaml`.** Bramownice Andersa i Tysiąclecia (`andersa-putry-approach-gantry`, `andersa-putry-portal-p40`, `tysiaclecia-s-putry-e1-portal`, `tysiaclecia-its-vms-gantry`, `tysiaclecia-s-putry-portal`) mają treści z G3 2024 (ADR 0162). Kadry #42 z 2019 ich nie podważają: P7-001 pokazuje ten sam układ 3 paneli co G3 2024 (s17).
- **Do sprawdzenia przy R2 (#62):** P7-010 / G3-C006 to E-1 z krzyżem na **najeździe od południa** (kamera 53,15691 N, 23,15223 E, ~240 m od ronda). W `overrides.yaml` nie znalazłem wpisu z „Augustów / Kuźnica” jako kierunkiem prosto i „Bobrowniki / Lublin” w prawo. Wszystkie wpisy `tysiaclecia-*` dotyczą jezdni południowej. Jeśli ten najazd leży w zakresie trasy C, brakuje tablicy (confidence low; decyduje ADR 0162 / world-builder).
- VMS: gra ma „TYSIĄCLECIA P.P. 5 MIN” (G3 2024), a P7-003 z 2019 pokazuje „7 MIN”. To stan chwilowy, bez zmian.
- P7-004 (DK8 N, E-14 Korycin… Kaunas) leży poza regionem C. Do zachowania jako referencja dla przyszłego regionu (R9).

## 5. Dla lidera
- **Zamknąć PR #42 bez scalania**, z komentarzem odsyłającym do tego raportu i do s17.
- Jeśli lider chce zachować jedyną użyteczną informację: dopisać P7-004 (CC0, 2024-05-30, E-14) i odczyt P7-010 do `research/gptpro/p7-s8-signs-2/REVIEW-NOTE.md` przy okazji innego commita. Nie wymaga to scalania gałęzi.
- Bloku FIX nie ma, bo werdykt to ZAMKNIJ.
