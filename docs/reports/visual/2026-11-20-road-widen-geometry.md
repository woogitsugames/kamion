# Kontrola geometrii D94 — G1/G2, 2026-11-20

Niezależny przegląd wg `.claude/skills/visual-qa/SKILL.md`, krok 5. Zakres: plan geometrii na ortofoto GUGiK HR;
bez Unity, zgodnie z poleceniem właściciela. Materiały, oświetlenie, wysokości i gotowe siatki krawężników nie są oceniane.

## Obejrzane dowody

- `artifacts/road-widen-s24/parking-g1-ortho.png`: cyjan = wstęgi dróg, żółty = obrys skrzyżowania,
  czerwony punkt = poprzedni blind-end E -208,01 / N -287,49.
- `artifacts/road-widen-s24/dk8-g1-ortho.png`: ten sam typ rzutu, E -600…-500 / N 170…270.
- Skrypty obu rzutów i diff `network.py` / `junctions.py` względem `44c697546`.

## Werdykt rzutów

**Parking: PASS w zakresie obrysu przejazdu.** Czerwony punkt jest wewnątrz ciągłej nawierzchni skrzyżowania;
pomarańczowa krawędź obrysu go nie przecina. Wejście z północy oraz połączenie z drogą biegnącą przy DK8 są otwarte.
Zachodnie i południowe wyokrąglenia dochodzą do istniejących przejazdów. Obrys nie tworzy w pokazanym miejscu ślepej
łezki asfaltu. To potwierdza usunięcie przyczyny na planie; wynik gotowych powierzchni i torów potwierdza road_consistency.

**DK8: PASS wyłącznie dla zachowania widocznego pasa rozdziału w tym kadrze.** Cyjanowe wstęgi jezdni są oddzielone;
nie pokrywają całego rzeczywistego pasa zieleni na osi. Widać też niewypełnione fragmenty asfaltu przy krawędzi tego
pasa. Sam rzut nie rozstrzyga fantomowej wyspy: nie pokazuje bocznych powierzchni ani klasyfikacji fidelity.
Nie daje podstaw do ogłoszenia wyniku „0 fantomowych wysp”.

## Uwagi do algorytmu G1

1. **P1, ochrona parkingu tylko z jednej strony** — `widening_clearance` i kierunkowy przydział wzrostu dotyczą
   wyłącznie oneway. Równoległa dwukierunkowa droga parkingowa rośnie symetrycznie i może pomniejszyć separator,
   mimo że sąsiednia jezdnia DK8 zachowuje swoją krawędź. Test G1 miał obu sąsiadów oneway. Zgłoszono autorowi;
   wspólne planowanie obu typów sekcji i regresja one-way + two-way są w przygotowaniu.
2. **P1, podwójne wydawanie nadwyżki** — każda strona pary dostaje całe `gap - reserve`. Gdy oba odcinki wybiorą tę
   samą szczelinę, suma wzrostów może przekroczyć nadwyżkę. Przykład: 12,25 m szczeliny i 12 m rezerwy pozwala obu
   stronom zużyć po 0,25 m, zostawiając 11,75 m. Potrzebny wspólny budżet pary lub konserwatywnie połowa nadwyżki.
3. **P2, szerokość lokalna** — offset_profile jest próbkowany, ale gap używa maksymalnych `width` obu sekcji.
   Przy width_profile może to zaklasyfikować rzeczywistą lokalną szczelinę jako nakładającą się nawierzchnię
   (`gap < 0.25`) i pominąć ograniczenie. Obie szerokości należy odczytywać w miejscach porównania.

Powyższe uwagi oznaczają **FAIL dla ogólnej gwarancji ochrony separatorów w G1**, mimo PASS obrysu parkingu.
Przegląd końcowych wyników wymaga aktualnego fidelity, road_consistency i combo_lane_check po poprawkach.
