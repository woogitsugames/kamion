# Zadania dla Mistral — runda 7 (s16, 2026-11-13): 5 długich sesji

Repo `woogitsugames/kamion`. **5 sesji, każda dostaje jeden blok (skopiuj całość).** Model: Mistral Large 4. Wzór: M33/M34 (najlepsze wyniki). Wnioski z recenzji r6 (`docs/reports/REVIEW-2026-11-13-s16-mistral-r6.md`) są wpisane w zasady: kod, który ma się kompilować, MUSI być skompilowany i uruchomiony; w PR surowe wyjście komend, nie tabele z pamięci; każde „plik nie istnieje” poparte komendą.

---

## M39 — nawigacja: numer zjazdu z ronda tylko dla wylotów dostępnych + komunikaty głosowe

```
Repo woogitsugames/kamion (Unity 6 C#; nawigacja game/Assets/_Project/Core/Navigation/*.cs; testy bez Unity: tools/nav-runner, .NET 8). Gałąź mistral/39-nav-roundabout-voice od NAJNOWSZEGO origin/main. Zadanie na wiele godzin — rzetelność ważniejsza niż tempo; używaj subagentów, jeśli masz.

PRZECZYTAJ: CLAUDE.md, docs/reports/REVIEW-2026-11-13-s16-mistral-r6.md (sekcja M35 — co poszło źle: kod się nie kompilował, trasy wzorcowe nie z C#), docs/adr/0164-*.md, docs/owner/ELEVENLABS-GPS-VOICE.md, tools/nav-runner/**.
ZAKRES: (1) numer zjazdu z ronda liczy TYLKO wyloty dostępne dla ciężarówki (oneway, access, hgv, limity KRTG v2) — dziś liczy wszystkie; testy na rondach regionu (Putry, Pamięci Bieżeństwa) z oczekiwanym numerem ustalonym z danych grafu (wypisz krawędzie); (2) pasma komunikatów głosowych: dziś do 6 komunikatów na manewr — ogranicz do realistycznych (np. 2 km/1 km/500 m/„Teraz” zależnie od prędkości i odległości między manewrami), uzasadnij czasem reakcji i drogą hamowania ciężarówki 40 t (źródło lub WORKING_VALUE z rachunkiem); (3) ETA liczone co klatkę po całej trasie → przyrostowo (koszt O(1) na klatkę), zero GC; (4) trasy wzorcowe: każda nowa/zmieniona trasa nagrana z C# (`--write-golden`), nie ręcznie.
NIE ZMIENIAJ: Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS, .asmdef, plików .bytes.
WERYFIKACJA (obowiązkowa): A. zainstaluj .NET 8 SDK i uruchom `dotnet test tools/nav-runner` — wklej SUROWE wyjście (ostatnie 30 linii) do PR; B. test mutacyjny każdego nowego testu (tabela + surowe wyjście dla ≥ 3); C. niezależny przegląd subagentami albo 3 przebiegi od zera; D. tuż przed PR `git fetch && git rebase origin/main`, ponów A; `git diff --stat origin/main` surowo w PR; E. każde twierdzenie o pliku poparte `git ls-tree origin/main <ścieżka>`.
CIĄGŁY ZAPIS: commit + push gałęzi co ok. godzinę. ODDANIE: jeden PR do main (nie draft), raport po polsku. NIE pushuj na main, NIE scalaj. Po PR NIE śledź go — napisz „M39 gotowe, PR #<numer>” i zakończ.
```

## M40 — fizyka: tłumienie dobicia zawieszenia (odbicie 80 % przy zrzucie 1 m)

