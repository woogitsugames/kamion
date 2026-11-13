# Przegląd M47-FIX-2 (P11 zdjęcia Dojlidy) — s20, 2026-11-13

**Werdykt: FIX ponownie** (pkt 4 bloku). Punkty 1, 2, 3 i 5 są przyjęte. Pełny audyt znaków (pkt 4) ma błędy w **13 z 27** sprawdzonych wierszy. W 9 z nich pojawiły się nowe zmyślone albo błędne kody (m.in. STOP w P11-087). Znaki zostały więc dalej zmyślane. Do tego wraca zgłoszony błąd naszego przeglądu s18 (P11-120 ma STOP). Blok poprawek: `docs/owner/MISTRAL-FIXES-11.md` § M47-FIX-3. Nic nie scalono i nic nie scommitowano. Komentarza w PR nie ma.

## 1. Zakres i metoda

- Commit `3da410039` na `origin/research/mistral-p11-dojlidy-photos`. Gałąź nie jest zrebase'owana (Mistral nie miał `git`). Mimo to `git diff --stat origin/main...3da410039` pokazuje **tylko 4 pliki** w `research/mistral/p11-dojlidy-photos/`: README, REVIEW-NOTE (identyczny z main), audit_20_percent.json i manifest.csv. Rodzic `b719292dd:manifest.csv` jest bajtowo równy `origin/main`, więc konfliktów nie ma. Diff stat w komentarzu PR #39 „odtworzono w difflib” i nie jest SUROWY: podaje 213/283/94, a git 215/284/95. To drobiazg.
- Diff wierszy (skrypt `python -I` w scratchu): 154→154 wiersze. Zmiany: `punkt_opis` 46 (43 znakowe + 3 erraty s17: 026, 027, 115), `typ_kadru` 1 (042), `uwagi` 1 (002), `ulica` 22. Kolumny licencji, autora, url i statusu są bez zmian.
- Oglądałem zdjęcia z `research/_incoming/mistral-p11-dojlidy-photos-v2b/files`. Każde pomniejszyłem do 960 px, a znaki obejrzałem na wycinkach z pełnej rozdzielczości 1600 px (powiększenie 2–5×, ImageMagick). Sprawdziłem **29 wierszy**, w tym 27 z poprawionym opisem znaku. Kody sprawdzałem według katalogu z Dz.U. 2019 poz. 2310.

## 2. Punkty bloku M47-FIX-2

| # | Punkt | Wynik |
|---|---|---|
| 1 | P11-002: tablica 12t + D-1, współrzędne i kierunek w uwagach | **OK.** Na wycinku widać 2× niebieską tablicę z ciężarówką w kole, strzałką skrętu i tabliczką „12t” oraz 2× D-1. W uwagach jest pozycja zdjęcia, oś jezdni E–W (~97°/277°), kierunek kamery UNVERIFIED i hala z Nominatim (OSM, legalne). Uwaga: kod tablicy nie został podany. Opis „wskazanie drogi dla ciężarówek” bez kodu jest poprawny. Dla P8 to istotne. |
| 2 | P11-057: A-30 z tabliczką | **OK.** A-30 na żółtym tle (oznakowanie tymczasowe) z tabliczką ze strzałką objazdu/przesunięcia. Na lawecie napis „POMOC DROGOWA”, bez marki. |
| 3 | P11-120 B-36 + kegi, `ulica`; 143 szlaban; 143/144 `ulica` | **OK według bloku, ale błąd po naszej stronie:** na wycinku bramy (x≈1020–1220, y≈650–800) **stoi znak B-20 STOP**. Przegląd s18 („brak STOP”) był w tym punkcie błędny, a Mistral usunął STOP zgodnie z poleceniem. B-36 i kegi są poprawne. B-2 nie ma (przy furtce są tylko tablice informacyjne). Szlaban w 143 jest poprawny. `ulica` = UNVERIFIED w 120/143/144 jest poprawne. Niespójność: `punkt_opis` nadal zaczyna się od „Jacka Kuronia —” (120, 122) i „Księdza Stanisława Suchowolca —” (143, z szyldem „Mickiewicza 49”). |
| 4 | Pełny audyt znaków w manifeście | **NIE.** Patrz §3. |
| 5 | `ulica` dla d > 25 m | **OK.** Obsłużono wszystkie 22 wiersze z d > 25 m według `uwagi` (082, 085, 090, 091, 120–126, 131–136, 139, 140, 142–144); poza nimi żaden wiersz nie ma d > 25 m. Wiersze 082 (d = 26,3) i 085 (d = 25,3) dostały „Myśliwska”. W PR podano odległość do Myśliwskiej 16,7 i 22,9 m (d w manifeście to odległość do poligonu ronda), ale **w `uwagi` tego nie dopisano**. Nie sprawdzałem tego (brak osmium/ogr na hoście). |

