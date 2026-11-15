# Przegląd PR #92 — P16 M59-FIX (s21) lampy ciągnika i naczepy — s21 cloud D, 2026-11-15

**Werdykt: FIX (bez zmian względem M59-FIX r2).** Od przeglądu `REVIEW-2026-11-15-s20-mistral-m59-fix.md` gałąź nie dostała nowego commita: głowa to nadal `7a902d8a3`. Blok r2 (kolumna `wartość`, README §2 i §9, nowe kadry) **nie jest wykonany**. Fotometria jest dobra, a 7/7 sprawdzonych cytatów zgadza się z Dz.U. Dlatego powtarzam blok FIX z jednym dodatkiem (pkt 5, uwaga o gamucie). PR #92 **zastępuje PR #55** (relacja w §5).

- Gałąź `origin/research/mistral-p16-truck-lamps-fix-s21` @ `7a902d8a3`. To 1 commit na głowie #55 (`73ccbe930`). Baza `b67b949d8` jest 711 commitów za `origin/main`.
- `git diff --stat origin/main...` daje 17 plików, wszystkie w `research/mistral/p16-truck-lamps/` ✓. Integracja tylko przez `git checkout origin/research/mistral-p16-truck-lamps-fix-s21 -- research/mistral/p16-truck-lamps`. Merge całej gałęzi odpada, bo przez starą bazę pokazuje ~1540 „usuniętych” plików.
- Manifest: 106 wierszy, separator `;`. W `files/` jest 12 JPG po 1280 px, bez kart producentów i bez PDF-ów ✓.

## 1. Kompletność (MISTRAL-FIXES-12 §M59-FIX oraz r2 z przeglądu s20)

| Pkt | Wymóg | Wynik |
|---|---|---|
| r2-1 | `wartość` w P16-201…223 przepisana z nowego opisu, usunięte kadry jako „WYCOFANE” | **NIE.** P16-206 nadal ma „gładki klosz”, 201 „zespół 7-komorowy pionowy”, 208/209/212/216 „2 zespoły 3-komorowe; od zewnątrz: kierunkowskaz…”, wszystkie ze statusem `SOURCED (obraz)`. Opis w tej samej linii mówi coś przeciwnego |
| r2-2 | README §2: przeciwmgłowe „75 cd” → warunkowo | **NIE.** README l. 53: „min **75 cd** w rombie” |
| r2-3 | README §9 bez ZIP i bez „tylko pliki tekstowe” | **NIE.** README l. 167 bez zmian |
| r2-4 / M59 kr. 4 | ≥ 15 zbliżeń tylnych lamp ECE (≥ 4 włączone, ≥ 3 o zmierzchu), ≥ 5 lampek tablicy ciężarówek | **NIE.** STATUS: „NIEZACZĘTE”. Realnie są 3 kadry ECE (204, 205, 206) i 0 lampek tablicy ciężarówek |
| (1), (3), (4), (5) z FIX-12 | przeklasyfikowanie, errata E1–E9, audyt, pliki | **TAK** (potwierdzone w s20 i ponownie na obrazach, §2) |
| zakres katalogu | tylko `research/mistral/p16-truck-lamps/` | **TAK** |

## 2. Obejrzane obrazy (12 z 12 plików w `files/`, każdy osobno, ≤ 960 px)

| Kadr | Licencja (Commons API, dziś) | Opis `opis_co_widać` vs obraz |
|---|---|---|
| P16-201 | CC0, Spielvogel ✓ | ✓ Koncept naczepy. Lampy L w narożach zderzaka (bursztyn u góry, czerwień niżej), górny czerwony pas z bursztynowymi końcami, w polu tablicy „VORSICHT” i 2 trójkąty |
| P16-202 | CC0 ✓ | ✓ Ten sam pojazd z drugiej strony. W polu tablicy czarny panel z napisem „STAU” (opis: „napis ostrzegawczy”, OK) |
| P16-204 | CC0 ✓ | ✓ Dwie poziome lampy pod skrzynią. Czerwone pole z drobnymi plamkami, po bokach bezbarwne sekcje z okrągłymi kubkami. Wygląda jak świecenie, ale EXIF ma flash = 9 (s20), więc „odblask flesza” jest uczciwy |
| P16-205 | CC0 | ✓ Ta sama lampa z dołu. Rura przeciwnajazdowa, tabliczka z napisem firmowym zamiast tablicy |
| P16-206 | CC0 ✓ | ✓ 4 sekcje: bezbarwna, czerwona z rozetą, 2 bezbarwne. Klosz nie jest gładki. Tablica na ramie nad zderzakiem, czerwono-żółte tablice ostrzegawcze na końcach |
| P16-208 | CC BY-SA 4.0, Eric Polk ✓ | ✓ USA, po 2 okrągłe czerwone na stronę, bursztynowe na narożach, taśma odblaskowa |
| P16-209 | CC BY-SA 4.0 | ✓ USA, chłodnia z blachy ryflowanej, 2 okrągłe na stronę |
| P16-212 | CC BY-SA 4.0, Xnatedawgx ✓ | ✓ Zardzewiała belka, okrągłe lampy, silny brud |
| P16-216 | CC BY-SA 4.0 ✓ | ✓ Pojedyncze okrągłe czerwone, okrągłe odblaski w białej obwódce, mała prostokątna czerwona lampa w środku, niebieska okrągła lampka |
| P16-218 | CC BY-SA 4.0 | ✓ Przyczepa kempingowa, wypukła osłona nad tablicą, okrągłe czerwone lampy na wspornikach, datownik 2008 |
| P16-219 | CC BY-SA 3.0 pl ✓ | ✓ SUV nocą, tablica równomiernie oświetlona z góry, świecą pozycyjne i trzecie stop |
| P16-221 | CC BY 4.0, RG72 ✓ | ✓ Cysterna nocą od tyłu-boku, tablica na zderzaku, lampki tablicy nie widać, 2 prostokątne elementy czerwono-bezbarwne, śnieg |

