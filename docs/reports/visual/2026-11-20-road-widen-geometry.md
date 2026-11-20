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

## Ponowny przegląd — `6c058ba9c`

Trzy konkretne uwagi G1 są **zamknięte w kodzie**:

- P1 parking: obliczenie clearance, przydział wzrostu i przesunięcie obejmują wszystkie sekcje poza roundabout,
  także dwukierunkową drogę parkingową. Test sąsiada parametryzuje teraz oba kierunki ruchu i obie strony.
- P1 budżet pary: każda ze stron ma najwyżej połowę nadwyżki ponad rezerwę. Suma wydatków obu stron nie przekracza
  tej nadwyżki. Dodano regresję z dwiema środkowymi jezdniami ograniczonymi przez zewnętrzne.
- P2 profile: obie szerokości są interpolowane z profili w miejscu próbki / projekcji. Nakładanie bez wspólnego
  węzła nie usuwa już ograniczenia, więc nie staje się fałszywie nieskończonym luzem. Dodano test profilu.

**PASS dla zamknięcia wskazanych uwag w kodzie.** Nie uruchamiano ciężkich poleceń ani Unity; ocena testów opiera
się na ich treści, a wykonanie raportuje autor. Poprzednie rzuty pokazują stan G1/G2, nie wynik nowej przebudowy.
Pełne PASS dla kafla C i zachowania ronda pozostaje zależne od aktualnych fidelity, road_consistency i combo_lane_check.
Rezerwa 12 m jest parametrem roboczym geometrii; sama w sobie nie jest pomiarem szerokości separatora z ortofoto.

## Parking — dwa oddzielne T (wariant diagnostyczny)

Obejrzano `artifacts/road-widen-s24/parking-separate-ortho.png` i mock `parking_separate.py`, bez zmiany kodu generatora.
**PASS kierunku geometrycznego:** dwa lokalne poligony T połączone krótką wstęgą lepiej odpowiadają ortofoto.
Południowe krawędzie zostawiają miejsce dla rzędu postojowego przy E -200 / N -297; wcześniejszy duży poligon G1
przykrywał jego koniec. Przejazd z północy jest otwarty na planie, a zachodnie i wschodnie połączenia są ciągłe.

Autor zgłosił, że pełny G1 usunął stary przypadek kerb, ale pozostał blind-end `None` w przeciwnym kierunku
(E -210,68 / N -279,71). Rzut nie pokazuje toru testowego ani gotowych powierzchni; po rozdzieleniu węzłów należy
powtórzyć klasyfikację obu kierunków. Samo pokrycie starego punktu poligonem nie wystarcza.

Reguła zachowania osobnych skrzyżowań wyłącznie klasy D, gdy łącznik ma co najmniej dwie szerokości jezdni,
jest sensownym ograniczeniem skali klastra. Połowa łącznika dostępna dla każdego T wymusza lokalne łuki zamiast
pochłaniania pętli. Dwie uwagi do wdrożenia:

- **P1:** mock bada klasy ramion tylko przy endpointach łącznika. W trakcie iteracyjnego scalania ich aktualne grupy
  mogą już zawierać drogę publiczną lub rondo przy innym węźle. Warunek musi obejmować wszystkie węzły obu obecnych
  grup (`ga + gb`) i wykluczać ring/compact, by deklarowane „publiczne i ronda bez zmian” było prawdziwe.
- **P2:** długość łukowa nie gwarantuje fizycznego odstępu dwóch T przy zakrzywionym łączniku. Po wdrożeniu warto
  objąć kontrolą taki przypadek i poprawność obu poligonów; obecny prosty łącznik parkingu tego ryzyka nie pokazuje.

Wariant ma **PASS dla przedstawionego planu**, ale ogólna reguła wymaga usunięcia P1 i ponownego road_consistency.

## DK8 — diagnostyka położenia `dk8-placement-b`

Obejrzano `artifacts/road-widen-s24/dk8-placement-strips.png` (N 180 / 220 / 260, po dwie wersje), skrypt rysujący
i `fit-placement-diagnostic.log`. Nie zmieniano danych. **PASS dla osobnej korekty pomiaru położenia -0,55 → +0,02 m.**
We wszystkich trzech parach przewidywana linia między pasami po korekcie trafia w linię wykrytą i widoczną na
ortofoto. Stara pozycja jest konsekwentnie odsunięta o około 0,5–0,6 m. Nowa granica bazowej jezdni po stronie
centralnego separatora dochodzi bliżej rzeczywistej krawędzi asfaltu; widoczny separator pozostaje poza nią.

Diagnostyczny fit dla `w238861874:8205694666-2081020082`: 17 użytecznych profili z 29, we wszystkich dwa pasy;
MAD trzech granic 0,09 / 0,05 / 0,10 m. Jest to mocniejszy dowód niż dotychczasowy center-only override opisany
`confidence: low`. Zmiana centrum powinna mieć własny opis źródła i dowodów, bez zmiany liczby pasów.

Rzut pokazuje stałe bazowe 8 m, nie końcową jezdnię GAMEPLAY ani pełną geometrię jej sąsiadów. Z tego powodu
ostateczne zachowanie separatora i usunięcie fantomowej wyspy wymagają ponownego fidelity oraz rzutu po przebudowie.
Ocena centrum nie oznacza automatycznej akceptacji całego diagnostycznego fitu (8,44 m i lane_edges).
