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