Erraty s17 (026, 027, 115, 042) zostały wprowadzone poprawnie. README §7 i §8 oraz `audit_20_percent.json` są spójne z manifestem, więc powtarzają też błędy z §3 (np. P11-128 „A-16”).

## 3. Oględziny znaków — 27 wierszy

✓ = kody zgodne z obrazem (dopuszczam pominięcie drobnego znaku), ✗ = błędny lub nieistniejący kod.

| id | Opis M47-FIX-2 | Co widać (wycinek pełnej rozdzielczości) | Ocena |
|---|---|---|---|
| 001 | B-33 20 | B-33 „20” z tabliczką; po prawej F-10 (kierunki na pasach) — pominięty | ✓ |
| 002 | tablica 12t + D-1 | jw. §2 | ✓ |
| 005 | C-2 | C-2 (strzałka pozioma w prawo) | ✓ |
| 013 | A-16, D-6, okrągły nieczytelny | **brak A-16**; D-6; okrągły = C-13/16 (pieszy + rower, czytelny); **A-7 (od tyłu) przy tablicy ulicy i A-7 nad D-6 w głębi — usunięte jako „zmyślone”** | ✗ |
| 014 | B-36 + tabliczka | B-36 z tabliczką tekstową; sygnalizacja | ✓ |
| 022 | A-7, B-2 | A-7 (od tyłu) ✓; **B-2 brak** — żółta tablica „zakaz wstępu / teren …” na ogrodzeniu | ✗ |
| 030 | „znak nieczytelny (biała tarcza z czerwonym obramowaniem)” | **B-2 wyraźny** (czerwona tarcza z białym pasem) + tabliczka „Nie dotyczy pracowników …” — stary opis „zakaz wjazdu” był POPRAWNY | ✗ (regres) |
| 037 | D-1 | D-1; żółta tablica „Uwaga zakaz wstępu na teren budowy” | ✓ |
| 039 | B-33 30, D-40, A-16, B-36 | B-33 30 ✓, B-36 ✓; **A-16 to D-6**; **D-40 brak** (jest D-3/niebieski kwadrat ze strzałką i D-18) | ✗ |
| 041 | D-18 + tabliczki SPP | D-18 ze strzałką + tabliczka z tekstem częściowo nieczytelnym; „strefa płatnego parkowania” nie wynika z kadru | ✓ (drobne) |
| 043 | B-5 + tabliczka | B-5 + tabliczka | ✓ |
| 054 | C-13, C-1/C-2 | C-13 ✓; strzałka ukośna w dół-prawo = **C-9**; A-7 od tyłu; sygnalizacja | ✗ |
| 057 | A-30 + tabliczka | jw. §2 | ✓ |
| 063 | C-1/C-2 | C-2 ✓; pominięte C-13 i **sygnalizacja** (s17: 063 ma sygnalizację) | ✓ (drobne) |
| 066 | B-5, B-20 | B-5 + tabliczka; ośmiokąt od tyłu (STOP) | ✓ |
| 073 | D-6, B-9, A-7 | A-7 od tyłu ✓; **B-9 brak** — okrągły niebieski C-13/16; **D-6 nie widać** (jest tylko zebra) | ✗ |
| 078 | B-33 20, A-16, niebieski nieczytelny | **B-33 „70”** (nie 20), B-36, D-3, **D-6 (nie A-16)**, C-13; **C-12 (×2) i A-7 wyraźne — usunięte** („nakaz dookoła ronda” był POPRAWNY) | ✗ |
| 079 | B-2, B-33 70, C-3/C-4, „kwadratowy z rowerem” | B-33 70 ✓; **B-36 (nie B-2)**; **D-3 (nie C-3/C-4)**; C-13 **okrągły**; D-6 po lewej | ✗ |
| 081 | C-12 | A-7 nad C-12 (A-7 pominięte) | ✓ |
| 086 | B-2, A-16, tablice 678 | B-2 ✓, tablice 678 ✓; **D-6 (nie A-16)** ×2 | ✗ |
| 087 | B-20 STOP | **B-2 (zakaz wjazdu)** pod A-7 od tyłu — STOP **zmyślony** | ✗ |
| 108 | D-6, B-2, trójkąt nieczytelny; „skrzyżowanie z sygnalizacją” | D-6 ✓; **B-5 + tabliczka (nie B-2)** — ważne dla P8; **brak trójkąta**; okrągły na słupie po lewej to lustro drogowe; sygnalizacji nie widać | ✗ |
| 120 | B-36 + kegi | B-36 ✓, kegi ✓, **B-20 STOP przy bramie** (błąd s18) | ✓ wg bloku / errata nasza |
| 128 | A-16, D-18, Starostwo | D-18 ✓, budynek nr 2 z flagami ✓; **D-6 (nie A-16)** | ✗ |
| 129 | B-20, B-33 20, C-1/C-2, szlaban | wszystko ✓ (strzałka zakrzywiona = C-1); w głębi B-2 — pominięty | ✓ |
| 131 | B-2, B-35 | **2× B-36** + tabliczka T-24 (odholowanie) + tablica „Droga pożarowa” — B-2 i B-35 brak | ✗ |
| 143 | szlaban | szlaban biało-czerwony ✓ | ✓ |

