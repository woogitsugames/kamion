# Prompt dla sesji Claude Code (2 agentów Opus) — zadania kodu s20

Wklej całość poniżej. Najlepiej w sesji LOKALNEJ (ta sama maszyna: Unity, uv, Blender). Jeśli sesja jest w chmurze (tylko GitHub) — patrz akapit „Bez dostępu do maszyny” na końcu promptu.

```
Pracujesz nad projektem Kamion — realistyczny mobilny symulator ciężarówki (Unity 6000.3.28f1 URP, Android), Białystok 1:1. Repo lokalnie: C:\Users\matma\Documents\Claude\kamion (GitHub: woogitsugames/kamion). Lider (inna sesja Claude) jest jedynym integratorem main — Ty NIE scalasz do main. Masz 2 agentów Opus; każdy robi jedno zadanie we własnym worktree i gałęzi.

NAJPIERW przeczytaj: CLAUDE.md, docs/owner/AGENT-RULES.md, docs/owner/S20-AGENT-PREAMBLE.md (worktree, sloty Unity, PHONE_RUN, ciągły zapis, raport), docs/06, HANDOVER.md (górne bloki „SESJA 20”).

ZADANIE A — ADR 0197: światła tylne ciągnika i naczepy zgodne z R148/R48 (agent Opus, n = lights-0197)
Źródło liczb: docs/reports/REVIEW-2026-11-14-s20-mistral-m59.md (fragment „Gra”) + research na gałęzi origin/research/mistral-p16-truck-lamps (cytaty R148/R150/R48). Stan gry: ADR 0178 (limiter świateł), ADR 0181 (soczewki, docs/adr/0181-lamp-lens-structure.md).
1. Stosunek intensywności STOP : pozycyjne ≥ 5:1 (R148 pkt 4.8.11) mierzony PO limiterze 0178 (dziś ~1:1 o zmierzchu — w renderach nierozróżnialne, High 200 vs 202). Napraw tak, by limiter nie zjadał różnicy.
2. Na naczepie rozdziel grupę TAIL_BRAKE (komory pozycyjne i stop świecą razem) na osobne grupy.
3. Bursztyn kierunkowskazów (1, 0.28, 0) leży poza obszarem R48 → (1, 0.22, 0) lub lepszy punkt w sRGB; test EditMode sprawdzający obszar chromatyczności R48 (zamiast pasma ADR 49/00). Czerwień (1,0,0) zostaje (pole ECE poza sRGB) — popraw tylko tekst ADR 0178.
4. Test luminancji tablicy rejestracyjnej ≥ 2,5 cd/m² w punkcie pomiarowym (R148 pkt 5.11.3).
Pętla: zmiana → TruckAssetBuilder.BuildBatch + TrailerAssetBuilder.BuildBatch (w worktree) → render kamer lamp (art-source/truck/exterior/qa/run_lamplens_0181.ps1 lub visual-qa: lamp-trailer, lamp-truck, plate-trailer, plate-truck-bobtail, truck-34, trailer-34; dusk + night + overcast; Low i High) → OBEJRZYJ → zmierz (średnie R/G/B w komorach stop vs pozycyjne) → popraw. Testy: nowe + pełny EditMode. ADR 0197 z liczbami.

ZADANIE B — ADR 0198: podpory estakady A ronda Putry (agent Opus, n = piers-0198)
Źródło: docs/reports/REVIEW-2026-11-14-s20-mistral-m56-fix.md (P1 dla gry) + research/mistral/p13-andersa-viaducts/ (w main; README z erratą lidera; wycinki research/_incoming/mistral-p13-andersa-viaducts-fix-crops/ c027, c022).
1. Pomost SW estakady A (łańcuch `c:w173956078`) ma przęsło 94,8 m bez podpór, a pomost NE 48,8 m i parę 16,4 m — to błąd generatora (rzędy podpór pominięte, bo słupy wypadały na nawierzchnię). Zdjęcia pokazują 5–6 i 3–4 rzędy w tych miejscach.
2. Dodaj `pier_lines_en` do wpisu Putry w Data/Regions/bialystok-industrial-c/viaduct_underdeck.json (stacje = WORKING_VALUE z wycinków/ortofoto), upewnij się, że `BLOCKED_COLS` jest pusty dla tych rzędów, kolumny nie stoją na jezdni pod spodem (jeśli muszą — zgłoś konflikt zamiast przesuwać jezdnię).
3. Popraw opisy/komentarze sprzeczne z danymi: „round piers” (słupy A prostokątne fazowane z głowicą), „cylindrical” dla B (dane: stadium), „southbound deck symmetric (UNVERIFIED)”.
Pętla: build_world bialystok-industrial-c (slot heavy) → import-region → render kamer Putry (sbs gate3 przy estakadzie: putry-above, g3b_eye_s1582, g3b_eye_s1632, route-putry-approach, driver-andersa-to-putry; Low i High) → SBS ze zdjęciami (sbs_references.json) → OBEJRZYJ → popraw. Budżet A/B (draws/tris), pytest tests/gis (używaj `uv run --project tools/worldgen python -m pytest`), EditMode. ADR 0198.

ZASADY (obie)
- Worktree: `pwsh scripts/new-agent-worktree.ps1 -Name <n>`; commit + push na gałąź <n> i dopisek do artifacts/live/<n>.md (z NASTĘPNYM KROKIEM jako komendą) po KAŻDYM kroku; kopia live do main artifacts/live/.
- Unity/build_world tylko przez `scripts/unity-slot.ps1` (pool unity/heavy); przed Unity sprawdź artifacts/locks/PHONE_RUN (jest = czekaj). Bez adb i telefonów. Długie kroki w tle, nie czekaj blokująco > 5 min.
- Nie zmieniaj ProjectSettings/, Packages/, asmdef, wspólnych scen; po Unity `git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings`.
- Nie zmyślaj liczb; każda wartość z raportu/źródła albo WORKING_VALUE. Pętla wizualna obowiązkowa — „test przeszedł” to nie dowód wyglądu.
- Na koniec: robocopy dowodów do main artifacts/<n>/, ADR (status PROPOSED), live „KONIEC”, raport ≤ 20 linii w C:\Users\matma\Documents\Claude\kamion\docs\reports\CODE-S20-<n>.md (gałąź + sha, liczby, testy, dowody, otwarte, „Gotowe do scalenia: TAK/NIE”). NIE scalaj do main.

Bez dostępu do maszyny (sesja w chmurze): rób tylko zmiany kodu/danych + testy jednostkowe, które da się uruchomić bez Unity i bez Data/raw (np. czysty Python/.NET), i w raporcie wypisz dokładne komendy do uruchomienia przez lidera (BuildBatch, build_world, import, visual-qa, EditMode). Wypchnij gałęzie lights-0197 / piers-0198 i otwórz PR (bez scalania).
```
