# E r8 preflight — ADR 0116 (read-only, 2026-11-11)

To jest przekazanie do późniejszej kolejki, nie rozpoczęcie r8. Nie zmieniono źródeł, nie uruchomiono Unity i nie utworzono worktree. Najpierw kończy D, następnie 0108 → 0109. Przyszła gałąź `gpt-firestation-r8` musi powstać z aktualnego main po tych integracjach; nie kontynuować produkcji z bazy r7 `901c427f`.

## Baza i materiały wejściowe

- Przeczytano aktualne `docs/owner/GPT-FEEDBACK-S10.md` oraz całą `docs/reports/visual/REVIEW-2026-11-11-s10-gpt-0087-0090.md`, szczególnie §2 remizy. Recenzja dotyczy historycznej gałęzi sprzed integracji, a nie obecnego main.
- Main podczas odczytu przeszedł z `1b2f2618` do `db787c8a` (ostatnia zmiana tylko HANDOVER). R7 jest już scalone w `b0685f51`, TRAKT w `1d695be1`; main ma także 0106 i jego diagnostykę. Nie przenosić ponownie starych konfliktujących plików generated ani całego `WorldInstances.cs` z E r7. Komunikat commita main podaje GIS 476/0; nie wykonywano tu nowego testu.
- Fizyczna referencja pozostaje rzeczywistym zdjęciem 7197, z jego udokumentowanym pochodzeniem. Źródło igieł `fir_tree_01` to przypięte CC0 fir/conifer, nie zweryfikowane Picea. Pakiet odtworzenia źródła z r7 nadal jest potrzebny.

## Rzeczywiste problemy i kolejność dowodzenia

1. **P1 — blade karty świerków.** Recenzja widzi żółtozielone, pozornie półprzezroczyste karty oraz wąskie kolumny, szczególnie przy prawym narożniku, zamiast ciemnych, szerokich i gęstych drzew ze zdjęcia. To opis wyglądu, nie dowód włączonego blendingu. Najpierw oddzielić pigment, pokrycie alpha/mipów, normalne i oświetlenie od niedostatecznej masy rdzenia. Następnie ocenić szerszą podstawę i gęstsze, połączone piętra bez ponownego zasłonięcia obu łuków. Proporcja około 2:1 i igły około 10% ciemniejsze od tui są propozycjami recenzenta, a nie zmierzonymi wymiarami/albedo obiektu. Bez globalnej zmiany zieleni B.
2. **P1 — kierunek gradientu szkła.** Zewnętrzny pomiar recenzenta: render góra około 72, dół 79–83; zdjęcie góra 62–67, dół 46–53. Sama średnia tafli w r7 mieściła się w paśmie overcast, ale nie dowodziła poprawnego gradientu. Clear według recenzji osiąga 94–104. Mierzyć górę i dół tych samych czystych tafli, osobno od szprosów, ram i roślin, w każdym tierze i świetle. Odróżnić cel właściciela 60–75 od nowej sugestii recenzenta 55–65; nie zmieniać po cichu kryterium. Źródło `sets_fire_station.py:386–387` ma słaby gradient 0.90→0.96, lecz większą wariację między taflami 0.85→1.15 i dodatkowy szum. To może przykrywać kierunek; nie zakładać bez próby, że wystarczy odwrócić UV lub jeszcze raz obniżyć cały skalar. Zachować D48 i nie dodawać unlit ani nowego slotu Low jako obejścia.
3. **P1 — fizyczne źródła zacieków.** Pod obróbką i parapetami brakuje czytelnego spływu; plama przy maszcie wygląda na oderwaną od źródła. W źródle r7 `g_top = P["h"] - pv` odnosi spływ do góry pasma atlasu, a nie automatycznie do konkretnej obróbki budynku. Prześledzić mapowanie pasm i zlokalizować plamę przy maszcie przed zmianą intensywności. Każdy większy zaciek musi zaczynać się pod rzeczywistą krawędzią/okapnikiem/parapetem; rozbryzg wiązać z gruntem (recenzja: około 0.3–0.5 m), nie ze środkiem czystej ściany. Nie zastępować tego ogólnym szumem lub równym brudnym pasem.
4. **P1 — fasety tui na Low.** Aktualny `build_thuja` używa 8 boków w LOD0 i 4 w LOD1; tuje nie dostają specjalnych normalnych rdzenia świerków. To źródłowa przesłanka, nie nowy render. Najpierw sprawdzić wygładzenie normalnych i obrys, potem ewentualne segmenty w granicach budżetu. Utrzymać hero-local paletę i rzeczywiste Low/High, pamiętając, że bliska kamera Low może wybrać LOD0.
5. **P2 — rytm i głębokość tui.** R7 spełniło numeryczny limit odstępu (maksimum 19.50%), ale obraz nadal czyta się jako równy szereg. Ocenić różnice głębokości i grupowania, a nie tylko kolejny seed; proponowane 0–1.5 m to wartość robocza. Zachować realne prześwity łuków i kontekst ogrodzenia.
6. **P2 — tablica i tło.** Pusta biała tablica wymaga danych właściciela albo uzasadnionej decyzji o usunięciu; nie wymyślać tekstu. Czarne ostre karty drzew za halą zgłosić do 0109/B, nie naprawiać ich globalnie w E. Skrzydło/tynk, brązowy klinkier i odsłonięcie łuków są osiągnięciami zachowywanymi, nie zadaniami do ponownego rozliczenia jako nowe poprawki.

