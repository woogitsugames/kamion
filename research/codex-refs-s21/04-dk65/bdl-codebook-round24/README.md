# BDL — wiek, rok i udział, runda 24

Odczyt 2026-11-16, bez dokładnej godziny. **Wniosek: nie wykazano powiązania `species_age=100` z rokiem `a_year=2017` ani przeliczenia `part_cd="5  "` na 50%. Oba pozostają UNVERIFIED.** R23 i główne manifesty niezmienione. Nie obliczono wieku na 2026 r., roku powstania lasu ani cech drzew przy jezdni.

## Dozwolona podstawa: instrukcja BDL

Ponownie użyto istniejącego dokumentu [TAKSATOR — Plany Uproszczone. Instrukcja użytkownika, Warszawa 2023](https://www4.bdl.lasy.gov.pl/portal/Media/UPUL/taksatorpu_instr_uzytk_2023.pdf), udostępnionego w portalu BDL. Wydawca PGL LP/DGLP wynika ze strony tytułowej; nie przypisano licencji CC. Nie wykonano drugiej kopii PDF.

SOURCED [s. 11, tekst i osobno obejrzana bitmapa]: program ma ustawienia pierwszego roku i okresu obowiązywania planu. Zrzut formularza przedstawia przykładowe lata 2017–2026. To przykład instrukcji, **nie dowód okresu planu jednostki z R23 ani definicja `a_year`**.

SOURCED [s. 17, tekst i osobno obejrzana bitmapa]: tabela opisu drzewostanu rozdziela warstwę od gatunków; po stronie gatunków są odrębne kolumny udziału i wieku. W ilustracyjnym przykładzie występują udział 10 i wiek 65. Instrukcja w tym miejscu nie określa przelicznika udziału ani nazw pól publikowanego REST. Niższe 100% dotyczy powierzchni zabiegu gospodarczego — nie jest legendą udziału gatunku.

## Wynik dla R23

| Surowe pole | Wniosek |
|---|---|
| `species_age=100` | Literalna wartość zachowana; dokładna definicja i rok odniesienia konkretnej warstwy UNVERIFIED. |
| `a_year=2017` | Literalna wartość zachowana; początek planu, stan danych, taksacja lub aktualizacja UNVERIFIED. Przykład z instrukcji nie rozstrzyga znaczenia. |
| `part_cd="5  "` | Literalny tekst zachowany; słownik kodów, jednostka i przelicznik na procent UNVERIFIED. Nie zamieniono na 50%. |

SO jako sosna zwyczajna pozostaje odrębnym ustaleniem R23 ze słownika BDL s. 20, którego ta runda nie rozszerza. Nie przenosić danych jednostki na każdy pień, szpaler ani stan terenu w 2026 r.

## Wykluczenie spoza zakresu źródeł

Podczas selekcji pobrano i odczytano ogólny podręcznik „Geomatyka w Lasach Państwowych, część II” ze strony lasy.gov.pl. **Nie wykazano łańcucha publikacji przez BDL; koordynator wykluczył go z core przed stabilizacją.** Nie używamy jego tabeli do ustalania semantyki pól ani jako źródła SOURCED w manifeście. Dokładny URL, SHA256 i ścieżka lokalna pozostały tylko w `excluded_source` JSON dla jawności audytu. Nie wykonywano dodatkowych żądań HTTP w poszukiwaniu powiązania.

## Dowody i zakres pracy

Dozwolone źródło PDF: `C:/Users/matma/Documents/Claude/kamion/Data/raw/refs/codex-s21/04-dk65/bdl-forest-context-round23/taksator-pu-2023.pdf`.

Dwie osobiście obejrzane strony poza gitem:

- `C:/Users/matma/Documents/Claude/kamion/Data/raw/refs/codex-s21/04-dk65/bdl-codebook-round24/taksator-page-11.png`
- `C:/Users/matma/Documents/Claude/kamion/Data/raw/refs/codex-s21/04-dk65/bdl-codebook-round24/taksator-page-17.png`

0 nowych punktów BDL/WMS/OSM/Overpass, 0 żądań Commons/Flickr, bez Chrome. 1 dokument BDL w manifeście, 0 nowych fotografii terenu. Po zapisaniu URL i SHA256 usunięto wyłącznie własny wykluczony podręcznik Geomatyka oraz jego render z folderu raw R24. Bezwzględne ścieżki sprawdzono przed usunięciem, brak obu plików potwierdzono. Instrukcja BDL i jej dwa rendery pozostały. Historyczne ścieżki usuniętych plików są jawnie opisane w JSON jako usunięte. Do repo trafiły wyłącznie własne parafrazy, linki i ograniczenia.
