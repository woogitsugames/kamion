# HANDOVER — kamion, sesja 5 (aktualizacja 2026-11-10 ok. 22:10; lider zapisuje ten plik po każdym scaleniu/starcie agenta)

## Najpierw (sesja 5 → następna)
- **Prompt startowy następnej sesji:** `docs/owner/START-PROMPT-S6.md`.
- **main = `417283e`+, wypchnięty.** Limit 5 h: 85 % o 21:52 (reset 01:10) — od 85 % max 2 agentów naraz. Scalone w sesji 5: świat r8 ADR 0060 (p10 ov 32–34, cel ≤ 28 NIE — potrzebna decyzja właściciela o ekspozycji ov), skany CC0 ADR 0063. Przód 0061 i źródła 0066 (WIP) scalone wcześniej.
- **Zgłoszenie właściciela:** pas ze strzałką wjeżdża w wysepkę z trawą (`artifacts/owner/bugs/2026-11-10-lane-into-island.webp`) + wymaganie: „drogi dosłownie jak w OSM, żeby mieszkaniec wiedział jak jechać” → agenci 0074/0075/audyt.
- Zasady dla agentów: `artifacts/handover/AGENT-RULES-S5.md`. Ostatni przydzielony ADR: **0075**.
- Przy przejęciu worktree: `git -C <wt> log main..HEAD`, STATUS.md (ścieżka poniżej), dokończ albo scal. Przed usunięciem: skopiuj `<wt>/artifacts`, `cmd /c rmdir` junctiony `<wt>/Data/raw/*`, `git worktree unlock`, `git worktree remove --force --force`, sprawdź `du -sh Data/raw/*` w main.

| zadanie | model | ADR | worktree `.claude/worktrees/` | gałąź | STATUS / dowody | stan |
|---|---|---|---|---|---|---|
| wyposażenie drogi wg Mapillary | Opus | 0069 | agent-a6651051778fa221f | worktree-agent-a6651051778fa221f | artifacts/street-r9 | w toku (import/render) |
| wiadukt hero | Fable | 0067 | agent-a1ec6028c4e13f527 | worktree-agent-a1ec6028c4e13f527 | artifacts/viaduct-r9 | w toku (build→import→render) |
| otwarte źródła + Kwadrat Park/straż | Sonnet | 0066 | agent-ab1fb0a47d2f0a491 | worktree-agent-ab1fb0a47d2f0a491 | artifacts/refs-opensources, artifacts/refs/{kwadrat-park,fire-station} | w toku (pobieranie) |
| straż pożarna hero (ref. `Data/photos/nowe/7197_May_2021_in_Białystok.jpg`) | Fable | 0070 | agent-aa9c74c62497e5d1f | worktree-agent-aa9c74c62497e5d1f | artifacts/firestation-r9 | w toku |
| Kwadrat Park hero | Fable | 0071 | agent-a1409e374f8c12b4f | worktree-agent-a1409e374f8c12b4f | artifacts/kwadrat-r9 | w toku |
| grill Low lowsun + szyba/dach/chrom | Opus | 0072 | (usunięty) | scalony | artifacts/truckshade-r9 | GOTOWE częściowo: toe D23 na Low poza kabiną (`exteriorToeParity`); otwarte: σ szyby słońce 4–6 < 8, N-8 prostokąt, dach High 8,4 % ≥ 97 % (decyzja D23 vs N-17), lamele LOD2 bez warg (truck-artist) |
| auta r9 sylwetki | Fable | 0073 | agent-adeef0c396335e1ed | worktree-agent-adeef0c396335e1ed | artifacts/cars-r9 | w toku |
| spójność nawierzchni (pas w wysepkę) | Opus | 0074 | agent-a49b0ff53eade0b91 | worktree-agent-a49b0ff53eade0b91 | artifacts/roadgeo-r9 | w toku |
| audyt mapy całej trasy | Opus | — | (usunięty) | scalony 417283e | artifacts/map-audit-r9/BUGS.md | GOTOWE: 21 błędów (4 P0: MA-010, MA-001, MA-002, MA-012) → przekazane 0074 (geometria) i 0069 (ekrany, sygnalizator, szlaban) |
| zgodność dróg z OSM/ortofoto | Opus | 0075 | agent-aee7234325983b8dc | fidelity-r9 | artifacts/fidelity-r9/DIFFS.md | w toku |

