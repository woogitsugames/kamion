# audio-0232 — odsłuch A/B (ADR 0232)

A = synteza z `origin/main`, B = model 0232. Te same przebiegi z fizyki (physics-runner, 100 Hz), to samo lustro miksu gry, te same prawa głośności; różnią się tylko pliki: siatka silnika i hamulca silnikowego, gwizd turbo, „pssst” turbo, zwolnienie hamulca roboczego, zaciągnięcie postojowego. Opony, wiatr, sprężarka, retarder, fazy AMT, osuszacz i zwolnienie postojowego to te same pliki w A i B.

Pliki: FLAC 48 kHz mono 16 bit (bezstratne; WAV to LFS w tym repo). `ext` = kamera zewnętrzna, `cab` = kabina. W obrębie pary A i B mają to samo wzmocnienie (głośniejszy z dwóch ma szczyt −1 dBFS), więc różnice poziomu są prawdziwe. Sceny mają różne wzmocnienia — kolumna „wzmocnienie sceny”.

Odsłuch: telefon (głośnik) i słuchawki, najlepiej na przemian A → B → A ten sam fragment. Spektrogramy z zaznaczonymi zdarzeniami: `spec/<scena>_<ext|cab>.jpg` (góra: telemetria; 0–600 Hz i 0–9 kHz, A nad B).

Agent nie słyszy: poniżej jest to, co wynika z pomiaru i z konstrukcji dźwięku; ocena brzmienia należy do właściciela.

## 1_ruszanie_40t

Ruszanie z ładunkiem 40 t pod górę 3 %, pełny gaz przez biegi, odpuszczenie gazu, częściowy gaz. Fizyka: `a0232_launch_laden@laden40`, okno 0–27 s przebiegu.

| plik | LUFS | szczyt dBFS | wzmocnienie sceny dB |
|---|---|---|---|
| `1_ruszanie_40t_ext_A.flac` | -16.9 | -1.7 | +3.3 |
| `1_ruszanie_40t_ext_B.flac` | -17.0 | -1.0 | +3.3 |
| `1_ruszanie_40t_cab_A.flac` | -14.9 | -1.4 | +4.0 |
| `1_ruszanie_40t_cab_B.flac` | -14.9 | -1.0 | +4.0 |

Czego słuchać:

- Bieg jałowy 0–1,5 s: w B słychać spalanie na biegu jałowym (klekot, więcej harmonicznych zapłonu do ~600 Hz); w A komórka „bez obciążenia” to silnik bez wtrysku, więc jałowy jest gładszy i bardziej pusty.
- Zwolnienie hamulca roboczego (1,6 s): B = wypływ z komór przez zawory (dwa strumienie, przód i tył), A = szum z obwiednią.
- Pełny gaz pod obciążeniem (np. 2–5,5 s i 13–18,5 s): w B ostrzejszy, bardziej „warczący” wydech (stromy front impulsu), gwizd turbo siedzi w szumie przepływu i ma wstęgi boczne; w A gwizd to prawie czysty ton 3,2–4,6 kHz.
- Zmiany biegów AMT (wysprzęglenie: 5,9, 8,6, 12,3, 18,7, 21,2 s; bieg włączony: 6,6, 9,3, 13,0, 19,4, 21,9 s): przerwa w momencie i spadek obrotów pochodzą z fizyki i są takie same w A i B; w B wyraźniej zmienia się barwa silnika w przerwie (obciążenie → 0 → 1). Stuki skrzyni i „pft” są te same (ADR 0176).
- „Pssst” turbo przy odjęciu momentu (5,8, 8,5, 12,2, 18,6, 21,0 s): B = upust powietrza doładowującego (ok. 0,3 s) + wybieg sprężarki, A = krótszy syk z opadającym tonem. Ostatnie (21,0 s) to odpuszczenie pedału przez kierowcę.
- Wybieg 21–24 s i częściowy gaz od 24 s: B na wybiegu ciemniejszy i bardziej „mechaniczny”, po dodaniu gazu 50 % wraca wydech.

