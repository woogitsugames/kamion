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
