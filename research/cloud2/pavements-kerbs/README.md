# R6 — nawierzchnie, krawężniki i drobna infrastruktura uliczna (trasa C + Dojlidy)

**Dokończenie 2026-11-15:** obejrzałem wszystkie **31 pobranych kadrów** (zad. 6; 22 z trasy C: Panoramax 2019 i KartaView 2019/2021, 9 z Dojlid: Commons CC0). Manifest ma teraz **113 wierszy**: 31 kadrów (R6-073…R6-103) i 10 zliczeń cech (R6-104…R6-113). Samokontrola nowych wierszy: seed 20261115, 9 z 41, wynik **8 PASS / 1 FIX** (poprawione). Recenzja: `REVIEW.md`. Kopie kadrów ≤ 1600 px są w repo (`files/jpg1600/` + `INDEX.csv`, 6,1 MB).

**Stan pierwotny —** Data: 2026-11-14 · gałąź `research/cloud2-pavements-kerbs` · **72 wiersze** manifestu (69 SOURCED, 3 UNVERIFIED) ·
**obejrzane obrazy: 3 strony dokumentu ZDM (rys. 3, rys. 9, s. 11); kadry uliczne: 0 obejrzanych** ·
samokontrola: **15 PASS / 0 FAIL** (seed 20261114, 15 z 72 = 21 %, 2 wiersze obrazowe ponownie obejrzane).

> *(Nieaktualne od 2026-11-15 — kadry obejrzane, patrz „Kadry”.)* **STAN 2026-11-14: PAKIET NIEDOKOŃCZONY — sesja przerwana na polecenie lidera (limit).** Zrobiona jest część normowa
> (zad. 1–5: liczby z dokumentów) i statystyka OSM. **Zadanie 6 (≥ 30 obejrzanych kadrów) NIE jest wykonane**:
> 31 kadrów wybrano i pobrano (`frames_selected.json`, sha256, azymuty z API), przygotowano widoki 960 px i wycinki 3×,
> ale ŻADEN nie został obejrzany — dlatego nie ma ich w manifeście i nie ma żadnego opisu „co widać”, liczby kadrów
> per typ kostki, ani oceny widoczności łat/spękań. Sekcja zasobów CC0 (ambientCG/Poly Haven) też nie powstała.

## Metoda
- Dokumenty pobrane (`fetch.py`, sha256), tekst przez `pdftotext -layout`, cytaty dosłowne z numerem punktu i strony PDF.
  Wytyczne ZDM mają uszkodzoną warstwę tekstową (brak polskich znaków): strony 10, 11, 18 wyrenderowano i obejrzano,
  cytaty z pozostałych stron mają diakrytyki odtworzone (zaznaczone w `uwagi`).
- OSM: Overpass niedostępny przez proxy → API 0.6 `/map` (24 kafle, 2026-11-14 17:08–17:09 UTC), `osm_analyze.py` → `osm_summary.json`.
- Niedostępne przez proxy sesji: gov.pl, archiwum.gddkia.gov.pl, web.archive.org, yadda.icm.edu.pl; Commons API — 429.
  Skutek: oryginałów KTKNPiP, DSN/SOSN GDDKiA, WR-D-63 i norm PN-EN nie otwarto; użyto kopii OST/SST z BIP gmin i wzorców WR-D.

