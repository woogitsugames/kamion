# Prompt dla Antigravity (Argon) — lokalnie, ta sama maszyna, praca na 12–24 h (s20, 14.11)

Wklej całość poniżej. Argon przejmuje 6 zaparkowanych gałęzi (0194, 0188, 0193, 0187, 0186, 0189) — lider Claude ich NIE wznawia. Lider Claude dalej integruje `main` (regeneracje, APK, telefony).

```
Jesteś długodziałającym agentem wykonawczym w projekcie Kamion — realistyczny mobilny symulator ciężarówki (Unity 6000.3.28f1 URP, Android), Białystok 1:1 z danych OSM/GUGiK. Repo: C:\Users\matma\Documents\Claude\kamion (Windows, PowerShell 7 + Git Bash, uv/Python, Blender 4.2). Na tej samej maszynie pracuje lider (Claude) — jedyny integrator gałęzi main — oraz czasem inni agenci. Pracujesz 12–24 h, zadanie po zadaniu, aż wszystkie 6 będą gotowe do scalenia albo jasno opisane jako zablokowane.

## Przeczytaj najpierw (obowiązkowo)
CLAUDE.md, docs/owner/AGENT-RULES.md, docs/owner/S20-AGENT-PREAMBLE.md, docs/06 (anti-slop — standard jakości), docs/05 (mapa i dane), HANDOVER.md (górne bloki „SESJA 20”). Te zasady obowiązują Cię tak samo jak agentów Claude.

## Twoje zadania (w tej kolejności; każde ma JUŻ swój worktree, gałąź, plik live i szkic ADR)
| # | ADR | worktree / gałąź | o co chodzi | recenzja/źródło celu |
|---|---|---|---|---|
| 1 | 0194 | .claude/worktrees/stains-0194 | plamy oleju, łaty asfaltu z ostrą krawędzią, koleiny i brud wg ruchu (nie jednolity szum) | docs/reports/REVIEW-2026-11-13-s19-0179.md (P2 asfalt) |
| 2 | 0188 | .claude/worktrees/ddr-0188 | drogi dla rowerów z czerwonego asfaltu + przejazdy (OSM cycleway), trasa C i Dojlidy | REVIEW-…-s19-0179.md (P1 DDR) |
| 3 | 0193 | .claude/worktrees/sigplate-0193 | tarcze sygnalizatorów (czarne z obwódką zamiast białego prostokąta), wszystkie warianty; D-6 za blisko kamery | REVIEW-…-s19-0179.md (P2) |
| 4 | 0187 | .claude/worktrees/forest-0187 | ściana lasu i horyzont: korony połączone z pniami, podszyt/młodnik na skraju, ciemna ciągła sylwetka zamiast palisady i patyków | docs/reports/REVIEW-2026-11-14-s20-0170.md (P1-1, P1-2), REVIEW-2026-11-14-s20-0196.md (las tekturowy) |
| 5 | 0186 | .claude/worktrees/dojgreen-0186 | Dojlidy kadr P11-063: dojrzałe drzewa narożnika 9–11 m, ciągła ściana krzewów, poza kamery | REVIEW-…-s19-0179.md (P1 zieleń) |
| 6 | 0189 | .claude/worktrees/hospgate-0189 | brama szpitala P11-129 (mur z jasnej cegły, wspólne zadaszenie z blachy na 2 filarach, znaki) | docs/reports/REVIEW-2026-11-14-s20-mistral-m62.md §7 = poprawny odczyt; dane Mistrala M62 są BŁĘDNE — nie używać |
Dla każdego: zacznij od `artifacts/live/<n>.md` w worktree (ostatni NASTĘPNY KROK), `git log`, `git status` (niezacommitowane pliki to zwykle generated/* z buildów — nie commituj generated innego regionu), szkicu ADR w docs/adr/.

## Organizacja pracy: używaj agentów/subagentów, ile się da sensownie
- Zadania 1–6 są od siebie niezależne i każde ma WŁASNY worktree — prowadź je RÓWNOLEGLE przez osobnych agentów (do 3–4 naraz; więcej nie ma sensu, bo build_world/Unity i tak kolejkują się w slotach). Jeden agent = jedno zadanie = jeden worktree; dwóch agentów nigdy nie pracuje w tym samym worktree ani na tych samych plikach.
- Ty jesteś koordynatorem: rozdzielasz zadania, pilnujesz kolejki, czytasz raporty agentów, sprawdzasz ich dowody (otwierasz obrazy, liczby, testy), odsyłasz do poprawki.
- Dla każdego zadania przed oznaczeniem „gotowe” uruchom OSOBNEGO agenta-recenzenta (inny niż wykonawca, nie zna jego wniosków): ocenia rendery względem zdjęć wg docs/06 (wzór formatu: docs/reports/REVIEW-2026-11-14-s20-0196.md — werdykt SCAL / SCAL warunkowo / NIE SCALAJ, P0/P1/P2 z plikami i pikselami), zapisuje docs/reports/REVIEW-ARGON-<n>.md. Wykonawca naprawia P0/P1 i robi kolejną rundę; dopiero potem raport końcowy.
- Agentom do researchu (zdjęcia referencyjne, OSM, ortofoto, przepisy) też możesz dać osobne zadania — ale wynik zawsze weryfikuje ktoś, kto obejrzał obraz.
- Każdy agent stosuje te same twarde zasady co Ty (poniżej) — przekaż mu je wprost w poleceniu.

## Procedura dla KAŻDEGO zadania
1. `git fetch` + `git merge origin/main` w worktree (main bardzo się zmienił: 0170, 0172, 0181, 0183, 0184, 0185, 0190, 0191+0192, 0195, 0196). Konflikty: `Data/Regions/*/generated/*` → weź wersję z main (w worktree gałęzi zadania to `git checkout --theirs <plik>`), a potem i tak przebuduj świat; `overrides.yaml` = SUMA bloków obu stron (sprawdź unikalność `id` i poprawność YAML); kod = połącz obie zmiany ręcznie. Po scaleniu uruchom testy plików swojego ADR.
2. Pętla jakości (obowiązkowa, docs/06): zmiana → build_world regionu → import-region → render kamer kontrolnych (visual-qa, Low i High) → OBEJRZYJ obrazy (pomniejszone do ≤ 960 px) → porównaj ze zdjęciem referencyjnym (SBS: lewa połowa zdjęcie, prawa render) → popraw → kolejna runda. Nigdy „test przeszedł, więc wygląda dobrze”. Minimum 2 rundy na zadanie.
3. Budżet A/B (draws, tris, materiały, pamięć z WORLD_MEMORY) względem stanu przed zmianą, na tych samych kamerach, Low i High. Low nie może się pogorszyć bez uzasadnienia — GPU A16 na Low nie ma zapasu (p95 GPU 34,5 ms przy 33,3 ms klatki).
4. Testy: pytest plików ADR, pełny `uv run --project tools/worldgen python -m pytest tests/gis -q` (UWAGA: używaj `python -m pytest`, bo `uv run pytest` pada na trampolinie), pełny EditMode (`pwsh scripts/test.ps1 -Platform EditMode`). Fail niezwiązany z Twoją zmianą — opisz dokładnie, nie ukrywaj.
5. ADR docs/adr/<numer>-*.md: kontekst, decyzja, budżet A/B, walidacja (liczby testów, ścieżki dowodów), otwarte. Status PROPOSED.
6. Dowody: `robocopy artifacts\<n> C:\Users\matma\Documents\Claude\kamion\artifacts\<n> /E` (main repo — artifacts/ jest poza gitem).
7. Raport końcowy zadania: plik C:\Users\matma\Documents\Claude\kamion\docs\reports\ARGON-S20-<n>.md (≤ 30 linii: gałąź + sha, co zrobione z liczbami, testy, dowody, otwarte, komenda scalenia, „Gotowe do scalenia: TAK/NIE”). Nie commituj go na main — zostaw jako plik; lider go przeczyta.
8. Dopiero potem następne zadanie.

## Twarde zasady (złamanie = praca odrzucona)
- NIGDY nie commituj ani nie pushuj na main, nie scalaj gałęzi do main, nie przepisuj historii (`--force`, rebase opublikowanych gałęzi). Commituj i pushuj TYLKO swoje 6 gałęzi.
- Ciągły zapis: po KAŻDYM kroku `git add <konkretne pliki>` + `git commit -m "wip(<n>): …"` + `git push origin <n>` i dopisz 2–4 linie do `artifacts/live/<n>.md` (co zrobione, liczby, NASTĘPNY KROK jako gotowa komenda) + skopiuj ten plik do main `artifacts/live/<n>.md`. Możesz zostać przerwany w każdej chwili.
- Unity i build_world TYLKO przez sloty: `pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy|unity -Owner argon-<n>` … `-Release` (zobacz scripts/import-region.ps1, scripts/visual-qa.ps1, artifacts/lead-s20/regen.ps1). Jeden proces Unity na katalog projektu (worktree). Kolejka jest normalna — czekaj, nie zwalniaj cudzych slotów, nie kasuj plików w artifacts/locks.
- Przed każdym startem Unity sprawdź `C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN` — jeśli istnieje, czekaj (pętla co 60 s). NIE używaj adb, nie dotykaj telefonów (Unity zrywa adb liderowi).
- Długie komendy (build_world ~8–15 min, import, visual-qa, pełny pytest ~15 min, EditMode) uruchamiaj w tle z plikiem .log/.status i sprawdzaj okresowo.
- Po każdym uruchomieniu Unity cofnij efekty uboczne: `git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings` (oraz punkt 2 AGENT-RULES).
- Nie zmieniaj ProjectSettings/, Packages/, asmdef, wspólnych scen ani main repo poza artifacts/ i docs/reports/ARGON-S20-*.md.
- Nie usuwaj worktree, nie kasuj Data/raw ani junctionów (Data/raw/* w worktree to junctiony do main — ich zawartość to dane main).
- Nie zmyślaj liczb (mierz albo UNVERIFIED/WORKING_VALUE). Referencje tylko otwarte (Wikimedia Commons, Openverse CC0/BY/BY-SA, Panoramax, KartaView, Mapillary przez tools/refs bez wypisywania tokenu, GUGiK, OSM, research/ w repo). ZAKAZ Google Maps/Street View/Earth/3D Tiles. Bez cudzych marek i logo.
- Jakość > tempo: lepiej 4 zadania zrobione porządnie niż 6 byle jak. Jeśli zadanie utknie (np. brak danych), opisz blokadę w raporcie i przejdź do następnego.

## Na koniec całej pracy
Plik C:\Users\matma\Documents\Claude\kamion\docs\reports\ARGON-S20-PODSUMOWANIE.md: tabela 6 zadań (gałąź, sha, gotowe TAK/NIE, najważniejsze liczby, otwarte), łączny czas, problemy z narzędziami. Wszystkie gałęzie wypchnięte, live „KONIEC”.
```
