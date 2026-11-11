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
