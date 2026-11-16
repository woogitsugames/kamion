# Test wrażeń z jazdy — bramka 2 na PC (D77) — instrukcja dla właściciela

Cel: ocenić, jak zestaw 40 t **czuje się w rękach** przy ruszaniu pod górę, hamowaniu, na rondzie i przy cofaniu pod rampę.
Testujesz na najnowszym exe PC, padem i/lub klawiaturą (D77). Kierownica z FFB będzie później i nie blokuje bramki 2.
Uwagi z testu idą do strojenia napędu i AMT (ADR 0201b), przegubu naczepy (ADR 0228) i wejścia pad/klawiatura (ADR 0264).
Czas: ok. 30–40 min. Klawisze i przyciski znajdziesz w **`docs/owner/JAK-GRAC-PC.md` §2**; tu są tylko te najważniejsze.
Poprzednia wersja tej instrukcji (dla telefonu) jest w historii gita.

## 1. Przed startem
1. Folder gry od lidera: `artifacts/win/kamion-<wersja>-<sha>-regions/` albo rozpakowany zip (JAK-GRAC-PC §1.1–1.2).
2. Start na placu testowym z zestawem 40 t, w oknie:
   `Kamion-okno.cmd -scene DrivingLab -trailer 40`
   (`-trailer 40` = 40 t całego zestawu. Bez argumentu plac startuje z ładunkiem 24 t, D53. JAK-GRAC-PC §1.3).
3. Tier i limit klatek: zostaw „auto” i 60 fps. Jeśli obraz się tnie, użyj `-tier Medium` albo `-tier Low -fps 30` (JAK-GRAC-PC §3–4).
4. Ustawienia sterowania zostaw domyślne. Jeśli coś przeszkadza, zmień **jedną rzecz naraz** i zapisz co (formularz, pkt 6).
5. Zapisz **godzinę startu** — lider znajdzie po niej Twoją sesję w logu.

Najważniejsze sterowanie (pełna tabela: JAK-GRAC-PC §2.1–2.3):

| Akcja | Klawiatura | Pad |
|---|---|---|
| Gaz / hamulec | W / S | prawy / lewy spust |
| Kierownica | A / D | lewa gałka |
| Hamulec postojowy (przełącz) | Spacja | A (dolny) |
| D / N / R | 1 / 2 / 3 | X / B / Back |
| Retarder mocniej / słabiej | X / Z | krzyżak w dół / klik lewej gałki |
| Kamera (kabina → pościg → orbita) | C lub Tab | Y |
| Kamera cofania (wymuś; sama włącza się na R) | V | — |
| Lusterka w okienkach | L | — |
| Menu / wstecz | Esc | Start |

## 2. Gdzie co jest na placu (DrivingLab)
Plac ma 400 × 400 m. Startujesz na jego południowym skraju, przy tablicy „START — przyspieszanie / hamowanie”; pas przyspieszania ze znacznikami co 10 m biegnie przed Tobą na północ.

| Miejsce | Gdzie względem startu | Do której próby |
|---|---|---|
| Rampy **6 % i 12 %** (z wypłaszczeniem na górze) | ok. 40–60 m w prawo i ok. 30 m do przodu | próba 1 (krótko) |
| Droga pod górę **7 %, 600 m**, z placem do zawracania | wjazd ok. 200 m w prawo i ok. 300 m do przodu (za wschodnią krawędzią placu) | próba 1 (główna) |
| Okrąg **R = 50 m** (tablica „OKRĄG R = 50 m”) | ok. 110 m w lewo i ok. 85 m do przodu | próba 3 |
| **Rampa załadunkowa** — 5 stanowisk, odboje, wysokość 1,20 m, linie naprowadzające | północny skraj placu, ok. 100–116 m w prawo i ok. 360 m do przodu | próba 4 |
| Mokra płyta z okręgiem R = 100 m | ok. 200–460 m w prawo, obok startu | opcjonalnie (hamowanie na mokrym) |

Odległości liczone z układu placu w kodzie (źródła na dole pliku). Na miejscu kieruj się tablicami i liniami.

