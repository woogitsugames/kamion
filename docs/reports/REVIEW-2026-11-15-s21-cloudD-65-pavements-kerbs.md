# Przegląd PR #65 — R6 pavements-kerbs (nawierzchnie, krawężniki, drobna infrastruktura) — s21 cloud D, 2026-11-15

**Werdykt: SCAL z erratą.** Część normowa jest uczciwa:
- 5 z 5 cytatów sprawdzonych w PDF-ach zgadza się dosłownie. Sprawdziłem też wynik negatywny R6-005: Dz.U. 2022 poz. 1518 rzeczywiście nie podaje wysokości krawężnika.
- **12 z 12 obejrzanych kadrów ma opis zgodny z obrazem.** W tym wpust na F14, który widać dopiero w wycinku.
- Główny wniosek „DDR w Dojlidach jest szara” niezależnie potwierdza ADR 0188.

Errata dotyczy trzech rzeczy:
- zdjęcia w gicie (6,2 MB);
- wymiary krawężników i kostki nie są potwierdzone kadrami (z obrazu ich nie da się zmierzyć, pakiet mówi to wprost);
- brak sekcji tekstur CC0.

- Gałąź `origin/research/cloud2-pavements-kerbs` @ `044fb9aab`, baza `81c9baee7` (612 commitów za `origin/main`).
- `git diff --stat origin/main...`: 51 plików, wszystkie w `research/cloud2/pavements-kerbs/` ✓.
- Manifest ma 113 wierszy: 72 normowe/OSM, 31 kadrów, 10 zliczeń.
- Wewnętrzny `REVIEW.md`: PASS z uwagami P2.

## 1. Kompletność (CLOUD2-PROMPT R6 oraz „Dokończenie”: obejrzeć i opisać 31 kadrów)
| Wymóg | Wynik | Dowód |
|---|---|---|
| Typy kostki (wymiary, kolory, wzory) | **CZĘŚCIOWO** | wymiary z OST/katalogu (20×10, „podwójne T” 198×163, starobruk). Kolory i wzory z kadrów tylko jakościowo (rzędy poprzeczne; jodełka UNVERIFIED) |
| Krawężniki i obrzeża (wymiary norm) | **TAK** | OST D-08.01.01b (10–12 cm, wyjątkowo 6/16), BN-80/6775-03/04, wytyczne ZDM Białystok (k1 25×12×100). Akt 2022/1518 bez liczby (wynik negatywny, sprawdzony) |
| Wpusty i studzienki | **TAK** (bez rozstawu) | Ø 500, D400, prześwit 600 (ZDM), rama z karty. Rozstaw UNVERIFIED |
| Łaty, spękania | **TAK** (progi) | WR-D-83-2: łata < 20 m, spękania ≥ 10 cm, koleiny 10/20/30 mm. Z kadrów: rzadkie ślady (R6-113) |
| Czerwony asfalt DDR | **TAK** | ZDM: „wyraźnie inny kolor”, przejazdy RAL 3020. Kadry: DDR w Dojlidach szara 7/7 |
| Zdjęcia z bliska z trasy C i Dojlid | **TAK** (31) | 22 z trasy C (Panoramax 2019, KartaView 2019/2021), 9 z Dojlid (Commons CC0) |
| Samokontrola 20 % z obejrzeniem | **TAK** | seed 20261114: 15/72 PASS. Seed 20261115: 9/41, 8 PASS / 1 FIX |
| Licencje, Google, marki | **TAK** | Panoramax/KartaView CC BY-SA 4.0, Commons CC0. Katalog producenta jako źródło liczb, bez nazwy w opisach dla gry. Brak Google |
| UA generyczny | **TAK** | `Mozilla/5.0 (X11; Linux x86_64) research-client/1.0` |
| Zdjęć nie commitować | **NIE** | `.gitignore`: `!files/jpg1600/`, 31 plików, 6,2 MB |
| Tekstury CC0 | **NIE** | README „Luki”: sekcja niezrobiona |
| Tylko własny katalog | **TAK** | — |

