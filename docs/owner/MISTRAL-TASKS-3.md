# Zadania dla Mistral Vibe Code — runda 3 (s14, 2026-11-12)

Repo: `woogitsugames/kamion`. **5 sesji, każda dostaje jeden blok poniżej (skopiuj całość).** Środowisko jak w rundzie 2: GitHub, bez Unity, telefonów i `Data/raw`, LFS widoczne tylko jako wskaźniki. Zadania wynikają z recenzji rundy 2 (`docs/reports/REVIEW-2026-11-12-s14-mistral-r2.md` na gałęzi `mistral-r2-int`, po scaleniu na `main`).

**Wspólne zasady (są w każdym prompcie):** gałąź `mistral/<nr>-<nazwa>` od `main`, na końcu PR do `main` (nie draft), raport po polsku w opisie PR. Nie pushujesz na `main` i nie scalasz. Nie zmieniasz `Data/**/generated/**`, `*.glb`, `*_meta.json`, `game/ProjectSettings/**`, `game/Packages/**`, `.gitattributes`, LFS. Nie zmyślasz: liczba zmierzona, zacytowana (z paragrafem/stroną) albo `UNVERIFIED`. Źródła wtórne (blogi, kalkulatory, serwisy ubezpieczeniowe) nie potwierdzają przepisów. Zakaz Google Maps, Street View, Earth, 3D Tiles. Na koniec napisz w sesji „M<nr> gotowe” z numerem PR.

---

## M16 — narzędzia audio: korekta oktawy w `comb_estimate`

```
Repo woogitsugames/kamion. Pracuj na gałęzi mistral/16-audio-octave od main, na końcu PR do main (nie draft). NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS. Raport po polsku w opisie PR. Nie zmyślaj liczb.

Kontekst: recenzja PR #10 potwierdziła błąd w tools/audio/el_analyze.py:146-160 (comb_estimate): korekta oktawy jest liczona, ale wynik jej nie używa. Test w tests/ dla tego przypadku ma Skip.
Zadanie: (1) napraw comb_estimate najmniejszą zmianą tak, by korekta oktawy była stosowana; (2) zdejmij Skip i dodaj testy na sygnałach syntetycznych (numpy): grzebień harmonicznych z f0 = 30, 46, 60, 90 Hz z silniejszą 2. harmoniczną — estymata f0 w ±3 %; sygnał z brakującą podstawową; szum (brak fałszywej detekcji); (3) uruchom pytest dla testów audio jak w .github/workflows/ci.yml. Nie zmieniaj innych funkcji poza koniecznością. W PR: przed/po na tych sygnałach (tabela f0 prawdziwe → estymata).
```

## M17 — źródła parametrów fizyki: R13 ostrzeżenie niskiego ciśnienia i strategia biegu startowego AMT

```
Repo woogitsugames/kamion. Pracuj na gałęzi mistral/17-physics-sources-2 od main, na końcu PR do main (nie draft). NIE pushuj na main, NIE scalaj. Nie zmieniaj żadnych danych gry ani kodu — tylko raport docs/reports/PHYSICS-SOURCES-2-2026-11-12-mistral.md. Raport po polsku. Nie zmyślaj.

Kontekst: docs/proposals/PHYSICS-PARAMS-2026-11-12.md (z PR #11) ma pozycje bez źródła: P2 (typowo 1,24), P3 (6,5 bar ostrzeżenie wg ECE R13 — bez paragrafu), P5, P8 (Pacejka — to książka o oponach, nie o kabinach), P10 (strategia biegu startowego AMT). Audyt docs/reports/AUDIT-PHYSICS-SOURCES-2026-11-12-mistral.md.
Zadanie: dla każdej pozycji znajdź źródło pierwotne: tekst regulaminu UNECE R13 (unece.org, konkretny paragraf/załącznik i wersja serii poprawek), normy, publikacje naukowe, dokumentacja techniczna producentów komponentów (bez marek w grze — w raporcie wolno cytować). Dla każdej: cytat ≤ 25 słów, odnośnik (URL + paragraf/strona), wartość, zakres stosowalności (ciągnik siodłowy 4x2 + naczepa 3-osiowa), pewność. Jeśli źródła nie ma — napisz to wprost (UNVERIFIED), nie zgaduj. Tabela: pozycja → stara treść → źródło → wartość → rekomendacja (wdrożyć / zostawić / zmierzyć).
```

## M18 — oznakowanie poziome: weryfikacja wymiarów z załącznika nr 2 (ISAP)

