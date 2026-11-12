# Uzupełnienie przygotowania r3

AKTUALIZACJA: hipoteza pełnych pasów co 15 m poniżej została ODRZUCONA do wdrożenia.
Dokument ENEA i zdjęcie wykonawcy zbadane później podważają skalowanie fotografii
z samego podanego GPS. Najpierw rozwiązać pozę; patrz ostatnia sekcja.

Najpierw zakończyć r2. To analiza referencji, bez zmian kominów ani plików life.
Niniejsza notatka koryguje NEXT-R3.md z r1 tam, gdzie podano CC0 lub trzy materiały
dla każdego LOD. Zdjęcie Rakoon 20200711 073128 jest CC BY 3.0, lokalna kopia
3840x2160 jest pomniejszona z oryginału 4608x2592. Oryginał zwrócił HTTP 429
przy dwóch próbach; nie twierdzić, że go obejrzano w pełnej rozdzielczości.

Szczegóły atrybucji: chimney-source-correction.json. Środki trzonów wyznaczone
maską czerwonej farby to 2969,75 i 3630,25 px. GPS i znane pozycje OSM wskazują
lewy w628899554 (trzy wyloty) i prawy w628899553 (jeden wylot). Kierunki z obu
środków różnią się o 0,860 stopnia; średnia 147,078 jest nadal WORKING_VALUE.

Pomiary granic pasów są w chimney-bands-preflight.json. Odcinki bez galerii mają
średnio 83,75 px na lewym i 105,67 px na prawym. Model otworkowy z ogniskową
27 mm i GPS daje około 14,64 i 15,08 m na pas; niepewność robocza co najmniej
2 m (GPS, ekwiwalent ogniskowej/crop, pitch). Hipoteza do porównania renderów:
15 m, biała podstawa 0..15, czerwone 15..30 itd. do czerwonego 105..120.
To nie pomiar całej budowli; nie zmieniać wysokości 120 m ani pozycji na oko.

Małe wyciągi aktualnego API OSM zachowano z atrybucją ODbL; nie skanowano PBF.
Wersje ways 2/3 z 2024-05-10 mają height=120. Średnice równoważne pól obrysów
wynoszą 7,502 i 8,272 m, środki zgodne z override do centymetrów. Obrys płaski
sam nie dowodzi średnicy zwieńczenia ani tego, czy zmapowano podstawę czy koronę.
Dotychczasowe top_d 4,5/4,8 pozostają WORKING_VALUE. Przed korektą szerokości
potrzeba porównania w dopasowanej pozie i sprawdzenia geometrii źródłowej.

Do pary zdjęcia 16:9 w r3 nie ucinać zwieńczenia prawego komina centralnym
kadrem pionowym (jest blisko górnej krawędzi). Można zachować QA 2340x1080,
użyć pełnego pionowego FOV zdjęcia i porównywać centralne 1920x1080 renderu
z całym zdjęciem 3840x2160. Liczby FOV zależą od kalibracji, nie są pomiarem.

Rzeczywisty life_props.chimney ma cztery materiały na High: chimney_concrete,
chimney_red, chimney_white, gantry_steel; Low ma trzy, bez galerii. Nowe Low
głowice muszą użyć istniejącej trójki, aby nie dodać draws. Nie edytować life_props.
Własne GLB + hero_building/landmarks za konfiguracją pozostają preferowanym
wariantem, wymagają sprawdzenia kolejności rejestracji i fallbacku w r3.

OSM wskazuje stronę https://radiopolska.pl/wykaz/obiekt/765 (komin w554).
Podaje posadowienie 137 m n.p.m. i zawieszenie anten 116 m n.p.t.; nie jest to
niezależny pomiar średnic. Zdjęcia RadioPolski wymagają zgody na reprodukcję;
nie pobrano ich ani nie dołączono do dowodów. Nie otwierano linku Google ze strony.

## Późniejsza kontrola techniczna — ważniejsza od hipotezy GPS

W opisie zamówienia ENEA z maja 2025 komin jednoprzewodowy nr 2 ma H=120 m,
zewnętrzną średnicę góry 4,80 m i podstawy 7,65 m, rok budowy 1974. EMKA w swoim
opisie realizacji potwierdza H=120 m komina wieloprzewodowego. Własne źródła i
linki są w chimney-technical-sources.json; nie kopiowano pełnego ogłoszenia.
Fotografia EMKA pokazuje długi biały dół i pasy na górnej części; obejrzana tylko
z cache TEMP, nie umieszczona w artifacts ani git. Brak zgody na reprodukcję.

Nie zmieniać wysokości ani szerokości do źle dopasowanego aparatu. Przedział
roboczy +/-2 m dla pasów nie obejmował systematycznego błędu pozy/GPS i nie jest
wiarygodną granicą. Liczby 14,64/15,08 m zachowano jako ślad odrzuconej hipotezy,
nie parametry do modelu. Dla r3 rozwiązać pozę na znanych 120 m i położeniach,
sprawdzić granice pasów i biały dół; nie wprowadzać pełnego malowania od podstawy.

Kontrola chimney-pose-consistency.json: przy pozycji GPS, ogniskowej 27 mm,
roboczych pikselach głowic i H120 oba zwieńczenia wymagają pitch -1,91 / -4,53
stopnia, różnica 2,62 stopnia. Tych założeń nie spełnia jedna kamera. NMT w GPS
wynosi 140,529 m; 1,65 m oczu jest WORKING_VALUE. To diagnoza niewyznaczonej
pozy/optyki, nie dowód, że trzeba zmienić wysokość albo poszerzyć trzon.
