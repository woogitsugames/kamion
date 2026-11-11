# Kabina r2 — praca w toku, bez zgłoszenia do scalenia

Gałąź gpt-cab-r2, start od r1 a8651008 i merge aktualnego main bez konfliktów. Poprawki K1–K3 pozostają w baseline. Nie scalano do main, nie pushowano i nie używano telefonów.

Zapisano i obejrzano 28 kadrów Low/High × clear/overcast, sześć natywnych odbić w każdym stanie oraz pełne 78 kamer Low/Gate3. High overcast zapisało komplet siedmiu kadrów; wrapper visual-qa zaakceptował znany błąd przy zamykaniu Mono zgodnie ze swoją ścieżką ADR 0083. Nie opisujemy tego jako niezależnie czystego zamknięcia Unity. Natywny audyt tego stanu zakończył się osobno.

Dodano konwerter Brown Leather (Rob Tuytel / Poly Haven, CC0), manifest plików z hashami oraz wyłączoną flagę integracji. Raw pozostają ignorowane. Gotowy materiał ma zachować istniejące rozmiary map 1024/512/256 i kanał perforacji. Kandydat czeka na slot heavy, nie został jeszcze przetworzony ani zintegrowany. Źródło skóry nie jest skanem tworzywa deski.

Korekta UV obręczy 5 cm→12 cm jest pod tą samą wyłączoną flagą. Trzy testy EditMode zaliczone: skala fizyczna, nietknięte UV piasty/AO/innych materiałów oraz odrzucenie niejednoznacznych granic. Walidacja na rzeczywistych trzech LOD pozostaje przed nami. W audycie powierzchni przywracamy teraz oryginalne referencje siatek przed zniszczeniem kopii.

Do wykonania: przetworzenie i kontrola map pod heavy gpt-cab-r2, rzeczywiste kadry materiału, diagnoza K4 i czytelność zużycia K6, dalsza ocena prześwitów K5, budżety wszystkich kamer przed/po i końcowe testy. Pełny GIS dopiero przy zamknięciu rundy. Przewidywane konflikty: addytywny fragment TruckAssetBuilder.cs; reszta plików należy do wnętrza kabiny. Nie zmieniano shaderów szyb ani zewnętrza.
