# Zmiany póz na main po zamrożeniu bazy r4

Odczyt około 15:16 potwierdza zmianę sześciu spornych kamer. Porównanie pochodzi z danych kamer zapisanych w migawce r4 i z konkretnego commitu main zapisanego w upstream-pose-comparison.json. Początek układu EPSG:2180 jest zgodny; poniższe delty można więc obliczyć bez zmiany ramy. Są to różnice zapisanych danych, nie nowy pomiar położenia w terenie.

| Kamera | Przesunięcie poziome | Zmiana absolutnego U | Zmiana pitch |
|---|---:|---:|---:|
| 275528 | 10,00 m | −0,467 m | −4,189° |
| 837235 | 16,12 m | +0,253 m | −3,503° |
| 328135 | 73,15 m | −0,937 m | +3,760° |
| 297817 | 84,85 m | +0,492 m | +2,883° |
| 180137 | 20,00 m | +0,309 m | −4,109° |
| 494288 | 3,00 m | −0,039 m | +1,794° |

FOV wszystkich sześciu kamer pozostał taki sam jak w r4. Kurs 297817 zmienił się o około +1,15°; pozostałe różnice kursu są na poziomie zaokrągleń zapisanych wektorów. Zmiana absolutnego U obejmuje zarówno poziom powierzchni, jak i wysokość oka; nie jest samodzielnym pomiarem zmiany nominalnego oka.

Recenzja ADR 0130 zaakceptowała korekty, ale wymaga świeżego renderu czterech stanów na main przed kompozycją i wpisem do rejestru. Jej częściowy wynik G3-B 6/10 nie jest wynikiem pełnych 25 par r4. Wskazane pozostałe problemy obejmują wysokość i czytelność portalu, skalę szewronu, pomost/latarnie Putry oraz ekran i zabudowę. Kadr 150280 ma osobno wskazany problem pitch.

R4 zachowuje swoją wcześniejszą bazę i świeżą ocenę 13/11/1 z właściwymi SHA. Przepis 15 wariantów starej pozy pozostaje historyczny i nie został uruchomiony. Po raporcie i dostawie r4 następna gałąź ma scalić bieżący main, zachować dane Claude, odtworzyć aktualny świat i wykonać pełną serię. Dopiero te obrazy pozwolą zweryfikować efekt zintegrowanych korekt i wybrać następną własną zmianę SBS.