Znaczniki czasu (T = telemetria fizyki, D = zdarzenie dźwiękowe wykryte przez lustro gry):

-  1.51 s  T  pedał gazu 0 % → 100 %
-  1.62 s  D  zwolnienie hamulca roboczego (szczyt 1.00)
-  5.69 s  T  AMT: początek zmiany biegu z 4 (1854 obr/min)
-  5.82 s  D  turbo: odpuszczenie gazu przy doładowaniu 0.93
-  5.88 s  D  AMT: wysprzęglenie, bieg neutralny
-  6.23 s  D  AMT: włączenie biegu 5
-  6.58 s  D  AMT: sprzęgło zamknięte
-  6.59 s  T  AMT: bieg 5 włączony (1436 obr/min)
-  8.37 s  T  AMT: początek zmiany biegu z 5 (1853 obr/min)
-  8.50 s  D  turbo: odpuszczenie gazu przy doładowaniu 0.93
-  8.57 s  D  AMT: wysprzęglenie, bieg neutralny
-  8.92 s  D  AMT: włączenie biegu 6
-  9.27 s  D  AMT: sprzęgło zamknięte
-  9.27 s  T  AMT: bieg 6 włączony (1419 obr/min)
- 12.10 s  T  AMT: początek zmiany biegu z 6 (1810 obr/min)
- 12.23 s  D  turbo: odpuszczenie gazu przy doładowaniu 0.93
- 12.30 s  D  AMT: wysprzęglenie, bieg neutralny
- 12.65 s  D  AMT: włączenie biegu 7
- 13.00 s  D  AMT: sprzęgło zamknięte
- 13.00 s  T  AMT: bieg 7 włączony (1427 obr/min)
- 18.48 s  T  AMT: początek zmiany biegu z 7 (1851 obr/min)
- 18.62 s  D  turbo: odpuszczenie gazu przy doładowaniu 0.92
- 18.67 s  D  AMT: wysprzęglenie, bieg neutralny
- 19.02 s  D  AMT: włączenie biegu 8
- 19.37 s  D  AMT: sprzęgło zamknięte
- 19.38 s  T  AMT: bieg 8 włączony (1406 obr/min)
- 21.00 s  D  turbo: odpuszczenie gazu przy doładowaniu 0.99
- 21.01 s  T  AMT: początek zmiany biegu z 8 (1441 obr/min)
- 21.01 s  T  pedał gazu 100 % → 0 %
- 21.20 s  D  AMT: wysprzęglenie, bieg neutralny
- 21.55 s  D  AMT: włączenie biegu 9
- 21.90 s  D  AMT: sprzęgło zamknięte
- 21.91 s  T  AMT: bieg 9 włączony (1074 obr/min)
- 24.01 s  T  pedał gazu 0 % → 50 %

## 2_biegi_pusty

Przyspieszanie pustym zestawem przez biegi: gaz 55 %, potem 100 %, odpuszczenie, gaz 70 %. Fizyka: `a0232_gears@empty`, okno 0–25 s przebiegu.

| plik | LUFS | szczyt dBFS | wzmocnienie sceny dB |
|---|---|---|---|
| `2_biegi_pusty_ext_A.flac` | -19.2 | -2.7 | +3.1 |
| `2_biegi_pusty_ext_B.flac` | -19.3 | -1.0 | +3.1 |
| `2_biegi_pusty_cab_A.flac` | -16.1 | -1.4 | +4.9 |
| `2_biegi_pusty_cab_B.flac` | -16.2 | -1.0 | +4.9 |

Czego słuchać:

