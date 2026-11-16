# R67 — jeden kontrolowany odczyt Commons

Wykonano 1 oficjalne żądanie API z metadanymi: 2026-11-16 06:34:46 w Brukseli, czyli 05:34:46 UTC (SOURCED request-log.json). HTTP 200, brak nagłówka Retry-After. Parametry i dokładny URL zapisano w logu; odpowiedź metadata.json to wyłącznie `{"batchcomplete":""}`. Zapytanie generator=search z namespace 6, limitem 12 i imageinfo/url/size/extmetadata: `filetype:bitmap ("articulated lorry" OR "semi-trailer") rear`.

Wynik tego jednego zapytania: 0 rekordów źródłowych, 0 licencji do weryfikacji, 0 pobranych/obejrzanych obrazów, 0 nowych A/B/zimowych/europejskich. To nie dowód globalnego braku takich fotografii na Commons. Nie ponawiano zapytania, nie używano innego hosta, rozmiaru ani wariantów API. Nie doszło do 403/429. User-Agent Mozilla/5.0, bez danych projektu lub właściciela.

Wcześniejsza ograniczona selekcja wyszukiwarką dała głównie kategorie oraz znane/niecelowe tropy, bez opisu nowych zdjęć z tytułów. Nie przypisano licencji do plików bez metadanych, nie pobierano starych P18 ani fotografii muzealnych. Brak zaakceptowanych kadrów oznacza manifest.csv z wymaganymi 10 nagłówkami i 0 wierszy fotografii; żaden log zapytania nie udaje referencji zdjęciowej.

Limit koordynatora 1 API respektowany; maksymalny budżet 2 obrazów nie został wykorzystany. Brak nowych żądań Flickr, brak UI, brak screenshotów i mediów na dysku. Parent, historyczne audyty i git nietknięte.