## 2. Obejrzane obrazy (12 z `files/jpg1600/`, każdy osobno ≤ 960 px, 2 wycinki F14)
| Kadr | Licencja (`INDEX.csv`; Commons sprawdzone przez API) | Ocena opisu |
|---|---|---|
| F04 Panoramax fc5ecd98 (estakada Maczka) | CC-BY-SA-4.0, stanton | ✓ szary asfalt, przy kamerze ciemniejszy pas poprzeczny, czerwonobrązowa kapa przy barierze, tablica „8 E67 Augustów / 65 Bobrowniki / Kuźnica / Lublin” |
| F06 Panoramax a228a704 (Tysiąclecia N) | CC-BY-SA-4.0 | ✓ krawężnik i pas prefabrykatów przy nim, ekran z białym cokołem, ciemne żłobione panele, szkło. Bramownica w tle |
| F12 KartaView (Andersa) | CC-BY-SA-4.0 | ✓ niski krawężnik, jasnoszary chodnik, billboardy (marki nieopisywane), pas dzielący z pomarańczowo-żółtym ogrodzeniem |
| F14 KartaView 3686129/265 (estakada Andersa) + 2 wycinki | CC-BY-SA-4.0 | ✓ wysoki krawężnik mostowy, bariera z linkami, czerwonobrązowa kapa po lewej. **Wpust widoczny w wycinku** (ciemny prostokąt w linii krawędziowej, drugi dalej) |
| F17 KartaView (Andersa NW) | CC-BY-SA-4.0 | ✓ szeroki pas szarej kostki oddzielony białą linią przerywaną, młode drzewa |
| F30 KartaView 2769366/190 (estakada) | CC-BY-SA-4.0 | ✓ prostokątny wpust z rdzawą kratą przy krawężniku, rdzawe zacieki, czerwona kapa po lewej |
| F31 Commons P11-001 (Kuronia) | CC0, Rakoon ✓ (API) | ✓ **szara asfaltowa DDR** z białymi liniami, chodnik z kostki w rzędach, czerwone słupki ogrodzenia |
| F35 Commons P11-097 (Kuronia) | CC0 ✓ | ✓ chodnik z kostki w rzędach poprzecznych, szara DDR z linią krawędziową, osią przerywaną i piktogramem. „Jaśniejszej wstawki (łaty)” nie rozstrzygam przy 960 px |
| F36 Commons P11-023 (Mickiewicza) | CC0, Rakoon ✓ | ✓ szara DDR z podłużnym pęknięciem przy linii krawędziowej, pas trawy z korytkiem prefabrykowanym, chodnik w układzie ukośnym (jodełka jako UNVERIFIED, słusznie) |
| F38 Commons P11-063 (Mickiewicza) | CC0 | ✓ pas z czerwonobrązowej kostki z szarym obrzeżem, pas dzielący z nieregularnej kostki kamiennej, słupki biało-czerwone z łańcuchami |
| F39 Commons P11-056 (Dywizjonu 303) | CC0, Rakoon ✓ | ✓ jednolity szary asfalt, w tle czerwony przejazd z białymi kwadratami |
| F05 Panoramax c0b69dac | CC-BY-SA-4.0 | ✓ (zjazd z estakady, kapa, bariera w pasie dzielącym) |

Zgodność **12/12**. Kolumna `autor` dla KartaView ma „UNVERIFIED (API nie zwraca autora)”. Licencja CC BY-SA wymaga atrybucji. R2 podaje dla tej samej sekwencji `userId 479`, więc można to uzupełnić (E3).

## 3. Liczby sprawdzone u źródła (5 cytatów + 1 wynik negatywny)
| Wiersz | Źródło (pobrane 2026-11-15, `pdftotext -layout`) | Wynik |
|---|---|---|
| R6-001 | OST D-08.01.01b (BIP gminy), „…powinno wynosić od 10 do 12 cm” | ✓ dosłownie |
| R6-002 | jw., „…może być zmniejszone do 6 cm lub zwiększone do 16 cm” | ✓ |
| R6-028 | Wytyczne ZDM Białystok (zał. 5), „…klasy D400 o wysokości korpusu 150 mm, prześwicie 600 mm” | ✓ (warstwa tekstowa bez polskich znaków, tak jak w uwagach) |
| R6-050 | jw., „…kolor RAL 3020, wykonane z masy chemoutwardzalnej ze środkiem uszorstniającym” | ✓ |
| R6-005 | Dz.U. 2022 poz. 1518 (ELI PDF), „Dopuszcza się uskok … o wysokości dostosowanej do potrzeb osób z niepełnosprawnościami wzroku” | ✓. W całym akcie 0 trafień „10–14 cm”, więc wynik negatywny jest potwierdzony |

SOURCED / ESTIMATED: 69 z 72 wierszy normowych ma cytat. Zliczenia z kadrów (R6-104…113) są ESTIMATED, a próba celowa, co metoda zaznacza. Wymiary z kadrów są wprost UNVERIFIED. Nie znalazłem liczby bez statusu.

