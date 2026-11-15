# Przegląd M60-FIX P17 zmierzch (PR #91, `research/mistral-p17-dusk-lighting-fix-s21`), s20, 2026-11-15

**Werdykt: SCAL przez checkout katalogu, z erratą 3 wierszy manifestu (pkt 5).** Wszystkie 8 punktów FIX są wykonane albo uczciwie zamknięte wariantem dopuszczonym w zadaniu. Przy serii „wieś” wariant brzmiał „jeśli się nie da — usuń”, przy horyzoncie „brak = UNVERIFIED w Lukach”. Obejrzałem 8 kadrów i opisy zgadzają się z obrazem; to istotna poprawa względem M60. Zostały dwie rzeczy:
- w `manifest.csv` nie usunięto zdania „~12× ciemniejsze niż wieś”, choć FIX (1) kazał je usunąć;
- 3 wiersze serii miejskiej nadal mają status SOURCED, a README mówi ESTIMATED.

Errata jest mechaniczna. Lider może scalić katalog i zlecić ją razem z następną rundą albo odesłać jako mikro-FIX przed scaleniem.

## 0. Gałąź i pliki
- `origin/research/mistral-p17-dusk-lighting-fix-s21` @ `3c10138aa`, na głowie #57 (`46a0fdd13`). Baza jest stara: 674 commity za `origin/main`.
- `git diff --stat origin/main...origin/…`: 42 pliki, +506, wszystkie `A` w `research/mistral/p17-dusk-lighting/` ✓, 0 usunięć. Integracja: **`git checkout origin/research/mistral-p17-dusk-lighting-fix-s21 -- research/mistral/p17-dusk-lighting`**. Nie scalać całej gałęzi, bo baza jest stara.
- `files/`: 37 JPG, 1280 px w poziomie albo 1600 px w pionie, ≈ 8,2 MB; sha256 jest w STATUS ✓ (FIX 7).
- Licencje: Commons CC0/CC BY/CC BY-SA, CC BY-SA z dopiskiem „tylko referencja, nie tekstura”. OSM ODbL, Wikipedia CC BY-SA (cytat definicji). Google i Mapillary: nie użyto ✓.

## 1. Punkty M60-FIX
| Pkt | Wynik |
|---|---|
| (1) seria „wieś” | **TAK (wariant „usuń”)**: kolumna i CCT usunięte z tabeli 1, P17-008…012 i 018…020 mają status UNVERIFIED, przeliczenia suplementu nie powtórzono (Luka 3). **Ale** zdanie „przy h0=−8° miasto ~12x ciemniejsze niż wieś” zostało w `uwagi` P17-014…017 |
| (2) horyzont | **TAK (UNVERIFIED)**: sprawdzono Nawar (arXiv 1011.3024, jednostki S10, bez przeliczenia) i Lee 1994 (tylko abstrakt). Dodano tabelę jakościową z 6 kadrów |
| (3) kadry osobno | **TAK**: 37/37 opisanych od nowa. Wszystkie wskazane poprawki (076/099, 077/105, 079, 100, 103, 106, 087, 089, 085, 075, 109) są w opisach i README. Teza o plamie pod każdą latarnią została wycofana. Zaznaczono, że kadry pokazują deptak Lipowa/Rynek, a nie trasę C |
| (4) EXIF | **TAK**: 083 −5,66°, 084 −6,45°, 087 ≈ −4,31° (pozycja przybliżona, błąd ±5 km daje < 0,1°), 109 +13,3°. `kierunek_deg` = UNVERIFIED |
| (5) okna | **CZĘŚCIOWO**: 19 kadrów z odsetkiem i h0, klatki liczone osobno (080: 8/10). Bloków lub biurowców przy h0 −4…−8° są tylko **4** (073, 083, 084, 087); ≥ 5 wychodzi dopiero z kamienicami. Nowych kadrów nie szukano, co zgłoszono w Luce 8 |
| (6) trasa | **TAK**: „trasa generalska” = ESTIMATED (definicja z pl.wikipedia), przetarg ≠ montaż. Rozstawy przeliczone z id node’ów: Tysiąclecia ≈ 38,7–39,0, Wysockiego ≈ 48,0 (zgodne z przeglądem s20). Lipnik usunięty |
| (7) pliki ≤ 1600 px + sha256 | **TAK** (w gałęzi zamiast ZIP-a) |
| (8) audyt | **TAK**: seed 20261115, 22/109 = 20,2 %, 8 kadrów obejrzanych ponownie (5 zgodnych, 3 poprawione). Niepotwierdzone cytaty wpisane jawnie (P17-032, TED) |