Wszystkie 12 opisów w kolumnie `opis_co_widać` zgadza się z obrazem. **Kolumna `wartość` jest sprzeczna z obrazem w 10 z 12 wierszy** (wyjątki: 218 i 219). Licencje 8/8 sprawdzonych przez `extmetadata` są zgodne. Google nie występuje. Marki (naczepy, podwozia, napisy firmowe) są widoczne na kadrach. Kadry są tylko referencją i README nie przenosi marek do opisów dla gry ✓.

## 3. Liczby sprawdzone u źródła (7 cytatów + 1 tabela)

Źródło: Cellar XHTML PL, `publications.europa.eu/resource/celex/42021X1719` (R148) i `…/42021X1718` (R48), pobrane 2026-11-15. Tekst normalizowany (soft hyphen, NBSP).

| Wiersz | Teza | Wynik |
|---|---|---|
| P16-020 | R148 tab. 4: „R1 lub RM1 (stałe) 4 17 8,5 MR 4 17 nd.” | ✓ dosłownie |
| P16-030/031 | tab. 7: „S1 (stałe) 60 260 130” | ✓ (obok S2 60/730/365) |
| P16-032 | pkt 5.5.3: „…nie może być mniejsza niż 0,3 cd; … 0,07 cd … S2 i S4 w nocy” | ✓ |
| P16-033 | pkt 5.5.4: „Emitowane światło musi mieć barwę czerwoną.” | ✓ |
| P16-035 | pkt 4.8.11: stop : pozycyjne „co najmniej 5: 1” w polu ±5 V × ±10 H | ✓ |
| P16-08x | F1 150/300 cd; pkt 5.9.2 odsyła do zał. 3 pkt 2.6 | ✓ (dlatego „75 cd” jest warunkowe, r2-2) |
| §4 README | pkt 5.11.3: B ≥ 2,5 cd/m² (kat. 1a, 1b, 1c, 2a, 2b), ≥ 2,0 (kat. 1 i 2) | ✓ |
| P16-111 | R48 pkt 2.11.1.3 „żółte samochodowe”: y = x − 0,120; y = 0,390; y = 0,790 − 0,670x; narożniki A1–A4 | ✓ dosłownie |

## 4. Wnioski dla gry (plik, liczba)

| Element | Gra dziś (`game/Assets/_Project/Vehicle/Runtime/TruckLights.cs`) | Źródło | Działanie |
|---|---|---|---|
| Stop : pozycyjne | `TailNits = 1.3e3`, `BrakeNits = 2.0e4`, czyli 15,4 : 1 | R148 4.8.11 ≥ 5 : 1 (SOURCED). Środki zakresów R1/S1 dają ok. 10–15 : 1 (ESTIMATED, s20) | ✓ zgodne, bez zmian |
| **Bursztyn** | `Amber = (1, 0.28, 0)` linear sRGB, czyli xy (0,524; 0,422). Komentarz ADR 0178: „pas 0,398 ≤ y ≤ 0,429” | R48 seria 07 §2.11.1.3 (SOURCED, §3). **Punkt gry leży poza obszarem**: y = 0,422 > x − 0,120 = 0,404 (granica zielona) i y < 0,790 − 0,670x = 0,439 (granica biała) | **P2, nowy wniosek recenzenta (pomiar):** cały obszar „żółte samochodowe” R48 leży **poza gamutem sRGB**. Krawędź R–G sRGB przy x = 0,545 ma y ≈ 0,405 < 0,425 (A1), a przy x = 0,597 y ≈ 0,364 < 0,390 (A4). Najbliższy punkt w gamucie to linear **(1, 0.25, 0)** → xy (0,533; 0,415), Δxy do A1 = 0,016 (dziś 0,021). Zmiana jest kosmetyczna i opcjonalna. **Obowiązkowo** trzeba poprawić podstawę w ADR 0178 i w komentarzu w kodzie: pas y 0,398–0,429 nie występuje w R48 seria 07 |
| WORKING_VALUE z przeglądu s20 | „xy ≈ (0,575; 0,415)” | — | **Errata do s20:** ten punkt leży poza sRGB (krawędź przy x = 0,575 ma y ≈ 0,382), więc w grze jest nieosiągalny. Zastąpić punktem z wiersza wyżej |
| Lampka tablicy | `m_Px[PLATE] = MarkerNits` (2e3) przy światłach mijania | R148 5.11.3: luminancja **tablicy** ≥ 2,5 cd/m² w każdym punkcie, gradient ≤ 2 × B₀/cm | bez zmian w kodzie. Kamera QA nocą musi pokazać równomierną tablicę bez gorącej plamki (WORKING_VALUE 3–5 cd/m², s20) |
| Wygląd lamp | ADR 0175/0181, `trailer_build.py` | **brak kadrów ECE** (kr. 4 niespełnione) | kolejność komór, LED/pryzmaty i wygląd po włączeniu zostają UNVERIFIED. Nie zmieniać geometrii na podstawie tego pakietu |
| Wymiar lampy naczepy | — | ≈ 420 × 140 × 80 mm (ESTIMATED, mediana 4 kart sklepowych, P16-304) | tylko jako zakres kontrolny dla Blendera |

