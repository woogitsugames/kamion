# Kontrola pionowej projekcji jezdni — dwa kadry po osi drogi

12 listopada 2026. Obejrzałem ponownie natywne zdjęcia 1280×960 oraz natywne rendery wariantów 328135-21 i 297817-26. Nie wyznaczam automatycznie nowego horyzontu z krzywej jezdni. W obu zdjęciach dalszy przebieg drogi znajduje się niżej w obrazie niż w renderze; portal trafia bliżej swojej wysokości zdjęciowej. Oznacza to konflikt kotwic, którego nie wolno zamknąć dopasowaniem wyłącznie belki portalu.

Ręczny, orientacyjny odczyt pasma dalszej jezdni w obrazie (nie pomiar poziomego horyzontu):

| Kadr | Zdjęcie: zakres y/960 | Render: zakres y/960 | Status |
|---|---|---|---|
| 328135 / wariant 21 | około 0,76–0,79 | około 0,66–0,69 | WORKING_VALUE; jezdnia i znaki są częściowo zasłonięte |
| 297817 / wariant 26 | około 0,76–0,79 | około 0,66–0,69 | WORKING_VALUE; jezdnia zmienia kierunek i niweletę |

To szerokie przedziały odczytane wzrokowo, nie dopasowane proste i nie skalibrowany pitch. Źródłowy zapis h=0,685 jest założeniem kamery, a nie dowodem, że droga ma zbiegać się dokładnie w tym y. Wzniesienie, krzywizna i przesunięta geometria mogą powodować część różnicy. Wysokość belki zależy również od roboczej wysokości i odległości portalu.

Następna minimalna próba w kolejnej rundzie: zamrozić XY i wysokość oka wariantów 21/26 oraz yaw/FOV; wyrenderować tylko dwa dodatkowe pitch odpowiadające h=0,74 i 0,77, wraz z kontrolnym h=0,685. Porównać jednocześnie portal, krawędzie jezdni i kierunek dalszego odcinka. Nie przesuwać portalu ani drogi. Nie uznawać niższego błędu jednej kotwicy za akceptację pozy. Każda z sześciu prób pozostanie C do niezależnego przeglądu.

W tej rundzie zamykam dowody bazowe, ranking oraz historię ocen. Dalsze eksperymenty z kamerą przechodzą do r4 po wymaganym końcowym pytest GIS i dostawie raportu r3; nie opóźniam tego kolejną szeroką siatką renderów.
