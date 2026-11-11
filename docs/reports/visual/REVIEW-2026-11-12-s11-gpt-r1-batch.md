# Recenzja niezależna — pakiet 4 rund GPT r1 (life, vegetation, cab, edge) — s11

Data: 2026-11-12 · Recenzent: visual-critic (Opus), niezależny od autorów i ich self-review.
Pytanie: czy każdą gałąź można **scalić do main**. Kryteria: (a) brak regresji rozpoznawalności trasy wg D51 i obrazu w kadrach trasy, (b) budżet Low (draws/tris) nie rośnie, (c) docs/06 — poprawa albo brak pogorszenia. Wygląd PARTIAL jest dopuszczalny, jeśli nie ma regresji.
Wszystko poniżej to render edytora (2340×1080). Żadna runda nie była na telefonie — koszt GPU A16 dla wszystkich czterech: UNVERIFIED.

Metoda własna (poza czytaniem REPORT/SELF-REVIEW): obejrzane pary przed/po i zdjęcie|render ≤960 px; różnica pikselowa (luminancja, 1/4 rozdzielczości, średnie |Δ| i odsetek pikseli z |Δ|>8) na pełnych zestawach PNG Low-clear każdej rundy; odczyt `budget-summary.json`, `comparison-0112-p2.json`, `all-cameras.csv`; symulacja scalenia `git merge-tree` main → life → vegetation → cab → edge (tylko obiekty wiszące, gałęzie nietknięte).

## Podsumowanie

| Runda | Werdykt scalenia | Jakość | (a) trasa D51 | (b) Low draws / tris | (c) anti-slop |
|---|---|---|---|---|---|
| life r1 | **SCAL** | PARTIAL | bez regresji (63/92 kamer identycznych, zmiany tylko w kadrach aut) | draws −24…0, tris −2k…0 | poprawa (usuwa plamy „pleśni” obecne w main) |
| vegetation r1 | **SCAL** | PARTIAL | bez regresji (trawa zmienia się w prawie każdym kadrze, układ/obiekty nie) | 0 / 0 % | niewielka poprawa trawy, berberys bez przebić |
| cab r1 | **SCAL** | PASS funkcji lusterek, PARTIAL wyglądu | bez regresji (70/78 kamer trasy identycznych, reszta to kadry kabiny) | draws 0; tris +480/LOD (≤ +1k zaokr., ≤ 0,5 %) | poprawa (koniec wnętrza kabiny w lusterkach) |
| edge r1 | **SCAL warunkowo** (patrz uwaga budżetowa) | PARTIAL, wizualnie ~0 | bez regresji (89/89 kamer z średnim |Δ| < 0,05) | draws 0; tris +792 stale (≈ +0,25 %, zaokr. +1k w 69/89 kamer) | neutralnie (poprawka geometrii niewidoczna z drogi) |

Konflikty: każda gałąź scala się z main bez konfliktów tekstowych; sekwencja life → vegetation → cab → edge też czysta. life i vegetation obie zmieniają `WorldPBR.shader` (rozłączne bloki: `_CARPAINT`/tablice vs grunt) i żadna nie widziała zmian drugiej — po scaleniu obowiązkowo kompilacja wariantów Low/Medium (GLES3/Vulkan) i przebieg kamer kontrolnych Low/High × clear/overcast na wspólnym stanie. vegetation ma bazę `4c9905b1` (44 commity za main), pozostałe `5f2aa277` (43 za main).

**Uwaga budżetowa (b).** Literalnie „tris nie rośnie” spełniają tylko life i vegetation. cab (+480 tris/LOD ramek szkieł) i edge (+792 tris apronu, stale w kadrze) rosną o ułamki procenta przy zerowej zmianie draws. Uznaję to za brak istotnego wzrostu (obaj autorzy mierzyli wobec kontraktowego limitu ≤ +2 % i draws +0; cab równocześnie obniża draws kamer RT lusterek: Kerb 83→77, Front 120→100). Jeśli lider trzyma twarde „0 tris”, edge jest jedyną rundą, której przyrost nie kupuje niczego widocznego — wtedy edge NIE SCALAJ do czasu kompensaty.