## Tabela dla generatora nawierzchni/decali (tylko wartości ze źródeł)
| Typ | Wymiary | Kolor (słownie) | Wzór | Gdzie | Częstość | Wiersze |
|---|---|---|---|---|---|---|
| krawężnik uliczny | 15×30×100 lub 20×30×100 cm; spoina ≤ 1 cm; światło 10–12 cm (wyjątkowo 6 / 16) | szary beton | moduł 1 m | krawędź jezdni | UNVERIFIED (kadry nieobejrzane) | R6-001, 002, 009, 012 |
| krawężnik przystankowy | światło 16 cm | — | — | zatoki/przystanki | wg G5 | G5 README pkt 2 (cytuję, nie dubluję) |
| krawężnik na przejściu (wyspa/pas dzielący) | ≤ 2 cm (przepis do 2022); dziś „uskok dostosowany”, przejazd rowerowy ≤ 1 cm | — | — | przejścia, przejazdy | — | R6-004, 005, 006 |
| krawężnik „na płask” (wjazd) | 20×30×100 cm ułożony na płask | szary | — | wjazdy bramowe | UNVERIFIED | R6-011 |
| krawężnik najazdowy przy DDR | 25×12×100 cm, skos 0 → +3 | szary | — | granica DDR/chodnik, przejazdy | UNVERIFIED | R6-015 |
| krawężnik drogowy | 12×25×100, 10×25×100 cm | szary | — | drogi bez chodnika | UNVERIFIED | R6-010 |
| obrzeże | 8×30×100 cm (SST), 6×20×100 cm (katalog) | szary | — | krawędź chodnika od zieleni | UNVERIFIED | R6-016, 017 |
| kostka prostokątna 20×10 | 100×200 mm, gr. 60 (piesi) / 80 (ruch pojazdów, parkowanie na chodniku — ZDM); spoina 3–5 mm; tolerancja ±2/±2/±3 mm | szary (beton niebarwiony); czerwony/grafit = barwiona warstwa ≥ 4 mm | UNVERIFIED (jodełka/półcegła — z kadrów) | chodniki, zjazdy | UNVERIFIED | R6-018…022, 026 |
| kostka „podwójne T” | 198×163 mm, gr. 60/80/100 | szary | zazębiana | zjazdy, place | UNVERIFIED | R6-023 |
| kostka typu starobruk | 120×180 / 120×120 / 120×90 mm, gr. 60/80 | — | wieniec wokół włazów (rys. ZDM) | obróbka studni, hydrantów, zasuw | przy każdym włazie w kostce (wymóg ZDM) | R6-024, 027 |
| płyta chodnikowa | 350×350×50, 500×500×50 mm; 30×30 — brak źródła | szara / czerwona / grafit (katalog) | UNVERIFIED | starsze chodniki | UNVERIFIED | R6-025 |
| właz w jezdni | prześwit 600 mm, D400, korpus 150 mm; oś włazu w osi pasa ruchu | żeliwo | — | jezdnia | rozstaw UNVERIFIED | R6-028, 030 |
| właz poza jezdnią | prześwit 600 mm, C250 żeliwno-betonowy | żeliwo + beton | — | chodnik, zieleniec, DDR | UNVERIFIED | R6-029 |
| wpust uliczny | studzienka Ø 500 mm; krata jezdniowa D400 z zawiasem i ryglem; rama 620×420 lub 500×500 mm (karta producenta) | żeliwo | — | przy krawężniku, poza śladem kół | **rozstaw UNVERIFIED** | R6-031…036, 038 |
| łata asfaltowa (decal) | „nałożona” lub „wbudowana” po frezowaniu; < 20 m długości (dłuższa na całą szer. pasa = nowa nawierzchnia) | UNVERIFIED | UNVERIFIED | jezdnia | UNVERIFIED | R6-042, 043 |
| spękania | siatkowe / pojedyncze podłużne / pojedyncze poprzeczne; rejestrowane ≥ 10 cm; także zalane | — | — | jezdnia | UNVERIFIED | R6-041, 044 |
| koleiny | progi GP/G/Z: 10 / 20 / 30 mm (pożądany / ostrzegawczy / krytyczny) | — | — | pasy ruchu | UNVERIFIED (to progi oceny, nie pomiar) | R6-046 |
| przejazd rowerowy | czerwony RAL 3020, masa chemoutwardzalna z uszorstnieniem (powierzchniowo); styk z jezdnią bezszwowy | czerwony | — | przejazdy | — | R6-050, 051 |
| DDR | „wyraźnie inny kolor” (ZDM); „czerwony i jego odcienie” (zalecenie WR-D-42-2); niżej niż chodnik, wyżej niż jezdnia | czerwony | — | wzdłuż ulic | inwentarz = M65 | R6-048, 049, 052 |

## Kadry (zad. 6, 2026-11-15) — co widać na 31 obejrzanych kadrach
Metoda: każdy kadr obejrzałem jako arkusz: pełny kadr 960 px + dwa wycinki dolnych narożników (ok. 2×), gdzie są krawężniki i pobocza. Opisy są w `frames_desc.json` i w kolumnie `opis_co_widać`. Wysokości krawężników **nie są mierzone** z obrazu (UNVERIFIED). Próba nie jest losowa: kadry dobrano pod trasę C i Dojlidy.

| Cecha | Kadrów (z 31) | Gdzie | Wiersz |
|---|---|---|---|
| jezdnia asfaltowa jako temat kadru | 24 | wszystkie kadry trasy C + F38, F39 | R6-104 |
| szary krawężnik betonowy przy jezdni | 21 | trasa C i Dojlidy | R6-105 |
| kapa chodnikowa **czerwonobrązowa** na obiektach mostowych (estakady Andersa/Maczka) + szary krawężnik mostowy + bariera na kotwach | 6 | F04, F05, F14, F19, F20, F30 | R6-106 |
| wpust z kratą przy krawężniku (prostokątny, krata rdzawa, w linii krawędziowej) | 2 | F14, F30 (estakada Andersa) | R6-107 |
| kostka betonowa prostokątna (chodnik/pas) | 9 | rzędy poprzeczne do osi (F31, F32, F34, F35), układ ukośny/jodełka (F36, F37 — UNVERIFIED), pas przy jezdni (F17) | R6-108 |
| płyty betonowe (chodnik/opaska) | 3 | F09, F16, F40 (duże płyty) | R6-109 |
| **droga dla rowerów z szarego asfaltu** | 7 | wszystkie DDR na kadrach Dojlid (Kuronia, Mickiewicza, Dywizjonu 303) | R6-110 |
| pas z czerwonej kostki betonowej | 1 | F38 (Mickiewicza; funkcja UNVERIFIED) | R6-111 |
| czerwony przejazd rowerowy | 1 | F39 (z daleka) | R6-112 |
| uszkodzenie lub ślad zużycia | 9 | F04 poprzeczny szew, F06 rysa, F11/F14 ciemne smugi, F20 wytarta linia, F30 rdzawe zacieki, F36 podłużne pęknięcie DDR, F35 łata w kostce, F09 brud | R6-113 |