## 5. Relacja #92 ↔ #55

#92 zawiera wszystkie 7 commitów #55 i dokłada jeden commit FIX. `git diff origin/research/mistral-p16-truck-lamps origin/research/mistral-p16-truck-lamps-fix-s21` pokazuje 17 plików (+211/−764), w tym `files/`, `STATUS.md` i przepisany manifest. **#92 w całości zastępuje #55. PR #55 należy zamknąć bez scalania** (osobny raport `REVIEW-2026-11-15-s21-cloudD-55-p16-truck-lamps.md`). Integrować tylko #92, po FIX r2.

## 6. Blok FIX (do wklejenia autorowi)

```
M59-FIX r2 (powtórzenie; research/mistral-p16-truck-lamps-fix-s21 → PR #92; zmieniaj tylko research/mistral/p16-truck-lamps/):
1. manifest.csv, P16-201…223, kolumna `wartość`: przepisz z `opis_co_widać`. Przykład dla 206:
   „lampa pozioma 4-sekcyjna; od zewn.: bezbarwna, czerwona, 2 bezbarwne; klosz z optyką/żebrowaniem;
   funkcje bezbarwnych UNVERIFIED”. Dla 201/202: „koncept: lampy L w narożach zderzaka + górny pas; nie typowa lampa”.
   Dla 208/209/212: „USA (FMVSS): 2 okrągłe czerwone na stronę”. Dla 216: „pojedyncze okrągłe”.
   Dla usuniętych (203, 207, 210, 211, 213–215, 217, 220, 222, 223) wpisz: „WYCOFANE (s21) — tyłu/lampy nie widać”.
   Status `SOURCED (obraz)` zostaw tylko tam, gdzie wartość opisuje to, co widać.
2. README §2 (l. 53): „min 75 cd” → „75 cd WARUNKOWO (zał. 3 pkt 2.6; pkt 5.9.2)”.
3. README §9 (l. 167): usuń zdania o ZIP i „w repo tylko pliki tekstowe” (kadry są w files/).
4. Nowe kadry wg MISTRAL-FIXES-12 §M59-FIX pkt 2: ≥ 15 zbliżeń tylnych lamp ECE naczep/ciągników
   (≥ 4 włączone, ≥ 3 zmierzch/noc), ≥ 5 lampek tablicy ciężarówek/naczep. Każdy kadr obejrzyj osobno,
   ≤ 960 px, wycinek 3×. Na tej podstawie przepisz README §5.1/§5.2/§6. Jeśli limit nie pozwoli: zrób 1–3,
   push, a pkt 4 oznacz w STATUS.md jako NIESPEŁNIONE.
5. README §2 (barwy): dopisz zdanie „obszar żółtej samochodowej R48 §2.11.1.3 leży w całości poza gamutem sRGB
   (pomiar recenzenta s21)”.
Integracja: git checkout origin/research/mistral-p16-truck-lamps-fix-s21 -- research/mistral/p16-truck-lamps
```

## 7. Dla lidera
- Nie scalać, dopóki nie będzie FIX r2 pkt 1–3. Pkt 4 może zostać jawnie NIESPEŁNIONY, tak jak przy częściowym przyjęciu M61. Wtedy integracja przez checkout katalogu.
- Do gry (niezależnie od PR): poprawić podstawę barwy bursztynowej w ADR 0178 i w komentarzu `TruckLights.cs` (§4). Opcjonalnie `Amber = (1, 0.25, 0)`. Zmiana dotyczy wspólnego kodu pojazdu, więc należy do lidera albo agenta pojazdu, nie do tego PR.
- Zamknąć PR #55 jako zastąpiony przez #92.
