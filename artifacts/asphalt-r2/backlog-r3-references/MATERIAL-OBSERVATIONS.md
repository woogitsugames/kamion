# Oględziny materiału do przyszłej rundy 3

Obejrzano oryginalny plik fotografii PCRT (SHA1 zgodny z Commons API), jego natywny wycinek 960x432 bez skalowania oraz pełny podgląd. Widać kostkę o zazębiających się, falujących konturach w regularnych rzędach. Spoiny są ciemniejsze, lecz mają umiarkowany kontrast; obraz nie przypomina mocnej czarnej siatki. Są drobne różnice tonu i lokalne ślady, bez mocnego dowodu na duże kontrastowe mokre wyspy w tym fragmencie.

Powierzchnia wygląda spokojnie: brak dominującego jasnego kruszywa i ostrych refleksów. Nie można oddzielić wpływu materiału, zachmurzenia, ekspozycji i obróbki, więc fotografia nie wyznacza albedo ani roughness. Farba zachowuje podziały kostki i ma miejscami nieregularne krawędzie.

Niezależny visual-critic potwierdził te obserwacje. Zalecił zbadać rodzinę kostki, kontrast spoin i wielkie plamy, a jako ryzyko wskazał przeniesienie jednego fragmentu na cały region lub wspólny materiał. Brak PASS: nie ma dopasowanego renderu, pozy kamery ani zweryfikowanego zasięgu całego placu. R2 nie jest częścią tej oceny. Wyłącznie referencja, bez wykorzystania jako tekstury albo kopiowania logo.

Źródło fotografii: Rakoon, 2020-07-11, CC BY 3.0; pełne URL, licencja, SHA i zakres wycinka w pcrt-ground-native-960-source.json. Źródło niezależnej oceny: asphalt_visual_critic, read-only, 2026-11-12.

## Kontrola aktualnej tekstury przed r3

Odczytano sets_scan.py i materials_spec.json: behaton_i_grey korzysta z Poly Haven concrete_pavers (Amal Kumar, CC0 1.0), deklarowane pole1,92×1,92m. Obejrzano rzeczywisty High/BaseColor1024×1024 obok natywnego wycinka PCRT. Tekstura ma zazębiające się kostki typu I, więc sama rodzina konturu jest zgodna z ogólną obserwacją fotografii; nie ma podstaw, by z nazwy skanu wywodzić konieczność zmiany zestawu. To nie potwierdza rozmiaru/orientacji/mapowania na placu ani jego materialID.

Na albedo widać duży kontrast niektórych spoin i drobne jasne rysy/ziarno. Fotografia w perspektywie ma spokojniejszy detal, ale jej skala, światło i ekspozycja są inne. Nie wyciągamy z tych dwóch plików liczbowego mnożnika albedo/normal/roughness. Świeży baseline r3 i zbliżenie rzeczywistego placu pozwolą rozdzielić bazową teksturę, brud GRIME i oświetlenie. SHA pliku obejrzanego w r2 zapisano osobno; po merge należy go ponownie sprawdzić.

## Możliwa rozbieżność danych nawierzchni — do zbadania

Lekki odczyt449KB streetscape_sources.json znalazł jeden obrys BDOT PTPL, którego bounding box przecina okolice sąsiednich geotagów. Ma materialnawierzchni „masa bitumiczna”, czyli paved.py mapuje ten rodzaj wejścia na yard_asphalt. Nie znaleziono nazwanego PCRT w osm.areas. Sam test przecięcia prostokątów nie identyfikuje placu i nie jest point-in-polygon. Zdjęcie3 nie ma GPS; fotografie1/2 pokazują uliczny kontekst, więc nie przesądzamy, czy ten obrys obejmuje fotografowany bruk. Możliwy konflikt zdjęcia z materiałem danych wymaga sprawdzenia świeżego GLB, obrysu, sąsiednich hal i miejsca zdjęcia. Nie naprawiać go globalną zmianą całego yard_asphalt ani edycją geometrii/override Claude. ID i SHA odczytanego źródła w source-surface-precheck.json.