Wnioski dla generatora (ESTIMATED z obrazu):
- **DDR w Dojlidach jest szara (asfalt), nie czerwona** (7/7 kadrów). Czerwień występuje tylko na przejazdach (F39) i w pojedynczym pasie kostki (F38). Zalecenie „czerwony” z WR-D-42-2 (R6-049) **nie opisuje stanu tych ulic**.
- Na estakadach trasy C kapy są czerwonobrązowe, a krawężniki szare, wysokie; wpusty są w linii krawędziowej przy krawężniku.
- Na kadrach nie widać wybojów, siatki spękań ani kolein. Nawierzchnia trasy C (2019–2021) jest w większości jednolita; ślady to pojedyncze szwy, rysy i smugi. Decale łat i spękań powinny być rzadkie.
- Panoramax: azymuty F06/F07 z API różnią się od kursu toru o ok. 55° (por. R9 PX17, R2-011). Do kamer używać kursu toru.
- Kadry tunelu/wykopu (F10 prześwietlony, F29 w pomarańczowym świetle) nie nadają się do oceny koloru nawierzchni.

## Najważniejsze ustalenia
1. **Dz.U. 2022 poz. 1518 nie podaje liczbowej wysokości krawężnika jezdni** (R6-005) — zakładane w zleceniu „10–14 cm / 0–2 cm” nie ma tam pokrycia. Liczby: 6–16 cm i ≤ 2 cm są w uchylonym Dz.U. 2016 poz. 124 (§ 43 ust. 5, § 127 ust. 10), 10–12 cm w OST D-08.01.01b.
2. Generator `KERB_HEIGHT = 0,13 m` leży 1 cm powyżej domyślnego zakresu OST (10–12), w granicach 6–16.
3. Technologia barwienia DDR (w masie vs powierzchniowo) — **w żadnym otwartym źródle nie rozstrzygnięta**; tylko przejazdy mają jawnie masę chemoutwardzalną RAL 3020.
4. OSM nie niesie koloru nawierzchni (0 tagów `colour`/`surface:colour`) ani włazów (0 węzłów `manhole`) przy trasie; `kerb=*` — 2 węzły.

## Co już było w repo / co nowe
| Temat | Było | Nowe tutaj |
|---|---|---|
| krawężnik przystankowy 16 cm, właz D400/600 | G5 (README pkt 2) | tylko cytowane; dodane C250/115 mm poza jezdnią, oś włazu |
| wpusty: „UNVERIFIED (brak wymiarów)” | p2-surfaces-2 M52-115 | Ø 500, typy i klasy krat (ZDM pkt 20–24), wymiary ram z karty |
| oznakowanie poziome, płytki dotykowe | p2-surfaces-2 | nie ruszane |
| inwentarz DDR | M65 (Mistral) | tylko wymagania barwy/technologii/poziomu |
| rozmiary kostki w materiałach | ADR 0063 (holland 20×10, płyta 35×35, behaton ~210×140 WORKING_VALUE) | wymiar katalogowy „podwójnego T” 198×163, grubości, spoiny, tolerancje |

## Luki (do domknięcia w następnej sesji)
- Zad. 6 zrobione 2026-11-15 (31 kadrów). Nadal brak kadrów: Sokólska, Wysockiego, Kombatantów; sekw. KartaView 1155711 (Tysiąclecia) nieużyta. Rozmiar kostki z obrazu: nie mierzony.
- Rozstaw wpustów [m], wymiar kraty 400×600, korytka odwodnienia liniowego, płyta 30×30 — brak źródła.
- PN-EN 1338/1339/1340, PN-EN 124 — tylko pośrednio (OST/STWiORB); PN-EN 1339 (płyty) bez cytatu.
- KTKNPiP, DSN/SOSN GDDKiA, WR-D-63 — hosty niedostępne; klasyfikacja uszkodzeń wzięta z WR-D-83-2 (drogi samorządowe).
- Numery stron dla R6-041 i R6-045 oznaczone UNVERIFIED (punkt pewny, strona nie sprawdzona).
- Sekcja tekstur CC0 — nie zrobiona (już użyte Poly Haven: lista w `art-source/world/cc0/cc0_manifest.json`).
- Strony ZDM 5, 6, 16, 19, 21: cytaty z warstwy tekstowej, strony nieobejrzane.

## Jak używać w grze
Tabela powyżej → parametry prototypów krawężnika/obrzeża i modułów kostki; progi WR-D-83-2 → reguły decali (łata < 20 m, spękanie ≥ 10 cm, wybój ≥ 5 cm). Częstości i wzory układania czekają na oględziny kadrów — do tego czasu WORKING_VALUE generatora zostają.
