# Zlecenie dla Codex (GPT, lokalnie na tym samym komputerze), s21, 15.11 wieczór — praca długa (~12 h)

Wklej:
```
Pracujesz w repo C:\Users\matma\Documents\Claude\kamion (Kamion: mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1; repo GitHub woogitsugames/kamion). Komunikacja po polsku. Na tej samej maszynie pracuje lider Claude (jedyny integrator main) i do 5 jego agentów w .claude/worktrees/*. Ty NIE scalasz do main i NIE pushujesz na main.

NAJPIERW przeczytaj: CLAUDE.md, docs/owner/AGENT-RULES.md, docs/owner/S20-AGENT-PREAMBLE.md, HANDOVER.md (blok „SESJA 20/21”, najnowsze wpisy na dole), docs/11_DECYZJE_WLASCICIELA.md (D63–D66), docs/06 (anti-slop), docs/owner/OWNER-PHOTOS-KNYSZYN.md, research/dk65-knyszyn-refs/README.md (K1), ADR 0203, 0209, 0212, 0216, 0218.

IZOLACJA (twarde zasady, bo dzielisz komputer):
- Utwórz własny worktree: `git worktree add .claude/worktrees/knyszyn-rynek-0227 -b knyszyn-rynek-0227 origin/main`. Pracuj TYLKO tam. Nie wchodź do innych worktree, nie zmieniaj plików w katalogu głównym repo.
- Jeden proces Unity na katalog projektu: Unity uruchamiaj tylko dla game/ w SWOIM worktree, batchmode, po jednym naraz.
- NIE używaj adb ani telefonów (Unity/adb zabija daemon liderowi). Nie ruszaj ProjectSettings/, Packages/, asmdef ani wspólnych scen.
- Przed każdym dużym krokiem sprawdź wolne miejsce na C: (`Get-PSDrive C`); poniżej 60 GB zatrzymaj się i zapisz to w STATUS.
- Dane Data/raw: jeśli w worktree ich brak, zrób junction do głównego Data/raw (jak w AGENT-RULES), a przed usunięciem worktree je odłącz.

ZADANIE (D65 z kolejki lidera): szlif Knyszyna według zdjęć właściciela, przede wszystkim Rynek (fontanna, kamienice pierzei, nawierzchnie, zieleń, oznakowanie, mała architektura), potem główna ulica przelotowa DK65 przez miasto. Zdjęcia: research/_incoming/owner-knyszyn-photos-2026-11-14/ i owner-dk65-photos-2026-11-14/. Służą WYŁĄCZNIE jako referencja: nie commituj ich, nie używaj jako tekstur. Geometria i położenie z danych (OSM/BDOT10k/ortofoto GUGiK w repo), wygląd i proporcje według zdjęć. Bez Google Maps, Street View, Earth i 3D Tiles, bez marek i logo (szyldy sklepów generyczne).
Kolejność:
1. Na początku `git merge origin/summer-led-0216`, jeśli ta gałąź nie jest jeszcze w main (latarnie LED Knyszyna, ADR 0216), żeby nie powstały konflikty. Raz na ok. 2 h `git fetch` i `git merge origin/main`: generated knyszyn* bierz z main, potem przebuduj; overrides = suma.
2. Audyt: baseline visual-qa regionu knyszyn (Low i High, clear i dusk) → artifacts/knyszyn-rynek-0227/before/; tabela „zdjęcie → co widać → co jest w grze → różnica”.
3. Poprawki jako kod i dane w tools/worldgen (generatory, overrides.yaml regionu knyszyn, authored_overrides), nie ręczne klikanie w Unity. Każda kamienica i obiekt Rynku z typologii (wysokości, dachy, rytm okien, kolory) z oznaczeniem SOURCED / ESTIMATED / WORKING_VALUE.
4. Pętla: build_world knyszyn → import (`pwsh scripts/import-region.ps1 -Region knyszyn`) → visual-qa → obejrzyj PNG obok zdjęcia → popraw. Rób co najmniej 3 iteracje. Dodaj kamery kontrolne Rynku (te same kadry co zdjęcia, mniej więcej).
5. Budżet: nie przekraczaj limitów z testów (High ≤ 2 mln tris na kamerę, Low bez pogorszenia wobec before; draw calls podaj przed/po). pytest tests/gis zielony, EditMode (`pwsh scripts/test.ps1 -Platform EditMode`) zielony.
6. ADR 0227 (docs/adr/0227-knyszyn-rynek.md), wpisy w docs/LICENSES.md, jeśli dochodzą zasoby.

ZAPIS POSTĘPU (lider sprawdza co godzinę o :17): po każdym kroku commit WIP na gałęzi knyszyn-rynek-0227 + push gałęzi; dopisuj artifacts/live/knyszyn-rynek-0227.md w GŁÓWNYM katalogu repo (to jedyny plik, który wolno ci tam zapisać): godzina (czas Brukseli), co zrobione, NASTĘPNY KROK jako komenda. Nie zmyślaj liczb.
KONIEC: PR (nie draft) knyszyn-rynek-0227 → main z raportem do 20 linii po polsku (co zmienione, rendery przed/po i ścieżki, budżet przed/po, testy, co otwarte, „Gotowe do scalenia po weryfikacji lidera: TAK/NIE”). Jeśli skończysz wcześniej niż w 12 h: kolejna iteracja jakości Rynku, potem pozostałe ulice Knyszyna z zdjęć. NIE scalaj.
```