Wspólna rysa procesowa: pełny GIS w vegetation/cab/edge kończy się porażką `test_road_fidelity::test_report_not_stale` (w cab dodatkowo `test_world_roads::test_export_is_deterministic`, chunk 0_0) — obecną już na bazie i udokumentowaną. Po integracji lider regeneruje fidelity_qa na main i wymaga zielonego GIS; nie dziedziczyć „znanej porażki”.

---

## 1. life r1 (osobówki R4) — SCAL · PARTIAL

Ważne: „przed” to kanoniczny main `5f2aa277`, który **już zawiera** brud R3 z ADR 0089, zakwestionowany w `REVIEW-2026-11-11-s10-gpt-0089.md` (P0-1). Ta runda go naprawia — to główny argument za scaleniem.

1. **P0-1 z poprzedniej recenzji zamknięty.** `review/High-overcast/r10_wheel_02.jpg`: przed — ciemnoszara rozmyta łata na środku drzwi białego kombi, po — brak oderwanych plam, nalot przy progu. `review/High-clear/g_current_black_wheel_02.jpg`: przed — „chmura” sadzy od progu do połowy drzwi z twardą górną krawędzią, po — czysto. Największa różnica pikselowa zestawu (r10_wheel_02: 24,7 % pikseli) to właśnie usunięcie tej plamy.
2. **Przegięcie w drugą stronę: za czysto.** Biały kombi (`r10_wheel_02`, `r10_front_04`) i szary (`r10b_grey_05`) wyglądają jak z salonu; nalot przy progu ledwo widoczny z 2–5 m w overcast. `g_dirt_level_3` (poziom maksymalny) czyta się jako ciemniejszy dolny pas i nic więcej. Listopad w Białymstoku to sól i błoto za kołami do wysokości klamek. docs/06 §2 „sterylna czystość” — nadal czerwona flaga, ale mniejsza niż fałszywa pleśń. Autor to uczciwie przyznaje.
3. **Tablice: realna poprawa powtarzalności.** `r10_rear_04`: przed „BI 9040U”, po „BMN 655YR” (powiat moniecki, poprawny format, pasek UE). Atlas 27 pól — w rzędach aut z 20 m klony wciąż do wypatrzenia; ograniczenie, nie blokada.
4. **Pearl bez fioletu utrzymany** (`r10b_grey_05`: ciemny sedan obok — przed granatowy połysk, po neutralny grafit). Felgi nadal płaskie wycinanki (`g_current_black_wheel_02`: białe ramiona bez fazy i głębi, opona bez boku), czerń w słońcu szara — bez zmian względem main.
5. **Tył auta nadal bez brudu** (`r10_rear_04`: klapa i zderzak czarnego hatchbacka gładkie) — najbrudniejsza zimą ściana auta; reszta P0-1 z 0089.
6. Budżet: 368 rekordów, max Δ draws/instancji = 0, Δ tris 0 %; 59/59 kontroli trasy w limicie. Moja różnica pikselowa Low-clear: 63/92 kamer identycznych, reszta to kadry aut (max poza nimi 0,59 w `r10_hall_4`, auta w tle). Trasa nietknięta.

Następna runda (life r2):
- Brud widoczny z 5 m w overcast: tył (klapa, zderzak) i wachlarz za kołami jako najmocniejsze strefy; kolor beż-szary; kalibracja na zdjęciu w podobnym świetle (nie lato vs listopad).
- Felga: faza ramion + ciemne wnętrze w albedo/AO; bok opony z fakturą (bez marek).
- Czerń w słońcu: stosunek drzwi/asfalt ~0,4–0,7 jak w referencji Mapillary.
- Kamera `sheet_far` floty z 20–45 m (P2-1 z 0089) do oceny klonów tablic i kolorów.

## 2. vegetation r1 (trawa, suchość, berberys) — SCAL · PARTIAL

