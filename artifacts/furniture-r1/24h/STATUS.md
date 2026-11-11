# Sesja 8 — furniture, r1 (ADR 0120)
Start 24 h: 2026-11-11, około 21:30 czasu Warszawy. Koniec: 2026-11-12, około 21:30.
Odczytano instrukcję 05, HANDOVER s10, CLAUDE, AGENT-RULES, anti-slop, budżety, decyzje D48–D50, recenzje HIL/0102-self i feedback s10.
Istniejący czysty worktree gpt-furniture-r1 przeniesiono na gpt-furniture; gałąź była w całości na main, więc wykonano fast-forward do 5f2aa277. Nie zmieniono main.
Skopiowano derived, cc0, cc0/_raw, megascans, _Generated; zachowano junctiony surowych referencji; git lfs checkout OK. Dawne dowody ADR 0102 pozostają w katalogu nadrzędnym, nowe dowody w 24h/.
Cel: podmurówka i deformacje siatki, rozpoznawalny słup betonowy, korozja uchwytów znaków. Bariery i geometria dróg poza zakresem.
NASTĘPNY KROK: uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c

21:33: generator baseline przerwany przed startem: stara .venv bez interpretera. Zachowano jako .venv.pre24h-invalid; uv odtwarza środowisko. NASTĘPNY KROK: powtórzyć build_world.

21:37: przygotowano ADR 0120 i runner Unity z acquire/release także przy błędzie. Przejrzano arkusz Commons: ogrodzenia przemysłowe i wyposażenie, bez dowodu dokładnego typu bocznych lamp. NASTĘPNY KROK: po build-before uruchomić pwsh artifacts/furniture-r1/24h/unity-step.ps1 -Step import -Phase before.

2026-11-11T21:37:11.6591530+01:00: opracowano izolowany wariant panel_candidate.py: krótsze przęsła na skarpie, szczeliny desek, odchylenie boczne siatki. Kod produkcyjny nietknięty do końca baseline. NASTĘPNY KROK: sprawdzić wzrost liczby trójkątów oraz zastosować po baseline.

2026-11-11T21:37:50.6953790+01:00: zmierzono kandydat na 15 m granicy (płasko, 10%, 40%); candidate-measurements.json. To test syntetyczny, nie wynik kamer ani telefonu. NASTĘPNY KROK: baseline import i pomiar rzeczywistych kadrów.

2026-11-11T21:38:53.2777977+01:00: kandydat zmniejsza syntetyczną odsłoniętą podmurówkę na spadku 40% z 1,20 do 0,447 m; 130→442 trójkąty na 15 m, trzy te same materiały. Zapisano odtwarzalny apply_r1.py, jeszcze nie uruchomiony. NASTĘPNY KROK: zakończyć baseline przed modyfikacją produkcji.

2026-11-11T21:40:32.2821582+01:00: kandydat tekstur zachowuje skan CC0, wzmacnia jego kontrast tylko na betonie i lokalizuje zacieki pod obejmami. Tył aluminiowego znaku otrzyma ślady od stalowych mocowań. NASTĘPNY KROK: zastosować apply_r1.py dopiero po baseline i zachowaniu produktów A/B.

2026-11-11T21:41:57.1901850+01:00: proponowane moduły przeszły kompilację i uruchomienie generatorów tekstur w izolowanej kopii; obejrzano wear-candidate.jpg. Dodano dwie kamery diagnostyczne w pliku dowodów (stopa betonu i obejmy), bez zmiany scen. NASTĘPNY KROK: import baseline, następnie pełne rendery A/B.

2026-11-11T21:42:55.8726766+01:00: odróżniono raporty ADR 0102 od nowej rundy. Raport nadrzędny oznaczony W TOKU, stary zachowany w legacy-0102. NASTĘPNY KROK: import baseline po zakończeniu generatora.

2026-11-11T21:45:03.7710219+01:00: dodano dwa przypadki regresji HIL. Na niezmienionym baseline oba zawodzą zgodnie z odtworzonymi problemami (pytest-review-red.log). NASTĘPNY KROK: po baseline zastosować zmianę i potwierdzić zielony wynik.

2026-11-11T21:45:38.4852512+01:00: przygotowano snapshot_geometry.py do porównania payloadów siatek poza meblami i kolizją własnych płotów. Pliki licencjonowane nie są kopiowane do gita; dowód zawiera tylko hashe. NASTĘPNY KROK: uv run --project tools/worldgen python artifacts/furniture-r1/24h/snapshot_geometry.py before po zakończeniu build-before.

2026-11-11T21:46:30.5137718+01:00: izolowany kandydat przeszedł 11 testów mebli (pytest-candidate.log), w tym oba czerwone przypadki HIL. Snapshot obejmuje także materiały barier i ekranów w węźle furniture. NASTĘPNY KROK: import baseline i zastosowanie kandydata produkcyjnie po zakończeniu generatora.

2026-11-11T21:51:05.1405616+01:00: sprawdzono katalog roboczy runnera i poprawiono liczbę poziomów ścieżki przed pierwszym Unity. Baseline przeszedł geometrię dróg, budynki i nawierzchnie; obecnie generuje wyposażenie. NASTĘPNY KROK: zakończyć baseline i cache PBR, następnie acquire/import.

2026-11-11T21:55:25.7113057+01:00: baseline build exit=0, brak fallback=True. Pierwszy snapshot zatrzymał się na jawnym stride glTF; poprawiono czytanie accessorów, bez modyfikacji produktów. Zapisano hashe i zastosowano zmiany w czterech plikach mebli. Testy mebli exit=0. NASTĘPNY KROK: import i render baseline przed generatorem po zmianach.