**Prawdziwe ronda (opcjonalnie, po próbach na placu):** Rondo Putry w Białymstoku (region C: `Kamion-okno.cmd -scene c`, trasa G3-B)
i rondo w Knyszynie DK65 × Tykocka (`Kamion-knyszyn.cmd`). Ich promieni nie mierzyliśmy, więc nie są to „R50” w sensie przepisów.
To ocena wrażenia w prawdziwym ruchu ulicznym, nie pomiar.

## 3. Cztery próby
Każdą próbę zrób **2 razy**: raz klawiaturą, raz padem. Jeśli coś odbiega od oczekiwań, powtórz trzeci raz.

| # | Próba | Jak | Na co patrzeć |
|---|---|---|---|
| 1 | **Ruszanie pod górę z 40 t** | Wjedź na drogę 7 % i zatrzymaj się w połowie. Włącz hamulec postojowy (Spacja / A), potem go zwolnij i ruszaj samym gazem. Powtórz na rampie 12 %. | Czy zestaw cofa się przy zwalnianiu postojowego i jak daleko. Czy AMT wybiera sensowny bieg (bez wahania między biegami). Czy da się ruszyć płynnie, czy szarpie. Ile trwa, zanim zestaw nabierze prędkości |
| 2 | **Hamowanie** | Na pasie przyspieszania (znaczniki co 10 m) rozpędź się do 50, a potem do 80 km/h. Hamuj (a) pełnym hamulcem, (b) dozując, (c) z samym retarderem (X). | Czy droga zatrzymania wygląda na 40 t: z 80 km/h ok. 40 m przy pełnym hamowaniu — wynik symulatora, nie pomiar w grze (`PHYSICS-VALIDATION-2026-11-16.md`). Czy przód nurkuje. Czy naczepa pcha albo ucieka na bok. Czy przy samym zatrzymaniu jest szarpnięcie lub odbicie — walidacja widziała krótkie odbicie 0–2 km/h |
| 3 | **Rondo / okrąg R = 50 m** | Jedź po okręgu R50 ze stałą prędkością 20, potem 30 km/h, w obie strony. Na koniec szybka zmiana kierunku (ósemka obok R25). | Czy da się trzymać linię gałką/klawiszami bez „piłowania”. Czy naczepa ścina do środka (to normalne). Czy przy 30 km/h zestaw jest stabilny. Czy kierownica wraca do środka z dobrą siłą |
| 4 | **Cofanie pod rampę** | Ustaw się ok. 30 m przed rampą załadunkową na osi stanowiska. Wrzuć R (3 / Back) i cofnij naczepą do odbojów. Użyj kamery cofania (włącza się sama) i lusterek (L). | Czy naczepa skręca w przewidywalną stronę. Czy da się korygować małymi ruchami. Czy kamera i lusterka wystarczą. Czy dojazd do odboju jest miękki (bez odbicia albo „wbicia”) |

Przycisk „Reset” w HUD (mysz) stawia zestaw z powrotem na starcie. Esc / Start otwiera menu bez restartu gry.

## 4. Skala ocen (1–5)

| Ocena | Znaczy |
|---|---|
| 5 | jak prawdziwa ciężarówka, nic nie zmieniać |
| 4 | dobre, drobne uwagi |
| 3 | da się jeździć, ale coś wyraźnie przeszkadza |
| 2 | źle, trzeba poprawić przed dalszą pracą |
| 1 | nie da się wykonać próby |

## 5. Co dołączyć
1. Zip logów z `Zbierz-logi.cmd` (z folderu gry), uruchomiony **zaraz po** teście, przed kolejnym startem gry (JAK-GRAC-PC §5).
   W `Player.log` są linie `[CONTROLS]` z Twoimi ustawieniami i wyborami w menu.
