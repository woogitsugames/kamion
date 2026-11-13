# STATUS perf-p99-0177 (ADR 0177 — regresja p99 33,6 -> 50 ms, A16 Low 30 FPS)
## Krok 1 (analiza CSV, bez telefonu) — wyniki wstępne
- p99 to metryka-klif: okno ~1840–2080 klatek, ranga 1 % = 18–20. Skoki to prawie zawsze POJEDYNCZA klatka 50 ms (1 pominięty vsync).
- Liczba klatek >40 ms w oknie: s16 A 14, B 14 (p99 33,6) | a7010f B 20 (33,78, na granicy) | s17 A 23, B 22 (p99 49,9).
- Nadwyżka s17 (~+8) skupia się w 25–36 s (początek okna pomiaru): A 26,4..35,5 s (8 skoków), B 25,0..26,6 s (7 skoków). s16 tam 1–2.
- W skokach CPU main zwykle 15–25 ms, GPU 29–35 ms -> nie wąskie gardło main thread; GPU p50 ~32 ms przy budżecie 33,3 (margines ~1 ms).
- Stałe w s16 i s17: skok 83–117 ms przy ~41,2 s (B) i okresowe skoki z gpu=0 co ~2,02/4,03 s w drugiej połowie.
- Następny krok: logcat (logcat-run.txt/diag-logcat.txt) wokół 25–36 s — streaming/GC/ładowanie; potem przegląd kodu 0168/0165.
