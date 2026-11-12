# Codex — jedna sesja na 12 h (s16, od 2026-11-12 ~23:00 do 2026-11-13 ~11:00)

Wklej blok poniżej do jednej sesji Codex (lokalnie, katalog `C:\Users\matma\Documents\Claude\kamion`).
Lider Claude (s16) równolegle prowadzi agentów: `fold-flicker` (0152, telefony), `putry-andersa` (0146, świat), `mistral-r4-int` (nawigacja/HUD). Ta sesja ma osobne dziedziny i osobny worktree.

```
Pracujesz lokalnie w repo C:\Users\matma\Documents\Claude\kamion (Kamion: realistyczny mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1 z OSM/GUGiK). Pracujesz 12 godzin (do ok. 11:00 13.11), samodzielnie, rundami, bez czekania na odpowiedzi. Liderem i jedynym integratorem main jest sesja Claude — Ty NIE scalasz do main, NIE pushujesz main, NIE usuwasz cudzych worktree ani gałęzi.

NAJPIERW PRZECZYTAJ: CLAUDE.md, docs/owner/AGENT-RULES.md, docs/owner/GPT-TASK-05-24H.md (sekcje „Najpierw przeczytaj” i „Protokół rundy” — obowiązują w całości, z wyjątkami poniżej), docs/11_DECYZJE_WLASCICIELA.md (D45, D51), docs/06 (anti-slop), górny blok HANDOVER.md.

WORKTREE: git worktree add .claude/worktrees/gpt-s16 -b gpt-s16-r1 origin/main (najpierw git fetch). Kolejne rundy w TYM SAMYM worktree: git switch -c gpt-s16-rN od poprzedniej rundy, potem git merge origin/main (konflikty Data/**/generated/*.json, *.glb, *_meta.json → --ours + regeneracja). Przygotowanie worktree wg „Protokołu rundy” pkt 2 (kopie Data\raw\derived, cc0, megascans, _Generated; bez Megascans generator po cichu robi fallback). Worktree gpt-life i argon-edge NIE są Twoje — nie ruszaj.

RUNDY (kolejność, każda = osobna gałąź, osobny ADR):
r1 — ADR 0153 „LOD1/LOD2 aut” (dziedzina life): osobówki i pojazdy statyczne na placach mają za dużo submeshy/draws — na A16 (Low) brakuje ~0,7 ms GPU p95 (ADR 0136 r2: GPU p95 34,0 ms vs cel 33,3). Zrób LOD1 i LOD2 z 1–2 submeshami (wspólny atlas materiałów), progi LOD z pomiaru w edytorze, LOD0 bez zmian wyglądu z bliska. Generator jako kod (Blender bpy / Python / Editor), odtwarzalny. Licz: draws, batches, tris na wszystkich kamerach kontrolnych Low i High przed/po (raportuj każdą kamerę osobno). Cel: Low draws ≤ przed, tris nie rosną, brak widocznego „pyknięcia” LOD w kadrach trasy.
r2 — ADR 0154 „zieleń ulic domów” (dziedzina vegetation): D51 PARTIAL — przy ulicach z domami jednorodzinnymi zieleń za rzadka: brak wysokich koron drzew w ogrodach i żywopłotów od ulicy. Porównaj ze zdjęciami referencyjnymi w repo (pary sbs, photolist) — NIE Google. Dodaj żywopłoty frontowe (część działek, z danych OSM/BDOT gdzie są; reszta WORKING_VALUE z uzasadnieniem) i wysokie korony (gatunki typowe dla Podlasia) w pliki streetscape/{vegetation,plantings,hedge_textures}.py. Budżet Low: draws +0 na kamerach trasy, tris ≤ +2 % (drzewa ogrodowe tier high pomijane na Low — zachowaj regułę z ADR 0132 r4b). Pary zdjęcie|render przed/po dla ≥ 6 ulic domów.
r3 (jeśli zostanie czas) — ADR 0155 „plamy słońca na wyspie pod wiaduktem” (ADR 0144 Open): jasne plamy słońca na wyspie pod pomostem wiaduktu Putry — sprawdź, czy pomost rzuca cień (shadow caster, kaskady, bias) na Low i High; popraw bez nowych przebiegów na Low.

KAŻDA RUNDA: baseline → zmiana → generator → import (pwsh scripts/import-region.ps1 -Region bialystok-industrial-c w worktree) → kamery kontrolne (pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low|High -Lighting clear|overcast -OutputDir <dir>) → OBEJRZYJ PNG i porównaj ze zdjęciami → popraw → testy: uv run --project tools/worldgen python -m pytest tests/gis -q oraz pwsh scripts/test.ps1 -Platform EditMode → ADR + artifacts/gpt-s16-rN/REPORT.md (polski, liczby przed/po, ścieżki par ≤ 960 px) → git push origin gpt-s16-rN (TYLKO swoją gałąź). Lider recenzuje, mierzy na telefonie i scala.

TWARDE ZASADY:
- Unity: przed KAŻDYM uruchomieniem pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-s16, po zakończeniu -Release. Jeśli istnieje C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN — NIE uruchamiaj Unity (zrywa adb pomiaru na telefonie), poczekaj aż zniknie. Po każdym Unity: git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings. Nie uruchamiaj setup-project.ps1. Równoległe buildy mogą zatrzymać wspólny demon Gradle („stop command received”) — wtedy ponów.
- Telefony i adb: NIE (robi lider). Nie usypiaj, nie blokuj, nie odłączaj telefonów.
- Zakaz Google Maps/Street View/Earth/3D Tiles. Fab/Megascans nigdy w gicie (D45). Bez marek i logo.
- Pliki Claude (nie ruszać): tools/worldgen/roads/*, overrides.yaml, bariery, krawężniki, oznakowanie, navgraph, streetscape/{plots,buildings_mesh,facade_kit,roofs,facade_atlas}.py, HUD/UI, fizyka, CameraRig, audio. Pliki wspólne (materials.py, WorldPBR/WorldSurface.shader, QualityProfile*) — tylko addytywnie, za flagą, opisane w REPORT.
- Nie zmyślaj: liczby zmierzone, wartości bez źródła = WORKING_VALUE, cytaty ze stroną.
- Dysk: nie kasuj nic poza swoim worktree; przed kopiowaniem dużych katalogów sprawdź (Get-PSDrive C).Free (nie schodź poniżej 100 GB).
- CIĄGŁY ZAPIS: po KAŻDYM kroku commit WIP w swojej gałęzi + artifacts/gpt-s16-rN/STATUS.md, a co najmniej co godzinę nadpisz C:\Users\matma\Documents\Claude\kamion\artifacts\gpt-s16\PRZEKAZANIE.md (godzina, gałąź, sha, runda, zrobione, liczby, w tle, NASTĘPNY KROK jako komenda, „gotowe do recenzji: TAK/NIE”). Lider zbiera to co godzinę (:07). Sesja może zostać przerwana w dowolnej chwili.
- Pracuj bez pytań. Jeśli coś wymaga decyzji właściciela — zapisz w PRZEKAZANIE.md jako „DECYZJA:” i przejdź dalej.
- Po 12 h albo po r3: zapisz WIP, PRZEKAZANIE.md z podsumowaniem wszystkich rund, push swoich gałęzi i zakończ.
```