## 4. Wnioski dla gry (plik, liczba)
| Element | Gra dziś | R6 | Działanie |
|---|---|---|---|
| Kolor DDR (`tools/worldgen/streetscape/cycleways.py`, ADR 0188) | Dojlidy: `cycle_asphalt` (ciepłoszary). Czerwony tylko 11 way przy Putry | kadry Dojlid 7/7 szara DDR, czerwień tylko na przejazdach (F39) i w pasie kostki (F38) | ✓ **niezależne potwierdzenie ADR 0188**. Bez zmian |
| Wysokość krawężnika (`tools/worldgen/roads/standards.py`, `KERB_HEIGHT = 0.13`) | 0,13 m | OST: 10–12 cm domyślnie, 6–16 wyjątkowo (SOURCED); akt 2022 bez liczby | **P2:** 0,13 mieści się w 6–16, ale jest 1 cm nad zakresem domyślnym. Opcja `0.12` (górna granica OST). Wymaga oceny wizualnej. Zostawienie 0,13 też jest uzasadnione, pod warunkiem dopisania źródła (R6-001/002) w komentarzu |
| Behaton (ADR 0063: „~210 × 140 mm rows”, WORKING_VALUE) | ~210 × 140 | „podwójne T” 198 × 163 mm (katalog, R6-023) | **P2:** jeśli skan ma rzędy 140 mm, a rzeczywisty wymiar to 163 mm, skala tekstury wynosi ×1,16 (wyliczenie recenzenta). Skorygować w ADR 0063 / mapie skal |
| Wpusty (`tools/worldgen/roads/decals.py`, `GULLY_SPACING_M = 35.0`, `GULLY_SIZE = (0.50, 0.60)`, WORKING_VALUE) | co 35 m, 0,50 × 0,60 | rozstaw UNVERIFIED. Rama 620 × 420 lub 500 × 500 (karta). Na estakadzie wpusty leżą w linii krawędziowej (F14, F30) | rozstaw bez zmian. **P2:** rozmiar 0,42 × 0,62 jako wariant karty. Na obiektach mostowych wpust w linii krawędziowej, tuż przy krawężniku |
| Kapa na estakadach trasy C (`tools/worldgen/streetscape/hero_bridge.py`: `cornice_h_m 0.57` „red precast cornice plate”) | czerwony gzyms | 6 kadrów: **powierzchnia kapy chodnikowej czerwonobrązowa**, krawężnik mostowy szary, wysoki | P2: kamerą kontrolną na estakadzie Andersa sprawdzić, czy czerwonobrązowa jest też górna powierzchnia kapy (nie tylko gzyms). Materiał kapy w `hero_bridge` / generatorze kap |
| Decale łat i spękań (`decals.py`, `LIFT_PATCH`) | — | trasa C 2019–2021: nawierzchnia jednolita, ślady pojedyncze (9 z 31 kadrów, ESTIMATED), bez wybojów i kolein. Progi WR-D-83-2: łata < 20 m, spękanie ≥ 10 cm | utrzymać rzadkie decale. Długość łaty < 20 m jako twardy limit |
| Wieniec z kostki wokół włazów w chodniku (ZDM, R6-027) | — | wymóg przy każdym włazie w kostce | P2 do `fab_details.py`: przy włazie w nawierzchni z kostki dodać obwódkę |

## 5. Errata (przy scaleniu albo w następnej paczce, nie blokuje)
1. **E1 (proces, decyzja lidera):** `files/jpg1600/` w gicie (31 plików, 6,2 MB), wbrew CLOUD2-PROMPT. Albo `git rm -r --cached research/cloud2/pavements-kerbs/files/jpg1600` i sam `files/*` w `.gitignore` (`fetch.py` sprawdza sha256 oryginałów), albo świadoma akceptacja z atrybucją w `INDEX.csv`.
2. **E2:** README, tabela „dla generatora”: kolumna „Częstość” ma wiele pozycji „UNVERIFIED (kadry nieobejrzane)” z 2026-11-14. Po zad. 6 należy wpisać zliczenia z R6-104…113, np. krawężnik szary 21/31, kostka 9/31, albo zmienić na „UNVERIFIED (z obrazu nie mierzono)”. Ostatnie zdanie „Częstości i wzory układania czekają na oględziny kadrów” jest nieaktualne.
3. **E3:** `INDEX.csv` i manifest, autor KartaView „UNVERIFIED”: uzupełnić z API (`userId` w odpowiedzi `photo/?sequenceId=`, R2 podaje 479 dla 3686129), bo CC BY-SA wymaga atrybucji.
4. **E4 (luka):** tekstury CC0 (ambientCG / Poly Haven) oraz kadry Sokólskiej, Wysockiego, Kombatantów i sekwencji 1155711. Do następnej paczki.

## 6. Dla lidera
- **Scalić PR #65.** E1 rozstrzygnąć przy scaleniu, E2 i E3 można nanieść przy scaleniu.
- Do gry: niezależne potwierdzenie ADR 0188 (szara DDR w Dojlidach) oraz P2: skala behatonu ×1,16, rozmiar wpustu, sprawdzenie koloru kapy na estakadzie, wieniec przy włazach. `KERB_HEIGHT` zostaje albo 0,12, ale w obu przypadkach z odnośnikiem do R6-001/002.
