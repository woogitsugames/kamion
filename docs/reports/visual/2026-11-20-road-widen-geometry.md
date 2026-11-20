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

### Ponowny przegląd właściwego kodu G2 `_service_tees_fit`

**PASS: obie uwagi implementacyjne wariantu diagnostycznego zamknięte.** Wywołanie przekazuje całe aktualne grupy
`ga` / `gb`. Helper zbiera ramiona wszystkich ich węzłów i sprawdza wszystkie sekcje każdego ramienia: wymagane D,
bez ring i bez compact (także pusty obiekt compact jest poprawnie wykluczony). Droga publiczna przy wcześniej
wchłoniętym węźle blokuje zastosowanie reguły. Próg uwzględnia najszerszą jezdnię w tych grupach.
Wymagana jest zarówno długość łącznika, jak i minimalny fizyczny odstęp węzłów obu grup co najmniej dwóch szerokości;
długi zakrzywiony łącznik o bliskich końcach nie wystarcza już do rozdzielenia skrzyżowań.

Przeczytano regresje publicznego wchłoniętego węzła, ring, compact i niewystarczającego odstępu oraz test rzeczywistego
parkingu: osobne T, zachowany niepochłonięty łącznik, dodatnia długość wstęgi między przycięciami i poprawne poligony.
Bez uruchamiania dodatkowych procesów. Wynik gotowych powierzchni i toru w obu kierunkach potwierdza dopiero aktualne QA.

## DK8 — wycofanie błędnej diagnostyki `dk8-placement-b`

**Poprzedni PASS dla -0,55 → +0,02 m na podstawie pasków N180/220/260 jest wycofany.**
Skrypt `dk8_placement_strips.py` wybrał `w238861874`, który zaczyna się przy N335,85. Projekcja trzech punktów
zatrzymywała się na końcu tej samej krawędzi, więc etykiety N180/220/260 nie opisywały faktycznych klatek.
Recenzja powinna była wychwycić powtarzającą się treść pasków; tamten obraz nie jest dowodem położenia w tych miejscach.
Autor przywrócił `dk8-placement-b` do -0,55. Wynik fitu tego edge nie stanowi zatwierdzonej korekty danych w tej recenzji.

## DK8 — właściwa krawędź `dk8-placement-a`

Obejrzano `artifacts/road-widen-s24/dk8-correct-edge-strips.png` i poprawiony skrypt z kontrolą zakresu projekcji.
Krawędź `w882366266:2256069816-8205694666` obejmuje N146,58…335,85; rzeczywiste środki próbek mają
N180,001 / 219,979 / 260,008. **PASS dla osobnej korekty położenia -0,50 → -0,18 m**, bez zmian liczby pasów i szerokości.

W trzech rzeczywistych próbkach linia między pasami jest wykryta przy -0,30 / -0,10 / -0,05 m. Błąd przewidywanej
linii spada odpowiednio z 0,20 / 0,40 / 0,45 m do 0,12 / 0,08 / 0,13 m; poprawa jest widoczna w parach pasków.
Fit całego edge: 9 użytecznych profili z 15, we wszystkich dwa pasy, MAD granic 0,07 / 0,07 / 0,05 m.

Granice bazowej jezdni 8 m po korekcie wynoszą [-4,18; +3,82] m. Mieszczą się w wykrytym asfalcie każdej próbki:
[-4,70; +3,90], [-4,40; +4,10], [-4,35; +4,20] m. Na pokazanych przekrojach nie zabierają rzeczywistego separatora.
To silniejszy dowód położenia niż dotychczasowy center-only override z `confidence: low`.

Rzut pokazuje bazowe 8 m, nie końcową jezdnię GAMEPLAY ani pełną geometrię sąsiadów. Ostateczne zachowanie separatora
i usunięcie fantomowej wyspy nadal wymagają aktualnego fidelity oraz rzutu po przebudowie.
