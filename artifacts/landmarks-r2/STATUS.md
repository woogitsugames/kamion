Sesja 7, runda r2: wyłącznie wiadukt DK8 pod pomostem. Gałąź gpt-landmarks-r2.
Początek od r1 cb699d7493bf52fa1191398d5e8ba3685514e5ef; integracja main 2c3939b22162659ea3ca42fb42be3d9a19cef2c2 do tej gałęzi. Nie scalano do main i nie pushowano.
Krok 1: jedyny konflikt generated/streetscape_qa rozwiązany wersją main, zgodnie z protokołem; przed baseline nastąpi pełna regeneracja pod heavy. Kod i materials_spec scaliły się automatycznie.
Zakres: wyłączyć niepotwierdzone schody przecinające ekran, poprawić powierzchnie filarów według natywnej fotografii 7204; pomost, kapa, bariery i ekrany pozostają własnością Claude.
Termin całej sesji pozostaje 2026-11-12 21:31:16 CET; runda nie resetuje 24 godzin.
NASTĘPNY KROK: przygotować własne kamery i wrappery r2, następnie heavy World -> import Unity -> baseline wszystkich kamer.

Krok 2: przygotowano oddzielne wrappery r2, dziewięć kamer detalu i referencję 7204 w pełnej rozdzielczości. Zsynchronizowano prywatne cache map Medium z main, zachowując własne mapy fire_station z r1; wynik w material-cache.json. Nie zmieniono jeszcze generatora ani konfiguracji wiaduktu. ADR 0119 zapisuje plan i status UNVERIFIED. NASTĘPNA KOMENDA: pwsh artifacts/landmarks-r2/baseline.ps1

Korekta kroku 2: preflight cache nie zakończył się — wykrył nowy zestaw car_grime_clean bez mapy Medium także w main. Wcześniejsze zdanie o pełnej synchronizacji nie jest potwierdzeniem. Generator baseline został uruchomiony pod heavy, ale import zostanie zatrzymany własnym markerem DIAGNOSTICS_RUNNING przed acquire Unity. Brakujące cache będą przygotowane osobno pod heavy po zwolnieniu slotu generatora; nie uruchomię dwóch prac pod jednym ownerem.

Krok 2b: dodano dziesiątą własną kamerę dk8-ref7204, opartą na GPS i ogniskowej 38 mm z fotografii Commons. Wysokość oczu, kierunek 280° i pitch 1,7° są WORKING_VALUE; dopasowanie kadru pozostaje UNVERIFIED do obejrzenia baseline. FOV pionowy 24,664° dla QA 2340x1080 zachowuje fotograficzne pole poziome. Nie zmieniono kamer sbs ani danych produkcyjnych.

Krok 2c: przygotowano porównanie kompletnego inwentarza 48 kamer kontrolnych i 10 własnych. Narzędzie wymaga zgodności obu zbiorów i rozmiarów obrazów, przetwarza po jednej parze PNG, zapisuje arkusze o szerokości 960 px. Nie uruchomiono renderów ani ciężkiego Pythona poza kolejką baseline; kod wiaduktu nadal bez zmian.

Krok 2d: do dowodów r2 skopiowano natywne kadry filarów i zapis ROI z oryginału 5520x3680. Referencja rozdziela szare ścięcie od ochrowej płaszczyzny, bez traktowania jasności zdjęcia jako odbicia materiału. Stan wykonania baseline pozostaje WAITING_HEAVY, bez uruchamiania dodatkowego ciężkiego zadania.

Krok 2e: preflight kolejnej rundy wykrył błędny opis referencji kominów w NEXT-R3 z r1. Strona autora podaje CC BY 3.0 (Rakoon), oryginał 4608x2592, a lokalny plik ma 3840x2160. Korekta z atrybucją zapisana w chimney-source-correction.json. Próba pobrania oryginału zwróciła HTTP 429; nie zapisano pliku i nie potwierdzono jego lokalnego SHA. Nie zmieniono modeli kominów ani źródeł r2.

