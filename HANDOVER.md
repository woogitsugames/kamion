# HANDOVER — kamion (TRUCK SIM PL), stan 2026-11-10 ok. 10:30

Dla nowej sesji Claude Code na tym samym komputerze (`C:\Users\matma\Documents\Claude\kamion`), inne konto Claude. Czytaj w kolejności: ten plik → `CLAUDE.md` → `docs/11_DECYZJE_WLASCICIELA.md` (D1–D29) → `docs/reports/GATE-3-draft.md` → `docs/reports/visual/REVIEW-2026-11-10-r5.md` → `docs/REFERENCES.md`.
Pamięć poprzednich sesji: `C:\Users\matma\.claude\projects\C--Users-matma-Documents-Claude-kamion\memory\` (MEMORY.md + pliki) — jeśli nowe konto jej nie ładuje automatycznie, przeczytaj ją ręcznie.

## Stałe polecenia właściciela
- Autonomicznie (bypass), wolno instalować narzędzia. **Jakość, nie cena** — „realistyczne na maksa i piękne”.
- Agenci równolegle (właściciel pozwalał na 10–20; każdy w swoim worktree, lider = jedyny integrator, `git merge --no-ff`, push na https://github.com/woogitsugames/kamion, potem `git worktree remove` + `git branch -D`).
- Modele: **Fable 5.2 (`model: "fable"`) do modeli 3D** (truck-artist, Blender, auta), **Opus** do grafiki/shaderów/świata/fizyki, Sonnet średnie, Haiku proste.
- Decyzje dla właściciela **klikalne** (AskUserQuestion), po polsku. Na koniec większego kroku: commit, push, krótki raport po polsku.
- **Zakaz Google Street View/Maps/Earth** (ADR 0002). Referencje: Wikimedia Commons (`data/photos/nowe/`, poza gitem, licencje w `docs/REFERENCES.md`), GUGiK/OSM. Zdjęcia prasowe/AI od właściciela = tylko wzór stylu, nigdy kopiowanie cudzej marki (CLAUDE.md §8).
- Telefony: zawsze `-Serial`; przed każdym przebiegiem `isKeyguardShowing=false` i temp. baterii < 36 °C; **nigdy KEYCODE_SLEEP/POWER, nigdy PIN**.
- **S24+ `RZCX60VE8ZY` to telefon roboczy właściciela (odbiera połączenia/SMS):** bateria nigdy < 20 %; przebieg tylko przy ≥ 40 %, < 30 % — koniec pracy na nim; po pomiarze `am force-stop` gry; tylko za zgodą właściciela. Ładuje się wolno z USB komputera (port USB-C bezpośredni). A16 `RFGL34SJYDZ` (Low) bez ograniczeń.
- **Przed usunięciem worktree skopiuj jego `artifacts/`** do głównego checkoutu (2026-11-10 straciliśmy tak zrzuty S24+ i klipy DK8). W briefach każ zapisywać dowody pod ścieżkę absolutną `C:\Users\matma\Documents\Claude\kamion\artifacts\...`.
- Po buildach cofaj efekty uboczne: `game/ProjectSettings/ProjectSettings.asset` (preloadedAssets), `QualitySettings.asset`, `M_Sky.mat`, pusty `game/Assets/Resources(.meta)`.

## Gdzie jesteśmy (main = ok. `ae97eff`)
- **Etap 3 (bramka, odcinki G3-A i G3-B: brama Kwadrat Parku → Rondo Putry)** — pomiary zrobione (`docs/reports/GATE-3-draft.md`):
  - A16 Low (sha `c59209e`): G3-A/G3-B p50/p95/p99 33,3/33,5/33,6 ms, PSS ~690 MB, bez grzania — **PASS**.
  - S24+ High (stary build `fefd804`): p95 50/33,5 ms — **FAIL**; poprawka ADR 0046 (adaptacyjna skala 1,00/0,85/0,80 + FSR1/RCAS, zejście do 30 FPS przy thermal ≥ 2, lżejsze cienie) scalona, **niezmierzona na telefonie**.
  - Zrzuty A16 37/37: `artifacts/gate3/final/` (+ `small/`). Zrzuty S24+ i klipy DK8 MSAA — **do powtórzenia** (za zgodą właściciela, bateria ≥ 40 %).
  - Narzędzie dowodów `scripts/gate3-evidence.ps1` (6 kontroli docs/06 §5); ostatnio FAIL tylko „obiekty vs teren” (7 latarni 12 m do 0,35 m nad terenem, 5 słupków znaków zakopanych do 0,86 m na wysepkach rond).
  - E6 limit świata w APK podniesiony do **≤ 110 MB** (D24, bez Play Asset Delivery); zmierzone ~94 MB górnej granicy.
  - Przejazd zestawu po rondach: `tests/physics/test_swept_path_gate3.py` (zjazd z ronda Bieżeństwa wymaga szerszego toru).
- **Ciężarówka TRAKT — nowy nowoczesny front** (D28, D29: pochylenie 1,5°, ADR 0047) w grze; eksport LOD0 102k / LOD1 43k / LOD2 15,3k, koła LOD2 okrągłe (ADR 0039). Wnętrze dopasowane (ADR 0045 szyba od środka). Lakier/brud ADR 0038, cień kontaktowy ADR 0021, lusterka ×6 ADR 0042, kierunkowskazy + żywe zegary (fuel/coolant/clock WORKING_VALUE).
- **Świat C** v3.4 + materiały PBR, zaparkowane auta (1076 → 921, generator `tools/worldgen/streetscape/life_cars.py`, ADR 0041), ekrany akustyczne, kosze, wiaty, rowy 1:1,5 (ADR 0033, ratchet 103 ścianek), zadaszenia na wszystkich tierach.
- **Wygląd:** D23 „jak zdjęcie z telefonu”; balans bieli 0,5 przy niskim słońcu (D27, ADR 0043); cab lift ADR 0029.
- **Menu testu jazdy właściciela** + `docs/owner/FEEL-TEST.md`, log `[CONTROLS]` bez alokacji. Test jazdy (D25) **po raporcie bramki 3**.

## Prace w toku w chwili przekazania (sprawdź, scal albo dokończ)
| Zadanie | Gdzie | Stan / co zrobić |
|---|---|---|
| TRAKT: wewnętrzna okładzina lewego słupka A (czarny klin ~12 % kadru z fotela) → ≤ b2+1° | worktree `.claude/worktrees/agent-a7bf651b0c37426a5` (gałąź `worktree-agent-a7bf651b0c37426a5`) | Fable 5.2; sprawdź `git log main..HEAD`, klatki w `artifacts/owner/modern-front/unity3/`; po scaleniu skopiuj gitignorowany `art-source/truck/interior/export/SM_CabInterior_LOD0.fbx` z worktree do main |
| Shader: przegląd ograniczenia brudu na gładkich częściach + czarne lamele grilla wychodzą szare | worktree `.claude/worktrees/agent-a97376698478165f6` | Opus; kadry w `artifacts/owner/modern-front/shader/` |

## Następne kroki (kolejność)
1. Dokończ/scal dwie prace powyżej; przebuduj prefab (`Game.Editor.Setup.TruckAssetBuilder.BuildBatch`), testy EditMode + PlayMode + `uv run --project tools/worldgen --with pytest --with scipy pytest tests/ -q` + dotnet runner (`%LOCALAPPDATA%\Microsoft\dotnet\dotnet.exe test tools/physics-runner -c Release`).
2. Recenzja wizualna **r6** (`visual-critic`, Opus) nowego frontu, aut, wnętrza na klatkach URP i A16.
3. Za zgodą właściciela: S24+ High z nowym buildem (ADR 0046) — G3-A/G3-B, zrzuty kamer, klipy DK8 (jazda, nie statyczna kamera), 30-min test termiczny; sprawdź natywną rozdzielczość buildu (QHD+ vs FHD+).
4. Raport bramki 3 do końca (sekcje wizualne, werdykt) → APK do testu jazdy właściciela (D25).
5. Otwarte: auta — mleczne szyby LOD0 na High, brud progów, przody kanciaste; latarnie/słupki vs teren; ścianki terenu na skrzyżowaniach (ratchet 103); linie WN rwą się subpikselowo (min. szerokość w px); zacieki pod attyką hal; lusterko przednie celuje w niebo; przetarcia na kierownicy/fotelu (generator wnętrza); lusterka 3→2/klatkę na High (propozycja w ADR 0046); szyba z zewnątrz wciąż „akwarium”.

## Narzędzia
Unity 6000.3.28f1 (`scripts/env.ps1`), Blender 4.2.9 `C:\Users\matma\AppData\Local\Programs\Blender4.2\blender-4.2.9-windows-x64\blender.exe -b` (**nigdy `Mesh.materials.clear()`**), .NET SDK user-local, uv/Python, ImageMagick, scrcpy, adb. Komendy w `CLAUDE.md`.

## Prompt startowy dla nowej sesji
Patrz `docs/owner/START-PROMPT.md` (do wklejenia jako pierwsza wiadomość).
