# ADR 0108 — światło, niebo, ekspozycja i post

## Runda r1 — w toku, 11 listopada 2026

Bazą jest main 4c9905b1, gałąź gpt-light-r1, worktree .claude/worktrees/gpt-light. Okno pracy: 11 listopada 2026 21:30–12 listopada 2026 21:30 czasu Warszawy.

RCAS: wykonano 40 PNG (4 wartości × clear/overcast × 5 kamer). High 0 / 0,25 / 0,5 / 0,75 daje HF asfaltu r=1,5 odpowiednio 3,4372 / 4,0386 / 4,5217 / 5,6999 poziomu sRGB. Żaden wariant przy dawnym końcowym ditheringu nie spełnia obu kryteriów jednocześnie (niebo ≤0,6 i asfalt ≥90% historycznego 5,28). Wybrano 0,75 jako WORKING_VALUE i usunięto końcowy dithering wyłącznie High, zachowując jawne rq_dither/rq_fsrsharp. Oddzielna ablacja bez dithera zachowała HF asfaltu 5,6757, a na czystym niebie obniżyła 0,636 do 0,1357. Liczby pochodzą z oryginalnych PNG, nie JPEG. Końcowa ocena bandingu pozostaje do oględzin, a telefon do lidera.

Niebo clear: proceduralną próbę odrzucono po oględzinach z powodu wielkich płaskich białych plam. Wybrano fotograficzną maskę cumulus i względną luminancję z Poly Haven kloofendal_48d_partly_cloudy_puresky (CC0, autorzy Greg Zaal / Jarod Guest; docs/LICENSES.md i ClearCloudsSource.json). To ogólna tekstura nieba, nie zdjęcie Białegostoku. PNG liniowy RG 4096×2048, mipmapy, ASTC6×6 Android. Nowe pole danych LightingPreset.clearCloudCover=1 tylko Clear; inne presety domyślnie 0. Jeden odczyt tekstury w istniejącym przebiegu skybox, bez nowego efektu ekranu. Model radiancji, pomiar EV, SH i natężenie słońca pozostają analityczne: wizualne uproszczenie, nie symulacja pogody.

Orientacja mapy: obrót azymutu, potem różnica elewacji; test zapobiega przechyleniu horyzontu przez samo wyrównanie słońc. W v2 znaleziono pionowy szew pochodnych U na zawinięciu lat-long. W v3 jawne zawinięte gradienty UV usunęły szew w tym samym natywnym wycinku. Wykonano 15/15 PNG v3 na Low i High.

Biel: porównanie 1,2/1,8 potwierdza rzeczywisty parametr po renderze. ROI furgonetki hall4 300×100 przy 1250,570: maksimum RGB 250/250/250 → 245/244/245; udział poszczególnych kanałów ≥250: 73,82/73,82/64,80% → 0/0/0%. ROI obejmuje też okna, nie jest maską lakieru. Szczyt house2 średnia R 234,664 → 229,591. Clear lookWhiteClip=1,8 WORKING_VALUE; EV bez zmian, kotwice krzywej do 0,18 pozostają stałe (test).

Cienie: 20/20 PNG ablacją filtrów Low/Medium/High, bliższych podziałów i atlasu 4096. Filtr High wygładza falistość, lecz zmiękcza krawędź; atlas 4K nie został włączony. Niezależny przegląd 43 PNG potwierdza poprawę, ale nie próg 10 m ani GPU. Wprowadzono addytywny flagą danych LightingPreset.highSunShadowFilter=3 wyłącznie LP_LowSun; EnvironmentLighting stosuje go tylko High. Inne presety/tiery resetują do dziedziczenia pipeline. Nie ma nowego pola QualityProfile ani zmiany jego danych. Potwierdzenie produkcyjnej polityki 8/8 PNG z kontrolą rzeczywistego filtru Low→High. Pierwszy crop metryczny był poza krawędzią, więc nie zgłaszam spełnienia metryki 10 m. Zachowano log znanego błędu sprzątania Mono dopiero po pełnym wyniku 20/20, zgodnie z wyjątkiem istniejącego visual-qa.ps1; nie mylić z awarią renderowania.

Walidacja po ostatniej zmianie: EditMode 264/264 (artifacts/tests/editmode-20261111-235211.xml). Pełny GIS i analiza SBS oczekują na heavy; nie zgłaszam ich PASS. Regeneracja bazowego świata dała zmiany raportów/generated spoza light; patch zachowano w artifacts/light-r1/generated-baseline-rebuild.patch i nie włączono tych plików do commitów produkcji light. Po testach wrócą do bazy przed scaleniem aktualnego main w r2.

Dowody SBS: 160/160 przed i 160/160 po, te same świeżo wygenerowane geometria i pozy. Stan przed jest kontrolowanym odtworzeniem dawnych parametrów, nie historyczną geometrią. 40 póz × Low/High × clear/overcast; tylko 27 dziennych póz dopuszczono do podsumowania ROI po wykluczeniu 6 błędnych i 8 zachodów (jedna wspólna). Pozy nadal WORKING_VALUE. Źródła sbs_references/sbs_cameras bez zmian. Analiza i galerie ≤960 px czekają w heavy.

Low: brak nowego przebiegu, zmiany skali, geometrii i liczby instancji. Koszt GPU dodatkowych obliczeń nieba na A16 pozostaje UNVERIFIED; urządzeń używa lider.

Komin na photo-biezenstwa-ground: uwaga przekazana w tym ADR i przyszłym REPORT właścicielowi landmarków. Nie zmieniam rotacji instancji. Pieprz ścian jest przypisany w recenzji do shadera ścian; nie maskuję go globalnym rozmyciem.

Przewidywane styki integracji: addytywna polityka High w QualityProfileApplier, presety LightingPreset i Sky.shader. ProjectSettings, Packages, sceny i pliki pozostałych dziedzin pozostają poza zmianą.