- Gaz 55 % (1–10 s), zmiany co ~1,5 s (wysprzęglenie: 3,5, 4,8, 6,3, 8,5, 12,0, 16,0, 18,2 s): słuchaj, czy silnik w B przy częściowym gazie brzmi inaczej niż przy pełnym (10–18 s), a nie tylko ciszej. W A warstwy różnią się głównie poziomem.
- Pełny gaz 10–18 s: gwizd turbo narasta z doładowaniem; „pssst” przy zmianach (11,9, 15,9, 18,0 s).
- Odpuszczenie gazu przy 18 s i powrót 70 % od 20,5 s: przejście wybieg → obciążenie (crossfade warstw off → on).

Znaczniki czasu (T = telemetria fizyki, D = zdarzenie dźwiękowe wykryte przez lustro gry):

-  1.00 s  D  zwolnienie hamulca roboczego (szczyt 1.00)
-  1.01 s  T  pedał gazu 0 % → 55 %
-  3.29 s  T  AMT: początek zmiany biegu z 4 (1517 obr/min)
-  3.48 s  D  AMT: wysprzęglenie, bieg neutralny
-  3.83 s  D  AMT: włączenie biegu 5
-  4.18 s  D  AMT: sprzęgło zamknięte
-  4.19 s  T  AMT: bieg 5 włączony (1330 obr/min)
-  4.61 s  T  AMT: początek zmiany biegu z 5 (1489 obr/min)
-  4.80 s  D  AMT: wysprzęglenie, bieg neutralny
-  5.15 s  D  AMT: włączenie biegu 6
-  5.50 s  D  AMT: sprzęgło zamknięte
-  5.51 s  T  AMT: bieg 6 włączony (1254 obr/min)
-  6.09 s  T  AMT: początek zmiany biegu z 6 (1418 obr/min)
-  6.28 s  D  AMT: wysprzęglenie, bieg neutralny
-  6.63 s  D  AMT: włączenie biegu 7
-  6.98 s  D  AMT: sprzęgło zamknięte
-  6.99 s  T  AMT: bieg 7 włączony (1196 obr/min)
-  8.31 s  T  AMT: początek zmiany biegu z 7 (1459 obr/min)
-  8.50 s  D  AMT: wysprzęglenie, bieg neutralny
-  8.85 s  D  AMT: włączenie biegu 8
-  9.20 s  D  AMT: sprzęgło zamknięte
-  9.21 s  T  AMT: bieg 8 włączony (1160 obr/min)
- 10.01 s  T  pedał gazu 55 % → 100 %
- 11.77 s  T  AMT: początek zmiany biegu z 8 (1681 obr/min)
- 11.90 s  D  turbo: odpuszczenie gazu przy doładowaniu 0.93
- 11.97 s  D  AMT: wysprzęglenie, bieg neutralny
- 12.32 s  D  AMT: włączenie biegu 9
- 12.67 s  D  AMT: sprzęgło zamknięte
- 12.67 s  T  AMT: bieg 9 włączony (1302 obr/min)
- 15.78 s  T  AMT: początek zmiany biegu z 9 (1712 obr/min)
- 15.92 s  D  turbo: odpuszczenie gazu przy doładowaniu 0.92
- 15.97 s  D  AMT: wysprzęglenie, bieg neutralny
- 16.32 s  D  AMT: włączenie biegu 10
- 16.67 s  D  AMT: sprzęgło zamknięte
- 16.68 s  T  AMT: bieg 10 włączony (1325 obr/min)
- 18.00 s  D  turbo: odpuszczenie gazu przy doładowaniu 0.98
- 18.01 s  T  AMT: początek zmiany biegu z 10 (1411 obr/min)
- 18.01 s  T  pedał gazu 100 % → 0 %
- 18.20 s  D  AMT: wysprzęglenie, bieg neutralny
- 18.55 s  D  AMT: włączenie biegu 11
- 18.90 s  D  AMT: sprzęgło zamknięte
- 18.91 s  T  AMT: bieg 11 włączony (1060 obr/min)
- 20.51 s  T  pedał gazu 0 % → 70 %

