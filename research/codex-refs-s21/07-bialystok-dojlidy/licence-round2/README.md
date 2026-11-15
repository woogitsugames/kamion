# „Drogi osie” — ponowne wykorzystanie wymaga dalszej oceny

Sprawdzenie: **15.11.2026, czas Brukseli (CET, UTC+1)**. Wynik: **LEGAL_REVIEW_REQUIRED** dla itemu `15cc2148e5074d8c88a1fd82a363e477`. Nie przypisano licencji CC ani zgody na przetwarzanie/redystrybucję geometrii. To wynik kontroli źródeł, nie rozstrzygnięcie prawne o niedopuszczalności użycia.

SOURCED [świeże metadane w `data/`]: item „Drogi osie”, właściciel `gis_umb`, organizacja `jN5LJsqeW33UjdlH`, jest publiczny; `licenseInfo=null`, `accessInformation` i `description` są puste. FeatureServer wskazuje ten sam `serviceItemId`, ma pusty `copyrightText`. Publiczne metadane organizacji podają nazwę **Urząd Miejski w Białymstoku**, ale nie zawierają warunków dla tego datasetu.

## Co rzeczywiście publikuje miasto

[BIP — ponowne wykorzystywanie informacji sektora publicznego](https://bip.bialystok.pl/urzad_miejski/dostep_do_informacji_publicznej/ponowne-wykorzystywanie-informac.html), sekcje „Warunki” i „Wniosek”, metryka aktualizacji **22.06.2026, 12:12**: miejskie warunki obejmują informacje publikowane w BIP, oficjalnych serwisach miasta i portalu danych. Wymagają oznaczenia źródła jako Prezydent Miasta Białegostoku, daty oraz określonego sposobu zachowania treści. Strona opisuje też tryb wnioskowy, gdy warunki informacji udostępnionej w innym systemie nie są ustalone. Nie wymienia konkretnego itemu ani usługi „Drogi osie”.

Odczytano pełne [zarządzenie 973/21 z 08.12.2021 — dostępny DOCX](https://bip.bialystok.pl/resource/187/Zarz%25C4%2585dzenie+973-21+ws+ustalenia+warunk%25C3%25B3w+ponownego+wykorzystania+informacji+sektora+publicznego+%2528do+odczytu%2529.docx) przy użyciu skilla `anthropic-skills:docx`, bez zapisu oryginału. SOURCED [§ 3]: poza atrybucją i datą wskazano zachowanie treści bez modyfikacji oraz oznaczanie fragmentów włączanych do większej całości. SOURCED [§ 6]: odrębnie opisano swobodę kopii, zmian i rozpowszechniania utworów/baz, do których Prezydent ma **prawa pierwotne**, oraz poszanowanie praw innych podmiotów i wskazywanie znanych twórców. **Nie wolno pominąć ani § 3, ani warunku praw pierwotnych z § 6.**

[Oficjalny GIS Białystok](https://www.gisbialystok.pl/), sekcje „Korzystanie z serwisu publicznego” i „Serwis publiczny”, opisuje oglądanie, drukowanie i zapisywanie zasobów oraz odsyła do miejskiego ArcGIS. Nie znaleziono tam warunków redystrybucji tego konkretnego FeatureServera. Możliwość technicznego eksportu innych warstw nie jest licencją „Drogi osie”.

## Brakujące powiązanie

Nie znaleziono jawnego oświadczenia łączącego **ten item** z określonym reżimem ponownego wykorzystania ani dowodu, że miastu przysługują prawa pierwotne do tej konkretnej bazy. Metadane instytucji potwierdzają wydawcę; nie rozstrzygają praw do danych i dopuszczalności ich zmian w generatorze. Nie oceniono, jak należy rozumieć relację § 3 i § 6 dla tego zastosowania — to część pozostająca do oceny.

Zachowano wcześniejszy status praw. Nie pobierano obiektów, geometrii, map, kafli ani eksportów; jedynie metadane `?f=pjson` oraz teksty miasta/BIP. Nie logowano się, nie wysyłano zapytań do urzędu i nie użyto ogólnych warunków platformy Esri jako licencji miasta.
