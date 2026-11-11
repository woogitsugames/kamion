# ADR 0118 — Materiał nawierzchni

## r1 — Low, ślady kół i widoczność istniejących napraw

Stan: WIP, wygląd i koszt GPU niezweryfikowane.

Bazą jest gpt-surface-wear scalone do aktualnego main w worktree gpt-asphalt. Recenzja 0099 wykazała brak zmiany asfaltu w kamerach trasy, pomijanie spękań przez Low i ukryty mnożnik przetarcia farby w importerze.

Zmiany będą sterowane osobnym blokiem danych materiału. Istniejące materiały bez tego bloku muszą zachować dotychczasowe działanie. Shader nawierzchni używany przez asfalt to WorldPBR, a nie starszy WorldSurface. Zmiany wspólnego shadera i importera obejmą wyłącznie warstwy asfaltu i farby za flagą danych. Nie zmieniamy geometrii dróg, ustawień jakości ani kontraktu liniowego _Tint.

Pierwszy wariant: obecna maska spękań na Low z jedną próbką koloru, bez próbkowania normalnej spękań; mocniejszy kontrast istniejącego pola kół i korekta tonu starego asfaltu. Wartości są WORKING_VALUE. Naprawy i olej już są generowane — baseline roads_qa podaje 316 łat i 286 plam, więc najpierw badamy ich widoczność zamiast zwiększać liczby w ciemno.

Dowody będą obejmować te same kamery przed i po w Low/High clear/overcast, zdjęcia ze wskazanych par sbs i osobne liczniki instancji. A16 pozostaje UNVERIFIED, ponieważ sesja nie używa telefonów. Bez potwierdzenia obrazu i budżetu zmiana nie otrzyma PASS.

Instrukcja właściciela z 2026-11-11 ~22:20: każdy ciężki producent Pythona i pytest GIS/physics/gate3 korzysta z puli heavy (max 3). Pełny GIS dopiero na końcu rundy; w trakcie rundy tylko konkretne pliki. Import nie może uruchamiać ukrytego build_all/build_world bez heavy. Własne runnery stosują aktualny skrypt slotów z main bez edycji wspólnego skryptu.

