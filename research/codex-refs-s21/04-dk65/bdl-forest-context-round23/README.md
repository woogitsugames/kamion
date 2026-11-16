# R23 — punktowy kontekst BDL przy kaflu dk65-08

Cel: sprawdzić, czy BDL dostarcza źródłowy opis lasu przy istniejącym TC17-02, zamiast zgadywać gatunki z korony. Wynik: **1 rekord wydzielenia,0 nowych zdjęć**. To kontekst drzewostanu, nie identyfikacja drzewa przy samej jezdni.

Root ponownie obejrzał istniejącą ortofotomapę800px GUGiK wTC17-02 i wybrał osobny punkt200,600px w gęściej zadrzewionym fragmencie po południowo-zachodniej stronie drogi. Z już zapisanego bbox i skali0,3m/px otrzymano EPSG2180 **765618,6;606031,9 ESTIMATED**. To punkt selekcji z obrazu, nie pozycja pnia ani pomiar GPS. Konwencja środka piksela zmienia wynik o0,15m, poniżej nieustalonej dokładności obrazu. K1km20/dk65-08 jest kontekstem trasy, nie krajowym kilometrażem.

SOURCED [publiczna warstwa BDL Wydzielenia pozaPGL LP wgPUL,ID6, dokładne zapytanie wsource-review.json]:

| Pole odpowiedzi | Odczyt dosłowny po usunięciu końcowych spacji |
|---|---|
| adress_forest | B020320009-104   -a   -00 |
| area_type_cd | D-STAN |
| site_type_cd | BŚW |
| species_cd_d | SO |
| species_age | 100 |
| a_year | 2017 |
| part_cd | 5 |

Nie rozwinięto automatycznieSO do nazwy gatunku bez właściwego słownika danych. Liczba100 i rok2017 są oddzielnymi polami; data odniesienia i jednostka wieku nie zostały niezależnie potwierdzone. Nie deklarujemy109lat w2026 ani udziału50% z kodu5. To surowe wartości źródłowe do dalszej weryfikacji, nie parametry generatora.

Dwie odpowiedzi WMS były puste: dla dawnej wybranej korony377,310 i dla tego punktu lasu. Również REST warstwy PGL5 dla punktu lasu zwrócił0obiektów. Dopiero właściwa osobna warstwa pozaPGL6 zwróciła1rekord. Pusty wynik nie dowodzi braku drzew ani błędu serwera. Nie ustalono przyczyny pustych odpowiedzi WMS. Zakończono po jednym wyniku; bez siatki punktów, pobierania geometrii lub danych właścicieli.

Oficjalny katalog usługBDL wskazuje endpointy. Metadane publicznego ArcGIS udostępniają operacjęQuery i pola warstwy. Wszystkie5własnych żądańAPI zwróciły200, User-Agent ogólny. SuroweXML/JSON i adresy żądań wyłącznie pozaGit wData/raw/refs/codex-s21/04-dk65/bdl-forest-context-round23. Repo zawiera własny odczyt, manifest i ślad; nie przypisanoCC ani nie pobrano nowych obrazów. Gatunki pojedynczych drzew przy DK65, rozstaw i odsunięcie pni pozostają UNVERIFIED.
