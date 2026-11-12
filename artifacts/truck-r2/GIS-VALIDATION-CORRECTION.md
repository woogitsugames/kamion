# Ograniczenie odczytane podczas przygotowania rundy 3

Rzeczywisty wynik rundy 2 pozostaje 575 passed, 1 failed, 1 xfailed, 657,56 s. Jednak po przygotowaniu bazy, a przed końcowym GIS, przywrócono world_manifest.json do wersji gałęzi. W prywatnym katalogu ignored pozostawał wygenerowany świat. Test test_export_is_deterministic porównuje zapisany manifest sprzed własnego builda z nowym buildem, więc przywrócenie starszego manifestu mogło spowodować tę porażkę.

Nie ustalono przyczyny różnicy chunk 0_0 i nie wykonano ponownego pełnego GIS poza końcem rundy. Występowanie tej samej nazwy błędu w r1 nie potwierdza, że jest to trwały błąd generatora ani że walidacja świeżej regeneracji r2 była poprawna. Wynik nie jest dowodem regresji shaderu truck. W r3 świeży manifest zostanie zachowany do końcowego GIS; generated innych dziedzin nadal nie trafią do commitów i zostaną cofnięte po konsumentach oraz testach.

To uzupełnienie ograniczeń dowodu, bez zmiany historycznego logu, wyniku ani sumy oryginalnie przekazanego REPORT. Powstało na gałęzi gpt-truck-r3 po przekazaniu r2.