## Następne kroki
0. **Fab (fab.com) — decyzja właściciela: najpierw sprawdzić licencję** (agent Sonnet, bez logowania i pobierania): Fab Standard License + Megascans + CC BY na Fab — użycie w Unity, gra komercyjna Android, publiczne repo (pliki źródłowe poza gitem?), atrybucja; lista przydatnych darmowych pozycji (sosny, lipy, krzewy, trawa, kamienie, krawężniki, śmieci). Wynik → pytanie klikalne do właściciela o rozszerzenie D40. YuE: notatka w docs/08 (po bramce 3).
1. Scalanie: 0069 → 0067 → 0072 → 0073 → 0074/0075 → 0070/0071 → 0066 (konflikty: generated/*.json = `--ours` + regeneracja; shadery/QualityProfile/RenderOverrides/LICENSES = unia).
2. Pełna integracja na main: build_region → build_world → import-region (CC0: najpierw `cc0_fetch.py`), Truck/Trailer BuildBatch, InstallBatch, pytest/EditMode/PlayMode/physics, czysty build Low + High. Uwaga: EditMode 2 inconclusive `TruckCabGlassTierTests` — sprawdzić.
3. Telefony pod `artifacts/locks/PHONE_RUN` (S24+ 46 %/33 °C o 21:15; A16 80 %): A16 Low gate3 + kabiny × 3 pory + świat ov; S24+ High A/B (cel 60 kl./s).
4. Decyzje właściciela do zebrania w r9: ekspozycja ov (p10, ADR 0060), D23 biel 0,7 vs przepał dachu N-17 (ADR 0072). APK High właścicielowi (FEEL-TEST), recenzja r9 (visual-critic) + decyzje (ekspozycja ov dla p10, wynik audytu mapy), raport bramki 3.

---
# HANDOVER — kamion (TRUCK SIM PL), stan 2026-11-10 ok. 20:00 (sesja 4, limit 86 %)

## Najpierw (sesja 4 → następna)
- **main = `1ff9fb5`, wypchnięty** (po 0e45111 doszły lusterka ADR 0068).** Scalone w sesji 4: metadane gate3 (gitSha z APK, `-Apk`, duplikaty md5), kamery gate3 jedna poza edytor/telefon + kadry kabiny na telefonie, auta r8 (0/81 dziur, LOD0 16 m, ADR 0041 r8), szkło r8 (ADR 0059: brak stożka/prążków lowsun, szyba drzwi), skala 0,70 + FSR + pacing 30 + plamy latarni dusk −5° (ADR 0062), wypiekana widoczność nieba + dalekie cienie (ADR 0064), Mapillary (ADR 0065, `tools/refs`), lista ujęć + pokrycie, recenzja r8, różnice gra vs Mapillary (`docs/reports/visual/REFS-MAPILLARY-FINDINGS-2026-11-10.md`).
- **Decyzje D36–D44** w `docs/11` (skala 0,70; próg farby względny; albedo trawy 35–40; panel dev zostaje; CC0 tak; właściciel NIE robi zdjęć — tylko otwarte źródła; Mapillary tak; σ szyby ≥ 8 tylko przy słońcu). Google Maps/3D Tiles/Street View — odmowa wyjaśniona właścicielowi (ToS + koszt + jakość).
- **Pomiary:** A16 Low e3671b4 `artifacts/gate3/20261110-a16-low-e3671b4/` (G3-A p99 50 ms > 40; cab-dash czerń 2,8–3,8 %; 0 duplikatów). S24+ High e3671b4: 43–47 kl./s (G3-A/G3-B w `artifacts/gate3/20261110-172908`, `-175241`).
- **Token Mapillary** w `C:\Users\matma\.kamion\secrets.env` (czyta `tools/refs/mapillary_fetch.py`; nigdy nie wypisywać).
- **Blokada telefonu:** `artifacts/locks/PHONE_RUN` — agenci nie startują Unity, gdy plik istnieje. Zakładaj przed pomiarem, zdejmij po.

## Agenci w toku przy końcu sesji 4 (worktree `.claude/worktrees/agent-<id>`, gałąź `worktree-agent-<id>`, STATUS.md w `<wt>/artifacts/<dir>/`)
| id | model | zadanie | ADR | dowody |
|---|---|---|---|---|
| a9eaaeb7a945e26bb | Opus | ciemne akcenty p10 ≤ 28, berberys (+ rozmieszczenie wg Mapillary: żwir pod wiaduktem), albedo trawy D38, próg farby D37 | 0060 | world-r8 |
| a6fd2182039af9a34 | Fable | przód TRAKT Low lowsun + aliasing napisu/wycieraczek + E7 obudowy lusterek + N-17 deflektor | 0061 | front-r8 |
| a173ed44d3c378718 | Opus | skany CC0 (Poly Haven/ambientCG) jako baza materiałów świata | 0063 | cc0-r8 |
| ab1fb0a47d2f0a491 | Sonnet | otwarte źródła referencji (KartaView, Panoramax, Commons, Openverse, ortofoto GUGiK, dane miasta) | 0066 | refs |
| a1ec6028c4e13f527 | Fable | wiadukt jako hero asset wg Mapillary | 0067 | viaduct-r9 |
| ~~a165b14c05122bf57~~ | Opus | lusterka — SCALONE 1ff9fb5 (A/B na S24+: `rq_ab mirrorcfg|mirrors|envcap|shadows|shadowcasc`, `rq_scale 1.0 rq_pacing 0`, ≥ 90 s) | 0068 | mirror-r9 |
| a6651051778fa221f | Opus | wyposażenie drogi wg Mapillary (ekrany, bramownice, bariery, sygnalizacja, strzałki) | 0069 | street-r9 |
Przy przejęciu: `git -C <wt> log main..HEAD`, przeczytaj STATUS.md, dokończ albo scal; konflikty możliwe w `tools/worldgen/build_world.py`, `WorldSurface.shader`, `QualityProfile.cs`/`RenderOverrides.cs` (unia pól). Przed usunięciem worktree: skopiuj artifacts, `cmd /c rmdir` junctiony Data/raw, potem `git worktree remove --force --force`.

## Następne kroki
1. Scal pozostałych agentów (kolejność: świat 0060 → CC0 0063 → ulica 0069 → wiadukt 0067 → przód 0061 → lusterka 0068).
2. Pełna integracja na main: build_region → build_world → import-region (zawiera WorldSkyBake), Truck/Trailer BuildBatch (szyba drzwi ADR 0059 — bez tego 3 testy `TruckDoorGlassTests` czerwone), InstallBatch, pytest/EditMode/PlayMode/physics, czysty build Low + High.
3. Telefony (blokada PHONE_RUN, bez Unity): A16 Low gate3 (koszt LOD aut 16 m, plamy latarni, WorldSkyBake: `rq_worldgi 0` A/B), S24+ High A/B wg ADR 0062/0068 (`rq_scalemin`, `rq_mirror_*`, `rq_shadow 60`). Przy `gate3-run` używaj `-Apk` i `pwsh -Command` dla parametrów tablicowych.
4. Recenzja r9 (visual-critic) z kadrami telefonu + montaże Mapillary; raport bramki 3 (`docs/reports/GATE-3-draft.md`) do decyzji właściciela.
5. Właściciel testuje jazdę (P + kierownica ADR 0058) na S24+ — APK e3671b4 High zainstalowany; poproś o wynik/logi `CONTROLS`.

---
## Najpierw (sesja 3 → następna)
- **main = `166fa76`, wypchnięty.** Scalone w sesji 3: crash visual-qa D3D12 (ADR 0051), kamera fotela/H-point (ADR 0052), belka maski r7b + przód r7c (ADR 0047), AO aut (ADR 0050), żywopłoty + kontrast farby (ADR 0049 r7), hale Low/High (ADR 0012 r7), capture odbić na wszystkich tierach (ADR 0056), przetarcia skóry (ADR 0044 r8), **ciemna kabina tylko w kadrach QA** (ADR 0044 r9, `ViewCameraResolver`), kierownica — model ręki/szybkość (ADR 0058), **hamulec postojowy trzyma + blokada ruszania AMT** (ADR 0004 addendum), Log bez stack trace, audyt albedo bez szkła/łat AO, `import-region` przebudowuje tekstury gdy `_src` nowsze.
- **Decyzje właściciela D30–D35** (progi r7) w `docs/11`. Zgoda na pomiar S24+ High **jest** (sesja 3), warunki z `docs/owner/S24-HIGH-RUN.md`.
- **Scalone po 16:00:** nowa kierownica r8b (Fable, ADR 0044 r8b; wnętrze LOD0 sha1 2ff350fb… w `art-source/truck/interior/export/`), ostrzeżenie P w HUD + gong + kontrolka (767ba9f).
- **W toku przy końcu sesji 3 (przejmij):** (1) build-qa na **main**: pełna integracja → czysty build Low+High → A16 Low gate3 → S24+ High (zgoda jest); status krok po kroku w `artifacts/handover/final-integration-status.md`, commity na main. (2) Fable, auta: dziura w aucie w `cab-dash` + LOD aut Low 8–12 m; worktree w `.claude/worktrees/agent-aeb4c025dbb5eae0c` (gałąź `worktree-agent-aeb4c025dbb5eae0c`, commity `wip(cars):`), status `artifacts/world-fixes/cars-r8/STATUS.md`. Sprawdź `git -C <wt> log main..HEAD`, dokończ, scal, odepnij junctiony Data/raw przed usunięciem worktree.
- Zablokowane (lock pid) puste worktree po scalonych agentach: `agent-a2435fdaafe42d6e9`, `agent-a6929d46dce94eb64`, `agent-a140cf18e9d148e78` — wszystkie scalone; usuń `git worktree remove -f -f` (najpierw odepnij Data/raw).
- **Tekstury PBR na main przebudowane** (asfalt 0,080), ale świat NIE zaimportowany po tym — zrób pełną integrację.
- **Pomiary telefonów:** A16 G3-A/G3-B na `f6abb8b` w `artifacts/gate3/20261110-a16-low-f6abb8b/` (p95 33,5 ms, PSS 739/769 MB, CPU p99 41,8–42 ms > 40). **cab-dash z telefonu nieważne** (błąd QA kamery, naprawiony w r9). A16 bywa `offline` → właściciel przepina kabel.
- **ADB: daemon zabija Unity** (każdy batch Unity). Pomiary telefonów tylko gdy ŻADEN Unity nie działa. `env.ps1` przypina adb z SDK Unity. `gate3-run -SkipBuild` instaluje NAJNOWSZY plik z `artifacts/apk` — pilnuj.
- Owner feel-test S24+ (f6abb8b): hamowało przez P (naprawione), kierownica za szybka (naprawione ADR 0058) — do ponownego testu.

## Następne kroki
1. Jeśli build-qa nie skończył: pełna integracja na main: build_region → build_world → import-region, Truck/Trailer BuildBatch, InstallBatch, wszystkie testy; **czysty (nie -dirty) build** Low + High.
2. Bez innych Unity: A16 Low gate3 G3-A + G3-B + kamery kabiny (cab-dash ≤ 8 % czerni, logcat `[CAB] view camera … cabView=True`), gate3-evidence. Potem S24+ High wg checklisty (bateria ≥ 40 %, < 36 °C, am force-stop na końcu).
3. Recenzja r8 (visual-critic) z kadrami telefonu; zainstaluj APK właścicielowi do testu jazdy (FEEL-TEST.md: P, kierownica).
4. r7 cz. 2 top (docs/reports/visual/REVIEW-2026-11-10-r7.md §9–14): auto z dziurą w cab-dash + toporny LOD aut na Low 8–12 m; szyba drzwi od środka + **regres: stożek/prążki w szybie przy lowsun (ADR 0056?)**; ciemne akcenty świata p10 ≤ 28; przód Low lowsun + aliasing TRAKT/wycieraczek; berberys kształt; σ szyby ≥ 8, jasny prostokąt w szybie, chrom lusterek.
5. Metadane gate3: `gitSha` = sha APK, nie HEAD; `g3b_eye_s1532` == `s1482` (duplikat); `putry_approach` poza.
6. Otwarte z sesji 2 (pkt 7 niżej) częściowo zrobione: żywopłoty, kontrast, ślady w dokach (nie odtworzone), hale, kamera fotela, lusterko kl. VI (OK), crash visual-qa.

---

# (sesja 2)
## Najpierw (sesja 2 → następna)
- **main = `0eb8b84`, wypchnięty.** Scalone w sesji 2: lusterka R46 + High 2 RT/klatkę (ea8ba23), druty WN min. px + łańcuchówka + zacieki attyki v2 (e7c6bae), shadery zewn. (firanka, niebo High, szyba, fp16 glint; 28f9a64), geometria TRAKT r6 (2e12e8c), wnętrze r6 kierownica (03e539d), auta v4 + naprawiony test budżetu (bb7549d), gate3 W-N10 + S24 checklista (29f4dfd), ulice r6 ADR 0049 + TRAKT r6b (8eb64fe), szkło aut + toe parity (0eb8b84).
- **Integracja na main zrobiona:** świat zregenerowany, Truck/Trailer BuildBatch, import-region, WorldTruckInstaller. Testy: pytest 185/185, EditMode 112/112, PlayMode 63+5 skip, physics 147/147. APK Low `artifacts/apk/kamion-0.1.0-0eb8b84a74.apk` (164,6 MB, SHA256 442ed5a6…a936e) — kompiluje się, **NIE zainstalowany**.
- **A16 `RFGL34SJYDZ` OFFLINE w adb** od ok. 12:40 (po przebiegu gate3; możliwe, że gra nadal działa — po podłączeniu `am force-stop com.woogitsugames.kamion`). Właściciel musi przepiąć kabel / zatwierdzić debugowanie USB. Demon adb bywa zabijany przez równoległe adb (scrcpy vs Unity SDK) — używaj tylko `$Adb` z `scripts/env.ps1`, jeden agent telefonowy naraz.
- **Dwa agenty w toku (worktree od 8eb64fe, jeszcze niescalone):** `agent-a6910633040021c05` (Fable: dziura w belce maski `grille_bar_mask` LOD0/LOD2, r6 E-N2 — ADR 0047 addendum r7) i `agent-ae69268ea41cf7bcc` (Opus: AO kontaktowe pod zaparkowanymi autami). **Oba zapisały WIP (niezweryfikowane):** belka `10dc12e` (ADR 0047 „Addendum r7b WIP”, kroki dalej tam; nowe wnętrze LOD0 w `artifacts/owner/modern-front/r7-maskbar/export/` → skopiuj do `art-source/truck/interior/export/`), AO aut `1b14744` (ADR 0050 + ADR 0041 „AO aut — WIP”; overcast p5 8–11 % > 8 %; sprawdź `test_parking_mix_and_neighbours` KeyError). Sprawdź `git -C <wt> log main..HEAD`, skopiuj `artifacts/`, scal `--no-ff`, potem regeneracja świata + BuildBatch/InstallBatch. **Uwaga przy sprzątaniu worktree:** agenci robią junctiony `Data/raw/gugik` i `Data/raw/osm` do main — najpierw `cmd /c rmdir` na junctionach, dopiero potem `git worktree remove --force`.
aw\gugik`/`osm` do main — najpierw `cmd /c rmdir` na junctionach, dopiero potem `git worktree remove --force`.
- `SM_CabInterior_LOD0.fbx` (poza gitem) skopiowany do `art-source/truck/interior/export/` z r6b — nie nadpisuj starszym.
- Stash `stash@{0}` = lokalne wyniki regeneracji sprzed sesji 2 (do wyrzucenia).
- Do usunięcia ręcznie (auto-mode zablokował): gałąź zdalna `origin/wip/wires-streaks` (zastąpiona), puste katalogi w `.claude/worktrees/`.

## Następne kroki
1. Scal dwa agenty powyżej, regeneruj, testy, build Low.
2. A16 Low: `pwsh scripts/gate3-run.ps1 -Serial RFGL34SJYDZ -Tier Low -Fps 30` (G3-A, G3-B) + `-TruckCameras`/`-TruckLightings` (truck-34, cab-dash × overcast/lowsun/dusk); potem `gate3-evidence.ps1 -PhoneDir <nowe>`. Ostatni pomiar A16 (`ecfd03b`, sprzed poprawek r6): p50/p95/p99 33,3/33,5/33,7 ms, PSS 675–701 MB, thermal 0; CPU main p99 42–45 ms (> 40, przyczyna UNVERIFIED); cab-dash z telefonu 30–47 % czerni (sprzed poprawek wnętrza).
3. Recenzja **r7** (`visual-critic`, Opus): kadry edytora już są — `artifacts/gate3/r7-editor-0eb8b84/` (246 renderów Low/High × overcast/lowsun/clear, wszystkie frame_exposure PASS; FAIL tylko albedo_histogram — głównie szkło, które audyt powinien wyłączyć — i texel_density płotów). Dorzuć kadry A16 i montaże ze zdjęciami (Scania R/S730, Bieżeństwa).
4. **Decyzje do właściciela (klikalnie) po r7:** progi r6 E2 szyba ≥60 % i E1 lakier ≥15 pkt (agent: fizycznie nieosiągalne w tym kadrze; szyba 38–41 %, akwarium zniknęło); szyby aut ≤20/≥40 % (jest 23–31/31–44 %, fizyczne odbicie nieba — albo przyciemnić model nieba ADR 0010); kierownica przy lowsun sat 18–19 % (próg 15; to kolor słońca LP_LowSun przy WB 0,5, D27).
5. S24+ High za zgodą (`docs/owner/S24-HIGH-RUN.md`; bateria ≥ 40 %; przy ostatnim sprawdzeniu 62 %).
6. Raport bramki 3 (`docs/reports/GATE-3-draft.md`) → APK do testu jazdy (D25, `docs/owner/FEEL-TEST.md`).
7. Otwarte: żywopłoty Bieżeństw wyglądają jak bryły; kontrast farba/asfalt 1,5 (krytyk chce ≥ 1,8 → ciemniejszy asfalt); ślady opon w dokach nie renderują się na Low; przetarcia kierownicy niewidoczne przy limicie albedo czarnego 0,05 (decyzja rendering-perf); Low/High różna geometria hal (rynny/doki tylko High); kamera na fotel kierowcy; lusterko kl. VI w całości pod osłoną przeciwsłoneczną w `cab-mirror-front` (sprawdzić po r6 geometry); visual-qa High lowsun crash przy zamykaniu Unity (−1073741819, kadr zapisany).


---

# (poprzednia wersja, sesja 1)

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

## Gdzie jesteśmy (main = ok. HEAD z 2026-11-10 ok. 11:30)
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

## Prace w toku w chwili przekazania (sprawdź `git -C <worktree> log main..HEAD`, skopiuj `artifacts/` do main, scal albo dokończ)
Scalone dziś już: TRAKT r3 (słupek A 7,0°), r4 (lamele grilla 20° w dół, lusterko kl. VI na ziemię, węższe lusterko 11,25°), shader czarnego plastiku (ADR 0047 r3), strażnik jednej warstwy szkła (ADR 0048; „podwójna szyba na Low” niepotwierdzona — sprawdzić dwa poziomy GLASS_* naraz albo szybę z CabInterior). Diagnoza „akwarium”: wnętrze ma fizycznie poprawną jasność, kabina jest przezroczysta na wylot (dowody `artifacts/owner/aquarium/`).

| Zadanie | Worktree (`.claude/worktrees/…`) | Uwagi |
|---|---|---|
| (scalone `ffbe6cf`) wnętrze: polerowanie wieńca/wybieraka, listwa u stopy słupka A, zasłony koi i drzwi pasażera; **sprawdzić**: przy lowsun zasłona pasażera przyciemnia piastę/konsolę (próg czerni `cab-dash` ≤ 8 %), połysk addytywny w CabInterior.shader do przeglądu rendering-perf; fotel/mata/drzwi poza kadrem — nieocenione | — | gotowe |
| (scalone `65f3acd` + regeneracja świata na main) latarnie/słupki: 0 zakopanych słupków, 3 latarnie wiszą 0,301–0,305 m (próg 0,30; podejrzenie: rzadsza kolizja terenu), ratchet ścianek 103 → 14, jedna prawdziwa ścianka `j:n1847044961` przy Rondzie Putry otwarta | — | gotowe |
| Opus: druty WN min. szerokość w px (P0 z r6) + zacieki pod attyką | `agent-a00eb437b0f666944` (kopia: `origin/wip/wires-streaks`) | **WIP `a1d4e81`, NIE scalać bez weryfikacji**: kod drutów (`_ScaledScreenParams`, rdzeń ≥1,2 px, AA) i zacieków (`parapet_runoff`, UV1, `_RUNOFF`) jest, ale rendery nie potwierdzają efektu; część ścian `hall_wall` bez TEXCOORD_1; addendum ADR 0022 opisuje to jako działające — poprawić. Dowody `artifacts/world-fixes/wires-streaks/` |

Scalone też: auta v3 (`b8c93ca`; felgi LOD1 „rim_dusty” przyciemnione w kodzie, nieprzerenderowane). Konflikty w `Data/Regions/bialystok-industrial-c/generated/*.json`: bierz `--ours` i wygeneruj świat ponownie po scaleniu wszystkich gałęzi świata.

**Czerwony test na main:** `tests/gis/test_world_v31.py::test_frame_budget_with_forest_hlod` (po autach v3, LOD0 aut 3,3–3,6 k tris) — napraw uczciwie (dystanse LOD aut / oszacowanie), bez luzowania limitu.

## Recenzja r6 (docs/reports/visual/REVIEW-2026-11-10-r6.md) — top poprawek
1. **P0** build ≥ obecny main na A16 (Low) i nowe 37 kadrów gate3 + `truck-34`/`cab-dash` (stare kadry są sprzed nowego frontu i aut). Akceptacja `cab-dash` < 3 % luma ≤ 8 %.
2. **P0** druty WN (w toku). 3. **P1** kierownica beżowa przy niskim słońcu / czarna dziura na Low (CabInterior lighting). 4. **P1** naczepa: ciemna plama na firance, jasna łata pod naczepą. 5. **P1** szyba z zewnątrz, odbicie ziemi w lakierze drzwi, narożniki maski jak dziury; lakier matowy/kredowy. 6. **P1** auta: rozrzut brył/kolorów/kątów, wolne miejsca, ta sama liczba na Low i High. 7. **P1** farba linii na A16 ≤ 217 sRGB (teraz 246–249), kamera `g3a_eye_s0012` w geometrii, automatyczna kontrola 37 kadrów. 8. **P2** napis TRAKT na Low, gradient nieba High (pochmurne = biel 254), żywopłoty Bieżeństwa, ślady w dokach, kadry lusterek nowej kabiny.

## Następne kroki (kolejność)
1. Dokończ/scal dwie prace powyżej; przebuduj prefab (`Game.Editor.Setup.TruckAssetBuilder.BuildBatch`), testy EditMode + PlayMode + `uv run --project tools/worldgen --with pytest --with scipy pytest tests/ -q` + dotnet runner (`%LOCALAPPDATA%\Microsoft\dotnet\dotnet.exe test tools/physics-runner -c Release`).
2. Recenzja wizualna **r6** (`visual-critic`, Opus) nowego frontu, aut, wnętrza na klatkach URP i A16.
3. Za zgodą właściciela: S24+ High z nowym buildem (ADR 0046) — G3-A/G3-B, zrzuty kamer, klipy DK8 (jazda, nie statyczna kamera), 30-min test termiczny; sprawdź natywną rozdzielczość buildu (QHD+ vs FHD+).
4. Raport bramki 3 do końca (sekcje wizualne, werdykt) → APK do testu jazdy właściciela (D25).
5. Otwarte: auta — mleczne szyby LOD0 na High, brud progów, przody kanciaste; latarnie/słupki vs teren; ścianki terenu na skrzyżowaniach (ratchet 103); linie WN rwą się subpikselowo (min. szerokość w px); zacieki pod attyką hal; lusterko przednie celuje w niebo; przetarcia na kierownicy/fotelu (generator wnętrza); lusterka 3→2/klatkę na High (propozycja w ADR 0046); lamele grilla pochylone czołem w dół (geometria, zamiast obejścia w shaderze — ADR 0047 r3); szyba z zewnątrz wciąż „akwarium”.

## Narzędzia
Unity 6000.3.28f1 (`scripts/env.ps1`), Blender 4.2.9 `C:\Users\matma\AppData\Local\Programs\Blender4.2\blender-4.2.9-windows-x64\blender.exe -b` (**nigdy `Mesh.materials.clear()`**), .NET SDK user-local, uv/Python, ImageMagick, scrcpy, adb. Komendy w `CLAUDE.md`.

## Prompt startowy dla nowej sesji
Patrz `docs/owner/START-PROMPT.md` (do wklejenia jako pierwsza wiadomość).
