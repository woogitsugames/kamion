# Gemini 4 (Antigravity, lokalnie) — zadanie próbne 01 (s16, 2026-11-13)

Cel próby: sprawdzić jakość pracy na zadaniu z jasnym kryterium (liczby, testy mutacyjne), w Unity lokalnie, obok innych agentów. Skopiuj cały blok poniżej do Antigravity.

```
Pracujesz lokalnie w repo C:\Users\matma\Documents\Claude\kamion (Kamion: realistyczny mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, C#). Na tej maszynie równolegle pracują inni agenci (Claude, Codex) — liderem i jedynym integratorem main jest sesja Claude. Ty NIE scalasz do main, NIE pushujesz main, NIE ruszasz cudzych worktree i gałęzi.

ZADANIE (ADR 0157 „testy zero-GC, które naprawdę mierzą”): w testach Unity część sprawdzeń „zero alokacji” używa System.GC.GetAllocatedBytesForCurrentThread(), które w edytorze Unity (Mono) zwraca 0 — te testy przechodzą zawsze i niczego nie chronią (ustalone w s15/s16: docs/reports/REVIEW-2026-11-12-s15-mistral-r3.md, REVIEW-2026-11-13-s16-mistral-r4.md, REVIEW-2026-11-13-s16-mistral-r5.md). Działający wzorzec: licznik UnityEngine.Profiling.Recorder dla markera "GC.Alloc" — patrz game/Assets/_Project/Tests/PlayMode/HudTextAllocTests.cs i WorldInstancesRenderGcTests (grep).
Pliki do poprawy (sprawdź grepem, czy nie ma więcej): game/Assets/_Project/Tests/EditMode/NavRoutingTests.cs (testy ZeroGc_*), ControlInputLoggerTests.cs, FurnitureRetroSourceAllocTests.cs, MirrorCostTests.cs, MirrorRefreshScheduleTests.cs.

KROKI:
1. Przeczytaj: CLAUDE.md, docs/owner/AGENT-RULES.md, wskazane raporty, HudTextAllocTests.cs. Ustal, czy Recorder("GC.Alloc") działa w EditMode, czy tylko w PlayMode (zmierz, nie zgaduj — napisz mały test próbny, który celowo alokuje, i sprawdź, czy licznik to widzi w obu trybach). Jeśli w EditMode nie działa — przenieś te testy do PlayMode (asmdef testów PlayMode już istnieje; NIE zmieniaj plików .asmdef bez potrzeby — jeśli musisz, opisz dlaczego).
2. Wspólny helper (jedna klasa w Tests, np. GcAllocCounter) zamiast kopii w każdym teście; rozgrzewka przed pomiarem (pierwsze wywołania mogą alokować legalnie — JIT, cache).
3. Przepisz każdy test na helper. Dla KAŻDEGO testu zrób test mutacyjny: tymczasowo wstaw alokację do mierzonego kodu produkcyjnego (np. new List<int>() w pętli) → test musi PAŚĆ; usuń mutację (nie commituj jej). Tabela: test → mutacja → wynik.
4. Jeśli któryś test po poprawce wykaże PRAWDZIWE alokacje w kodzie gry — NIE poprawiaj kodu gry w tym zadaniu; oznacz test [Ignore("ADR 0157: realna alokacja X B/wywołanie w plik:linia — do osobnej poprawki")] i opisz w raporcie z liczbami.
5. Uruchom: pwsh scripts/test.ps1 -Platform EditMode oraz -Platform PlayMode — liczby przed/po (znane porażki środowiskowe: CarPaintMaterialTests.DepositionChannel ×2 i testy wymagające zbudowanego prefabu ciężarówki — nie Twoje).
6. ADR docs/adr/0157-zero-gc-tests-recorder.md (Context, Decision, tabela mutacji, liczby, Open) + raport w artifacts/gemini-0157/REPORT.md po polsku.

ŚRODOWISKO I ZASADY:
- Worktree: git fetch && git worktree add .claude/worktrees/gemini-0157 -b gemini-0157 origin/main. Pracuj tylko w nim. Pierwszy import Unity w nowym worktree trwa długo — to normalne.
- Unity: przed KAŻDYM uruchomieniem pwsh scripts/unity-slot.ps1 -Acquire -Owner gemini-0157, po zakończeniu -Release. Jeśli istnieje C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN — NIE uruchamiaj Unity (zabija adb pomiaru na telefonie), czekaj aż zniknie. Po każdym Unity: git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings. Nie uruchamiaj scripts/setup-project.ps1.
- Telefony/adb: NIE. Google Maps/Street View/Earth: zakaz.
- Nie zmieniaj: kodu gry poza Tests (chyba że helper wymaga — opisz), Data/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS.
- Nie zmyślaj liczb — wszystko z logów/XML wyników (artifacts/tests/*.xml), ścieżki w raporcie.
- Ciągły zapis: po każdym kroku commit WIP w gałęzi gemini-0157 + nadpisz C:\Users\matma\Documents\Claude\kamion\artifacts\live\gemini-0157.md (godzina, sha, zrobione, NASTĘPNY KROK jako komenda, „Gotowe do recenzji: TAK/NIE”).
- Przed oddaniem: git fetch && git merge origin/main w gałęzi, ponów testy z kroku 5. Potem git push origin gemini-0157 (tylko ta gałąź) i napisz „0157 gotowe” z podsumowaniem: tabela mutacji, liczby testów przed/po, realne alokacje znalezione, czego nie zrobiłeś.
```