```
Repo woogitsugames/kamion (fizyka ciężarówki w C#, testy bez Unity: tools/physics-runner, .NET 8). Gałąź mistral/40-suspension-bumpstop od NAJNOWSZEGO origin/main. Zadanie na wiele godzin; rzetelność > tempo; subagenci mile widziani.

PRZECZYTAJ: CLAUDE.md, docs/04_*.md, docs/adr/0158-physics-airborne-energy.md (Open: zrzut z 1 m odbija prawie sprężyście — pierwszy apeks oddaje ~80 % energii spadku; tłumienie dobicia zawieszenia za małe), scenariusz tests/physics/scenarios/free_fall_drop_comb.json, kod zawieszenia w game/Assets/_Project/Vehicle/Physics/** (tylko czytaj, chyba że poprawka jest konieczna — wtedy minimalna i opisana).
ZAKRES: (1) zmierz energię odbicia przy zrzucie 0,3/0,6/1,0 m pusty i 40 t; (2) znajdź w literaturze (Gillespie, Bosch, dane katalogowe odbojów gumowych/poliuretanowych ciężarówek — źródło pierwotne ze stroną) typowy współczynnik restytucji / energii pochłoniętej przez odboje; (3) jeśli model nie ma charakterystyki odboju (bump stop) albo tłumienie przy dobiciu jest zerowe — zaproponuj i wdroż minimalnie (progresywna sztywność + tłumienie histerezowe), bez zmiany zachowania w normalnej jeździe (wszystkie istniejące scenariusze bez regresji — liczby przed/po); (4) checki w free_fall_drop_comb: odbicie ≤ WORKING_VALUE z uzasadnieniem.
NIE ZMIENIAJ: Data/**, *.glb, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS, .asmdef.
WERYFIKACJA: A. `dotnet test tools/physics-runner/PhysicsRunner.sln -c Release` i `dotnet run -c Release --project tools/physics-runner/Runner` — SUROWE wyjście (podsumowanie) przed i po w PR; B. test mutacyjny (usuń tłumienie odboju → FAIL; surowe wyjście); C. przegląd subagentami lub 3 przebiegi; D. rebase przed PR + ponów A; E. twierdzenia o plikach poparte komendą.
ODDANIE: PR do main (nie draft), raport po polsku; NIE śledź PR — „M40 gotowe, PR #<numer>” i koniec.
```

## M41 — walidator świata: precyzja i znane błędy (poprawki po recenzji M37)

```
Repo woogitsugames/kamion (walidator świata tools/worldgen/validate/ — Mistral M37; dane Data/Regions/bialystok-industrial-c/generated/*.json tylko do odczytu). Gałąź mistral/41-validator-precision od NAJNOWSZEGO origin/main. Zadanie na wiele godzin; subagenci mile widziani.

PRZECZYTAJ: CLAUDE.md, docs/reports/REVIEW-2026-11-13-s16-mistral-r6.md (M37: najwyższe błędy na trasie G3 były fałszywymi alarmami — tablice na bramownicach, latarnia niewygenerowana; 4 ściany terenu z ADR 0146 nieuchwycone; precyzja „100 %” się nie potwierdziła), docs/reports/visual/REVIEW-2026-11-13-s16b-final.md (aktualne prawdziwe błędy: 962702 bariera po złej stronie, 482392 zbędna ściana, horyzont, sygnalizatory 182011 itd.), ADR 0159, 0160.
ZAKRES: (1) wyeliminuj klasy fałszywych alarmów (obiekty nad jezdnią z założenia: bramownice, wysięgniki; obiekty niewygenerowane); (2) dodaj wykrywanie ścian terenu tak, by łapało 4 znane (ADR 0146 / raporty integracji: max 0,345 m); (3) dodaj kontrole dla błędów z krytyka (bariera po stronie kamery/jezdni — lico bariery vs kierunek ruchu; podwójne ściany/mury przy krawędzi); (4) zmierz precyzję na ≥ 30 losowych znaleziskach (sprawdź w danych) i czułość na liście znanych błędów — tabela.
NIE ZMIENIAJ: generatorów (tools/worldgen/roads/*, streetscape/*), Data/**, game/**.
WERYFIKACJA: A. `uv run --project tools/worldgen python -m pytest tests/gis -q -m unit` + testy walidatora — SUROWE wyjście w PR; B. test mutacyjny każdej kontroli (wstrzyknięty błąd → wykryty; surowe wyjście dla ≥ 3); C. subagenci lub 3 przebiegi; D. rebase + ponów A; E. twierdzenia o plikach poparte komendą.
ODDANIE: PR do main (nie draft), raport po polsku; NIE śledź PR — „M41 gotowe, PR #<numer>” i koniec.
```

## M42 — perfgate: historia bramek i odrzucanie nieważnych pomiarów

