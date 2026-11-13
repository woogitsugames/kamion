# STATUS perf-p99-0177 (ADR 0177 — regresja p99 33,6 -> 50 ms, A16 Low 30 FPS)
## Krok 1 (analiza CSV, bez telefonu) — wyniki wstępne
- p99 to metryka-klif: okno ~1840–2080 klatek, ranga 1 % = 18–20. Skoki to prawie zawsze POJEDYNCZA klatka 50 ms (1 pominięty vsync).
- Liczba klatek >40 ms w oknie: s16 A 14, B 14 (p99 33,6) | a7010f B 20 (33,78, na granicy) | s17 A 23, B 22 (p99 49,9).
- Nadwyżka s17 (~+8) skupia się w 25–36 s (początek okna pomiaru): A 26,4..35,5 s (8 skoków), B 25,0..26,6 s (7 skoków). s16 tam 1–2.
- W skokach CPU main zwykle 15–25 ms, GPU 29–35 ms -> nie wąskie gardło main thread; GPU p50 ~32 ms przy budżecie 33,3 (margines ~1 ms).
- Stałe w s16 i s17: skok 83–117 ms przy ~41,2 s (B) i okresowe skoki z gpu=0 co ~2,02/4,03 s w drugiej połowie.
- Następny krok: logcat (logcat-run.txt/diag-logcat.txt) wokół 25–36 s — streaming/GC/ładowanie; potem przegląd kodu 0168/0165.
## Hipoteza główna (krok 1b)
- Kolekcje PSO (`Rendering/Resources/Pso/pso_Vulkan_Low_g3{a,b}`, ADR 0113) nagrane 2026-11-11 — ten sam stan w s16 i s17 (78/140, 67/134). ADR 0113 „Otwarte 3”: po nowych treściach nagrać ponownie. 0161–0169 dodały materiały/obiekty (meble, tablice, drzewa ogrodów, budynki) -> pierwsze użycie stanów w pierwszych ~10 s okna = pojedyncze 50 ms. Zgodne z rozkładem.
- Następny krok: przegląd kodu 0168/0165 (alokacje), potem A16: `spike_probe 1` na czystym APK (gc/pos), build Development z `pso_trace` -> nowe kolekcje -> pomiar przed/po ×2.
## STOP na limicie 93 % (koordynator) — PHONE_RUN nie zakładany, telefon nie używany
Następne kroki (komendy):
1. Przegląd kodu 0168 (NavigationService/RouteTracker 1 Hz) i 0165 pod alokacje: `git -C C:\Users\matma\Documents\Claude\kamion log --stat -5 -- game/Assets/_Project/Navigation` (dowód GC da `spike_probe 1`, pole gc=).
2. A16 (lock `artifacts\locks\PHONE_RUN`): czysty APK s17 z argumentem `spike_probe 1` (release: dt/gc/pos) — wzór uruchomienia: `artifacts\perf-low-r2\run-diag2.ps1` (pso_trace/pso_tag, build Development przez `artifacts\perf-low-r2\build2.ps1`).
3. Nagrać nowe kolekcje `pso_trace 90 pso_tag g3a|g3b` (Development), `adb pull` -> `game/Assets/_Project/Rendering/Resources/Pso/`, build release, gate3 A i B ×2 przed/po; analiza `python tools/perf/p99_spikes.py <ts...>`.
4. ADR `docs/adr/0177-perf-p99-pso-refresh.md`; rozważyć też p99 liczone bez klifu (licznik >40 ms jako metryka dodatkowa).
