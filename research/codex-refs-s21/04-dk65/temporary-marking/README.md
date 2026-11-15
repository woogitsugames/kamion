# Oznakowanie czasowe — źródłowe uzupełnienie DK65

Cel: dostarczyć zasady wyglądu i interpretacji do pakietu 04. To notatka normatywna, bez obserwacji bieżącego placu budowy. Notatkę po recenzji przeniesiono do pakietu04.

## Wyniki

`regulations.csv`: 17 ustaleń SOURCED i 1 otwarty warunek terenowy UNVERIFIED. Zero nowych fotografii. Sześć stron rysunków urzędowych obejrzano osobno, nie wnioskując o wyglądzie wyłącznie z nazw: strony PDF części 2: 292, 293, 347, 348, 349, 351. To odpowiednio drukowane strony Dz.U. 817, 818, 872, 873, 874, 876.

- SOURCED [§85 ust.3]: żółte znaki mają pierwszeństwo, gdy białe i żółte wskazują różny sposób zachowania.
- SOURCED [zał.2 pkt1.3, s.529]: żółte oznakowanie czasowe przy pozostawionym stałym białym; białe oznakowanie czasowe po usunięciu lub zakryciu dotychczasowych znaków. Nieobowiązujące białe przekreśla się żółtymi kreskami o szerokości minimum 12 cm.
- SOURCED [zał.4 pkt2.3.1, rys.2.3.1]: U-3 to **tablice prowadzące**, czerwone szewrony na białym tle. U-3a/b mają kierunek prawo/lewo; U-3c/d są ciągłe; U-3e dwustronna. Ciągłe tarcze mają wysokość 600 mm i długości 1200–3000 mm w typoszeregu podanym w CSV.
- SOURCED [zał.4 pkt11.2, rys.11.2.1]: U-20 to **zapory drogowe**. U-20a ma tarczę wysokości 250 mm, U-20b 500 mm. Pola naprzemiennie białe/czerwone, oba końce czerwone. Wysokość górnej krawędzi nad drogą 0,9–1,1 m z opisanym w CSV wyjątkiem widoczności na skrzyżowaniu.
- SOURCED [zał.4 rys.11.3.1]: pionowe tablice w ukośne czerwono-białe pasy to rodzina **U-21 — tablice kierujące**. Tekst pkt11.3 zawiera niespójne odwołania U-23a/b; nie uznajemy ich za poprawny alias. Rysunek jednoznacznie podpisuje U-21a–f. Przy odwzorowaniu użyć rysunku, a nie omyłkowego odwołania tekstowego.
- UNVERIFIED: konkretne typy, liczby, pozycje i stan urządzeń na DK65/S19 w dacie świata gry. Należy dołączyć aktualne kadry lub zatwierdzony projekt organizacji ruchu.

## Aktualność i źródła

Sprawdzenie 2026-11-15: metadane ELI wskazują teksty jednolite 2019/2310 i 2019/2311 jako obowiązujące. Sprawdzono pełne treści późniejszych zmian wskazanych przez ELI, łącznie z 2026/132 i 2026/133 obowiązującymi od 2026-02-19. Badane §85, zał.2 pkt1.3 oraz zał.4 pkt2.3.1 i11.2–11.3 nie zostały przez te zmiany zmodyfikowane. To kontrola konkretnych punktów, nie stwierdzenie, że cały tekst z 2019 r. pozostał bez zmian. Sprostowanie 2020/862 dotyczy innych rysunków załącznika1.

- [Znaki i sygnały — pełny tekst Dz.U.2019 poz.2310, §85](https://eli.gov.pl/api/acts/DU/2019/2310/text.html).
- [Warunki techniczne — Dz.U.2019 poz.2311, pełny PDF część2](https://eli.gov.pl/api/acts/DU/2019/2311/text/I/D20192311-c2.pdf).
- [Nowelizacja techniczna 2026/132](https://eli.gov.pl/eli/DU/2026/132/ogl), [nowelizacja znaków 2026/133](https://eli.gov.pl/eli/DU/2026/133/ogl).
- Dokładny łańcuch nowelizacji, zakres kontroli, adresy i hash lokalnego PDF: `source-evidence.json`.

Pliki pełnych źródeł i sześć podglądów rysunków pozostają poza gitem w `C:\Users\matma\Documents\Claude\kamion\Data\raw\refs\codex-s21\01-lampy\temporary-road-marking`. PDF części2 ma 381 stron; strona drukowana = strona PDF +525. Pełny PDF ma około28 MB i nie jest kopiowany do repo. Urzędowe akty i rysunki są materiałem urzędowym; nie przypisujemy im licencji CC fotografii. Nie skopiowano fotografii właściciela.

Dla generatora: liczby są wymaganiami normatywnymi, nie pomiarami konkretnego zdjęcia. Nie dodawano ESTIMATED. CSV zawiera parafrazy wraz z warunkami i źródłami; tekstów z wyników wyszukiwania nie traktowano jako dowodu.
