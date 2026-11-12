# Oryginalny EXIF dwóch kandydatów początku trasy

12 listopada około 12:53 wykonano jedno anonimowe zapytanie API Commons o metadata, commonmetadata i size dla cm109685822 oraz cm92458760. Nie pobierano oryginalnych obrazów i nie korzystano z urządzeń. Pełna odpowiedź, URL zapytania i czas są w commons-first300-original-metadata.json.

Oba oryginały mają 4608×2592 px, Orientation=1, Make=samsung, Model=SM-A720F, FocalLength=3,6 mm i FocalLengthIn35mmFilm=27. Nie znaleziono GPSImgDirection ani innego kierunku optycznego. To nowe dane do dalszej kalibracji: dotychczasowe założenie „lokalna miniatura nie ma EXIF” pozostaje prawdziwe dla miniatury, ale nie oznacza braku EXIF w oryginale.

EXIF obu zdjęć podaje tę samą pozycję 53,1527777778 N, 23,1683333333 E. Publiczny geotag Commons cm109685822 wynosi natomiast 53,152931 N, 23,168504 E. Są to różne wskazania źródła; nie wolno arbitralnie zastąpić jednego drugim. Dla cm92458760 publiczny geotag odpowiada EXIF z dokładnością zaokrąglenia. GPSAltitude wynosi odpowiednio 172 i 0 m; nie używać tych liczb do osadzenia oka nad jezdnią.

27 mm eq jest wskazówką optyki, nie gotowym poziomym FOV. Trzeba rozstrzygnąć konwencję ekwiwalentu i crop 16:9 względem sensora, możliwą korekcję programową oraz porównać trwałe kotwice. Orientation=1 nie dowodzi zerowego roll. Metadane aktualnego pliku na Commons nie zostały jeszcze związane bajtowo z lokalną miniaturą; przed ich użyciem do kalibracji należy wykluczyć zmianę wersji źródła i związać właściwy obraz z jego SHA. Produkcyjne kamery i referencje pozostają bez zmian, nadal C. Przygotowane próby r4 dotyczą sześciu innych zdjęć i nie korzystają z tego EXIF.

Źródła: [cm109685822](https://commons.wikimedia.org/?curid=109685822), [cm92458760](https://commons.wikimedia.org/?curid=92458760). Metadane licencji zachowano w commons-first300-metadata.json: pierwsze zdjęcie CC0, drugie CC BY 3.0; atrybucja nie jest znoszona przez odczyt EXIF.
