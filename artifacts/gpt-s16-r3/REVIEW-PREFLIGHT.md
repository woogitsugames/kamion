# ADR 0155 — niezależny preflight diagnostyki

**Wynik: PARTIAL / diagnoza otwarta.** Nie ma jeszcze pasujących renderów baseline ani dowodu przyczyny plam na głównej wyspie. Nie akceptuję na tym etapie zmiany produkcyjnego renderu. Poniższe uwagi dotyczą jakości rozumowania i granic narzędzi diagnostycznych, nie potwierdzonej usterki cieniowania.

Przeczytano ADR 0155, PutryShadowProbe.cs, trace_island.py, STATUS.md oraz owning sources dla RenderOverrides, zastosowania profilu, WorldSurface ShadowCaster i KamionFarShadow. Obejrzano reference-sheet.jpg. Bez Unity, adb, generatorów, testów i zmian kodu.

## Co wynika z fotografii

Oba zdjęcia richlv pokazują rzeczywisty pomost, podpory oraz obszerny cień na żwirowej wyspie. Zarazem bliski żwir i część skraju wyspy są wyraźnie jasne mimo położenia pod obrysem wiaduktu na obrazie. Nie można więc przyjąć reguły „cały żwir pod wiaduktem powinien być ciemny”. Perspektywa, otwarte boki pomostu i kierunek słońca decydują o miejscu granicy. Pozy klasy B i niekalibrowane światło nie pozwalają wskazać każdego poprawnego piksela ani docelowego poziomu albedo.

## Konkretne granice i potencjalne błędy diagnozy

1. **Promienie dotyczą innego fragmentu.** trace_island.py bada mały północny nos E534–540 / N−700…−690 w dwóch chunkach; wyklucza hero. Korekta została jawnie zapisana. Wynik nie dowodzi osłonięcia głównej wyspy E558 / N−734. Przeniesienie wniosku „większość próbek blocked” na główną wyspę byłoby błędem. Nie ma potrzeby powtarzać tego małego testu przed natywnym baseline.
2. **Blocked w ray teście nie oznacza udziału w shadow mapie.** Test przecina trójkąty GLB bez wybranego runtime LOD, shadow mask, wyłączeń materiału, zasięgu kaskad, rastryzacji i bias. Klasyfikacja front/back używa średnich zapisanych normalnych, a nie faktycznego stanu rasteryzera i orientacji trójkąta po pełnym imporcie. To użyteczny sygnał geometryczny, nie symulacja Unity Cull Back. Ograniczenie 30 m i odbiornik +0,05 m są dodatkowymi warunkami testu.
3. **HeroLods w probe nie dowodzi aktywnego castera nad wyspą.** Odczytywane są prototypy pasujące do prefixu, ich lokalne mesh.bounds i maski. Nie ma macierzy konkretnej instancji, jej world bounds, faktycznie wybranego LOD dla kamery ani potwierdzenia zgłoszenia do shadow pass. Lista materiałów oznacza noShadowMaterials, lecz nie przedstawia stanu wszystkich shaderów/passów i ewentualnych dodatkowych wyłączeń. Nie wolno z samego wpisu On wnioskować, że dana płyta rzeczywiście osłania wyspę w konkretnym renderze.
4. **Raport profilu nie jest odczytem efektywnego renderu.** Probe otwiera sceny Low/High i wypisuje pola profilu oraz Sun, ale nie ustawia środowiska, jakości i aktywnego URP jak runner VQA. Nie odczytuje też efektywnego przełącznika używania ustawień pipeline przez światło. Ostatecznym dowodem działania rq_shadowbias/rq_shadownormal ma być log `[RQ_PIPELINE]` z właściwego renderu i rzeczywiste ustawienie światła, nie sam diagnostic-report.json.
5. **rq_shadow=0 nie oznacza „wszystkie cienie wyłączone”.** W funkcji KamionFarShadow w KamionWorldGI.hlsl brak realtime shadow keyword daje fade=1, a wynik nadal uwzględnia bakedSun. Taka ablacja przełącza analizę w stronę cienia wypieczonego; nie izoluje całkowitego braku occluderów. Jeśli plamy zostaną, nie dowodzi to błędu albedo. Jeśli znikną, również trzeba rozdzielić realtime od wypieku, zamiast od razu poprawiać geometrię.
6. **TwoSided jest węższym testem, a restore ma założenie.** Probe zmienia tylko MeshRenderer nazwany bridge w określonym zakresie, nie hero instancje. Brak reakcji nie wyklucza problemu cullingu hero. Tryb restore ustawia On, nie odtwarza zapisanej wartości każdego renderera; jest prawidłowy wyłącznie po potwierdzeniu, że wszystkie zmienione renderery miały On w baseline. W przeciwnym razie trzeba wrócić do zachowanego stanu/importu. Nie przyjmować TwoSided jako naprawy przed wykazaniem, że odpowiednia powierzchnia trafia do badanego castera.

## Najkrótsza sensowna kolejność kolejnych testów

1. **Baseline jednej bliskiej kamery głównej wyspy, High-clear i Low-clear.** Stała kamera, słońce i ekspozycja. Oznaczyć na obrazie dokładne plamy oraz granicę cienia. Potwierdzić rzeczywiste occludery nad tym obszarem, world transform i wybrany LOD hero, a także aktualny zasięg realtime shadows. Nie zaczynać od zmiany wszystkich kontrolnych kamer naraz.
2. **Jeden render z rq_shadowbias=0 i rq_shadownormal=0.** Pozostałe ustawienia i odległość bez zmian. To krótki test, czy bias uczestniczy w zjawisku, nie proponowana wartość produkcyjna. Jeżeli efekt jest wyraźny, dopiero wtedy rozdzielić dwa rendery: sam depth bias 0 i sam normal bias 0. Przy braku efektu nie stroić tych dwóch parametrów na ślepo.
3. **Rozdzielić realtime i wypiek zmianą rq_shadow.** Dla tej samej kamery porównać 0 oraz odległość wystarczającą do objęcia całej wyspy realtime, z tym samym bias. rq_shadow=0 opisać jako far/baked branch. Duża odległość jest ablacją diagnostyczną, nie akceptacją kosztu Low. Zmiana plam wraz z odległością wskazuje na przejście realtime/baked lub zasięg, a nie automatycznie brak płyty.
4. **Dopiero zależnie od wyniku:** przy problemie pozostającym wewnątrz realtime i poprawnie zgłoszonym chunk bridge wykonać TwoSided tego castera. Przy problemie związanym z far branch obejrzeć próbki G/B oraz wysokość odbiornika z rzeczywistego GI map dla głównej wyspy i porównać z geometrią używaną do bake. Przy problemie wyłącznie hero badać jego faktyczny shadow pass/LOD zamiast powtarzać chunk TwoSided.

Overcast jest kontrolą ogólnego materiału/ambientu, lecz słabszy kontrast słońca może ukryć błąd bez jego usunięcia. Nie akceptować poprawki tylko dlatego, że plamy są mniej widoczne w overcast. Nie zmieniać albedo żwiru, nie zamykać szczeliny i nie dodawać zasłony bez dowodu geometrycznego.

## Warunek dalszej oceny

Czekam na natywne baseline i pasujące ablacje. Przed obrazami nie wydaję PASS wizualnego ani werdyktu o przyczynie. Każda późniejsza akceptacja powinna rozdzielić naprawę plam w tych kadrach od zgodności fotograficznej pozy B, od innych kamer/G3 oraz od urządzenia i przejazdu w ruchu.