## Ultra — kontrola integracji lidera, nie nowe strojenie E

Feedback mówi, że lider rozszerzył hero leaf na Ultra. Odczyt main `db787c8a` potwierdza poprawkę tylko częściowo:

- `game/Assets/_Project/World/Runtime/WorldInstances.cs:132`: `ReadTier` wyznacza żądany stan dla `High || Ultra`.
- Ten sam plik, linia **169**: `BuildMaterials` zapisuje `m_HeroLeafHigh` nadal tylko dla `High`; linia **197** od tego pola uzależnia hero copy.
- `IsFoliage` (linie 161–163) nie obejmuje nazwy `M_fire_station_thuja_shell`. Aktualny wygenerowany materiał źródłowy ma URP Lit (GUID `933532a4fcc9baf4fa0491de14d08ed7`, zgodny z `Lit.shader.meta`). Przy Ultra i dostępnej ścieżce simple/template hero pozostaje więc URP Lit, bez kopii Vegetation i parametrów .25/0. Przejście High→Ultra także usuwa poprawną kopię. To **zły shader względem intencji**, nie tylko koszt cache.
- Na kolejnym `ReadTier` po zastosowaniu profilu porównanie nadal widzi true/false i przebudowuje materiały. Nie jest to automatycznie przebudowa co klatkę: `OnTierApplied` (240) unieważnia odczyt, a `OnBeginCamera` (293) wywołuje go tylko przy `!m_TierRead`.
- ROOT niezależnie potwierdził tę asymetrię. Obok jest **niezastosowany** `E-R8-ULTRA-INTEGRATION.patch`: jeden warunek w linii169, bez zmiany 0106 i bez zmian źródeł w tej rundzie. Prośba do lidera o integrację osobno. Przyszły test: Low→High→Ultra→Low przy niezmienionym simpleFoliage, właściwy shader i parametry, brak mutacji assetu oraz brak ponownej kopii na ponownym odczycie Ultra. To na razie dowód źródłowy, nie wykonany test/GPU.

## Warunki rozpoczęcia i akceptacji przyszłego r8

- Nowa, rzeczywiście aktualna baza po kolejce 0108/0109; świeży świat i **kanoniczny pojazd przed końcowym importem bazowej sceny**, następnie baseline. Zapisać world-pose wszystkich kamer i korzeni pojazdu/naczepy, obiektywy oraz hashe. Nie powtórzyć ograniczenia przyczynowości 17 kamer pojazdu z r7.
- Zachować D48 plaster-only x1.15, dach/opaski/biuro, istniejące makro i pogodę. Chronione piksele oznaczają texele atlasu, nie wszystkie piksele sceny. Nie przenosić starego generated na aktualny main.
- Najpierw mała próba rzeczywistych kamer ref7197/route na Low i High w clear/overcast, z osobnymi maskami góry/dołu szkła, łuków, igieł i tui; potem pełne porównanie i niezależna recenzja. Zrzuty r7 sprzed 0106 nie stanowią dowodu aktualnej ścieżki Low.
- Budżet Low bez wzrostu drawów i w granicach przydzielonych trójkątów; osobno jawny koszt dodatkowego High/Ultra pass. Oceniać alpha w rzeczywistych mipach i ruchu, nie tylko emisyjny podgląd źródła. GIS/EditMode po ostatnich produktach; telefon wyłącznie zgodnie z osobnym upoważnieniem i blokadami.
- ADR **0116** jest zarezerwowane dla r8. Nie utworzono go tutaj. Niniejszy dokument nie zmienia zamknięcia technicznego r7 ani jego jawnego appearance PARTIAL/FAIL.
