# Status sesji cab, runda 1
Przeczytano instrukcje startowe i recenzję JK. Worktree przeniesiony z historycznego gpt-cab-r1 do gpt-cab; poprzednia scalona gałąź zachowana jako gpt-cab-0104-archive. Nowa gpt-cab-r1 pochodzi z main 4c9905b1.
Skopiowano wymagane dane i _Generated; junctiony surowych źródeł służą wyłącznie do odczytu. git lfs checkout zakończony.
Następny krok: pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-cab; baseline Low i High, potem korekta kamer V/VI i ramion. Wszystkie liczby po zmianie pozostają UNVERIFIED.
Start pętli: 2026-11-11 21:31 Europe/Warsaw. Planowany koniec: 2026-11-12 21:31 Europe/Warsaw.
Historyczny raport ADR 0104 zachowano w history-0104; nowe dowody powstają w baseline i następnie result-0112. Nie traktować starego katalogu after jako dowodu nowej rundy.
Wykryto near clip V/VI 1,881/1,973 m, który może wycinać dach przed wirtualnym okiem; render bazowy w toku. Kopia venv z historycznego worktree ma nieaktualny interpreter, dlatego Python uruchamiany z UV_PROJECT_ENVIRONMENT=.venv-cab.
Następny krok: natywne RT baseline przez Game.Editor.VisualQA.CabMirrorAudit.Run, potem korekta near clip i cullingu.
Obejrzano baseline Low clear: cab-mirrors-left i cab-mirror-front. Wspornik rzeczywiście przechodzi przed dolnym szkłem. Odrębny pomiar źródłowej geometrii (2400 promieni/szkło) wykrył 73/2400 WideL i 131/2400 WideR zasłoniętych przez dolne ramiona. To udział całej powierzchni, nie dolnej połowy kadru z recenzji.
Próby przesunięcia mocowania przy głowicy za jej tylną płaszczyznę o 80/160/240 mm dały 0 trafień w ramiona dla wszystkich czterech szkieł. Są to wyłącznie promienie na geometrii źródłowej, wymagają potwierdzenia w eksporcie i renderze Unity.
Następny krok: audyt baseline natywnych RT (oczekuje na slot), potem wprowadzić bliższy near clip V/VI i ukrywanie wnętrza ze sprawdzeniem przywrócenia stanu rendererów.
Dodano do CabMirrorAudit diagnostyczne przejście identyfikujące piksele wnętrza przez chwilowy materiał magenta, z przywróceniem materiałów po pomiarze. Zwykły obraz RT jest zapisywany osobno. Nie zmieniono jeszcze zachowania runtime ani kamer: pomiar baseline pozostaje bazowy.
Następny krok: poczekać na zakończenie baseline-native-Low-clear.log, obejrzeć RT i interior-pixels.tsv, następnie poprawić runtime.
Sprostowano ADR 0104 i zapisano ADR 0112 ze stanem hipotez oraz rozróżnieniem dowodów historycznych i bieżących. Następny krok: baseline-native po zwolnieniu Unity.
