# M59 — ledger istniejących dowodów, obieg6

Audyt dokumentacyjny istniejących manifestów i zapisanych oględzin z15.11.2026. **0 nowych oględzin, 0 pobrań.** Nie jest to wymagany w M59 audyt wizualny≥20% wierszy ani deklaracja zamknięcia M59. Kwalifikacje są rekonstrukcją zapisanej dokumentacji; CSV wskazuje manifest i review dla każdego ID. Powtórzone wpisy w manifeście głównym i podkatalogach liczone raz. Miniatura/wycinek/powiększenie/review nie są nową fotografią.

## Kryteria i jednostki

SOURCED [docs/owner/MISTRAL-FIXES-12.md, M59-FIX pkt2; docs/reports/REVIEW-2026-11-15-s20-mistral-m59-fix.md, pkt1 iFIX4]: potrzeba≥15 zbliżeń **tylnych** lamp zespolonych ECE ciągników/naczep; lampa≥10% szerokości kadru albo≥300px na wycinku oryginału. W tej grupie≥4włączone i≥3zmierzch/noc; osobno≥5lampek tablicy ciężarówek/naczep. Widoczność funkcji, optyki, komór, emisji i barw nie wynika automatycznie z E. Ten ledger dodatkowo rozdziela rygorystyczny odczyt E+numer+symbole, którego nie utożsamia z ukończonym progiem15.

## Liczniki z dokumentacji

SOURCED [manifest.csv w katalogu nadrzędnym,37unikalnych ID; ledger.csv]: **37 wybranych kadrów**:8lokalnych i29link-only. Pięć kadrów LNK to katalogi z niepotwierdzoną techniką wykonania; nie twierdzimy, że wszystkie37są fotografiami fizycznych egzemplarzy. Jeden kadr może pokazywać dwie lampy; trzy kadry jednej galerii nie oznaczają trzech egzemplarzy.

- **4kadry z E+pełnym numerem w odczytanym zakresie+symbolami**: EUP-001 (tylny klosz E9/5497), VOL-003 (przednia etykieta E9, odrębne grupy30/6243), FA5-01 (przednia etykieta E2/11057 po korekcieURL), EUP3-003 (**tylko boczna grupa** E9/6985 przySM1/IA). To4różne zespoły części w dokumentacji; nie4pełne homologacje tylnych lamp. Numer głównej grupy EuropointIII pozostajeUNVERIFIED;6243 nie łączono z30 w jeden numer.
- **1kadr tylko z pewnym symbolemE**: UP4-03 E2, numer i funkcjeUNVERIFIED. Dodatkowe **4kadry E+symbole bez pełnego numeru**:01-001 E1/S1 (strażacki), LNK-004/005 E9/L-00 (katalog, zastosowanie ciężaroweUNVERIFIED), EUP3-002 przycięteE9 i funkcje. Nie scalać dwóch kadrów EuropointIII w rekonstrukcję przetartego numeru głównego.
- **1kadr MD/EMC**: MAN-002, E1 przy10R oraz MD E24 5884. Nie zaliczono pełnej homologacji fotometrycznej. Dodatkowe EMC widoczne przy EUP-001 iFA5-01 nie są nowymi kadrami/egzemplarzami.
- **1nocny kontekst emisji zestawu**: RN3-04, czerwone tylne pola ciągnika i odbicia pod przednią częścią naczepy;1fotografia/1zestaw, nie2fotografie za dwa zespoły lamp. E i konkretna funkcjaUNVERIFIED; **0potwierdzonych włączonych/nocnych zbliżeń w grupie kwalifikacyjnej M59**.
- **1AUXnocny**: RNE5-02, ciężarówka z żurawiem i platformą, niepotwierdzony ciągnik+naczepa. Tylnego prześwietlonego punktu nie przypisano do pozycji/stopu. Pozostałe22wybrane kadry to kontekst bez pewnegoE oraz3kadry katalogowe bezE (kategorie rozłączne wCSV; częścioweE opisano powyżej).

SOURCED [cztery manifesty nocne i reviews wCSV]: poza głównym37skatalogowano **9obejrzanych odrzuceń** i **3NOT_REVIEWED**. To zamknięty zakres tych czterech dzienników, **nie całkowity bilans wszystkich historycznych wyszukiwań**. Starsze `query_log.json` i`agent-lamps-search-log.json` zawierają kolejne odrzucenia i blokady; nie dodano ich do9ani nie policzono nieobejrzanych metadanych jako fotografii. Nie zmieniono ich historycznych opisów.

## Egzemplarze i nadal otwarte braki

Globalna liczba unikalnych fizycznych egzemplarzy w37kadrach: **UNVERIFIED**. `grupa_egzemplarza` i`liczba_egzemplarzy_i_limit` jawnie grupują galerie: Volvo3→1reflektor; MAN2→1lampa; EuropointII2→1; EuropointIII3→1; IvecoTediTrans4→1; DAF2→1; RenaultFA53→1. To7grup z19kadrami, nie dowód globalnej unikalności pomiędzy wszystkimi źródłami. Dwa przeciwne widoki IvecoIro i dwie lampy kompletu RenaultUP4 zachowano rozdzielone; nie uznano ich za jedną część. Katalogi nie dają potwierdzonych fizycznych egzemplarzy. Nocny zestaw liczymy jako pojazd/zestaw, a nie egzemplarz lampy.

**M59 nadal NIESPEŁNIONE.** EUP-001 to1najmocniejszy kandydat tylnego zbliżenia z pełnym odczytem na kloszu i niezależnymreview; w tej rundzie nie mierzono ponownie≥10%/300px. Formalny licznik spełnienia całego progu15 pozostajeUNVERIFIED, nie utożsamiamy go z liczbą odczytówE. Brakuje kolejnych tylnych zbliżeń o udokumentowanej geometrii, całej wymaganej podgrupy4włączonych/3nocnych zbliżeń oraz5lampek tablicy o potwierdzonym zastosowaniu ciężarowym. Samo L EuropointIII lub okienko pod spodem nie dowodzi obserwacji pracy lampki; brak montażu nie jest osobnym progiem, lecz trzeba potwierdzić zastosowanie i widoczną optykę. Obecny bezsporny licznik takich referencji tablicy w dokumentacji:0; dwa generyczne LNK pozostają pomocnicze.

Braki jakościowe: pełny numer głównej grupy EuropointIII, pełny numer/funkcjeDAF, jednoznaczne przypisanie pól do funkcji, liczba komór vs pola optyczne, warunki świecenia i wygląd po włączeniu. PrzednieFH4/Renault są wartościowe dla własnego zakresu, ale nie zwiększają tylnych progówM59. Homologacje nadal nie są identyfikacją certyfikatu ani dowodem aktualności prawnej2026.

Zakres czasowy: snapshot głównego manifestu37kadrów po commicie524a421f7, odczyt15.11.2026. Późniejsze kadry wymagają osobnego uzupełnienia; liczby nie są automatycznie bieżącym stanem gałęzi. Koordynator sprawdził rozłączność kategorii i rozdzielenie4odczytów na2przednie/1tylny/1bocznągrupę, bez nowych deklarowanych oględzin.
