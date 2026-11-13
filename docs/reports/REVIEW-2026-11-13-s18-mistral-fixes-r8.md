# Przegląd zgłoszeń Mistrala „M44/M46/M48/M49/M52/M54/M55-FIX gotowe” + ZIP P11 v2b — s18, 2026-11-13

Zakres: zgłoszenie właściciela „M46-FIX, M44-FIX, M49-FIX, M54-FIX, M55-FIX, M52-FIX gotowe” oraz M48-FIX (dopisane przez lidera). Wymagania: `docs/owner/MISTRAL-FIXES-8.md`. Poprzednie przeglądy: `docs/reports/REVIEW-2026-11-13-s17-mistral-r8-*.md`. Stan po `git fetch` (origin/main @ 93e2b3173). Niczego nie scalono, nie wypchnięto ani nie skomentowano.
Pozostałe błędy do przekazania Mistralowi są w `docs/owner/MISTRAL-FIXES-9.md`.

## 1. Werdykty

| FIX | PR | Gdzie jest poprawka | Werdykt | Akcja lidera |
|---|---|---|---|---|
| M44 | #41 (scalony) | `origin/research/mistral-p4-truck-regulations` +1 commit `e7bfc91c3` „M44/FIX r2” | **PRZYJĘTY** | scalić (komenda niżej) |
| M52 | #48 (scalony) | `origin/research/mistral-p2-surfaces-2` +1 commit `a6c5110a6` „M52-FIX r2” | **CZĘŚCIOWO** (rysunki OK, kadry nie) | scalić r2 (poprawia main) + M52-FIX-3 |
| M49 | #46 (scalony) | już w main (`f7a4f289f`), przyjęty w ponownym przeglądzie s17; gałąź `research/mistral/p6-dojlidy-gates` (slash) to duplikat | **PRZYJĘTY** (bez zmian) | nic nie scalać; drobiazg w M49-FIX-2 |
| M46 | #43 (scalony) | w main (`398d5ae3f`), gałąź 0 commitów ponad main | **PRZYJĘTY** (bez zmian) | nic |
| M54 | #44 (scalony) | w main (`f48342bb6`, `10effe7d0`), 0 commitów ponad main | **PRZYJĘTY Z ERRATĄ** (jak w s17) | M54-FIX-2: 2 opisy w photos.csv |
| M55 | #47 (scalony) | w main (`3b5ee5156`), 0 commitów ponad main | **PRZYJĘTY** (bez zmian) | nic |
| M48 | #40 (scalony) | w main, 0 commitów ponad main | **PRZYJĘTY** | opcjonalnie M48-FIX-2 (pliki data/) |
| P11 ZIP v2b | #39 (scalony) | `research/_incoming/mistral-p11-dojlidy-photos-v2b/files` (135 JPG) | **CZĘŚCIOWO**: obraz bez zmian, opisy znaków błędne w 3/7 | M47-FIX-2 |

W przypadku M46, M54, M55 i M49 Mistral zgłosił jako „gotowe” pracę, którą ponowny przegląd s17 już sprawdził i która jest scalona. Po tamtym przeglądzie nie ma nowych commitów.

## 2. Komendy scalenia (dla lidera; nie wykonano)

```
git fetch origin
git checkout main && git pull --ff-only
git merge --no-ff origin/research/mistral-p4-truck-regulations -m "Merge Mistral M44-FIX r2 (p4-truck-regulations) after s18 review"
git merge --no-ff origin/research/mistral-p2-surfaces-2 -m "Merge Mistral M52-FIX r2 (p2-surfaces-2) after s18 review"
git push origin main
```

`git merge-tree --write-tree origin/main <gałąź>`: obie gałęzie scalają się bez konfliktów. Każda zmienia 4 pliki, wyłącznie w swoim katalogu `research/mistral/p4-…` lub `p2-…`. Zmiany względem merge-base: p4 +53/−27, p2 +416/−268.
Gałąź `origin/research/mistral/p6-dojlidy-gates` (ze slashem) dodaje 4 pliki identyczne z main (`git diff origin/main` pokazuje tylko brak `.gitignore`). Scalenie byłoby pustą operacją. Gałąź można usunąć: `git push origin --delete research/mistral/p6-dojlidy-gates` (decyzja lidera).

## 3. Szczegóły

### M44 r2 — PRZYJĘTY
Sprawdzone 3/3 punkty ponownego przeglądu s17 (REVIEW-…-p4.md, l. 118–120):
- (a) CMS dla klas II/IV. README §3 (l. 42), „Punkty otwarte (a)” (l. 113–123) i `uwagi` P4-093 teraz mówią: „TAK od Suppl. 2 do serii 04 (E/ECE/324/Rev.1/Add.45/Rev.6, 18.06.2016); w OJ tylko 04 + Suppl. 1; status w UE S”. Zgadza się z ustaleniem przeglądu.
- (b) Pełna lista zmian Dz.U. 2026/891: § 2, 6, 7, 18, 19, 20, 21 pkt 1, 22 i zał. 13. Zał. 12 bez zmian. Zgadza się z ELI (przegląd s17).
- 520×114: opis metody zmieniony na „odczyt etykiet wymiarowych”, piksele służą tylko do kontroli. Dodano R10 i ramkę 7 mm.
- P4-134: `warunek` doprecyzowany (pkt 3.3), zbędny nawias usunięty.
- Drobiazgi, które nie blokują scalenia: (1) README l. 42 przypisuje cytat „optional replacement of mirrors of Classes I to IV…” Suplementowi 2, a to cytat z propozycji GRSG/2015/2 (l. 119 podaje to poprawnie); (2) numer „pkt 6.2.1.3” różni się od „6.2.2.3” w przeglądzie s17. Nie weryfikowałem ponownie tekstu Rev.6, bo nie ma go lokalnie.

