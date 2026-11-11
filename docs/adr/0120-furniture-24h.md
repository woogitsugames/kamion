# ADR 0120 — Meble uliczne, sesja 8

Data rozpoczęcia: 2026-11-11. Status: praca w toku, bez zgody na integrację.

## r1 — Podmurówki, betonowe latarnie i tyły znaków

Źródło problemów: `docs/reports/visual/REVIEW-2026-11-11-s10-gpt-HIL.md`, I1–I5.
Punktem odniesienia jest main `5f2aa277`, a nie stare rendery ADR 0102.
Czysty poprzedni worktree przeniesiono do `.claude/worktrees/gpt-furniture`;
istniejąca gałąź `gpt-furniture-r1` została przesunięta fast-forward do main.
Dowody tej sesji są w `artifacts/furniture-r1/24h`, wcześniejsze ADR 0102 w katalogu nadrzędnym.

Zakres obejmuje wyłącznie ogrodzenia posesji, prototypy lamp i znaki.
Funkcje barier, ekranów, mostów, drogi oraz cudze pliki pozostają poza zakresem.

Plan sprawdzenia: baseline generatora i importu, wszystkie kamery Low/High przy słońcu
i zachmurzeniu, zmiana, ponowna generacja/import, porównanie każdej kamery.
Draws instancji należy raportować osobno. Liczniki edytora nie są pomiarem telefonu.
Budżet Low: draws +0, trójkąty do +2%; wynik wymaga pomiaru.

Podmurówka ma otrzymać krótsze poziome przęsła tam, gdzie skarpa powoduje
nadmierną odsłoniętą wysokość. Detal betonowych żerdzi powinien wynikać
z istniejącej bazy skanu CC0 i masek zależnych od wysokości oraz okuć.
Aluminiowa tarcza znaku nie otrzymuje korozji żelaza na całej powierzchni:
rdza może spływać od stalowych mocowań, a blacha ma utlenienie i brud.
Wymiary i zasięgi zużycia pozostają WORKING_VALUE do porównania ze zdjęciami.

Referencje lokalne: Mapillary p12/p15/p20/p26/p30 (ADR 0069/0102),
`docs/refs/posesje-bialystok.md` oraz Commons z istniejących manifestów.
Dotychczasowe klatki nie potwierdzają rodziny każdej lampy bocznej ulicy:
mapowanie pozostaje UNVERIFIED. Piksele referencji nie wchodzą do builda.

Przed każdym procesem Unity `unity-slot.ps1 -Acquire -Owner gpt-furniture`,
po nim `-Release`; bardzo wysoki próg StaleHours zapobiega usuwaniu cudzych slotów.
Telefony, push i scalanie do main nie są częścią tej sesji.

## Aktualizacja protokołu obciążenia, 2026-11-11 wieczorem

Po pilnym poleceniu właściciela także build_world, build_all, pełny GIS,
physics/gate3 i fidelity wymagają puli `heavy`, maksymalnie trzy zadania na maszynie.
`artifacts/furniture-r1/24h/heavy-step.ps1` pobiera tę pulę dla aktualnej gałęzi
i zwalnia ją w `finally`. Pełny GIS jest uruchamiany wyłącznie na końcu rundy.
W trakcie stosujemy pojedyncze pliki testów. Bieżący import ma już gotowe produkty
świata i PBR; następne importy sprawdzają ich kompletność przed slotem Unity,
aby skrypt importu nie uruchomił ciężkiego generatora poza pulą.
Gate jest wywoływany z aktualnego main; nie zmieniono wspólnego skryptu w gałęzi.

## Stan przed renderami r1

Baseline generatora: exit 0, 64 chunki, brak `fallback=True` w logu.
Przygotowanie cache PBR: exit 0; wersjonowana specyfikacja materiałów bez zmian.
19 testów mebli przechodzi, w tym krótka stroma skarpa, zakres UV pięciu kształtów
oraz rejestracja maski rdzy pod rzeczywistymi mocowaniami A-7 i C-12.
Niezależne ustalenia kodowe zapisano w `24h/REVIEW-CODE.md` i uwzględniono
w geometrii oraz UV. Nie jest to jeszcze zatwierdzenie wyglądu ani budżetu.

Koszt prototypów lamp i znaków pozostaje bez zmian; stara betonowa lampa Low
ma 91 trójkątów i 4 sloty. Lokalny koszt ogrodzeń wzrasta i wymaga pomiaru
na wszystkich kamerach. Przygotowano 6833 hashe chronionych prymitywów baseline.
Jaśniejszy cokół ma oddzielną teksturę; dane zmieniono addytywnie wyłącznie
w aliasie `furniture_footing` w `materials.py`. Nie dodano slotów prototypu.

Cztery dzienne źródła i atrybucje są w `24h/reference-selection.json`.
Zdjęcie SBS 297817221966185 nie pokazuje czytelnej rdzy; wzór zużycia w modelu
pozostaje propozycją do oceny, nie pomiarem tego konkretnego znaku.
Brak pewnego zbliżenia dokładnie tej okrągłej betonowej latarni nadal pozostaje luką.
