# R4 — kontrola dostępności źródła do oglądu

2026-11-16, zapis date-only. Wynik: **0 nowych norm, 0 obejrzanych stron R4, 0 fotografii, 0 pobrań**. Brak lokalnej kopii w sprawdzonych katalogach nie jest dowodem braku dokumentu w całym projekcie ani w internecie.

Sprawdzono `../plate-geometry-round8/README.md`, `norms.csv`, `../legacy-regulations-round2/source-review.json` i `regulations.csv`, bazowy `../regulations.csv` oraz manifest P4. W PG8 nie ma wskazanego `source-review.json`. Wcześniejszy zapis podaje pełny odczyt tekstu web R4, lecz brak bitmap; L02 potwierdza `pdf_copy_saved=false`. Lokalny P4-001.pdf jest R48. Inne pliki P4 obejmują R46, R58, R73, R104 i poprawkę R70. Przegląd nazw PDF w `Data/raw/refs/codex-s21/01-lampy` nie wskazał R4. Koordynator potwierdził pomyłkę wskazania, agent lampy nie podał innej kopii.

Po odrębnym upoważnieniu wykonano jedną kwerendę: `site:unece.org "R004r3e.pdf" "2013"`; wyszukiwarka zwróciła pusty wynik. Nie otwierano żadnego nowego adresu dokumentu, nie ponawiano UNECE po 403 ani zablokowanego EUR-Lex 2009 i jego wariantów. Nie zgadywano nowych ścieżek ani symbolu pliku.

Dotychczas spisane luminancja, gradient, powierzchnia pomiarowa, kierunek pomiaru, średnica pola, współczynnik odbicia i geometria padania pozostają w istniejących tabelach. Nie dodano ich ponownie jako nowych warunków. Siatka R4 i przyporządkowanie etykiet rysunków pozostają **UNVERIFIED / NOT_VISUALLY_REVIEWED**. Nie potwierdzano aktualności prawnej w 2026 r.; poprzedni snapshot jest datowany na 2013 r.

Manifest ewidencjonuje wyłącznie audyt dokumentacji, a nie nowy odczyt urzędowego PDF. Brak zmian parentów, Git, kodu lub plików źródłowych.
