# Status sesji truck — runda 1
Start: 11 listopada 2026, 21:31 CET. Planowany koniec: 12 listopada 2026, 21:31 CET.
Przeczytano instrukcje właściciela, zasady projektu i recenzję 0087/0090. Worktree utworzono z main 5f2aa277.
Zakres: zewnętrze ciągnika TRAKT i naczepy. Bez scalania do main, pushowania i telefonów. Właściciel slotu Unity: gpt-truck.
Następny krok: skopiować lokalne zasoby według protokołu, wykonać git lfs checkout i zapisać baseline Low/High.

Krok 2: skopiowano derived, CC0, Megascans i _Generated; robocopy bez błędów, LFS 777/777. Junctiony surowych danych wskazują na main i są używane wyłącznie do odczytu. Kopiowanie Library trwa. Następny krok: pwsh artifacts/truck-r1/baseline.ps1 (każdy start Unity osobno pod slotem gpt-truck).

Krok 3: przygotowano procedurę baseline i ADR 0115. Obejrzano zdjęcia Commons: ciągnik użytkowy oraz lakier z odbiciami otoczenia. Library nadal się kopiuje; Unity jeszcze nie uruchamiano. Następny krok: pwsh artifacts/truck-r1/baseline.ps1.

Krok 4: Library skopiowano bez błędów (53144 pliki). Baseline czeka na slot 4/4; równolegle uruchomiono wymagane testy GIS. Przygotowano jawne prostokątne ROI oraz arkusze przed/po do 960 px. Następny krok: uv run --project tools/worldgen python artifacts/truck-r1/measure.py before (po renderze).

Krok 5: zapisano SHA-256 shaderów, TruckLights i wszystkich źródłowych FBX zewnętrza/naczepy przed zmianami. Baseline nadal w kolejce Unity, bez uruchomienia poza blokadą. Następny krok: po zapisaniu baseline zmierzyć ROI i poprawić zgodność FragFast.

Krok 6: przed pierwszym startem Unity poprawiono wybór sceny: High używa WorldC_High, Low WorldC. Zatrzymano wyłącznie własny proces czekający na slot i wznowiono kolejkę. Następny krok: pwsh artifacts/truck-r1/baseline.ps1.
