# 04 — DK65: datowany stan inwestycji i organizacja ruchu — WIP

Cel: oddzielić otwartą S19 od aktualnej budowy S16 i archiwalnych zwężeń DK65. Pakiet zawiera 4 rekordy dokumentacyjne, **0 kadrów pobranych / 0 kadrów link-only**. Nie opisuje zdjęć na stronach GDDKiA, których nie oglądano.

## Ustalenia

- 04-D01/02: SOURCED [komunikat GDDKiA z 20.10.2026, źródło i sekcje w manifeście]. Odcinek S19 otwarty. To pierwotne urzędowe potwierdzenie dla luki K1, gdzie dostępne były tylko źródła wtórne.
- 04-D03: SOURCED [komunikat GDDKiA z 18.05.2026]. Dane o Fastach mają datę historyczną i zapowiadany koniec; nie stanowią potwierdzenia organizacji w listopadzie.
- 04-D04: UNVERIFIED — nie odczytano pełnego rekordu aktualnych utrudnień. Nie przeniesiono do generatora samych fragmentów indeksu wyszukiwarki.

## Wnioski i luki

Otwarcie S19 nie oznacza automatycznie końca robót S16 ani likwidacji każdego ograniczenia na DK65. Lokalny stan dojazdów, żółte oznakowanie, zapory, bariery i ich rozmieszczenie na 15.11.2026 pozostają UNVERIFIED. Nie wyprowadzono z komunikatu wymiarów jezdni DK65. Brak nowych pomiarów rozstawu/gatunków drzew, zatok i rowów. Trwa szukanie urzędowych rekordów oraz otwartych kadrów.

Teksty gov.pl: CC BY-SA 4.0 według stopki odczytanych stron. Zdjęcia w stopce mają inną licencję (domyślnie CC BY-NC-ND 4.0), dlatego żadnej fotografii GDDKiA nie pobrano ani nie skopiowano. Do gita trafiają parafrazy i odnośniki.

## Ortofoto — nieregularność drzew

04-O01: ponownie obejrzany K1-132, bez nowego pobrania ortofoto; 1 miniatura ≤800 px. SOURCED [obraz]: po zachodniej stronie pojedyncze korony na pasie trawy, po wschodniej nieregularne grupy z przerwami. ESTIMATED: ręcznie wskazano 6 większych koron; odległości między tymi wybranymi środkami zapisano w `tree-crown-picks.json`, wraz z bbox i skalą. Nie są to potwierdzone kolejne pnie. Nie wyliczono średniego rozstawu wszystkich drzew ani gatunków. Dawnego skrótu K1 „8 drzew / 200 m” nie potwierdzono jako kompletnego inwentarza.

Ponowna próba listy utrudnień15.11.2026: HTTP200 zwróciło tylko212bajtową odpowiedź skryptową ochrony automatyzacji, bez tabeli. Nie wykonywano dodatkowego żądania zasobu ochrony ani rozwiązywania wyzwania. Sam status200 nie jest dowodem odczytu aktualnych utrudnień; pozostają UNVERIFIED.

## Źródłowe oznakowanie czasowe

`temporary-marking/` zawiera17 ustaleń normatywnych SOURCED i1 warunek terenowy UNVERIFIED: żółte/białe oznakowanie oraz U-3/U-20/U-21. Źródła sprawdzono z nowelizacjami do2026. Agent obejrzał6 stron rysunków; koordynator ponownie obejrzał3, dodając wymiary wariantów U-21. To zasady i rysunki urzędowe, nie nowe kadry robót. Nie ustalają rozmieszczenia urządzeń w poszczególnych kaflach.

## Lokalne kadry właściciela — tylko obserwacje tekstowe

Osobno obejrzano3 kadry DK65, bez kopiowania zdjęć do repo ani tworzenia miniaturek. `data/owner-dk65-observations.json` zachowuje opis widocznych robót, poboczy, drzew i oznakowania; daty z nazw nie są potwierdzonym EXIF, kafle i azymuty UNVERIFIED. Widoczny jest fragment żółtych linii w osi oraz prosta biała strzałka na niebieskim kole z tabliczką wyjątku dla pojazdów budowy.

**Korekta kodu znaku:** kształt widoczny na dwóch kadrach odpowiada C-5, a nie C-1. Nazwy sprawdzono w §35 ust.1 pkt5/pkt1 Dz.U.2019poz.2310: C-5 nakazuje jazdę prosto, C-1 w prawo przed znakiem. Robocza wzmianka C-1/nakaz prosto w opisie zdjęć właściciela jest niespójna. Pozostałych małych tarcz i symbolu prawnego żółtych linii nie rozstrzygnięto. To obserwacje chwili zdjęcia, nie inwentaryzacja robót na15.11.2026.
