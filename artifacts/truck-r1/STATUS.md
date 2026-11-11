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

Krok 7: przygotowano adapter diagnostyczny w art-source/truck/exterior/qa. Generuje tylko ignorowany kod edytora, zachowuje przywracanie materiałów i dodaje tymczasowy ciemny pigment oraz osobny katalog wyników. Jeszcze go nie aktywowano. Następny krok: po baseline uruchomić prepare_round_0115.py i cztery kontrole pigment/refleks.

Krok 8: zapisano procedurę czterech kontroli lakieru: biały/ciemny × odbicie włączone/wyłączone radiancyjnie, bez zmiany szorstkości podłoża. Adapter zachowuje kontrolę SHA produkcji i przywraca materiały w finally. Następny krok: pwsh artifacts/truck-r1/paint-controls.ps1 po baseline.

Krok 9: testy GIS bazowego worktree wykazały już niepowodzenia przed jakąkolwiek zmianą produkcyjnego kodu truck. Czekamy na pełne tracebacki, aby oddzielić stan wejściowy od regresji. Baseline graficzny nadal oczekuje na slot Unity. Następny krok: odczytać artifacts/truck-r1/gis.log po zakończeniu testów.

Krok 10: dodano atrybucję i licencje obu pomniejszonych zdjęć Commons. Jawnie opisano, że są odniesieniem do materiałów, nie tym samym pojazdem i kadrem. Pierwszy render nadal odtwarza cache/kompiluje skrypty. Następny krok: obejrzeć wynik Low-overcast.
Baseline Low overcast zapisany. Następny krok: obejrzeć PNG i zmierzyć lakier, szybę oraz DRL.

Krok 11: GIS zakończone: 488 passed, 5 failed, 1 xfailed w 1297,55 s. Błędy bazowe: far-field SHA, wiadukt różnica 3 mm przy tolerancji 2 mm, przeterminowany fidelity, brak prototypu plot_drive_gravel, deterministyczność chunk 0_0. Zapisano JSON-owy patch efektów ubocznych testów i przywrócono sześć wygenerowanych plików innych dziedzin. Obejrzano arkusz Low-overcast oraz ROI: górna szyba 21,46%, dolna 19,13%, profil drzwi 3,49 punktu. Następny krok: dokończyć baseline i uruchomić kontrole pigmentu.

Krok 12: przygotowano dodatkowy pełny zestaw wszystkich kamer Low/High overcast przed i po zmianie. Będzie służył do jawnego zestawienia rendererów i instancji każdej kamery, obok kadrów zbliżeń truck w obu pogodach. Następny krok: po baseline pwsh artifacts/truck-r1/all-cameras.ps1 -Stage before-all.