```
Repo woogitsugames/kamion (narzędzie tools/perf/ — Mistral M38 „perfgate”; pomiary z telefonów w artifacts/gate3/**, artifacts/device/**, artifacts/fold-flicker/** — sprawdź, co jest w gicie). Gałąź mistral/42-perfgate-history od NAJNOWSZEGO origin/main. Zadanie na wiele godzin; subagenci mile widziani.

PRZECZYTAJ: CLAUDE.md (zasada 2), docs/reports/REVIEW-2026-11-13-s16-mistral-r6.md (M38: naprzemienność z czasów klatek nie odróżniała przebiegu z błędem; dodano campose.py; warm-up z metrics.json), tools/perf/**, scripts/gate3-run.ps1, scripts/device-metrics.ps1, ADR 0136, 0152.
ZAKRES: (1) parser wyników `gate3-result.json` + logów gate3 (A16 13.11: G3-A/G3-B p95 33,4 ms, GPU p95 34,15/34,02 — artifacts/gate3/20261113-*); (2) zbiorcza historia bramek: tabela wszystkich pomiarów w repo (data, telefon, tier, APK, segment, FPS p50/p95/p99, GPU p95, PSS, thermal) + wykres trendu GPU p95 vs cel 33,3 ms; (3) automatyczne odrzucanie nieważnych pomiarów (telefon zablokowany/ekran wyłączony, bateria < 40 %, temperatura startowa > 36 °C, PHONE_RUN brak, Unity równolegle — z logów), z powodem; (4) porównanie przed/po z przedziałem ufności (bootstrap) jako CLI.
NIE ZMIENIAJ: scripts/*.ps1, game/**, Data/**.
WERYFIKACJA: A. pytest tools/perf — SUROWE wyjście w PR; B. ręczne przeliczenie (numpy, osobny skrypt) dla ≥ 3 prawdziwych pomiarów vs narzędzie — surowe wyjście; C. test mutacyjny metryk; D. rebase + ponów; E. twierdzenia o plikach poparte komendą.
ODDANIE: PR do main (nie draft), raport po polsku; NIE śledź PR — „M42 gotowe, PR #<numer>” i koniec.
```

## M43 — przepisy: oznakowanie i skrajnia dla ciężarówki (wsparcie regionu Dojlidy/Krywlany)

```
Repo woogitsugames/kamion (świat Białegostoku z OSM; parametry w tools/worldgen/roads/standards.py; nowy region Dojlidy/Krywlany — ADR 0166 w toku). Gałąź mistral/43-truck-clearance-standards od NAJNOWSZEGO origin/main. Zadanie na wiele godzin; subagenci mile widziani.

PRZECZYTAJ: CLAUDE.md, docs/reports/ROAD-STANDARDS-2026-11-13-mistral.md (M36), research/g10-truck-restrictions/README.md, research/gptpro/2-next-regions/README.md, docs/11_DECYZJE_WLASCICIELA.md (D60).
ZAKRES: (1) skrajnia pionowa i pozioma dróg (PTB 2022 Dz.U. 2022 poz. 1518 ze zm. 2025 poz. 1352 — paragraf, tabela, strona) dla klas dróg w regionie; wiadukty w obecnym kaflu (Putry, Andersa) — czy generator zapewnia wymagany prześwit (dane generated, tylko odczyt) — tabela; (2) znaki B-16/B-18/B-19/B-5 — wymiary i umieszczenie (Dz.U. 2019 poz. 2311 + zmiany) — porównanie z generatorem znaków; (3) wnioski dla regionu Dojlidy/Krywlany: jakie klasy dróg, jakie wymagania (ramp, łuków, pasów) mają wpływ na generator; (4) testy pytest (marker unit) z cytatem w docstringu; zmiany stałych tylko przy jednoznacznym przepisie.
NIE ZMIENIAJ: Data/**/generated/**, *.glb, game/**, .gitattributes, LFS. Źródła wtórne nie potwierdzają przepisów; uchylone akty = błąd (sprawdź status w ELI).
WERYFIKACJA: A. pytest gis -m unit — SUROWE wyjście w PR; B. ≥ 30 % cytatów sprawdzonych przez subagenta z otwartym PDF (lista); C. test mutacyjny; D. rebase + ponów; E. twierdzenia o plikach poparte komendą.
ODDANIE: PR do main (nie draft), raport po polsku; NIE śledź PR — „M43 gotowe, PR #<numer>” i koniec.
```
