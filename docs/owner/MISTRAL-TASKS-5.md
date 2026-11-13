# Zadania dla Mistral Vibe Code — runda 5 (s16, 2026-11-12)

Repo: `woogitsugames/kamion`. **7 sesji, każda dostaje jeden blok poniżej (skopiuj całość).** Środowisko jak w rundach 2–4: GitHub, bez Unity, telefonów i `Data/raw`, LFS widoczne tylko jako wskaźniki. Zadania wynikają z recenzji rundy 3 (`docs/reports/REVIEW-2026-11-12-s15-mistral-r3.md`, „Osobne zadania”) i z otwartych punktów ADR 0132, 0141, 0144, 0150. Runda 4 (M21–M25, PR #21–#25) jest w integracji na gałęzi `mistral-r4-int` — nie powtarzaj jej.

**Wspólne zasady (są w każdym prompcie):** gałąź `mistral/<nr>-<nazwa>`, na końcu push gałęzi i jeden PR do `main` (nie draft) z raportem po polsku w opisie. **Po utworzeniu PR NIE śledzisz go: nie czekasz na CI, recenzję ani komentarze, niczego nie poprawiasz po fakcie — piszesz „M<nr> gotowe, PR #<numer>” i kończysz sesję.** Nie pushujesz na `main` i nie scalasz. Nie zmieniasz `Data/**/generated/**`, `*.glb`, `*_meta.json`, `game/ProjectSettings/**`, `game/Packages/**`, `.gitattributes`, LFS, `.asmdef`. Nie zmyślasz: liczba zmierzona, zacytowana (z paragrafem/stroną) albo `UNVERIFIED`. Źródła wtórne (blogi, kalkulatory) nie potwierdzają przepisów. Zakaz Google Maps, Street View, Earth, 3D Tiles. Nie uruchomisz Unity — kod C# pisz starannie (przestrzenie nazw jak w istniejącym kodzie); lider skompiluje i uruchomi testy.

---

## M26 — audio: test oktawy, który łapie stary błąd `comb_estimate`

```
Repo woogitsugames/kamion. Pracuj na gałęzi mistral/26-audio-octave-test od main. Na końcu: git push gałęzi, jeden PR do main (nie draft), raport po polsku w opisie PR. Po utworzeniu PR NIE śledź go (nie czekaj na CI, recenzję ani komentarze) — napisz „M26 gotowe, PR #<numer>” i zakończ sesję. NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS, .asmdef. Nie zmyślaj.

Kontekst: recenzja rundy 3 (docs/reports/REVIEW-2026-11-12-s15-mistral-r3.md, „Osobne zadania” pkt 1): test tools/audio/tests/test_comb_octave.py przechodzi także na starej implementacji comb_estimate (tools/audio/el_analyze.py), więc nie chroni przed regresją błędu oktawy. Brak WAV w środowisku (LFS) — testy muszą działać na sygnałach syntetycznych.
Zadanie: (1) znajdź w historii gita (git log -p -- tools/audio/el_analyze.py) wersję comb_estimate sprzed poprawki oktawy; (2) napisz test(y) pytest na syntetycznych sygnałach, które PADAJĄ na starej wersji i PRZECHODZĄ na obecnej — np. harmoniczne z tłumionymi nieparzystymi, szum różowy + harmoniczne, f0 30–60 Hz typowe dla diesla na jałowym; (3) udowodnij to: uruchom testy przeciw starej funkcji (np. fixture importujący starą wersję z pliku pomocniczego w tests/ albo parametr) i wklej wynik obu przebiegów do raportu; (4) uv run --project tools/audio pytest — zielono. Raport: opis sygnałów, wyniki stara/nowa, czas testów.
```

## M27 — GPS: „Brak dojazdu” (Olsztyńska/Buska) + generator grafu w `build_world`

```
Repo woogitsugames/kamion. Pracuj na gałęzi mistral/27-nav-reachability — od origin/mistral-r4-int, jeśli ta gałąź istnieje (zawiera format KRTG v2 z rundy 4), w przeciwnym razie od main (napisz w raporcie, od czego). Na końcu: git push gałęzi, jeden PR do main (nie draft), raport po polsku w opisie PR. Po utworzeniu PR NIE śledź go (nie czekaj na CI, recenzję ani komentarze) — napisz „M27 gotowe, PR #<numer>” i zakończ sesję. NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS, .asmdef. Nie zmyślaj.

Kontekst: ADR 0150 (docs/adr/0150-map-minimap-gps.md): region przycięty do 2 km ma części połączone tylko poza kaflem (np. Olsztyńska/Buska, 55 węzłów) — gracz może wybrać tam cel i dostaje „Brak dojazdu”. Generator tools/worldgen/navgraph/build_route_graph.py nie jest wpięty w tools/worldgen/roads/build_world.py (lider uruchamia go ręcznie).
Zadanie: (1) w generatorze policz składowe spójności grafu (skierowanego — uwzględnij jednokierunkowe) i raportuj je (liczba węzłów/krawędzi, nazwy ulic); (2) oznacz w pliku grafu węzły/krawędzie spoza głównej silnie spójnej składowej jako „poza zasięgiem” (bez zmiany wersji formatu, jeśli da się użyć istniejącego pola/flagi; jeśli nie — wersja +1 z zgodnością wstecz w parserze Python i czytniku C#); (3) w C#: wybór celu tapem przyciąga do najbliższego węzła głównej składowej, a tap w części „poza zasięgiem” daje jasny komunikat po polsku zamiast „Brak dojazdu” (tekst krótki, w stylu obecnego HUD); (4) wepnij build_route_graph jako krok build_world (po eksporcie dróg, z flagą wyłączającą), bez uruchamiania pełnej budowy świata; test, że krok jest wywoływany (mock); (5) testy pytest (składowe na małym grafie testowym + na grafie regionu w repo, tylko odczyt) i EditMode NUnit (wzoruj się na NavRoutingTests). NIE regeneruj .bytes w repo (lider). Raport: liczby składowych, lista ulic poza zasięgiem.
```

## M28 — GPS: linia trasy po osi jezdni łącznicy, nie po osi OSM

```
Repo woogitsugames/kamion. Pracuj na gałęzi mistral/28-nav-route-axis — od origin/mistral-r4-int, jeśli istnieje, w przeciwnym razie od main (napisz w raporcie, od czego). Na końcu: git push gałęzi, jeden PR do main (nie draft), raport po polsku w opisie PR. Po utworzeniu PR NIE śledź go (nie czekaj na CI, recenzję ani komentarze) — napisz „M28 gotowe, PR #<numer>” i zakończ sesję. NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS, .asmdef. Nie zmyślaj.

Kontekst: ADR 0144 (docs/adr/0144-*.md, „Open”): na węzłach generator dróg przesuwa oś jezdni łącznic względem osi OSM (geometria w Data/Regions/<region>/generated/*.json — w repo, tylko do odczytu), a linia trasy GPS (tools/worldgen/navgraph/build_route_graph.py → mapa/minimapa) idzie po surowej osi OSM, więc na łącznicach rozjeżdża się z jezdnią widoczną w grze.
Zadanie: (1) znajdź w danych generated, gdzie jest finalna oś jezdni (polilinia po przesunięciach) i jak mapuje się na id drogi OSM; (2) zmierz przed zmianą: dla każdej krawędzi grafu maks. i średnie odsunięcie poprzeczne linii trasy od osi jezdni (m) — tabela top 10; (3) w generatorze grafu bierz geometrię krawędzi z osi jezdni z danych generated, gdy jest dostępna (fallback: oś OSM), bez zmiany topologii i długości używanych do kosztu A* (lub z uzasadnieniem, jeśli długość się zmienia); (4) test pytest: maks. odsunięcie < WORKING_VALUE (zaproponuj z pomiaru, np. 0,5 m) dla wszystkich krawędzi z dostępną osią. NIE regeneruj .bytes w repo (lider). Raport: tabela przed/po.
```

## M29 — bariery: wolne końce na pomostach i podwójne rzędy na edge-west

```
Repo woogitsugames/kamion. Pracuj na gałęzi mistral/29-barrier-ends od main. Na końcu: git push gałęzi, jeden PR do main (nie draft), raport po polsku w opisie PR. Po utworzeniu PR NIE śledź go (nie czekaj na CI, recenzję ani komentarze) — napisz „M29 gotowe, PR #<numer>” i zakończ sesję. NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS, .asmdef. Nie zmyślaj.

Kontekst: ADR 0144 („Open” pkt 3): 34 końce biegów barier na pomostach nie mają kontynuacji w 2,5 m (m.in. wiadukt Putry) — w grze widać luki przy wlotach na obiekt. ADR 0141 (P2): na krawędzi edge-west dwa rzędy zapór nachodzą na siebie ~2 m. Kod: tools/worldgen/roads/meshing.py, gores.py, standards.py, build_world.py (grep barrier); dane wyjściowe w Data/Regions/**/generated (tylko odczyt).
Zadanie: (1) skrypt/funkcja analizy na danych generated w repo: lista wolnych końców (brak kontynuacji ≤ 2,5 m) i nakładających się rzędów (równoległe < 0,5 m, wspólny odcinek > 0,5 m) z pozycją i id drogi; (2) przyczyna w generatorze i poprawka: ciągłość bariery z pomostu na dojazd (przejście), usunięcie zdublowanego rzędu; zakończenia, które naprawdę są końcem, wg przepisów o barierach (znajdź źródło pierwotne — np. Dz.U. 2019 poz. 2311 lub wytyczne GDDKiA dla barier — z cytatem i stroną; brak źródła = WORKING_VALUE); (3) pytest: liczby wolnych końców i nakładek z danych w repo jako xfail z aktualnymi liczbami (lider zregeneruje świat i zdejmie xfail) + testy jednostkowe poprawki na geometrii syntetycznej. NIE regeneruj świata. Raport: liczby przed, przewidywane po, lista 10 przykładów z pozycją.
```

## M30 — ogrodzenia: skośny panel `r16_drive_3`

```
Repo woogitsugames/kamion. Pracuj na gałęzi mistral/30-fence-drive-panel od main. Na końcu: git push gałęzi, jeden PR do main (nie draft), raport po polsku w opisie PR. Po utworzeniu PR NIE śledź go (nie czekaj na CI, recenzję ani komentarze) — napisz „M30 gotowe, PR #<numer>” i zakończ sesję. NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS, .asmdef. Nie zmyślaj.

Kontekst: ADR 0132 (docs/adr/0132-buildings-r9.md, l. ~38, ~55, ~197): przy wjeździe r16_drive_3 nadal widać skośny panel płotu ściany bocznej przy bramie (brama stoi już w narożniku; panel to płot sąsiada). Kod ogrodzeń działek w tools/worldgen (grep: drive, fence, plot, gate, r16 — poza .venv).
Zadanie: (1) znajdź kod budowy ogrodzeń i przypadek r16_drive_3 (dane wejściowe w repo, tylko odczyt); (2) ustal regułę, która tworzy skośny panel (np. panel boczny łączący narożnik bramy z płotem sąsiada pod kątem), i popraw ją ogólnie — nie wyjątek dla jednej działki: panel boczny prostopadły do frontu albo pominięty, gdy sąsiedni płot już zamyka bok (próg kąta/odległości jako WORKING_VALUE z uzasadnieniem); (3) pytest: na danych w repo policz panele odchylone od kierunku frontu/boku > 15° przed/po; test jednostkowy na geometrii syntetycznej; (4) sprawdź, że reguła nie psuje istniejących testów ogrodzeń/zabudowy (uv run --project tools/worldgen pytest tests/gis -q, część bez Data/raw). NIE regeneruj świata. Raport: liczby przed/po, lista dotkniętych działek.
```

## M31 — licencje: automatyczny audyt `docs/LICENSES.md`

```
Repo woogitsugames/kamion. Pracuj na gałęzi mistral/31-licenses-audit od main. Na końcu: git push gałęzi, jeden PR do main (nie draft), raport po polsku w opisie PR. Po utworzeniu PR NIE śledź go (nie czekaj na CI, recenzję ani komentarze) — napisz „M31 gotowe, PR #<numer>” i zakończ sesję. NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS, .asmdef. Nie zmyślaj.

Kontekst: CLAUDE.md zasada 8 — każdy zasób w docs/LICENSES.md; Fab/Megascans nigdy w gicie; zakaz Google Maps/Street View/Earth/3D Tiles; Suno free = brak praw komercyjnych. Ręczny audyt już był (docs/reports/AUDIT-LICENSES-2026-11-12-mistral.md, AUDIT-DOCS-2026-11-12-mistral.md) — NIE powtarzaj go; zamień go w automatyczny test, żeby nowe zasoby bez wpisu były wyłapywane same.
Zadanie: (1) skrypt Python (tools/licenses/audit.py lub podobnie, z uv/pyproject jak inne narzędzia) listujący ŚLEDZONE przez git zasoby (git ls-files: tekstury, audio, modele, fonty, HDRI, zdjęcia referencyjne; pomiń generowane przez kod — określ regułę i ją opisz) i sprawdzający, czy każdy jest pokryty wpisem w docs/LICENSES.md (ścieżka lub wzorzec); (2) testy: żaden śledzony plik nie pochodzi z Fab/Megascans (nazwy/ścieżki, metadane), brak plików z nazwami/ścieżkami wskazującymi Google; (3) uzupełnij brakujące wpisy TYLKO gdy źródło wynika z repo (ADR, commit, plik README obok zasobu) — z odnośnikiem; inaczej wpis „UNVERIFIED — do uzupełnienia przez lidera” z listą plików; (4) pytest zielony (brakujące jako xfail z liczbą). Raport: liczba zasobów, pokrytych, UNVERIFIED, podejrzanych.
```

## M32 — pętla jazdy: wdrożenie poprawek z audytu GC (poza HUD)

```
Repo woogitsugames/kamion (Unity 6 C#). Pracuj na gałęzi mistral/32-gc-audit od main. Na końcu: git push gałęzi, jeden PR do main (nie draft), raport po polsku w opisie PR. Po utworzeniu PR NIE śledź go (nie czekaj na CI, recenzję ani komentarze) — napisz „M32 gotowe, PR #<numer>” i zakończ sesję. NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS, .asmdef. Nie zmyślaj.

Kontekst: CLAUDE.md — zero alokacji GC w pętli jazdy. Statyczny audyt już jest: docs/reports/AUDIT-GC-2026-11-12-mistral.md (baza e0328ea4) — NIE pisz nowego raportu od zera; zweryfikuj jego znaleziska na obecnym main (część mogła zostać poprawiona) i WDRÓŻ poprawki. HUD/overlay jest objęty osobnym PR #22 (M23) — NIE ruszaj plików, które zmienia PR #22 (gh pr diff 22 --name-only).
Zadanie: (1) dla każdego znaleziska z AUDIT-GC poza plikami PR #22: czy nadal istnieje na main (plik:linia); uzupełnij tylko to, co audyt pominął, przeglądając game/Assets/_Project/** (bez Editor/, bez Tests/, bez plików PR #22): wszystkie Update/LateUpdate/FixedUpdate/OnAnimatorMove/kod wywoływany co klatkę (fizyka pojazdu, audio, kamera, ruch, świat/streaming, nawigacja) i znajdź alokacje: new tablic/list/obiektów klas, LINQ, konkatenacja/interpolacja stringów, lambdy z przechwyceniem, boxing (np. enum w Dictionary bez komparatora, params object[]), foreach po interfejsie, GetComponent/FindObjectOfType co klatkę, Debug.Log bez warunku, Physics.*All bez NonAlloc, Mesh.vertices/.normals (kopiują tablice); (2) tabela: plik:linia, rodzaj, częstotliwość (co klatkę / co krok fizyki / rzadko), szacowany koszt; (3) popraw pozycje „co klatkę/co krok” (prealokacja, NonAlloc, cache, struct enumeratory) bez zmiany zachowania; (4) testy EditMode/PlayMode z ProfilerRecorder „GC.Alloc” (nie GetAllocatedBytesForCurrentThread — w edytorze zwraca 0) dla poprawionych ścieżek — wzoruj się na istniejących testach w game/Assets/_Project/Tests/; jeśli kod jest czystym C# testowanym w tools/physics-runner, dodaj tam test. Lider uruchomi Unity i pomiar na telefonie. Raport: tabela przed/po, czego nie poprawiłeś i dlaczego.
```
