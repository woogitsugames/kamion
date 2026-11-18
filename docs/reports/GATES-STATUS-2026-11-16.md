# Stan bramek — 2026-11-16 (sesja 23, zadanie P15)

Baza: `origin/main` `65eab5bd5`. Autor: agent chmurowy sesji P (tylko dokument; bez Unity, bez Windows, bez telefonu — nic tu nie jest
mierzone, liczby są przepisane ze źródeł). Kryteria: `docs/03_ETAPY_I_BRAMKI.md` w wersji po D73/D74 (ADR 0260/0266).
Poprzednie zestawienia: `docs/reports/GATES-STATUS-S20.md`, `GATES-STATUS-S21.md` (oba mierzą bramki jeszcze telefonem — przed D73).
Każdy plik i sha z kolumny „Dowód” sprawdzony w `origin/main` (`git show origin/main:<plik>`, `git cat-file -e` + `merge-base --is-ancestor`).

**Zasada tego raportu (D73, docs/03 „Build jest prawdą”):** bramka jest zaliczona na PC dopiero z liczbami z playera Windows
zebranymi przez `scripts/pc-metrics.ps1`. **W `origin/main` nie ma ani jednego raportu `pc-metrics`** (brak `pc-report.*` w
`docs/reports/`, żaden raport ani HANDOVER nie cytuje przebiegu; nagłówek `scripts/pc-metrics.ps1:5` nadal mówi „SZKIC — … not run
yet”). Dlatego żadna bramka nie jest zaliczona na PC. Pomiary tierów z `INTEGRATION-2026-11-15-int-pc-s23.md` §4 (Low 535 / Medium 379
/ High 334 / Ultra 194 fps, RTX 5070) pochodzą z `build-windows.ps1 -Run` (55 s, bez powtórzeń, inne procesy Unity na maszynie) —
są informacyjne, nie bramkowe.

Klasy PC (D74) mierzymy **emulacją na RTX 5070** (D76): klasa „min” = `-Tier Low -Fps 30` 1920×1080, „zalecany” = `-Tier High -Fps 60`
1920×1080. Każdy taki wynik ma w raporcie adnotację **„emulacja”**. Przed publiczną obietnicą wymagań — pomiar na HD 630 / GTX 660 /
GTX 1660 (D76).

Legenda kolumny „Co jest”: **Z+M** zrobione i zmierzone (w playerze Windows) · **Z** zrobione, bez pomiaru w playerze Windows ·
**B** brak.

## 1. Tabela bramek

