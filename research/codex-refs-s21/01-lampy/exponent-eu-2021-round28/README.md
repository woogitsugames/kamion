# R148 — cztery wartości w osobnym urzędowym wydaniu UE 2021

16.11.2026 obejrzano rzeczywiście wyrenderowaną tabelę 8 w pełnej publicznej [HTML CELEX 42021X1719](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:42021X1719). Nagłówek identyfikuje R148 [2021/1719], Dz.U. UE L 347 z 30.09.2021, początek s. 123, oraz Supplement 3 do oryginalnej wersji z podaną datą wejścia w życie 30.09.2021. To **odrębny datowany snapshot dokumentacyjny**, nie deklaracja aktualnego prawa 2026 ani tekst Am5/Rev1Am2. Nagłówek zastrzega znaczenie autentycznych tekstów UNECE.

Tabela ma zwykły zapis dziesiętny, **nie wykładniki potęg**. Odczyt wzrokowy wierszy, granic kolumn i jednostki cd potwierdził:

| Kategoria | Pole tabeli 8 | Wartość z renderu | Warunek |
|---|---|---:|---|
| 5 | minimum | 0,6 cd | §5.6.1(b): kierunek A według zał. 2; nie ogólne minimum w osi odniesienia |
| 11a | maksimum pojedynczej lampy | 1000 cd | §5.6.1 i nagłówek tabeli: maksimum w dowolnym kierunku |
| 11b | maksimum pojedynczej lampy | 1200 cd | ten sam warunek; nie kolumna D |
| 11c | maksimum pojedynczej lampy | 1200 cd | ten sam warunek; nie kolumna D |

Ważna różnica: **11a ma w tej publikacji 1000 cd**, a nie 1200 cd. Nie przenosimy wartości nowszego wydania do 2021 ani w odwrotną stronę. Przeliczenie 0,6 = 6 × 10⁻¹, 1000 = 1 × 10³ i 1200 = 1,2 × 10³ jest tylko równoważnym zapisem arytmetycznym, a nie odczytanym drukiem potęgi. Wiersze `eu-2021-norms.csv` zachowują zapis dziesiętny źródła i warunki.

§5.6.1 dotyczy każdej z dwóch dostarczonych lamp; nie sumy dwóch lamp. Minimum kategorii 11a/11b/11c sprawdza się w osi odniesienia zgodnie z §5.6.1(a), lecz **badane tutaj maksimum** ma szerszy zakres kierunkowy z nagłówka tabeli. Dla kategorii 11a/11b/11c kolumna D ma N.A.; nie podstawiamy tam połowy wartości single. Dla kategorii 5 pełny §5.6.4 dodatkowo wymaga 0,6 cd ku tyłowi w całym polu określonym w części A zał. 2, jako odstępstwa od §4.8.3 i §4.8.3.1. Schematów kątowych zał. 2 nie oglądano w tej rundzie, więc nie dopisano nowych kątów z pamięci.

Metoda: jedno normalne otwarcie URL w Chrome, odczyt nagłówka i wersji z pełnej strony, przejście do widocznej tabeli 8 przez jej nagłówek, ogląd bitmapy widoku oraz odczyt komórek tabeli i §5.6.1–5.6.4 z DOM. Bez CAPTCHA, logowania, pobrania PDF, zapisanych screenshotów i obrazów. Webtool wcześniej pokazał bramkę wymagającą JavaScript; nie ponawiano go ani nie zmieniano hosta. Normalna przeglądarka wczytała publiczną HTML bez tej przeszkody.

Wskazany w zleceniu katalog `regulation-extraction-comparison-round9` nie istniał w odczytanym worktree. Odpowiadające cztery nierozstrzygnięte rozbieżności znaleziono w `../table8-comparison-round6/comparison.csv`: kat. 5 minimum oraz kat. 11a/11b/11c maksimum single, w ekstraktach Am5 i Rev1Am2. **Ich statusu UNVERIFIED nie zmieniono.** Nie obejrzano tu bitmap UNECE 2020/Am5/Rev1Am2, nie wykazano tożsamości wydań ani pełnego łańcucha zmian. Wynik 2021 nie jest rozstrzygnięciem błędu ekstrakcji względem druku w innym dokumencie.

Jedno źródło urzędowe, cztery wiersze normatywne, zero fotografii i zero nowych pełnych homologacji. Wszystkie zmiany wyłącznie w tym podkatalogu; bez edycji parenta i bez Git.

Odrębna kontrola root potwierdziła render tabeli i cztery powyższe wartości; zapis w `root-peer-review.json`. Nie rozszerza to zakresu na inne wydania.