## 2. Co obejrzałem sam (8 z 37 = 22 %, każdy osobno)
| Kadr | Opis w PR | Ocena |
|---|---|---|
| 103 (h0 −3,2°) | wysokie oprawy drogowe nie świecą, świecą 2 niskie lampy; ciepły brzoskwiniowy pas pod chmurami po lewej, wyżej bladoszaro-lawendowo | ✓ Zgodne. Dwie głowice na masztach (lewa i prawa krawędź) są ciemne, a 2 niskie lampy przy budynku świecą. Pas brzoskwiniowy jest przy horyzoncie po lewej |
| 083 (−5,7°) | niebo granatowe, przy horyzoncie szaroniebieskie, bez różu; arteria z HPS i plamami; blok ≈ 13 % okien, klatki zapalone | ✓ Zgodne. Pionowe ciągi klatek świecą pomarańczowo, plamy na jezdni widać z wysoka. Odsetek okien jest wiarygodny |
| 087 (−4,3°) | niebo niebieskie z chmurami, świeci 1 latarnia ciepłobiała, plam brak; blok L ≈ 5/35 | ✓ Zgodne |
| 080 (−14,3°) | niebo pomarańczowo-brązowe (łuna), latarnia z białą kulą, klatki ≈ 8/10, mieszkania ≈ 8/98 | ✓ Zgodne. Wieżyczki klatek są prawie całe zapalone, w mieszkaniach pojedyncze okna |
| 106 (−15,6°) | mgła, maszty dwuramienne o barwie sodowej, halo z mgły, nawierzchnia równo oświetlona | ✓ Zgodne |
| 077 (−7,3°) | drzewa w białych lampkach, pierzeja bez zapalonych okien | ✓ Zgodne. Białe światła to lampki choinkowe LED; w lewej pierzei nie ma zapalonych okien |
| 076 (−8,4°) | Rynek, karuzela, białe girlandy i kolorowe ozdoby, ozdobne ciepłe latarnie, ≈ 5–8/35 okien | ✓ Zgodne |
| 109 (+13°) | dzień, ozdobna latarnia z pomarańczowymi kloszami; „czy świecą — nierozstrzygalne” | **≈** Kategoria „dzień” jest słuszna. Klosze i dwie dalsze oprawy w tle wyglądają na **zapalone**: równomiernie świecą na tle nieba, także te w cieniu. To drobiazg, nie blokuje |

## 3. Drobne niespójności
- P17-015/016/017 mają status SOURCED, a README (tabela 1 i pkt 1 „Co zmieniono”) mówi, że seria miejska jest ESTIMATED. P17-013/014 już są ESTIMATED.
- `uwagi` P17-014…017 nadal zawierają „przy h0=−8° miasto ~12x ciemniejsze niż wieś”, czego FIX (1) kazał się pozbyć.
- 103: README podaje h0 −3,3°, manifest −3,16°. Wnioski się nie zmieniają.

## 4. Wnioski dla gry (cykl dnia, ADR o oświetleniu / follow-up 0182)
- **Ev poziome w czyste niebo** (miasto, ESTIMATED; zgodne z AMS przy −6°): h0 −4° 36 lx, −5° 11 lx, −6° 3,5 lx, −7° 1,1 lx, −8° 0,5 lx. Spadek wynosi ok. ×10 na 2° (Koomen). Luminancja zenitu przy −6° ≈ 0,29 cd/m² (ESTIMATED).
- **Włączenie latarni** przy h0 ok. **−3…−3,5°** (n = 3, ESTIMATED). Przy −3,2° oprawy drogowe jeszcze nie świecą.
- **Okna w blokach**: ok. **10–15 %** przy h0 −4…−6°, **15–20 %** przy −12…−19°. Żaden kadr nie przekracza 30 %. **Klatki schodowe prawie wszystkie zapalone (≈ 80 %).** Kamienice deptaka: 0–8 %.
- **Horyzont**: brak liczb. Jakościowo: od strony Słońca ciepły pas brzoskwiniowy przy ok. −3°, po przeciwnej stronie i przy −5…−8° niebieski lub granatowy, bez różu.
- **Rozstaw latarni** (OSM, ESTIMATED, n ≤ 6): Andersa ≈ 31,5 m, Kombatantów 31–33 m, Tysiąclecia ≈ 39 m, Wysockiego ≈ 48 m. Klasa M, wysokość i stan LED na trasie: UNVERIFIED.
- **Halo i plamy**: silne halo tylko we mgle (efekt pogody, nie lampy). Plamy pod latarniami są słabe, wyraźne tylko z wysoka na asfalcie. W shaderze nie przesadzać z plamami.

## 5. Errata (mikro-FIX, do wklejenia autorowi albo do następnej rundy)
```
M60-FIX r2 (research/mistral-p17-dusk-lighting-fix-s21, push do PR #91; tylko research/mistral/p17-dusk-lighting/):
1. manifest.csv P17-014…017, kolumna `uwagi`: usuń zdanie „(przy h0=-8° miasto ~12x ciemniejsze niż wieś — …)”.
2. manifest.csv P17-015/016/017: status SOURCED → ESTIMATED (jak P17-013/014 i README tabela 1).
3. README „Horyzont”/„Timeline”: h0 kadru 103 ujednolicić z manifestem (−3,2°).
Opcjonalnie (Luka 8): ≥ 2 kadry bloków przy h0 −4…−8° (Commons „Blocks of flats at night in Poland”, „Blue hour in Poland”) z odsetkiem okien.
```
Nic nie scalono ani nie scommitowano.