1. **Trawa lepsza, a co najmniej nie gorsza.** `before|after/Low-clear/r10_shed_1.png`: przed — nasycony zielony dywan z regularnymi pręgami, po — bardziej oliwkowa, przesuszona, z większymi łatami; bliżej poboczy ze zdjęć Mapillary (`photo-pairs/Low-clear-photo-2048x1536-sbs-g3-b-209622370971977.jpg`, żółto-zielone pobocze). Odchylenie bloków 32 px rośnie we wszystkich 4 warunkach (np. Low-overcast 3,61→5,17) — liczby zgodne z tym, co widać.
2. **Ryzyko sezonowe:** mediana jasności trawy +18–19 sRGB. Pasuje do letnich zdjęć; przy przyszłym wariancie listopadowym trzeba to przestroić parametrem, nie kolejną warstwą. Notatka, nie blokada.
3. **Berberys:** `contacts/focus-Low-clear-g3a-rondo-bie-approach.jpg` — przebicia rdzenia zniknęły, ale żywopłot to dalej **bordowe bale/cegły** z twardym bokiem (lewa krawędź kadru i pas za przejściem). Z daleka czyta się jak rzeźba, nie krzew. Bez pogorszenia, bez poprawy wyglądu.
4. **D51:** zdjęcie g3-b-209622370971977 vs render — wiadukt, ekran akustyczny i latarnie układem się zgadzają; brakuje rytmu młodych drzew wzdłuż muru oporowego (płaski pas trawy). To otwarty backlog nasadzeń Putry, nie regresja tej rundy.
5. Różnica pikselowa: tylko 4/67 kamer identycznych, bo trawa jest prawie w każdym kadrze. Przejrzane największe (`r10_shed_1`, `trailer-side`, `cab-mirrors-left`, `fire-station-*`): wyłącznie kolor trawy; żadnej zmiany geometrii, budynków, znaków ani dróg. Budżet: 0 draws / 0 % tris w 322 porównaniach; żywopłoty 18 402 tris przed i po.

Następna runda (vegetation r2):
- Berberys: rozbity obrys (kępy, alpha-cut liści), zmienna wysokość, przerwy, przejście do gruntu — porównanie z bliskim zdjęciem.
- Nasadzenia wzdłuż Putry (rytm drzew z g3-b-*), sosny (płaskie piętra) i tuje (wrzeciona).
- Trawa: pas przy krawężniku (niekoszony, piasek/sól), koszenie powiązane z użytkowaniem miejsca.
- Suchość jako parametr sezonowy.

## 3. cab r1 (lusterka) — SCAL · PASS funkcji / PARTIAL wyglądu

1. **Realny błąd naprawiony, widoczny gołym okiem.** `native-K1-before-after-960.jpg`: Kerb i Front przed — w lusterku **wnętrze kabiny od góry z fotelami** (kamera RT w środku kabiny), po — dach/drzwi z zewnątrz i kostka placu. Błąd, który kierowca zauważa w sekundę. Piksele wnętrza Kerb 3366→0, Front 5364→0 we wszystkich 4 warunkach; draws kamer RT spadają (Kerb 83→77, Front 120→100).
2. **Podpory** (`left-K2-before-after-960.jpg`): końce ramion cofnięte za szkło — przed ramię „wchodzi” w odbicie, po nie. Subtelne, ale poprawne.
3. **Ramka szkieł** (`bezel-inspection-right-960.jpg`): zaokrąglony brzeg — obudowa przestaje wyglądać jak wycięty prostokąt. Prawy wide-angle nadal częściowo zasłonięty ciemnym kanałem drzwi (P1, ujawnione).
4. **Front po** (`native-K1`, prawy dolny): kremowa plama w lewej górnej ćwiartce to przód kabiny — poprawne geometrycznie, ale bez żadnego detalu (zero spoin, lamp, osłony), a obok wisi ciemny uchwyt lusterka kerb, który wygląda na oderwany od bryły. To jedyny punkt odniesienia kierowcy przy krawężniku — P1.
5. Niska rozdzielczość RT Kerb/Front (schodki na krawędzi dachu i linii) — bez zmian względem main.
6. Trasa: 70/78 kamer identycznych, pozostałe 8 to kadry kabiny/ciężarówki (max średnie |Δ| 1,53 w `cab-mirrors-left`). `comparison-0112-p2.json`: result PASS, max Δ tris +1000 zaokr. (`truck-34r`), draws 0.

Następna runda (cab r2):
- Przód kabiny w lusterku przednim: spoiny, osłona, lampy obrysowe — detal w albedo/normal, bez nowych draws.
- Prawy wide-angle: usunąć okluzję kanału drzwi.
- Smuga deski i skóra CC0 wg `R2-PLAN.md` — najpierw obraz z telefonu, potem tekstury.
- Pomiar A16 (RT lusterek to największy pojedynczy koszt kabiny na Low).

## 4. edge r1 (kontynuacje jezdni, apron) — SCAL warunkowo · PARTIAL, wizualnie neutralne

