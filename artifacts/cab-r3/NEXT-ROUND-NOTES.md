# Kandydat następnej rundy cab — zużycie i szerokie pasmo deski

Stan po obejrzeniu natywnego cab-grain Low overcast night1 oraz rzeczywistego DAF XF Cockpit (Spacekid, CC0; dane w cab-r1/REFERENCES-0112.md). Nie wprowadzono jeszcze zmian gry.

Zdjęcie pokazuje satynowe przejścia na dotykanej kierownicy, matową deskę i lokalne zabrudzenia. Inna poza, model i nieznana ekspozycja wykluczają kopiowanie wartości RGB. Render ma czytelne drobne tłoczenie, ale szerokie ciemne pasmo zmiękcza powierzchnię pod kratką. Pochodzenie pasma wymaga rozdzielenia geometrii/normali, wypieku diffuse i barw wierzchołkowych. Nie przypisywać go rozciągnięciu UV: poprzedni pomiar tego nie potwierdził. Odrzucony odzysk fill z r2 nie usunął pasma.

Pierwszy pomiar r4 po merge main: świeży baseline, kontrolowane obrazy tej samej kamery z normalnym materiałem oraz osobno bez wypieku, bez detalu i z płaską roughness/barwą w pamięci. Korzystać z istniejących narzędzi QA, jeśli obejmują te warianty; nie dodawać automatycznie kolejnego helpera. Dopiero po wyniku wybrać zmianę danych albo źródłowego bake. Zachować rzeczywiste szczeliny i cień pod kratką, bez globalnego rozjaśnienia kabiny.

Jeśli pasmo okaże się uzasadnioną formą/geometrią, przejść do lokalnego zużycia kontaktowego: źródło już ma maski dłoni 10/2, podłokietników i uchwytów. Sama zmiana mnożnika nie jest dowodem poprawy. Wymagane oglądanie przed/po i kontrola, by czarne części nie stały się beżowymi lub chromowanymi. Low bez dodatkowych draws/pass/fetch; foto i render do 960 px, parametry WORKING_VALUE.

Szeroki ciemny obszar WideR z bieżącego oka jest zawartością RT, nie fizyczną osłoną. Nie przesuwać kanału, oka lub optyki w celu jego ukrycia.

Doprecyzowanie po ponownym obejrzeniu istniejącego k4-channel-crops-960.jpg z r2: ablacja ao-flat usuwa szerokie ciemne pasmo; roughness-flat i detail-off go nie usuwają. Istnieją już wyniki CabSurfaceAudit (r1/surface-audit-High-clear) i nie należy bez potrzeby powtarzać całego rozpoznania. R4 ma zacząć od odczytu tych wyników i atlasu/bake, a świeży baseline po merge służy sprawdzeniu aktualnego stanu. Nie zgłaszamy jeszcze zmiany mapy ani wizualnej poprawy.

Kandydat konkretnej ablacji r4: shader mnoży albedo przez lerp(0.4,1,smoothstep(0.04,0.28,ao)) oprócz tłumienia całego GI przez ten sam wypiek. Dotychczasowy odrzucony fill-recovery zmieniał jedynie _CabFill, pozostawiając to szerokie tłumienie albedo. Sprawdzić osobno wyłączenie samego mnożnika albedo w pamięci, z pozostawieniem GI/specular AO oraz sceny/ekspozycji. Jeżeli usuwa pasmo kosztem szczelin, ocenić węższy zakres wyłącznie głębokich kontaktów, oparty na próbkach atlasu; dane i progi WORKING_VALUE. Nie przyjmować poprawy przed obejrzeniem Low/High clear/overcast i szczelin. Bez dodatkowych sampli lub przebiegów.

Recenzja s12 batch B (REVIEW-2026-11-12-s12-gpt-batch-b.md) daje konkretniejszy priorytet materiału: duże fale skórzanego tłoczenia czytają się jak skaj, a nie TPO/PP. R4 rozważy high-pass normalnych Plastic przed dalszym zwiększaniem zużycia. Obecny konwerter skaluje XY normalnej jednolicie, zachowując niskie częstotliwości. Kandydat powinien odjąć wygładzoną składową XY w fizycznie opisanej skali, ponownie znormalizować wektory, zachować tryb zero jako bitowo zgodny oraz nie dotykać Leather. Wymagana reprodukcja map, brak zmian alfy i A/B High/Low; samo widmo normalnych nie dowodzi lepszego obrazu.

Recenzja nie uznaje wcześniejszej porażki determinizmu za dowiedzioną bazę main. R1/r2 dowodzą jej powtarzania w tej linii cab, nie wyniku czystego main. Nie rozszerzać scope na kod świata. Końcowy GIS r3 na świeżym World/Fidelity poda bieżący wynik; niezależny czysty main pozostaje po stronie lidera.