Krok 2f: lekki odczyt GPS zdjęcia i istniejących pozycji kominów przewiduje kolejność lewo-prawo: w628899554, w628899553, separacja kątowa 9,817 stopnia. Wynik jest wstępnym przypisaniem przestrzennym, bez potwierdzenia pozy i proporcji malowania. Generator baseline r2 właśnie uzyskał heavy, więc do jego ukończenia nie zmieniam źródeł.

Krok 2g: kontrola separacji kominów porównuje model otworkowy ogniskowej 27 mm z centrami lokalnych kadrów. Pozostaje rozbieżność kierunku między dwoma przypisaniami; json jawnie oznacza pozę UNVERIFIED. Nie dopasowano ani nie przesunięto modeli do zdjęcia.

Krok 3: świeży baseline świata po merge main wygenerowany pod heavy, bez fallback=True. Agregaty i spec podmostowy zachowane. NASTĘPNY KROK: import i wszystkie kamery trasy wraz z dziewięcioma własnymi kadrami detalu pod slotem Unity.

Krok 3a: zapisano CANDIDATE.md z dokładnym planem flag schodów, podziału ścięć bez dodatkowych trójkątów i testów zachowania kolizji oraz UV1/COL pomostu. To plan, nie wdrożona zmiana. Przygotowanie map nadal oczekuje heavy; Unity nie zostało uruchomione.

Krok 4: brakujące nowe cache PBR po merge main przygotowano osobno pod heavy i zweryfikowano PNG. Zachowano własny fire_station. Własny marker zwalnia import; żaden generator nie startował po cichu z Unity.

Krok 4a: import Low+High zakończony IMPORT_RESULT OK; baseline 58 kamer rozpoczęty w Low-overcast pod Unity. Przygotowano photo_pair.py, zapisujące pary 960 px i jawny status pozy UNVERIFIED, z opisem centralnego kadrowania referencji. Nie twierdzę jeszcze, że kadr odpowiada fotografii.

Krok 5: baseline zakończony 58/58 w każdej z czterech kombinacji, kod wyjścia 0. Obejrzano pary referencyjne oraz detale schodów i filarów. Schody przecinają ekran; żółty pigment obejmuje również fazy. Kierunek kamery GPS 280 stopni jest niedopasowany, dlatego przed zmianą źródeł wykonuję trzy próby 295/305/315 stopni z tej samej pozycji i FOV. Bazowe 232 PNG pozostają zachowane.

Krok 5a: obejrzano próby 295/305/315. Wybrano 295 stopni jako najbliższe położenie końca wiaduktu i bramownicy w kadrze, przy niezmienionym GPS/FOV. Poza pozostaje UNVERIFIED, widoczne różnice ekranów i geometrii drogowej należą do Claude. Oryginalna definicja kamery zachowana w cameras-gps280.json. Przed zmianą źródeł wykonuję baseline tylko dk8-ref7204 do pose-final; później zachowam oryginalne PNG/statystyki i podmienię wyłącznie parę wierszy tej kamery.

Krok 6: wdrożono jawne wyłączenie schodów przy planowaniu i emisji starego spec, podział istniejących ścian faz na bridge_concrete bez dodatkowych tris i bez zmiany pełnej kolizji. Testy rozszerzono o UV1/COL pomostu oraz sprzeczne flagi starego spec. Addytywny blok materials.py odczytuje tylko pier_paint.enabled z własnej konfiguracji; pigment [0.46,0.34,0.135] pozostaje WORKING_VALUE. Po obejrzeniu natywnego cropu ROI skrócono, aby omijały abstrakcyjną plamę i cień w dolnej części kolumny. Testy i wygląd po zmianie jeszcze UNVERIFIED. NASTĘPNY KROK: regeneracja świata pod heavy, pojedynczy plik testów, import i render wszystkich kamer.