1. **Zmiana w obrazie praktycznie zerowa.** Różnica pikselowa Low-clear: 89/89 kamer ze średnim |Δ| < 0,05, max `edge-south` 0,03 (0,1 % pikseli). Mapa różnic `edge-south` High-clear po auto-level jest czarna. Pary `pairs/*-edge-east|south|pietrasze-driver.jpg` są nierozróżnialne.
2. **Co naprawiono — geometria, nie obraz.** Kontynuacje były zakopane do −8,8 m pod apronem (min. prześwit −8,80 → +0,04 m). Dowód: `preview/mask-final-edge-south.jpg` — magentowe paski asfaltu za barierą, kilka pikseli wysokości z poziomu drogi. Poprawne i potrzebne pod wyższe kamery, z kabiny niewidoczne.
3. **Najgorsza rzecz tych kadrów zostaje: biało-czerwone bariery na końcu świata.** `Low-clear-edge-pietrasze-driver`: dwujezdniowa DK8 kończy się barierą w lesie; `edge-east`/`edge-south`: 3–4 pasy kończą się barierą kilkaset metrów dalej. Czyta się natychmiast jako „koniec mapy gry”. Nie regresja tej rundy, ale P1 dla D51 (horyzont drogi wylotowej to element rozpoznawalności).
4. **Budżet:** draws 0 we wszystkich 356 parach; tris +792 (apron 10 176 → 10 968), w zaokrągleniu +1k w 69/89 kamer Low — stały koszt bez widocznej korzyści. Akceptowalne tylko w tolerancji ≤ +2 %; to najsłabiej uzasadniony przyrost z czterech rund. Warunek scalenia: lider akceptuje tolerancję; inaczej skompensować (np. decymacja apronu poza osią kontynuacji).
5. UV1 = (−1, 5) usuwa zabrudzenie brzegu na całej szerokości kontynuacji — dobry kontrakt, bez skutków ubocznych w kadrach.
6. Pary zdjęcie|render (136) mają pozy WORKING_VALUE i są wyraźnie przesunięte (np. `pairs/photo-High-clear-sbs-g3-b-150280503737744.jpg`) — nie są dowodem tej rundy. Widać w nich za to stan tła: rzadka, niska zabudowa, brak wysokich budynków i pylonów na horyzoncie.

Następna runda (edge r2):
- Wysokości LoD1 sylwetki miasta (parser 0 → prototyp 36 971 wysokości) — realna zmiana obrazu tła, priorytet.
- Zakończenia jezdni: zamiast widocznej bariery jezdnia ciągnąca się w far-field i znikająca w tle; sprawdzić z `edge-pietrasze-driver`.
- Las w osi DK8: potwierdzić z danych (BDOT10k).
- Pomiar A16 kosztu apronu.

---

## Oceny 1–10 (stan po rundzie; w nawiasie zmiana vs main)

| Kategoria | life | vegetation | cab | edge |
|---|---|---|---|---|
| Skala i proporcje | 5 (0) | 6 (0) | 6 (0) | 5 (0) |
| Światło i ekspozycja | 5 (0) | 6 (0) | 6 (0) | 5 (0) |
| Materiały | 5 (+1) | 5 (+1) | 5 (0) | 5 (0) |
| Zużycie i osadzenie | 4 (+1) | 5 (0) | 5 (0) | 4 (0) |
| Powtarzalność | 5 (+1) | 4 (0) | — | 4 (0) |
| Realia PL | 6 (+1, tablice) | 5 (0) | — | 4 (0, bariery końca świata) |
| Czytelność | 5 (+1) | 6 (0) | 7 (+3, lusterka) | 5 (0) |
| Artefakty | 6 (+1) | 7 (+1, berberys) | 7 (+3, wnętrze w RT) | 6 (0) |
| Budżet Low | 9 | 9 | 8 | 7 |

Wniosek: cztery gałęzie bez regresji na trasie, wszystkie do scalenia (edge z warunkiem budżetowym). Żadna poza cab nie zmienia obrazu widzianego z kabiny w sposób, który kierowca zauważy. Całość nadal czyta się jako czysty edytorowy render ze słonecznego dnia, nie zdjęcie z Białegostoku — to zadanie kolejnych rund, nie powód do blokady scalenia.