2026-11-11T21:57:32.3902640+01:00: przegląd kodu wykazał wspólną teksturę betonu słupa i cokołu. Oddzielono atlas cokołu od brudnej dolnej strefy słupa, aby nie pogłębiać I3. Addytywny alias furniture_footing w materials.py, bez nowych slotów. Testy mebli exit=0. NASTĘPNY KROK: sprawdzić render cokołu oraz koszt dodatkowej tekstury po imporcie.

2026-11-11T21:58:10.5042450+01:00: odbudowa cache PBR zakończona kodem 0, log pbr-before.log. NASTĘPNY KROK: sprawdzić brak brakujących plików przed importem baseline.

2026-11-11T22:00:47.0873077+01:00: promień próbkowania podparcia starej betonowej lampy dopasowano do nowej podstawy 0,15 m. Import baseline czeka na slot (4/4); nie uruchomiono Unity poza protokołem. NASTĘPNY KROK: zakończyć import baseline i render czterech wariantów.

2026-11-11T22:02:01.6553961+01:00: zapisano prototype-cost.json z licznikami geometrii i slotów przed/po względem 5f2aa277, oraz atlas cokołu do oględzin. To liczby generatora, nie GPU. NASTĘPNY KROK: import po przydzieleniu slotu i pełna walidacja kadrów.

2026-11-11T22:03:47.8638782+01:00: przygotowano compare_frames.py: wszystkie kamery, osobne draws siatek i instancji, konserwatywna granica kwantyzacji trisK, arkusze ≤960 px. NASTĘPNY KROK: uruchomić po kompletnych renderach before/after; obejrzeć każdy arkusz.

2026-11-11T22:10:23.4376323+01:00: niezależny review wykrył limit .35 m na krótkiej skarpie i rozjazd korozji A-7. Usunięto próg długości podziału, poprawiono wspólny kontrakt UV/masek, czyste obrzeża i tyły E-2. Dodano regresję krótkiej skarpy i UV pięciu kształtów; testy exit=0. NASTĘPNY KROK: import i rendery po zwolnieniu slotu; globalny budżet nadal niezweryfikowany.

2026-11-11T22:15:27.5786881+01:00: zapisano niezależny REVIEW-CODE.md i zabezpieczono jednorazowy apply_r1.py przed nadpisaniem poprawek review. Test rejestracji rdzy odczytuje UV wyeksportowanej geometrii i próbkuje atlas poniżej rzeczywistych obejm A-7/C-12; exit=0. NASTĘPNY KROK: finalne rendery i niezależny przegląd wyglądu.

2026-11-11T22:18:03.1109563+01:00: niezależny przegląd znalazł cztery dzienne referencje (reference-selection.json, arkusz). Brak potwierdzenia dokładnej rodziny okrągłego słupa; znak SBS 297817… nie pokazuje czytelnej rdzy, co ogranicza ocenę zużycia. Dodano osobny render referencyjny z właściwą proporcją kadru, osobny acquire/release. NASTĘPNY KROK: obejrzeć referencje i wykonać sbs-sign przed/po.

2026-11-11T22:21:03.0699120+01:00: PILNA ZMIANA PROTOKOŁU: każde ciężkie zadanie Pythona przez heavy-step.ps1 (pula heavy max3, owner=gałąź rundy), pełny GIS wyłącznie na końcu rundy. Baseline world i PBR zakończyły się przed tą zmianą, żaden ciężki Python tej sesji teraz nie działa. Runner importu sprawdza cache, aby nie uruchomić generatora bez heavy slotu. Nowy gate czytany z main, bez modyfikacji wspólnego skryptu w gałęzi. NASTĘPNY KROK: zakończyć oczekujący import baseline; przyszły build-after: pwsh artifacts/furniture-r1/24h/heavy-step.ps1 -Step world -Phase after.

2026-11-11T22:25:41.3503984+01:00: ADR uzupełniono o pulę heavy, stan 19 testów, niezmieniony koszt prototypów i otwarte ograniczenia referencji. Składnia wrapperów sprawdzona parserem PowerShell. NASTĘPNY KROK: kontynuować oczekujący import baseline; nie uruchamiać pełnego GIS w trakcie rundy.

2026-11-11T22:29:41.3553029+01:00: stary proces samego oczekiwania (PID 110476) zakończono przed zdobyciem slotu i przed Unity. Potwierdzono brak własnego Unity i własnego slotu. Wznawiam import z nowym preflight cache i aktualnym gate main; polling 10 s nie zmienia limitów 4/3. NASTĘPNY KROK: pwsh artifacts/furniture-r1/24h/unity-step.ps1 -Step import -Phase before.

2026-11-11T22:31:51.6272278+01:00: Unity import before Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-11T22:33:31.8590179+01:00: Unity render before Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-11T22:33:59.8509636+01:00: Unity render before Low clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-11T22:34:42.6890648+01:00: Unity render before High overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-11T22:35:11.1090844+01:00: Unity render before High clear; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-11T22:36:20.8888700+01:00: Unity sbs-sign before High overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.

2026-11-11T22:41:13.6655077+01:00: 4×55 baseline + 1 SBS zakończone. Dwie nowe kamery diagnostyczne wyznaczono błędnie ze starej wysokości: bieżąca instancja ma U141,573 zamiast założonego U143,973. Poprawiono wyłącznie te dwie pozy względem instancji i zachowano stare PNG/JSON w rejected-diagnostic-poses. Runner częściowy zachowuje statystyki pozostałych 53 kamer. NASTĘPNY KROK: ponowić tylko oba zbliżenia w czterech wariantach.

2026-11-11T22:41:41.2239928+01:00: Unity render before Low overcast; sukces=True. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG.
