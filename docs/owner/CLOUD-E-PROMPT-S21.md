# Zlecenie dla sesji Claude Code w CHMURZE „E” (do 5 agentów, Fable dozwolony), s21, 15.11 wieczór

Wklej:
```
Repo GitHub woogitsugames/kamion (Kamion: mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1). Jesteś w chmurze: NIE masz Unity, telefonów ani Data/raw. Masz do 5 agentów (możesz używać Fable); każdy robi jedno zadanie na swojej gałęzi od origin/main. Subagenci nie tworzą subagentów. Lider (sesja lokalna) jest jedynym integratorem main: skompiluje w Unity, wyrenderuje, zmierzy na telefonie i scali. Ty NIE scalasz.

NAJPIERW przeczytaj: CLAUDE.md, docs/owner/AGENT-RULES.md, HANDOVER.md (blok „SESJA 21” na dole), docs/owner/BACKLOG-S21.md (Top 15), docs/03 (etapy i bramki), docs/11_DECYZJE_WLASCICIELA.md, oraz dokumenty dziedzinowe dla swojego zadania (docs/04 fizyka, docs/08 audio, docs/10 architektura, docs/LICENSES.md).

Uruchamiasz tylko to, co działa bez Unity: `dotnet test` dla tools/physics-runner (i innych projektów .NET w repo), `uv run --project tools/worldgen python -m pytest tests/gis -k <wybrane>`, `cd tools/audio; uv run python ...`. Kodu C# gry nie skompilujesz w Unity: pisz ostrożnie, dodaj testy EditMode/PlayMode, a w raporcie podaj DOKŁADNE komendy dla lidera (`pwsh scripts/test.ps1 -Platform EditMode`, build, visual-qa, pomiar na telefonie).

NIE dotykaj (inni pracują): ProjectSettings/, Packages/, asmdef, wspólnych scen i prefabów; generatora dróg regionu C i budżetu trójkątów (lokalny budget-fix-s21, ADR 0221); tunelu (0211); latarni Knyszyna (0216); Ełckiej/placu budowy dk65-05/06 (#80); Knyszyna Rynek (Codex, 0227); szpalerów, toru wzdłuż DK65, narzędzia szwów, recenzji research i #93 (chmura D, 0222–0226); folderu research/codex-refs-s21 (Codex). Nowe ADR: E1=0228, E2=0229, E3=0230, E4=0231, E5=0232.

E1 przegub i jackknife (gałąź jackknife-0228; BACKLOG B-077, bramka 2): brak kontaktu ciągnik–naczepa przy złożeniu ≥ 90°, samokolizja, prawie sprężyste lądowanie. Zaprojektuj i zaimplementuj w kodzie fizyki: ogranicznik kąta przegubu jako fizyczny kontakt (zderzak kabiny/błotnika z przodem naczepy z geometrii z docs/07 i danych pojazdu), tłumienie uderzenia, brak eksplozji solvera; restytucja i sztywności z uzasadnieniem (SOURCED/WORKING_VALUE). Scenariusze w tools/physics-runner: złożenie 90°, 120°, cofanie z kontrą, upadek z 0,5 m; kryteria liczbowe w ADR. Zero alokacji GC w pętli fizyki.
E2 wybór regionu w buildzie (gałąź region-select-0229): APK zawiera dziś tylko Boot, DrivingLab i WorldC (BuildCommands bierze EditorBuildSettings). Przygotuj: (a) w Game.Editor.Build.BuildCommands opcjonalną listę scen regionów (parametr `-Regions c,dojlidy,dk65-01,...,knyszyn` albo plik Data/build_regions.json) BEZ zmiany EditorBuildSettings w gicie; (b) w menu runtime wybór regionu/trasy budowany w kodzie (bez edycji sceny Boot w YAML), start ciężarówki w punkcie startu trasy z danych regionu (*_route.bytes w CabDisplay/Nav); (c) testy EditMode. Oszacuj rozmiar APK i RAM na region z plików _Generated (w raporcie, ESTIMATED). Lider sprawdzi na A16.
E3 legalność i atrybucje (gałąź legal-0230; B-131, B-065): domknij docs/LICENSES.md i ekran „Informacje” (docs/owner/ATTRIBUTION-SCREEN-DRAFT.md, raporty LICENSES-AUDIT-S20 i BRAND-SWEEP-S20): status licencyjny Danych Miasta Białystok (cytuj regulamin/licencję portalu; jeśli brak, opisz ryzyko i zaproponuj zamiennik z OSM/GUGiK), atrybucje BDL, Mapillary, KartaView, Panoramax, OSM ODbL; pozostałe nazwy marek w JSON-ach i kodzie gry (poza research/) zamień na neutralne, jeśli nie są w obszarach zakazanych wyżej. Tekst ekranu jako dane (JSON/Resources), testy.
E4 następny pierścień regionów, wersja „z grubsza” (gałąź ring-0231; D63, docs/owner/S20-REGION-RING-BRIEF.md, PR #66 R9): zdefiniuj kolejne kafle za Knyszynem i wokół Mońki/Tykocin (wpisy w tools/worldgen regions.py, bbox, drogi przelotowe, overrides w stylu ADR 0205/0209/0212/0214), z testami definicji na danych w gicie. Nie zmieniaj istniejących wpisów regions.py. Komendy build_world/import dla lidera w raporcie.
E5 dźwięk silnika i układu (gałąź audio-0232; docs/08, B-098): w tools/audio (uv) popraw warstwowy dźwięk sterowany fizyką: obroty/obciążenie, turbo, hamulec silnikowy/retarder, pneumatyka, przełożenia AMT; wyrenderuj WAV-y A/B (stary vs nowy, te same scenariusze z telemetrii) do artifacts/audio-0232/ z opisem, co słuchać. Bez nagrań producentów i bez cudzych marek; ElevenLabs/Suno nie używaj. Właściciel oceni odsłuch.

ZASADY: commit i push po każdym kroku; nie zmyślaj liczb (źródło, ESTIMATED albo WORKING_VALUE); bez Google Maps, Street View, Earth i 3D Tiles; bez marek i logo; nagłówki HTTP bez nazwy projektu; stopka commitów zgodna z modelem. Na koniec każdego zadania PR (nie draft) z raportem do 20 linii po polsku:
- co zmienione;
- testy uruchomione i ich wynik;
- testy NIEuruchomione;
- DOKŁADNE komendy dla lidera;
- co otwarte;
- „Gotowe do scalenia po weryfikacji lidera: TAK/NIE”.
NIE scalaj. Na końcu podsumowanie z numerami PR.
```