| Bramka | Warunek (docs/03 po D73) | Stan | Dowód (w `origin/main`) | Co jest / czego brakuje | Kto |
|---|---|---|---|---|---|
| **Etap 0** Fundament | Player Windows z czystego klonu jedną komendą, `Player.log` bez wyjątków, scena Boot zmierzona `pc-metrics`, PNG z harnessu obejrzany, `doctor` zielony; Android nadal się kompiluje | **OTWARTA** | `docs/reports/GATE-0.md` (telefon, „CZĘŚCIOWO”); ADR 0261 (merge `6182b3966`): build Windows, start bez wyjątków; `INTEGRATION-2026-11-15-int-pc-s23.md` §6 (exe `e28533ca3`, `BUILD_RESULT: Succeeded`, brak wyjątków); tag `v0.0-gate0` → `e421b00e3` | **Z:** build Windows jedną komendą (`build-windows.ps1`), player startuje, log bez wyjątków, harness VQA. **B:** build z czystego klonu na Windows, pomiar Boot `pc-metrics` (żadnego przebiegu), aktualny `GATE-0.md` pod PC, potwierdzenie, że APK się kompiluje po D73 (HANDOVER 16.11 04:4x: „APK/A16 po D73 niski priorytet”) | lider lokalnie |
| **Etap 1** Ciągnik (tor F) | §6 `docs/04` dla ciągnika solo zielone; brak dryfu/oscylacji, krawężnik bez teleportu; 3× 0–80 ±3 %; **wszystko w playerze Windows**, przy limicie 30 i 60 FPS te same liczby w tolerancji | **OTWARTA** | `docs/04` §6a (runner @ `31c1383ca`: 141 przebiegów / 833 kontrole PASS, `dotnet test` 287/287; 0–80 solo 14,06 s, powtarzalność 0,00 %); `docs/reports/PHYSICS-VALIDATION-2026-11-16.md` (merge `3d8a2e0aa`); `GATE-1.md` (werdykt „SZKIC — czeka na telefon”); `GATE12-PHONE-2026-11-14-A16.md` (A16, APK `77cfd94bf8` — sprzed D73 i sprzed 0201b `f9781a32b`) | **Z:** solver (runner .NET, bez Unity/PhysX), PlayMode z 13.11, autopilot `straight080` w grze. **B:** żaden przebieg w playerze Windows; brak porównania 30 vs 60 FPS; brak narzędzia „gate12” dla Windows (jest tylko `scripts/gate12-phone.ps1`); `GATE-1.md` nieprzepisany pod PC | lider lokalnie (pomiar), chmura (raport) |
| **Etap 2** Naczepa, pneumatyka, napęd (tor F) | Pełny pakiet §6 (pusty i 40 t), jackknife możliwy, brak eksplozji solvera, golden w `tests/golden/`; **feel test właściciela na PC** (pad/klawiatura; D77) z listą uwag i realizacją | **OTWARTA** | `docs/04` §6a (hamowanie 60→0 R13 24,10 m ≤ 36,7 m; 80→0 40 t 41,31 m; jackknife 87,45°); ADR 0280 (merge `14375caf6`); `docs/owner/FEEL-TEST.md` (merge `82cb109d6`); `GATE-2.md` („SZKIC”); D77, D79, D80 w `docs/11` | **Z:** pakiet w runnerze zielony **poza pierścieniem skrętu 96/53/WE** (`tests/physics/scenarios_expected_fail/ring_96_53_comb.json`; D79 7,60 m przyjęte, ale **niewdrożone** — `art-source/truck/dims.json:48` nadal −7,70 m); instrukcja feel testu gotowa. **B:** feel test właściciela (4 manewry), przebiegi zestawu w playerze Windows, jackknife wg ADR 0228 (#113 nie w main), D80 (pad) niewdrożone | właściciel (feel test), lider lokalnie (D79, integracja H3, build, pomiar) |
| **Tor A** Ciężarówka premium (przed Etapem 5) | Checklista `docs/07` §6 zaliczona; zrzuty z playera Windows (High i Ultra); budżet tris/draw calls/pamięci klasy „zalecany”; 🔒 LOD-y telefonu zostają | **OTWARTA** | `docs/reports/visual/truck-A7/` (kroki A2–A8 wizualnie); `GATES-STATUS-S20.md` §4 (ocena kryteriów A.1a–A.3); decyzje D16/D17/D19/D28/D29/D47 | **Z:** model A7 + naczepa A8 (rendery edytora, kadry z telefonu). **B:** raport bramki toru A (`GATE-A*.md` nie istnieje), ocena checklisty `docs/07` §6, zrzuty z playera High/Ultra, pomiar `pc-metrics` z ciężarówką w kadrze, akceptacja gotowego modelu; model Blendera po D79 (ADR 0280 §5) | lider lokalnie (Blender, rendery z playera), właściciel (akceptacja) |
| **Etap 3** Próbka jakości (anty-slop) | Side-by-side ze zdjęciami miejsca, checklista `docs/06` §5, akceptacja kierunku przez właściciela. Na PC tylko pomiar kontrolny „zalecany” + pary zdjęcie\|render z playera High | **ZALICZONA** (telefon, D57) | `GATE-3.md` (merge `263847db7`; A16 Low `3ffbf13881`); utrzymanie na `af2570fccd` (`6624550e4`); D57 w `docs/11:78` | **Z+M (telefon):** A16 Low G3-A/G3-B. **B na PC:** pomiar kontrolny `pc-metrics` (region `c`, High/60, klasa „zalecany”, emulacja), pakiet par z playera High — nie zaliczają, tylko sprawdzają brak regresji | lider lokalnie |
| **Etap 4** Pipeline świata 2×2 km | Regeneracja 2×2 km jedną komendą, override'y przeżywają reimport, przejazd całości bez wpadnięcia pod teren, zero dziur kolizji, odchyłka osi w tolerancji, raport `low_confidence`; **czas ładowania regionu w playerze Windows** (`run.json: regionLoad`) w budżecie klasy | **OTWARTA** (bez raportu) | `GATES-STATUS-S20.md` §6 (kryteria 4.1–4.7); regeneracje s23 w HANDOVER (np. `feb542757` rail: jedna regeneracja 17 kafli); `docs/reports/WORLDGEN-PERF-2026-11-16.md` | **Z:** generator, 21 regionów w buildzie `d67-full`, fidelity, QA. **B:** `GATE-4.md`, regeneracja jedną komendą w gicie, przejazd całej sieci kafla, test dziur kolizji, `regionLoad` z `pc-metrics`. Ryzyko procesu: HANDOVER 16.11 12:2x — `Data/raw/derived` w worktree był kopią, build `build-s23` zatrzymany | lider lokalnie + chmura D |
| **Etap 5** Vertical slice | Slice 3× bez soft-locka; 30 min w playerze Windows bez crasha z `pc-metrics` (klasa „zalecany” i „min”), raport wizualny z playera (dzień/zmierzch/deszcz/noc) | **NIEROZPOCZĘTA** | — (wymaga bramki toru A i Etapu 4) | Częściowo istnieją elementy zakresu (HUD PC ADR 0265, menu i tiery ADR 0269, start poza zaporami ADR 0262), ale bramka nie ma raportu ani pomiaru; crash przy zamykaniu playera (`FIX-2026-11-16-pc-shadows-s23.md:66`) | — |
| **Etap 6** Cały Białystok | Per dzielnica: checklista, koszt produkcji, brak regresji `pc-metrics` (ta sama trasa i maszyna), ciągłość sieci | **NIEROZPOCZĘTA** | — | **B:** wszystko | — |
| **Etap 7** Obrzeża + DLC | Przejazd przez granicę paczek bez przycięcia (0 klatek > 100 ms w `pc-metrics`), testy DLC z `docs/10` | **NIEROZPOCZĘTA** | — (PR #112 paczki regionów otwarty wg `OPEN-DECISIONS.md`) | **B:** wszystko; kanał dystrybucji paczek PC = decyzja właściciela (`docs/10` §3a) | właściciel (decyzja) |

### Walidacja fizyki bez Unity a wymóg „w playerze Windows”
Runner (`tools/physics-runner`) kompiluje rdzeń fizyki gry w czystym .NET (ADR 0004) — to mocny dowód poprawności solvera, ale **nie
spełnia warunku bramek 1–2**: nie sprawdza PhysX, kolizji ze światem, rampy (§6.10), kosztu kroku w buildzie (§6.12) ani niezależności
od FPS w playerze. `docs/04` §6a sam to wymienia („Niesprawdzone bez Unity…”). Status bramek 1–2 = **Z**, nie **Z+M**.

## 2. Najbliższe 5 kroków do następnej bramki (Etap 2, potem Etap 1 i 0 tym samym exe)

1. **Lider lokalnie — świeży exe.** Po odbudowie `Data/raw/derived` i integracji H3 (#113 → #118 → #117 → #141 → #142) oraz D79
   (dane naczepy 7,60 m wg ADR 0280 §5, scenariusz `ring_96_53_comb` z oczekiwanego błędu na PASS):
   `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64` → `pwsh scripts/build-windows.ps1 -Regions d67-full`.
2. **Lider lokalnie — pierwszy przebieg `pc-metrics` (skrypt nigdy nie uruchomiony) na Boot = dowód Etapu 0:**
   `pwsh scripts/doctor.ps1`, potem
   `pwsh scripts/pc-metrics.ps1 -Exe artifacts/win/kamion-<ver>-<sha>-regions/Kamion.exe -Tier High -Fps 60 -Width 1920 -Height 1080 -DurationSeconds 90 -Class zalecany`
   i to samo z `-Tier Low -Fps 30 -Class min` (adnotacja „emulacja”, D76). Wcześniej poprawić `referenceMachines`/`gate_eligible`
   (rozbieżność R1), inaczej parser oznaczy każdy wynik jako „nie zalicza bramki”.
3. **Lider lokalnie — Etap 1 i 2 w playerze, przy 30 i 60 FPS** (autopilot `straight080`, telemetria jak w `gate12-phone.ps1`):
   `pwsh scripts/pc-metrics.ps1 -Exe <exe> -Scene DrivingLab -Extra autopilot=straight080,speed=80,trailer=solo,telemetry=1 -Tier High -Fps 60 -DurationSeconds 70 -Class zalecany`
   ×3, potem `-Fps 30`, potem `trailer=empty` i `trailer=40` (120 s); analiza CSV `persistentDataPath/telemetry/drive-*.csv`:
   `uv run --project tools/perf python scripts/gate12_telemetry.py <katalog>` (UNVERIFIED: skrypt pisany pod układ katalogów z telefonu).
4. **Właściciel — feel test bramki 2 na tym exe** wg `docs/owner/FEEL-TEST.md`: `Kamion-okno.cmd -scene DrivingLab -trailer 40`,
   4 próby (ruszanie pod górę 40 t, hamowanie awaryjne, okrąg R50/rondo, cofanie pod rampę), każda klawiaturą i padem; formularz uwag.
5. **Chmura — raporty:** przepisać `GATE-0/1/2.md` pod PC z liczbami z kroków 2–3 (klasa, emulacja, tier, rozdzielczość,
   p50/p95/p99, RAM/VRAM) i listą uwag z kroku 4 → realizacja (ADR 0201b/0228/0264); po zaliczeniu tag w git i `docs/STATUS.md`.

## 3. Rozbieżności (docs/03 ↔ raporty bramek ↔ HANDOVER ↔ decyzje)

- **R1 — D76 nie wdrożony w narzędziu i w docs/03.** `docs/03:25-27` i `ADR 0266` nadal: maszyna dev „nie zalicza klasy min ani
  zalecany”, dopóki właściciel nie zaakceptuje metody zastępczej — D76 ją zaakceptował. `tools/pcperf/budgets/pc-budgets.json:8`
  `"referenceMachines": []`, a `tools/pcperf/pc_metrics.py:333` liczy `gate_eligible = reference_machine and PASS` i drukuje
  „nie zalicza bramki” (`:366`). Brak pola „emulacja”.
- **R2 — `pc-metrics.ps1` nigdy nie uruchomiony** (`scripts/pc-metrics.ps1:5` „SZKIC … not run yet”, ADR 0266 „Walidacja:
  nieuruchomione”), a HANDOVER 16.11 04:0x pisze „tiery PC zmierzone” — to pomiar `build-windows.ps1 -Run`, nie bramkowy.
- **R3 — `OPEN-DECISIONS.md`** nadal ma w indeksie OD-001/OD-002/OD-003 jako otwarte, choć rozstrzygnęły je D76/D77/D78; nagłówek
  sprawdzony tylko do D75.
- **R4 — D79 przyjęte, niewdrożone:** ADR 0280 ma status „Proposed”; `art-source/truck/dims.json:48` = −7,70 m; `docs/04` §6a
  opisuje pierścień jako znaną porażkę. HANDOVER 16.11 12:5x: wdrożenie po integracji H3.
- **R5 — D80 a feel test:** D80 każe ocenić warstwę Back+przycisk w feel teście, ale `FEEL-TEST.md` §1 nadal ma „R = Back” na padzie,
  a wdrożenie D80 jest zlecone chmurze H r4 po H3 — na obecnym exe nie da się go ocenić.
- **R6 — Exe do feel testu:** najnowszy exe w HANDOVER to `e28533ca31` (bez spawn-fix r2, ronda r3, cieni, H3/#113 jackknife);
  build `build-s23` zatrzymany (12:2x). `FEEL-TEST.md` mówi o „najnowszym exe” i ADR 0228 (#113 nie w main).
- **R7 — Raporty bramek sprzed D73:** `GATE-0.md`, `GATE-1.md`, `GATE-2.md` mają werdykty „czeka na telefon”; `GATES-STATUS-S21.md`
  ocenia Etapy 1–2 jako „CZĘŚCIOWO” na podstawie A16. Po D73 kryterium to player Windows — oceny są nieaktualne co do platformy.
- **R8 — Proces po bramce (`docs/03`: tag + `docs/STATUS.md` + `docs/ROADMAP.md`):** jedyny tag `v0.0-gate0` (`e421b00e3`) stoi na
  bramce 0, która jest „CZĘŚCIOWO”; zaliczona bramka 3 (D57) nie ma tagu; `docs/STATUS.md` ostatnio zmieniony 2026-11-09
  (`6694783ad`, mówi o PIN-ie A16); `docs/ROADMAP.md` nie istnieje.
- **R9 — Tor A, profil telefonu:** `docs/03` (🔒 tor A) każe trzymać budżet „profilu Medium (Samsung A)”, a D49 ustawił A16 na Low —
  sprzeczność zgłoszona już w `GATES-STATUS-S20.md` §4, nadal nierozstrzygnięta.
- **R10 — Liczby runnera w dwóch miejscach:** `PHYSICS-VALIDATION-2026-11-16.md` (135 przebiegów / 789 kontroli, `dotnet` 279/279)
  i `docs/04` §6a (141 / 833, 287/287) — nie sprzeczność (§6a jest późniejszy, `31c1383ca`), ale raport bramki 2 powinien cytować §6a.
  HANDOVER 12:5x: `tests/physics` 18 passed, 14 errors (wymagają zbudowanego świata) — niezweryfikowane po odbudowie derived.
