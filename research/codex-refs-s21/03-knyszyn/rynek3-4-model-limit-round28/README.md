# Rynek 3 / 4 — ograniczenie istniejącego PRG, runda 28

Odczyt: 2026-11-16, bez odtwarzania godziny. **0 nowych modeli, figur, zdjęć i zapytań sieciowych.**

Ponownie odczytano wyłącznie istniejący `kina-addresses.gml` z R23: 3421 bajtów, SHA256 `8d5881646e5bbbf475b35a8d68fafc6dffb52ff06358bec20ccfd358193bbcdb`. Pola odpowiedzi `numberMatched=2` i `numberReturned=2`; zawartość to **Knyszyn, Rynek 1** oraz **Knyszyn, Rynek 2**. Brak punktów Rynek 3 i Rynek 4 w tym pliku — SOURCED [literalne rekordy GML].

To mały ekstrakt z zapytania R23, nie pełny wykaz adresów miasta. Brak rekordów nie dowodzi nieistnienia adresów w PRG. Nie wykonywano nowego, rozszerzonego zapytania ani pobierania ZIP.

Warunek wyboru nowego sąsiedniego modelu nie został spełniony. **Rynek 3/4 → buildingId pozostaje UNVERIFIED.** Nie dobierano bryły na podstawie najbliższego centroidu, kolejności numeracji lub fotografii innego adresu. Nie było potrzeby ponownie skanować SQLite i ZIP, ponieważ brak punktu selekcji wskazanego przez zadanie.

Istniejące modele 3002 (R22/R23, kandydat Rynek 1) i 3031 (R25, kandydat Rynek 2) nie są nowym wynikiem. Wcześniejszy katalog NID Rynek 3/4 nie tworzy wspólnego klucza z CityGML/BDOT.

Manifest ma sam nagłówek. Nie kopiowano danych źródłowych ani zdjęć. Całe shared `Data/raw/gugik`, R23 i R25 oraz parenty pozostały bez zmian; bez Chrome i git.