## 3_zjazd_hamulce_dlugotrwale

Zjazd 7 % z 75 km/h, 40 t: wybieg, dźwignia stopień 2, maksimum, zwolnienie, gaz 60 %. Fizyka: `a0232_downhill@laden40`, okno 0–26 s przebiegu.

| plik | LUFS | szczyt dBFS | wzmocnienie sceny dB |
|---|---|---|---|
| `3_zjazd_hamulce_dlugotrwale_ext_A.flac` | -17.0 | -1.0 | +2.7 |
| `3_zjazd_hamulce_dlugotrwale_ext_B.flac` | -17.4 | -1.4 | +2.7 |
| `3_zjazd_hamulce_dlugotrwale_cab_A.flac` | -14.5 | -1.0 | +6.0 |
| `3_zjazd_hamulce_dlugotrwale_cab_B.flac` | -14.9 | -1.4 | +6.0 |

Czego słuchać:

- Wybieg 0–3 s na 12. biegu (~1050 obr/min): tło to głównie opony i wiatr przy 75–80 km/h (te same w A i B).
- Dźwignia na 2 przy 3 s: redukcja 12 → 10 z przegazówką, hamulec silnikowy od 4,0 s (~1840 obr/min). W B poziom hamulca silnikowego wynika z krzywej momentu hamującego z fizyki: przy wysokich obrotach prawie jak w A, przy niskich wyraźnie ciszej (1000 obr/min: różnica w tabeli niżej).
- Dźwignia na maksimum od 9 s: retarder (ton łopatek + szum oleju) — te same pliki w A i B (ADR 0176), różnica A/B tylko w warstwie silnika pod spodem.
- Zwolnienie przy 19 s (zmiana 10 → 12; zdarzenie zwolnienia przepustnicy jest tu celowo nieme, bo trwa zmiana biegu), gaz 60 % od 21,5 s: wraca wydech i gwizd turbo.

Znaczniki czasu (T = telemetria fizyki, D = zdarzenie dźwiękowe wykryte przez lustro gry):

-  0.20 s  D  AMT: wysprzęglenie, bieg neutralny
-  0.55 s  D  AMT: włączenie biegu 12
-  0.90 s  D  AMT: sprzęgło zamknięte
-  0.91 s  T  AMT: bieg 12 włączony (1017 obr/min)
-  3.01 s  T  AMT: początek zmiany biegu z 12 (1073 obr/min)
-  3.01 s  T  dźwignia hamulców długotrwałych 0 → 2
-  3.20 s  D  AMT: wysprzęglenie, bieg neutralny
-  3.60 s  D  AMT: włączenie biegu 10
-  3.95 s  D  AMT: sprzęgło zamknięte
-  3.96 s  T  AMT: bieg 10 włączony (1836 obr/min)
-  4.00 s  D  hamulec silnikowy: włączenie
-  9.01 s  T  dźwignia hamulców długotrwałych 2 → 5
- 19.01 s  T  AMT: początek zmiany biegu z 10 (1625 obr/min)
- 19.01 s  T  dźwignia hamulców długotrwałych 5 → 0
- 19.20 s  D  AMT: wysprzęglenie, bieg neutralny
- 19.62 s  D  AMT: włączenie biegu 12
- 19.97 s  D  AMT: sprzęgło zamknięte
- 19.97 s  T  AMT: bieg 12 włączony (1009 obr/min)
- 21.51 s  T  pedał gazu 0 % → 60 %

## 4_postoj_pneumatyka

Postój 40 t: sprężarka na podwyższonych obrotach, odcięcie regulatora (osuszacz), zwolnienie hamulca postojowego, ruszenie, zatrzymanie, zaciągnięcie postojowego. Fizyka: `a0232_standstill_air@laden40`, okno 32–60 s przebiegu.

