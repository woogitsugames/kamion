# Kandydat następnej rundy cab — zużycie i szerokie pasmo deski

Stan po obejrzeniu natywnego cab-grain Low overcast night1 oraz rzeczywistego DAF XF Cockpit (Spacekid, CC0; dane w cab-r1/REFERENCES-0112.md). Nie wprowadzono jeszcze zmian gry.

Zdjęcie pokazuje satynowe przejścia na dotykanej kierownicy, matową deskę i lokalne zabrudzenia. Inna poza, model i nieznana ekspozycja wykluczają kopiowanie wartości RGB. Render ma czytelne drobne tłoczenie, ale szerokie ciemne pasmo zmiękcza powierzchnię pod kratką. Pochodzenie pasma wymaga rozdzielenia geometrii/normali, wypieku diffuse i barw wierzchołkowych. Nie przypisywać go rozciągnięciu UV: poprzedni pomiar tego nie potwierdził. Odrzucony odzysk fill z r2 nie usunął pasma.

Pierwszy pomiar r4 po merge main: świeży baseline, kontrolowane obrazy tej samej kamery z normalnym materiałem oraz osobno bez wypieku, bez detalu i z płaską roughness/barwą w pamięci. Korzystać z istniejących narzędzi QA, jeśli obejmują te warianty; nie dodawać automatycznie kolejnego helpera. Dopiero po wyniku wybrać zmianę danych albo źródłowego bake. Zachować rzeczywiste szczeliny i cień pod kratką, bez globalnego rozjaśnienia kabiny.

Jeśli pasmo okaże się uzasadnioną formą/geometrią, przejść do lokalnego zużycia kontaktowego: źródło już ma maski dłoni 10/2, podłokietników i uchwytów. Sama zmiana mnożnika nie jest dowodem poprawy. Wymagane oglądanie przed/po i kontrola, by czarne części nie stały się beżowymi lub chromowanymi. Low bez dodatkowych draws/pass/fetch; foto i render do 960 px, parametry WORKING_VALUE.

Szeroki ciemny obszar WideR z bieżącego oka jest zawartością RT, nie fizyczną osłoną. Nie przesuwać kanału, oka lub optyki w celu jego ukrycia.

Doprecyzowanie po ponownym obejrzeniu istniejącego k4-channel-crops-960.jpg z r2: ablacja ao-flat usuwa szerokie ciemne pasmo; roughness-flat i detail-off go nie usuwają. Istnieją już wyniki CabSurfaceAudit (r1/surface-audit-High-clear) i nie należy bez potrzeby powtarzać całego rozpoznania. R4 ma zacząć od odczytu tych wyników i atlasu/bake, a świeży baseline po merge służy sprawdzeniu aktualnego stanu. Nie zgłaszamy jeszcze zmiany mapy ani wizualnej poprawy.
