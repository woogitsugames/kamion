# Przegląd M59-FIX P16 lampy (PR #92, `research/mistral-p16-truck-lamps-fix-s21`), s20, 2026-11-15

**Werdykt: FIX (krótki).** Errata E1–E9 jest wprowadzona poprawnie, kadry przeklasyfikowano z obrazu, a audyt jest nowy. PR uczciwie pisze, że punkt (2), czyli nowe zbliżenia lamp ECE, jest **niezaczęty**. Przegląd znalazł jeszcze jedną usterkę, której PR nie zgłasza: w `manifest.csv` kolumna `wartość` wierszy kadrów **wciąż zawiera wycofane opisy z M59** i ma status `SOURCED (obraz)`. Kto czyta manifest maszynowo, dostanie obalone tezy.

Fotometria jest gotowa do użycia już teraz. Jeśli lider przyjmie paczkę częściowo, tak jak M61-FIX, to integruje ją **wyłącznie przez checkout katalogu**, i to dopiero po poprawce kolumny `wartość` (pkt 1 bloku FIX).

## 0. Gałąź i pliki
- `origin/research/mistral-p16-truck-lamps-fix-s21` @ `7a902d8a3`, 1 commit na głowie #55 (`73ccbe930`). Baza jest stara: 675 commitów za `origin/main`.
- `git diff --stat origin/main...origin/…` (od merge-base): 17 plików, +394, wszystkie `A` w `research/mistral/p16-truck-lamps/` ✓, 0 usunięć.
- `git diff origin/main origin/…` (dwie kropki) pokazuje ~1540 plików „usuniętych”. To skutek starej bazy, a nie zmiana gałęzi. **Integracja: `git checkout origin/research/mistral-p16-truck-lamps-fix-s21 -- research/mistral/p16-truck-lamps`**, nie merge ani squash całej gałęzi.
- `files/`: 12 JPG o szerokości 1280 px. Kart producentów i PDF-ów nie ma ✓. Zamiast ZIP-a kadry są w gałęzi, co jest akceptowalne.
- Licencje: Commons CC0/CC BY/CC BY-SA. Google: brak ✓.

## 1. Punkty M59-FIX
| Pkt | Wynik |
|---|---|
| (1) kadry przeklasyfikowane z obrazu | **TAK w `opis_co_widać`/`uwagi`/README §5–§7**. 11 kadrów usuniętych (203, 207, 210, 211, 213–215, 217, 220, 222, 223). 208/209/212/216 przeniesione do „inne systemy”. 201/202 = koncept L, 204/205 = flesz, 206 = 4 sekcje, klosz nie gładki. **NIE w kolumnie `wartość`** (§3) |
| (2) ≥ 15 zbliżeń ECE, ≥ 4 włączone, ≥ 3 o zmierzchu, ≥ 5 lampek tablicy ciężarówek | **NIEZACZĘTE**, zgłoszone wprost. Realnie są 3 kadry ECE (204, 205, 206) i 0 lampek tablicy ciężarówek |
| (3) E1–E9 | **TAK**. E1: P16-020 „R1 lub RM1 (stałe) 4 17 8,5”, uwaga „nd. = MR” ✓. E2: P16-302 „24 V 4xASS2” ✓. E3: P16-304 mediana czterech kart, 80,15 → ≈ 80 ✓. E4: w uwagach P16-082 jest pełny cytat warunku „znaczącej miejscowej zmienności” ✓, ale **README §2 nadal podaje „min 75 cd” bez słowa „warunkowe”**. E5: P16-095 → ESTIMATED ✓. E6: README §1 „połączenie … nr 3, 27, 69, 70 i 104” ✓. E7: „≤ 2 × B₀/cm” ✓. E8 → UNVERIFIED ✓. E9: P16-122 i inne mają cytat PL ✓ |
| (4) audyt | **TAK**: seed 20261115, 22/106 = 20,8 %, metoda losowania jawna. Kadry: 6, w tym 5 zgodnych i 1 poprawiony (216). Cytaty: 16, w tym 15 zgodnych, a P16-303 ma status „SOURCED (sklep, odczyt 13.11, niepowtarzalny)” ✓ |
| (5) pliki bez kart producentów | **TAK**. Ale README §9 nadal mówi „ZIP … w repo tylko pliki tekstowe”, co jest sprzeczne z `files/` |
| komentarz PR z surowym `git diff --stat` | jest w opisie PR. Pełne wyjście (1541 wierszy) obcięte z uzasadnieniem, a wycinek dla katalogu jest kompletny ✓ |

## 2. Co obejrzałem sam (3 z 12 plików = 25 %, każdy osobno)
| Plik | Opis w PR | Ocena |
|---|---|---|
| `P16-206.jpg` | pozioma lampa 4-sekcyjna. Od zewnątrz: bezbarwna z fakturą, duża czerwona z rozetą, dwie bezbarwne z żebrowaniem; klosz nie gładki; lampki tablicy nie widać; odblaskowe tablice czerwono-żółte | ✓ Zgodne. Lewa lampa: bezbarwna, czerwona, 2 bezbarwne; prawa w lustrzanym układzie. Tablica jest na ramie nad zderzakiem, lampki nad nią nie widać. Tablice ostrzegawcze czerwono-żółte są na końcach zderzaka |
| `P16-201.jpg` | koncept, lampy L w zderzaku, w miejscu tablicy napis ostrzegawczy | ✓ Lampy w kształcie L (czerwone + bursztynowy segment) w narożnikach, górny pas czerwony z bursztynowymi narożnikami, w polu tablicy „VORSICHT” i 2 trójkąty. To koncept, nie typowa lampa |
| `P16-218.jpg` | przyczepa kempingowa: wypukła osłona lampki nad tablicą, lampy pojedyncze okrągłe | ✓ Zgodne. Czerwone okrągłe lampy na wspornikach, nad tablicą biała wypukła osłona. Kadr z datownikiem z 2008 roku |