### M52 r2 — CZĘŚCIOWO
- Rysunki, punkty (a)–(c) z ponownego przeglądu s17: manifest r2 zgadza się z faktami, które przegląd s17 odczytał ze stron 539/571–573 Dz.U. 2019/2311 (render 150 dpi). Wartości: P-3b kreska/przerwa 1,00/1,00 (M52-006 uwagi, README l. 115); P-13 podstawa 0,50, wysokość 0,70, odstęp 0,25 (M52-019; hipoteza 0,75 wycofana); P-12 szer. 0,50 (M52-017); P-14 0,75 × 0,50, odstęp 0,25 (M52-021/022). Kolumny `kolor_srgb`/`metoda_koloru` usunięte (17 kolumn, sprawdzone w nagłówku). `.gitignore` jest. W tej rundzie nie renderowałem PDF ponownie i opieram się na odczycie s17. Nowe etykiety r2 (P-7a/P-7c, P-21, P-23, P-25) są niesprawdzone.
- (d) P-5 nie jest domknięte. M52-012 nadal pisze o „rozbieżności 2× wewnętrznej rozporządzenia”, choć M52-011 sam stwierdza 2 pary linii (0,32 = 2 × 0,16).
- Błędy kopiuj-wklej w `uwagi`: M52-006 (zaczyna się od „przerwa 2,00 m”), M52-014/015 (uwagi zamienione), M52-027 (sprzeczne zdania). P-3b kreska/przerwa nie ma osobnego wiersza.
- Kadry: README r2 przyznaje, że kadry nadal NIE są obejrzane („nie obejrzano w sesjach M52-FIX/r2”). Obejrzałem próbę 4 kadrów (route/andersa-2769366-03, crossings/cross-tys-07, crossings/cross-andersa-10, route/sokolska-02). Wynik: 3 zgodne co do ulicy i obiektu (Andersa z EC w tle, Tysiąclecia przy skrzyżowaniu, estakada z barierami). **1 błędny: sokolska-02 (M52-104) leży na Al. Tysiąclecia.** Overpass `way(around:25)` w 53.151415, 23.154418 zwraca tylko Al. Tysiąclecia (536419697, 946729184, 999223603) i ścieżki. M52-103/105 to ta sama sekwencja 1155711 w odległości ≤ 10 m. Wszystkie 3 wiersze „Sokólska” są więc błędne, a to ten sam błąd przypisania co w P1B.
- Ocena: r2 jest lepsze od tego, co jest w main (rysunki), więc warto je scalić. Kadry wracają do Mistrala (M52-FIX-3).

### M49 — PRZYJĘTY (w main)
Punkty 1–6 sprawdzone w main (README §4, §6, §7, §11; manifest): G10 UNVERIFIED, wartości 11/8,3 usunięte; G12 UNVERIFIED; RS16 to pas do Miasta, 1296 m od parkingu przy DK19, ESTIMATED ±50 m; TVP3 cytowane tylko z tytułu; Karpińskiego unclassified. ZIP v2 (`research/_incoming/mistral-p6-dojlidy-gates-v2/files`) zawiera 13 plików R-*.png (bez R-G10, celowo), M49-G12-gate.jpg, PFU 2015/2020 i zał. 5.
Obejrzałem M49-G12-gate.jpg (1600×1600). Widać teren EC: zbiornik akumulacyjny, rurociągi, płot, wjazd od Bitwy Białostockiej. Okno obejmuje bramę, jak deklarowano. Obejrzałem też R-G05.png (400×400): łącznik z rondem Hasbacha z naczepą na łuku, zgodne z definicją J w FILES.md.
Drobiazg: `uwagi` M49-030 („node = wjazd drogowy”, „wjazd ciężarowy od Elewatorskiej”) przeczą G10 UNVERIFIED. Trafia do M49-FIX-2.

### M46 — PRZYJĘTY (w main, bez zmian od s17)
Ponowna próba 4 kadrów z ZIP v2 (P1B-005, 012, 020, 030): 4/4 opisów zgodnych z obrazem. P1B-005 to bloki z rozmyciem ruchu, jakość 2. P1B-012 to jezdnia estakady bez ringu. P1B-020 to łukowy wiadukt z banerem Opery Podlaskiej. P1B-030 to baner „WYNAJMĘ” i autobus.