```
Repo woogitsugames/kamion. Pracuj na gałęzi mistral/18-markings-verify od main, na końcu PR do main (nie draft). NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS. Raport po polsku. Nie zmyślaj.

Kontekst: raport M10 (docs/reports/AUDIT-MARKINGS-PL-2026-11-12*.md z PR #13) oparł statusy „ZGODNE” na serwisach wtórnych; recenzja oznaczyła jako wątpliwe m.in.: P-10 długość max 16 m, wysokość trójkąta P-13 0,70 m, progi 70 km/h dla P-1a/P-1b/P-8, numery paragrafów PTB 2022, zdanie o „uchyleniu w 2022 r.”.
Zadanie: zweryfikuj każdą pozycję raportu M10 w źródle pierwotnym: Rozporządzenie w sprawie szczegółowych warunków technicznych dla znaków i sygnałów drogowych oraz urządzeń bezpieczeństwa ruchu drogowego i warunków ich umieszczania na drogach — załącznik nr 2 (oznakowanie poziome), tekst jednolity z isap.sejm.gov.pl (podaj Dz.U. rok/poz., stronę PDF, numer rysunku/tabeli). Dla każdej pozycji: wartość z rozporządzenia, wartość w kodzie (plik:linia, tools/worldgen/**), status ZGODNE / NIEZGODNE / BRAK W PRZEPISACH. Popraw raport M10 (statusy, usuń sprzeczności). Jeśli kod jest NIEZGODNY — nie zmieniaj generatora; dopisz test pytest oznaczony xfail(strict=True) z cytatem i markerem `unit`. 
```

## M19 — runner fizyki: jawna lista oczekiwanych porażek w `ExpectedFailureTests`

```
Repo woogitsugames/kamion. Projekt .NET tools/physics-runner (xUnit, rdzeń fizyki współdzielony z grą). Pracuj na gałęzi mistral/19-expected-failures od main, na końcu PR do main (nie draft). NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS ani rdzenia fizyki. Raport po polsku. Nie zmyślaj liczb.

Kontekst: recenzja PR #9: ExpectedFailureTests sprawdza tylko, że jakikolwiek check scenariusza pada — więc scenariusz może „oczekiwanie paść” z innego powodu niż opisany i test nadal przejdzie.
Zadanie: dla każdego scenariusza z expectedFail/expectedFailReason zapisz w danych scenariusza jawną listę metryk, które mają padać (np. ["radius_error_m"]), i zmień test tak, by: (a) padały dokładnie te metryki, (b) wszystkie pozostałe checki przechodziły, (c) gdy oczekiwana metryka zacznie przechodzić — test pada z komunikatem „naprawione? zdejmij expectedFail”. Uruchom dotnet test i runner scenariuszy jak w ci.yml. Nie zmieniaj progów ani goldenów. W PR: tabela scenariusz → metryki oczekiwanych porażek → wartość obecna vs próg.
```

## M20 — HUD bez alokacji: teksty liczbowe bez tworzenia stringów

```
Repo woogitsugames/kamion (Unity 6 C#, TextMeshPro). Pracuj na gałęzi mistral/20-hud-zero-alloc od main, na końcu PR do main (nie draft). NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS. Raport po polsku. Nie zmyślaj liczb.

Kontekst: PR #6 ograniczył odświeżanie etykiety gyro do 5 Hz, ale HUD nadal tworzy 2–3 stringi co 0,2 s, a inne etykiety HUD (prędkość, bieg, obroty, debug) mogą formatować stringi co klatkę. Zasada projektu: zero alokacji GC w pętli jazdy.
Zadanie: w game/Assets/_Project/** (bez Editor/ i Tests/) znajdź wszystkie aktualizacje tekstu UI w Update/LateUpdate/FixedUpdate i wołanych metodach. Zamień na bezalokacyjne: TMP_Text.SetText(format, float...) z formatem liczbowym albo char[]/StringBuilder z wielokrotnym użyciem + SetCharArray; aktualizuj tylko przy zmianie wyświetlanej wartości (po zaokrągleniu). Zachowaj identyczny wygląd tekstu (format, jednostki, miejsca po przecinku) — dla każdej etykiety w PR: przed (kod formatu) → po → przykład wyniku dla 3 wartości. Nie masz Unity: używaj tylko API TMP i Unity, które już występują w repo (sprawdź w game/Packages/packages-lock.json wersję TMP / com.unity.ugui). Każda etykieta = osobny commit. Lider skompiluje i zmierzy alokacje.
```
