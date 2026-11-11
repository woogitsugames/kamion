# Kabina r2 — praca w toku, bez zgłoszenia do scalenia

Gałąź gpt-cab-r2, start od r1 a8651008 i merge aktualnego main bez konfliktów. Poprawki K1–K3 pozostają w baseline. Nie scalano do main, nie pushowano i nie używano telefonów.

Zapisano i obejrzano 28 kadrów Low/High × clear/overcast, sześć natywnych odbić w każdym stanie oraz pełne 78 kamer Low/Gate3. High overcast zapisało komplet siedmiu kadrów; wrapper visual-qa zaakceptował znany błąd przy zamykaniu Mono zgodnie ze swoją ścieżką ADR 0083. Nie opisujemy tego jako niezależnie czystego zamknięcia Unity. Natywny audyt tego stanu zakończył się osobno.

Dodano konwerter Brown Leather (Rob Tuytel / Poly Haven, CC0) i manifest plików z hashami. Raw pozostają ignorowane. Pierwszy wariant skóry przetworzono pod heavy, exit 0; flaga integracji jest włączona. Sześć map zachowuje rozmiary 1024/512/256. Crop 614 px z pola 2048 px ma fizycznie 0,119921875 m. Kanał perforacji High porównano z oryginalnym obiektem LFS: AE=0. Obejrzane pary Low/High clear pokazują mniej regularne ziarno na obręczy i tapicerce; pełna walidacja rundy jeszcze trwa.

Korekta UV obręczy 5 cm→12 cm jest pod tą samą flagą skóry. Trzy testy EditMode zaliczone: skala fizyczna, nietknięte UV piasty/AO/innych materiałów oraz odrzucenie niejednoznacznych granic. BuildBatch i InstallBatch zakończyły się exit 0; na rzeczywistych LOD zmieniono UV 4278/862/623 wierzchołków mnożnikiem 0,416667, bez zmiany liczby wierzchołków i indeksów. W audycie powierzchni przywracamy teraz oryginalne referencje siatek przed zniszczeniem kopii.

K4: wariant AO bez mipów zakończył się exit 0 i nie zmienił widocznie smugi High clear. UV atlasu AO w centralnym rzutowanym obszarze: 170 trójkątów, minimum 314,41 texeli/m, mediana 577,12 texeli/m, p95 anizotropii 1,344. To pomiar geometrii bez testu okluzji i bez dokładnego wyboru części. Nie zgłoszono naprawy smugi. Przygotowano wyłączony profil ziarna tworzywa: rekonstrukcja tłoczenia oparta na skanie skóry, nie skan elementu deski. Crop 20 cm→kafel 10 cm i amplitudy są WORKING_VALUE; profil nie jest jeszcze przetworzony ani zintegrowany.

Do wykonania: ocena profilu tworzywa po kontrolnym World pod heavy, dalsza diagnoza K4 i czytelność zużycia K6, ocena prześwitów K5, budżety wszystkich kamer przed/po i końcowe testy. Pełny GIS dopiero przy zamknięciu rundy. Przewidywane konflikty: addytywny fragment TruckAssetBuilder.cs; reszta plików należy do wnętrza kabiny. Nie zmieniano shaderów szyb ani zewnętrza.