### M54 — PRZYJĘTY Z ERRATĄ (w main)
`photos.csv` **jest w gicie** (`research/mistral/p8-restrictions-3/photos.csv`). REVIEW-NOTE błędnie podaje „ZIP, poza gitem”. Plik nadal zawiera oba błędne opisy z s17 (l. 28 `s8_0a2121ca` „nierówności”, l. 37 `wolukrainy_4ac8cbd1` „B-1”). Trafiają do M54-FIX-2.

### M55 — PRZYJĘTY (w main, bez zmian od s17)
Ponowny przegląd s17 (bitrate ffprobe 8/8, atrybucje, analiza B8R) jest aktualny. Nie ma nowych commitów.

### M48 — PRZYJĘTY (w main)
- (1) Flagi `poza_kaflem` sprawdziłem pyproj (EPSG:4326 → 2180) dla 39 landmarków w `data/landmarks.json` i `data/landmark-colors.json`. **Wynik: 17 `true`, 22 `false`, 0 niezgodności z kaflem [779019, 589055, 781067, 591103].** BISON (034) i Odlewnia (036) mają `false`, hangar (004) ma `true`.
  **Errata 13→17:** poprawna liczba to **17**. „13” było tylko w komentarzu M48-FIX pod PR #40. Mistral sprostował to w kolejnym komentarzu (lista 17 ID: 003, 004, 006, 007, 015, 024, 026–033, 035, 037, 039). README nie podaje tej liczby wprost (w tekście są markery „poza kaflem”). Manifest ma 18 wierszy P12-0xx z frazą „poza kaflem”, ale 18. to P12-001 z opisem „zachodni koniec nieco poza kaflem”, a jego flaga to `false`. To spójne.
- (2) Linki Commons: 5/5 tytułów `File:` zgodnych z API (pageids 30474259, 52199842, 20463837, 30730935, 21441453).
- (3) A-11a = „próg zwalniający” (P12-072, README l. 101).
- (4) Art-Glas/Zintronic: wspólny plac z jedną bramą OSM (node 2999785151), osobne bramy UNVERIFIED (README l. 155). Akceptowalne, bo FIX dopuszczał UNVERIFIED.
- (5) Surowe zrzuty OSM usunięte, sposób odtworzenia opisany, `tools/` w katalogu paczki. W `data/` zostały jednak oprócz 3 wymaganych plików także `road-geom.json` (551 KB), `region-summary.json`, `typologia*.json`. To nie blokuje, ale trafia do opcjonalnego M48-FIX-2.

### P11 ZIP v2b — 7 zmienionych kadrów
Wymiary są identyczne z v2. Różnica to tylko kodowanie (rozmiar pliku ±0–10 %), treść obrazu się nie zmieniła (porównanie wizualne v2 i v2b). Manifest w main: 154 wiersze, 135 SOURCED = 135 JPG. Wszystkie 7 obejrzałem w całości, a 002, 057 i 120 dodatkowo w zbliżeniach na znaki:

| Kadr | Obiekt główny | Znaki / ulica |
|---|---|---|
| P11-002 | ✓ hala Masterpress, płot z żywopłotem, czerwone słupki | ✗ „zakaz wjazdu”: w kadrze jest niebieska tablica z ciężarówką w kole i tabliczką „12t” (wskazanie drogi dla ciężarówek) oraz D-1 |
| P11-057 | ✓ dom z dachem dwuspadowym, laweta „POMOC DROGOWA” | ✗ „zakaz skrętu w lewo, zakręt”: w kadrze jest A-30 („!”) z tabliczką ze strzałką przesunięcia |
| P11-072 | ✓ łuk jezdni, ciąg latarni, tablica projektu UE, trawa | — |
| P11-107 | ✓ brama cmentarna z krzyżem prawosławnym i kratą | — |
| P11-120 | ✓ brama browaru z zielonym ogrodzeniem | ✗ „zakaz wjazdu, STOP”: w kadrze jest B-36 i stosy kegów; ✗ ulica „Kuronia” przy d = 374 m |
| P11-143 | ✓ czerwony budynek WSWFiT z szyldem „Mickiewicza 49” | „taśma” to szlaban; ulica „Suchowolca” przy d = 145 m |
| P11-144 | ✓ pałac Lubomirskich, parking, piesi | ulica przy d = 235 m |

Wynik: obiekty główne 7/7 poprawne, znaki zmyślone w 3/7. Trafia do M47-FIX-2. Ważne dla P8: przy Masterpress (Kuronia) stoi znak kierujący ciężarówki „12t”.

## 4. Czego nie sprawdzono
- PDF Dz.U. 2019/2311 i R46 Rev.6 nie były pobierane w tej rundzie. Ocena M52 (rysunki) i M44 opiera się na odczytach ze źródeł z ponownego przeglądu s17.
- Nowe etykiety M52 r2 (P-7a/P-7c, P-21a/b, P-23, P-25) są niesprawdzone.
- Pozostałych 74 kadrów M52 i reszty manifestu P11 nie oglądałem (próba: M52 4, P1B 4, P11 7, P6 2).