## 3. Usterka nowa: kolumna `wartość` w wierszach kadrów (P16-201…223)
Przykłady wartości, które dziś są w manifeście:
- P16-206: „zespół 4-komorowy; od zewnątrz: kierunkowskaz, pozycyjne/stop, cofania, obrysowe; **gładki klosz** …” ze statusem `SOURCED (obraz)`. Opis w tym samym wierszu mówi, że klosz NIE jest gładki, a funkcje są nieweryfikowalne.
- P16-201/202: „zespół 7-komorowy pionowy …”. W rzeczywistości to lampy L konceptu.
- P16-216: „2 zespoły 3-komorowe; od zewnątrz: kierunkowskaz …”. W rzeczywistości pojedyncze okrągłe.
- P16-208/209/212 (FMVSS) i 204: stary szablon „od zewnątrz: kierunkowskaz, pozycyjne/stop, cofania”.
- Usunięte wiersze (203, 207, …) mają status UNVERIFIED, ale `wartość` dalej zawiera stary szablon.

## 4. Liczby dla gry (z pakietu; Dz.U. L 347 z 30.9.2021, wersja pierwotna R148/R150/R48)
- **STOP : pozycyjne ≥ 5 : 1**: R148 pkt 4.8.11, gdy oba światła są wzajemnie sprzężone, w polu ±5° V × ±10° H (P16-035). Zakresy: pozycyjne tylne R1 4–17 cd (zespół „D” 8,5), stop S1 60–260 cd (S2 zmienne 60–730 cd). Proporcja środków zakresów to ok. **10–15 : 1** (ESTIMATED, wyliczenie recenzenta). Do shadera: pozycyjne ≈ 8–10 cd, stop ≈ 100–130 cd, czyli mnożnik emisji komory wspólnej ×12 (WORKING_VALUE, mieści się w ≥ 5 : 1).
- **Bursztyn (żółta samochodowa, R48 §2.11)**: granice y ≤ x − 0,120; y ≥ 0,390; y ≥ 0,790 − 0,670x; narożniki (0,545; 0,425), (0,560; 0,440), (0,609; 0,390), (0,597; 0,390). Arytmetykę narożników sprawdziłem. Punkt docelowy do gry: **xy ≈ (0,575; 0,415)** (WORKING_VALUE, wewnątrz obszaru). **Czerwień**: y ≤ 0,335, y ≥ 0,980 − x; narożniki (0,645; 0,335), (0,665; 0,335), (0,735; 0,265), (0,721; 0,259).
- **Tablica rejestracyjna**: luminancja **≥ 2,5 cd/m² w każdym punkcie** (kat. 1a/1b/1c/2a/2b; R148 pkt 5.11.3), gradient **≤ 2 × B₀/cm**, kąt padania ≤ 82°, światło bezbarwne, bez emisji do tyłu. Dla gry: tablica oświetlona równomiernie, bez gorącej plamki; luminancja docelowa ok. 3–5 cd/m² (WORKING_VALUE).
- Pozostałe: kierunkowskaz 2a 50–500 cd; przeciwmgłowe F1 150–300 cd; cofania 80–300 cd (w h i wyżej); boczne SM1 4–25 cd; lampa 7-funkcyjna naczepy ≈ 420 × 140 × 80 mm (ESTIMATED, mediana 4 kart).
- Wyglądu lamp (kolejności komór, LED/pryzmaty, wyglądu po włączeniu) **nie da się wziąć z tego pakietu**: brak kadrów, UNVERIFIED.

## 5. Blok FIX (do wklejenia autorowi)
```
M59-FIX r2 (research/mistral-p16-truck-lamps-fix-s21, push do PR #92; zmieniaj tylko research/mistral/p16-truck-lamps/):
1. manifest.csv, wiersze P16-201…223, kolumna `wartość`: przepisz z nowego `opis_co_widać`
   (np. 206: „lampa pozioma 4-sekcyjna; od zewn.: bezbarwna, czerwona, 2 bezbarwne; klosz z optyką/żebrowaniem; funkcje bezbarwnych UNVERIFIED”).
   Dla usuniętych (203, 207, 210, 211, 213–215, 217, 220, 222, 223) wpisz „WYCOFANE (s21) — tyłu/lampy nie widać” zamiast starego szablonu.
   Status „SOURCED (obraz)” zostaw tylko dla tego, co faktycznie widać.
2. README §2, punkt o przeciwmgłowych: „min 75 cd” → „75 cd WARUNKOWO (zał. 3 pkt 2.6, tylko przy znaczącej miejscowej zmienności)”.
3. README §9: usuń zdania o ZIP i „w repo tylko pliki tekstowe” (kadry są w files/).
4. (2) NOWE KADRY — bez zmian wg MISTRAL-FIXES-12 §M59-FIX pkt 2: ≥ 15 zbliżeń tylnych lamp ECE naczep/ciągników
   (≥ 4 włączone, ≥ 3 zmierzch/noc), ≥ 5 lampek tablicy ciężarówek/naczep; każdy kadr osobno; README §5.1/§5.2/§6 z tych opisów.
   Jeśli limit nie pozwoli — zrób 1–3, push, a (2) zostaw jawnie jako NIESPEŁNIONE w STATUS.
Integracja tylko: git checkout origin/research/mistral-p16-truck-lamps-fix-s21 -- research/mistral/p16-truck-lamps
```
Cytatów nie weryfikowałem ponownie u źródła, bo zrobił to przegląd s20 M59. Nic nie scalono ani nie scommitowano.