| plik | LUFS | szczyt dBFS | wzmocnienie sceny dB |
|---|---|---|---|
| `4_postoj_pneumatyka_ext_A.flac` | -20.7 | -1.0 | +5.0 |
| `4_postoj_pneumatyka_ext_B.flac` | -21.6 | -2.1 | +5.0 |
| `4_postoj_pneumatyka_cab_A.flac` | -15.9 | -1.0 | +9.7 |
| `4_postoj_pneumatyka_cab_B.flac` | -17.1 | -1.2 | +9.7 |

Czego słuchać:

- 0–8 s: postój na podwyższonych obrotach (~1900 obr/min, kierowca dopompowuje układ), sprężarka pracuje cicho pod silnikiem (ten sam plik w A i B).
- Odcięcie regulatora i wydmuch osuszacza (6,0 s): ten sam plik w A i B (ADR 0176).
- 8–11 s: obroty spadają do jałowych; od ~11 s bieg jałowy — tu różnica silnika A/B jest największa (klekot spalania w B).
- Zwolnienie hamulca postojowego (12,5 s): ten sam plik w A i B.
- Zwolnienie hamulca roboczego (14,0, 25,0 s): B = model wypływu z komór; drugie zwolnienie jest cichsze (słabsze hamowanie).
- Ruszenie 14–19 s, hamowanie do zatrzymania 19–21 s (fizyka dokłada hamulec silnikowy: 19,1 s).
- Zaciągnięcie hamulca postojowego (24,0 s): B = wypływ z komór sprężynowych, stuk sprężyn ok. 0,45 s po otwarciu zaworu (ciśnienie spada do progu sprężyn z definicji pojazdu); A = długi szum z kliknięciem po 1,75 s.

Znaczniki czasu (T = telemetria fizyki, D = zdarzenie dźwiękowe wykryte przez lustro gry):

-  6.05 s  T  sprężarka: odcięcie (12.5 bar)
-  6.05 s  D  odcięcie regulatora przy 12.5 bar: wydmuch osuszacza
-  8.01 s  T  pedał gazu 14 % → 0 %
- 12.52 s  D  hamulec postojowy: zwolnienie
- 14.01 s  T  pedał gazu 0 % → 45 %
- 14.02 s  D  zwolnienie hamulca roboczego (szczyt 1.00)
- 19.01 s  T  pedał gazu 45 % → 0 %
- 19.05 s  D  hamulec silnikowy: włączenie
- 19.68 s  D  hamulec silnikowy: wyłączenie
- 24.02 s  D  hamulec postojowy: zaciągnięcie
- 25.02 s  D  zwolnienie hamulca roboczego (szczyt 0.41)

## Pomiary banków (A = main, B = 0232)

| komórka | A LUFS | B LUFS |
|---|---|---|
| silnik ext off 600 obr/min | -39.9 | -37.8 |
| silnik ext on 600 obr/min | -27.9 | -28.7 |
| silnik ext off 1300 obr/min | -33.1 | -33.4 |
| silnik ext mid 1300 obr/min | -25.4 | -25.6 |
| silnik ext on 1300 obr/min | -21.1 | -21.1 |
| silnik cab on 1300 obr/min | -18.7 | -18.7 |
| silnik ext on 2100 obr/min | -15.0 | -15.0 |
| hamulec silnikowy ext 1000 obr/min | -23.5 | -27.1 |
| hamulec silnikowy ext 1500 obr/min | -21.9 | -22.6 |
| hamulec silnikowy ext 2000 obr/min | -18.4 | -19.1 |

| warstwa | A LUFS | B LUFS |
|---|---|---|
| `turbo_whistle_loop` | -10.1 | -10.1 |
| `air_brake_release` | -20.9 | -20.9 |
| `parking_brake_set` | -20.4 | -20.4 |
| `turbo_liftoff` | -15.3 | -16.7 |

Odtworzenie: `cd tools/audio; uv run python render_ab0232.py --rebuild` (telemetria: `uv run python telemetry0232.py --refresh`, wymaga .NET 8).
