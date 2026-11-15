# LK38 — kontrola mapowania kilometrażu do przejazdu DW671

Odczyt: 15.11.2026, czas Brukseli. **0 nowych dokumentów, 0 fotografii, 0 potwierdzonych węzłów OSM.** Manifest zawiera tylko nagłówek. To log konkretnej próby lokalizacji, bez pozornego zwiększania zbioru referencji.

Pełny słownik węzłów istniejącego K1 `data/osm_corridor.json` nie zawierał punktu w małym rejonie 53.289,22.882–53.295,22.889 ani poszukiwanego oznaczenia 038029522. Istniejąca ekstrakcja 05 ma tylko trzy przejazdy Fastów. Celowane przeszukanie lokalnego research pod literalne 038029522 i 038 029 522 również nie znalazło źródła. To ograniczenie zawartości zapisanych materiałów, nie dowód braku przejazdu w OSM.

Jedno celowane zapytanie Overpass zwróciło **HTTP 406**; nie ponawiano. Jeden zapasowy publiczny odczyt małego bbox przez API OSM zwrócił **HTTP 429**. Po 429 zatrzymano zapytania, bez zmian hostów, wariantów URL i automatycznych retry. Pełne zapytanie i statusy w `query-log.json` i `osm-api-log.json`.

Nie otrzymano żadnego węzła ani tagów, więc **nie potwierdzono ref 038029522, kilometrażu w OSM ani drogi ref 671 współdzielącej punkt przecięcia z torem**. Nie utworzono wniosku z samego podobieństwa numeru. Poszukiwany ciąg jest hipotezą roboczą z polecenia, nie odczytem naklejki ani tagu. OSM API nie jest Mapillary API; Mapillary oglądano wyłącznie w poprzednich rundach przez UI.

Urzędowy dowód rundy 6 pozostaje ważny w swoim zakresie: obwieszczenie z 18.11.2025, s.3/17 pkt 5, istniejący przejazd km 29+522 oznaczono kat. B w wykazie rozbiórek. **Powiązanie tego kilometrażu z DW671 i kadrami 2019 pozostaje UNVERIFIED.** Projektowany wiadukt 29+394 jest odrębnym zapisem. Nie zmieniono poprzednich pakietów ani kategorii fotografii.

Oficjalne wyszukiwanie nie dostarczyło nowego mapowania; niedozwolony mirror pozostawiono nietknięty. Wartości viewportu nie są GPS kamery, więc nie nadają się do brakującego przypisania FrameID→node. Nie dodano nowych zdjęć ani powtórki ogólnych norm A–D.
