# Zlecenie dla drugiej sesji Codex (z przeglądarką), s21 — ciągłe zbieranie referencji

Wklej:
```
Pracujesz dla projektu Kamion (mobilny symulator ciężarówki, Białystok 1:1 → DK65 → Knyszyn). Repo: C:\Users\matma\Documents\Claude\kamion (GitHub woogitsugames/kamion). Komunikacja po polsku, godziny w czasie Brukseli. Twoja rola: CIĄGŁE zbieranie referencji (zdjęcia, dane, przepisy) dla generatorów świata i ciężarówki. Pracujesz długo (wiele godzin): po każdym pakiecie bierzesz następny z kolejki. Nie piszesz kodu gry, nie uruchamiasz Unity ani adb. Na tej maszynie pracują też lider Claude, jego agenci i druga sesja Codex (worktree knyszyn-rynek-0227).

NAJPIERW przeczytaj: CLAUDE.md, docs/owner/AGENT-RULES.md (zwłaszcza p. 5), docs/LICENSES.md, docs/owner/OWNER-PHOTOS-KNYSZYN.md, research/dk65-knyszyn-refs/README.md (K1, wzór formatu manifestu), docs/owner/MISTRAL-FIXES-12.md (format bloków M*-FIX) i docs/reports/REVIEW-2026-11-15-s20-mistral-m59-fix.md.

IZOLACJA: `git worktree add .claude/worktrees/codex-refs-s21 -b research/codex-refs-s21 origin/main`; pracujesz TYLKO tam. Push tylko tej gałęzi (nigdy main). Duże pliki (> 5 MB lub > 200 zdjęć na pakiet) trzymaj poza gitem w `C:\Users\matma\Documents\Claude\kamion\Data\raw\refs\codex-s21\<pakiet>\`, a do gita daj tylko manifest i miniatury ≤ 800 px.

ŹRÓDŁA DOZWOLONE: Wikimedia Commons, Openverse (CC0/CC BY/CC BY-SA), Flickr tylko z licencją CC0/BY/BY-SA, Panoramax, KartaView, Mapillary (przeglądarka; nie wypisuj tokenów), OSM/Overpass, Geoportal GUGiK (ortofoto, BDOT10k, LoD), BDL, otwarte dane miast i gmin, ISAP/Dz.U., UNECE, GDDKiA (dokumenty publiczne), PKP PLK (dokumenty publiczne). Zdjęcia z mediów, sklepów, forów, Facebooka i stron firm: TYLKO jako link w manifeście z dopiskiem „link-only, all rights reserved”, bez pobierania.
ZAKAZ: Google Maps, Street View, Google Earth, 3D Tiles (także przez inne narzędzia AI), generatory obrazów AI, logowanie się na cudze konta, CAPTCHA. Nagłówki HTTP i User-Agent bez nazwy projektu i danych właściciela. Rozsądne tempo zapytań (bez masowego scrapowania; Overpass ≤ 1 zapytanie / 10 s).

FORMAT KAŻDEGO PAKIETU: katalog research/codex-refs-s21/<NN-temat>/ z README.md (cel, wnioski, liczby z oznaczeniem SOURCED [źródło] / ESTIMATED / UNVERIFIED) i manifest.csv: id, plik_lub_url, źródło, autor, licencja, data zdjęcia, współrzędne (jeśli są), kierunek patrzenia (jeśli znany; zaznacz magnetyczny/geograficzny), CO WIDAĆ (z obejrzenia obrazu, nie z tytułu), do czego w grze. Każdy kadr OBEJRZYJ, zanim go opiszesz. Opis sprzeczny z obrazem albo SOURCED bez źródła to błąd (za to odrzucaliśmy wcześniejsze pakiety). Nie zmyślaj liczb.

KOLEJKA (w tej kolejności; po skończeniu wróć na początek i pogłębiaj tam, gdzie najmniej materiału):
1. M59-FIX luki (lampy ciągnika i naczepy): zbliżenia lamp tylnych i przednich ciężarówek europejskich z czytelnym znakiem homologacji ECE (E-numer, R48, R148/R149/R150, R7, R6, R4), kolumna wartości (kolor, kształt, liczba komór) dla każdego kadru; dane fotometryczne z regulaminów UNECE (cytuj paragrafy).
2. M61-FIX luki (brud tyłu naczepy): ≥ 20 kadrów drzwi naczep z brudem, ≥ 6 zimowych (sól, błoto pośniegowe), ≥ 6 z europejskich dróg; opis rozkładu brudu (strefy, wysokość, smugi).
3. Knyszyn (dla sesji Codex knyszyn-rynek-0227): Rynek, fontanna, kamienice pierzei, kościół, nawierzchnie, zieleń, mała architektura, znaki; ulica przelotowa DK65 przez miasto. Proporcje i kolory elewacji, liczba kondygnacji, typ dachu. Co godzinę dopisz najważniejsze wnioski do `artifacts/live/codex-refs-s21.md` w GŁÓWNYM katalogu repo (tam też czyta je sesja knyszyn-rynek).
4. Korytarz DK65 Białystok → Knyszyn (kafle dk65-01…11): szpalery i aleje drzew (gatunki, rozstaw, odsunięcie od jezdni), place budowy S19 (oznakowanie tymczasowe żółte, zapory, wygrodzenia), bariery, zatoki autobusowe, przystanki, ekrany, zjazdy do posesji, rowy i pobocza.
5. Linia kolejowa nr 38 (Białystok–Ełk) w okolicy DK65 i Knyszyna: przejazdy (kategoria A–D, rogatki, sygnalizacja, krzyże G-3/G-4), nawierzchnia przejazdu, słupy trakcyjne (czy linia zelektryfikowana: SOURCED), podsypka.
6. Następny pierścień regionów (docs/owner/S20-REGION-RING-BRIEF.md, PR #66 R9): Mońki, Tykocin, DW671 — charakterystyczne obiekty, zabudowa, ronda.
7. Białystok trasa C i Dojlidy: luki wskazane w docs/owner/BACKLOG-S21.md (filtruj „research” i „ref”).

ZAPIS POSTĘPU: po każdym pakiecie commit + push gałęzi research/codex-refs-s21; co ok. godzinę wpis w `artifacts/live/codex-refs-s21.md` w GŁÓWNYM katalogu repo (to jedyny plik, który wolno ci tam zapisać): godzina, pakiet, liczba kadrów (pobrane / link-only), najważniejsze liczby, NASTĘPNY pakiet. Po każdych 2 pakietach otwórz albo zaktualizuj PR (nie draft) research/codex-refs-s21 → main z raportem do 20 linii po polsku (co zebrano, licencje, czego brakuje, „Gotowe do scalenia po recenzji lidera: TAK/NIE”). NIE scalaj. Nie commituj zdjęć właściciela.
```