2. Opcjonalnie dane jazdy: uruchom grę z `-telemetry 1`
   (`Kamion-okno.cmd -scene DrivingLab -trailer 40 -telemetry 1`). Pliki CSV zapiszą się w `telemetry\`, w tym samym folderze co `Player.log`.
3. Zrzuty ekranu (Win + Shift + S) albo krótkie nagranie miejsc, które Ci nie pasują.
4. Wypełniony formularz niżej — skopiuj ten plik albo wklej sam formularz w wiadomości do lidera.

## 6. Formularz (do wypełnienia)

```
Data i godzina startu / końca: ____ / ____
Wersja gry (nazwa folderu albo zipa): ____
Tier / FPS / okno czy pełny ekran: ____
Pad (jaki) / klawiatura: ____
Zmienione ustawienia (jedna rzecz naraz): ____

Próba 1 — ruszanie pod górę 40 t     klawiatura: _/5   pad: _/5
  cofanie się przy postojowym: tak / nie (ile ok.: __ m)   wahanie biegów: tak / nie
  uwagi: ____
Próba 2 — hamowanie                  klawiatura: _/5   pad: _/5
  szarpnięcie/odbicie przy zatrzymaniu: tak / nie   naczepa pcha: tak / nie
  uwagi: ____
Próba 3 — okrąg R50 / rondo          klawiatura: _/5   pad: _/5
  piłowanie kierownicą: tak / nie   stabilnie przy 30 km/h: tak / nie
  uwagi: ____
Próba 4 — cofanie pod rampę          klawiatura: _/5   pad: _/5
  kamera cofania wystarcza: tak / nie   dojazd do odboju miękki: tak / nie
  uwagi: ____

3 największe problemy (własnymi słowami):
1. ____
2. ____
3. ____
Czy bramka 2 może przejść: tak / nie / tak, po poprawkach: ____
```

<!-- źródła (origin/main 2b0b01e52):
D77: docs/11_DECYZJE_WLASCICIELA.md:136-137
plac 400×400 m, start (0,-180), pas do z=190: game/Assets/_Project/Gameplay/DrivingLabLayout.cs:12-17
okrąg R50 środek (-110,-95): game/Assets/_Project/Gameplay/DrivingLabLayout.cs:20-21; tablica „OKRĄG R = 50 m”: game/Assets/_Project/Editor/Setup/DrivingLabSceneBuilder.cs:127
R25 i ósemka: game/Assets/_Project/Gameplay/DrivingLabLayout.cs:22-26
rampy 6 %/12 % x=40/58, start z=-150, wys. 1,5 m: game/Assets/_Project/Gameplay/DrivingLabLayout.cs:29-30; game/Assets/_Project/Editor/Setup/DrivingLabSceneBuilder.cs:134-135
rampa załadunkowa z=184, wys. 1,20 m, x od 100, 5 stanowisk co 4 m, linie 34 m: game/Assets/_Project/Gameplay/DrivingLabLayout.cs:50-52
droga 7 %, 600 m, z=130, od x=200, plac 120 m: game/Assets/_Project/Gameplay/DrivingLabLayout.cs:56
mokra płyta x 200-460, z -230..-10, R100: game/Assets/_Project/Gameplay/DrivingLabLayout.cs:60-62
osie X=wschód, Z=północ: CLAUDE.md (reguły techniczne)
-trailer 40 = Gross40t, 24 = Cargo24t; domyślnie Cargo24t: game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:38, :289-292
-telemetry 1: game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:251; katalog telemetry: game/Assets/_Project/Vehicle/Runtime/VehicleTelemetryRecorder.cs:27
[CONTROLS] w logu: game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:245, game/Assets/_Project/Gameplay/GameBootstrap.cs:161
hamowanie 80→0 40 t 41,31 m, odbicie 0–2 km/h: docs/reports/PHYSICS-VALIDATION-2026-11-16.md
tablica START i znaczniki co 10 m: game/Assets/_Project/Editor/Setup/DrivingLabSceneBuilder.cs:113-120
przycisk Reset w HUD: game/Assets/_Project/UI/Driving/DrivingHud.cs:462
klawisze/pad: docs/owner/JAK-GRAC-PC.md §2.1–2.4 (tam źródła plik:linia)
-->