Dodatkowo, bez liczenia: 068 — D-6 i TAXI potwierdzone, A-7/D-40 nierozstrzygnięte w 960 px. 106 — D-6 i sygnalizacja ✓; „znak ostrzegawczy” to żółta skrzynka przycisku dla pieszych (nie znak).

**Wynik: 14/27 ✓, 13/27 ✗ (48 %).** Wzorce błędów:
- (a) **D-6 opisane jako A-16** w 5 wierszach (013, 039, 078, 086, 128). Niebieski kwadrat z pieszym to D-6, A-16 to czerwony trójkąt.
- (b) **Zmyślone lub błędnie odczytane znaki zakazu**: B-2 w 022/079/108/131, B-20 w 087, B-9 w 073, D-40 w 039, B-35 w 131, „20” zamiast „70” w 078.
- (c) **Usunięte znaki, które widać**: A-7 w 013, C-12 i A-7 w 078, B-2 w 030, STOP w 120 (nasz błąd). W `audit_20_percent.json` są one na liście „usunięte zmyślone”.
- (d) **Znak od tyłu** (szara tarcza) jest raz uznawany za znak (066 ✓), a raz usuwany (013 ✗). Potrzebna jest reguła.

Wiersze z błędem P8 (ruch ciężarówek): **108 = B-5** (opisano B-2), 043 i 066 = B-5 (poprawne). Do P8 trafia też P11-002 (tablica 12t).

## 4. Licencje

Commit nie zmienia kolumn `licencja`, `autor`, `url_źródła` ani `status`. Licencje są takie jak w przeglądach s17/s18 (Commons, CC0/CC BY-SA, odrzucone NC tylko jako link). Nowe treści to tylko opisy. Napis „POMOC DROGOWA” jest opisem, nie marką. Pozycję Masterpress wzięto z Nominatim (OSM, dozwolone). Nie ma Google.

## 5. Dla lidera

- **Nie scalać** commitu `3da410039` w obecnej postaci: kody znaków w manifeście są niewiarygodne (48 % błędów w próbie). Jeśli trzeba scalić przed rundą Mistrala, lider może sam nanieść erratę z tabeli §3 (13 wierszy + STOP w 120). Do README trzeba wtedy dopisać: „kody znaków niezweryfikowane poza wierszami z REVIEW s20 §3”.
- **Errata do naszego s18:** P11-120 ma STOP (B-20). Uwzględniono to w bloku M47-FIX-3.
