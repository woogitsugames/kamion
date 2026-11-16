# Commons — pojedyncza kontrola po wielogodzinnej przerwie

16.11.2026 o04:15 czasuBrukseli (zmierzony UTC03:15:08 wJSON) wykonano jedno oficjalne imageinfo dla istniejącego P18-168. Ostatnie nieudane żądanie podglądu nastąpiło w poprzednim obiegu około01:20–01:23; tej godziny nie odtwarza się jako dokładnego logu nowego requestu. Nie wykonywano prób pośrednich ani wariantów hostów.

SOURCED [access-check.json, metadata.json]: odpowiedźHTTP200, poprawnyJSON i licencjaCCBY-SA3.0. Metadane nie są oglądem obrazu, nie dowodzą brudu, nie zwiększają pokrycia70/88 i nie zaliczają A/B. Autor i inne pola zachowano w surowymJSON. Źródłowy zapis daty0002 z wcześniejszego audytu nie jest prawidłowo ustaloną datą zdjęcia.

Pierwszy etap kontroli obejmował1zapytanieAPI/0obrazów. Nie uruchomiono automatycznie kolejki ani pobierania fotografii. Host metadanych i host obrazów mogą mieć różny wynik; wcześniejszy STOP obrazów trwa do osobnej świadomej kontroli. Nagłówek User-Agent Mozilla/5.0, bez nazwy projektu/właściciela. Nie zapisano odpowiedzi błędu jako obrazu. Kolejne obserwacje, jeśli powstaną, muszą mieć oddzielny log i indywidualny ogląd przed opisem.

## Drugi etap: jeden dokładny oryginał i ogląd

O04:16:16Brukseli (zmierzony UTC03:16:16 wimage-access-check.json) wykonano jeden GET dokładnegoURL oryginału otrzymanego zAPI. HTTP200/image/jpeg,49193bajty; raw pozaGit. Potem root osobno obejrzał640×480 przez lokalnyview_image. Nie było ponowienia, zmiany hosta, rozmiaru ani parametrów. CC BY-SA3.0 iXnatedawgx odczytane przed pobraniem; niczego nieopisano z tytułu.

SOURCED [indywidualny obraz]: przewrócony pojazd/podwozie po lewej, zielony otwarty kontener po prawej, śnieg na podłożu. **Brak kwalifikowanej pary tylnych drzwi**. A/B bez przyrostu; nie awansowano śnieguAUX do zimowegoA. PhotoDate0002 nadalUNVERIFIED. PokrycieP18 wzrasta70→71 z88, pozostaje17NOT_REVIEWED; to jeden rekord niezależnie od liczby narzędziowych odczytów. Historyczne round30/ledger18 zachowane jako snapshoty, aktualizacja w audit-delta.csv.

Łącznie tej kontroli:1metadataAPI+1originalGET,1pobranydoRAW/1obejrzanyobraz,0kopiiGit/miniatur,0przyjętychbrudnychdrzwi. Jednostkowe200 nie gwarantuje działania całej usługi. Kolejny mały obieg przekazano wyłącznie jednemu agentowi, maks6pozostałychrekordów, co najmniej10s międzyżądaniami i ponownySTOPprzypierwszym429. Flickrdownloads nadalSTOP. Nie uruchomiono masowego scrapowania.
