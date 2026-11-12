# STATUS g3b-lowread (ADR 0127)

## 1. Worktree + baseline + kod (2026-11-12)
Worktree `.claude/worktrees/g3b-lowread` (gałąź `g3b-lowread` z main 31e54e00), dane skopiowane, junctiony Data/raw/{gugik,osm,refs,mapillary,fab}, Library skopiowane.
Baseline = świat main (regen d) bez przebudowy: 40 SBS Low-overcast + Low-clear w `artifacts/g3b-lowread/baseline/renders/`.
Kod: bramownica LOD1 = kratownica (było: 2 pudła), polityka LOD portal/tablice OB [100,800]/[50,800] (Low: 50/400 m, było 25/125), tablice stoją na belce (+0,25 m), tył tablic OB gładki; słup WN 3 poprzeczniki + LOD1 grubszy + pylon_steel ciemny, 6 przewodów + odgromowy na ramionach; ekrany: słupy 0,22 m (wiadukt co 2 m), szkło `screen` (horyzont nieba, film, linie na wiadukcie; keyword _SCREEN_SHEET). Testy `tests/gis/test_g3b_lowread.py` 9 passed.
NASTĘPNY KROK: `pwsh artifacts/g3b-lowread/run-build.ps1 -Log build-world-1.log; pwsh artifacts/g3b-lowread/run-import.ps1 -Log import-1.log; pwsh artifacts/g3b-lowread/run-sbs.ps1 -Name after1`

## 2. Build 1 + ADR draft (2026-11-12 ~13:50)
build_world 1 OK (522 s, pylon 26, glazed 616 m, gantries stale 0). Import 1 padł na `ArrayMemoryError` w build_all.py (brak RAM, przejściowe) -> ponowienie importu + SBS after1 biegnie w tle (pętla do 3 prób).
Dodane: strefa glazed dla odsuniętego ekranu przy 1801374 (ortho: świat OK, rozjazd = FOV/poza SBS), ADR 0127 draft, `ortho-check.py`, `proto-preview.py` (sylwetki LOD0/LOD1). Strefa glazed weszła po starcie builda 1 -> potrzebny build 2.
NASTĘPNY KROK: `pwsh artifacts/g3b-lowread/run-import.ps1 -Log import-1.log; pwsh artifacts/g3b-lowread/run-sbs.ps1 -Name after1; bash artifacts/g3b-lowread/make-pairs.sh after1; python artifacts/g3b-lowread/stats-diff.py after1` -> obejrzeć pary (837235, 381800, 297817, 3678296, 494288, 1801374), potem build 2 (`run-build.ps1 -Log build-world-2.log`), pytest (`run-pytest.ps1`), EditMode (`run-editmode.ps1`), SBS Low-clear (`run-sbs.ps1 -Name after -Lighting clear`).

## 3. after1 obejrzane, cykl 2 uruchomiony (~14:20)
Import 1 OK po ponowieniu; SBS Low-overcast after1 (40 kadrów), pary `pairs-after1/`. G3-B (20 kamer, stats-diff-after1.txt): draws razem +0..+13, mediana +1; tris statyczne +1..+3k, instancje +0..+4k.
Obejrzane: 837235 / 297817 / 275528 - portal czyta się jako kratownica (297817: było pełna rama), tablice na belce, tyły gładkie; 3678296 - słup WN ciemny, 3 poprzeczniki, przewody; 494288 - ekran = jasna płaszczyzna z grubymi ciemnymi słupami i liniami. 1801374 bez zmiany (strefa glazed dopiero w buildzie 2).
W tle: `run-all-2.ps1 -Name after -Tag 2` (build 2 -> fidelity -> pytest gis+gate3 || import -> SBS overcast+clear -> EditMode), znacznik `all-2.done`.
NASTĘPNY KROK: po `all-2.done`: `bash artifacts/g3b-lowread/make-pairs.sh after; python artifacts/g3b-lowread/stats-diff.py after > artifacts/g3b-lowread/stats-diff-after.txt; tail artifacts/g3b-lowread/pytest-gis.log artifacts/g3b-lowread/editmode.log` -> ADR Results, LICENSES, kopia dowodów do main.

## 4. Rozszerzenie zakresu (recenzja s12-0130) + merge main (~14:45)
Scalono main (552257d4; konflikt tylko LICENSES - unia). Cykl 2 sprzed merge'a zatrzymany w kolejce (nie wystartował).
(1) Wysokość portalu: ortofoto hi-res GUGiK (`crops/ortho-gantry-hr.jpg`): belka 14,0 m (reguła dawała 16 m), cień słupa 6,1 m; zdjęcie 275528: (wierzch nad horyzontem)/rozpiętość = 0,354 -> ~6,2-6,5 m przy 14 m. Teza "8,5-9 m" NIE potwierdzona; proporcja H/rozpiętość była dobra, portal był o 14 % za szeroki -> `columns_en` (rozpiętość 14 m), H z reguły 7,0 m.
(2) Ekran Tysiąclecia (1801374): strefy glazed z `height_m: 5.2`, pas 2,2 m (odczyt ze zdjęcia wzgl. cokołu 0,6 m), odsunięty ekran przeszklony od narożnika.
Baseline dla nowych póz: `baseline-newpose/` = kopia `artifacts/sbs-poses/final/renders` (main przed 0127).
W tle: `run-all-2.ps1 -Name after -Tag 2`, znacznik `all-2.done`.
NASTĘPNY KROK: po `all-2.done`: `cd artifacts/g3b-lowread; BASE=baseline-newpose OUT=pairs-after bash make-pairs.sh after; BASE=baseline-newpose LIGHT=Low-clear OUT=pairs-after-clear bash make-pairs.sh after; BASE=baseline-newpose python stats-diff.py after > stats-diff-after.txt; tail pytest-gis.log editmode.log`

## 5. STOP na limicie (~15:00) - stan do wznowienia
Build 2 OK (`build-world-2.log`, exit 0). W TLE DZIAŁA `run-all-2.ps1 -Name after -Tag 2`: fidelity (`fidelity.log`) -> pytest gis+gate3 (`pytest-gis.log`) pod slotem heavy; równolegle `run-unity-2.ps1`: import (`import-2.log`, do 3 prób) -> SBS Low-overcast + Low-clear do `after/renders/` -> EditMode (`editmode.log`); log zbiorczy `all-2.log`, `unity-2.log`; koniec = plik `all-2.done`. Sloty zwalniają się same (finally).
Nie scommitowane celowo: `Data/Regions/.../generated/*`, `art-source/world/props/*` (regeneracja builda 2 - scommitować po zielonych testach jako `chore(world): regenerate`).
ADR 0127 kompletny poza sekcją Results (liczby po cyklu 2); LICENSES gotowe. Otwarte: orientacja ramion słupa WN vs zdjęcie (UNVERIFIED, w ADR).
NASTĘPNY KROK: gdy istnieje `artifacts/g3b-lowread/all-2.done`: `cd artifacts/g3b-lowread; BASE=baseline-newpose OUT=pairs-after bash make-pairs.sh after; BASE=baseline-newpose LIGHT=Low-clear OUT=pairs-after-clear bash make-pairs.sh after; BASE=baseline-newpose python stats-diff.py after > stats-diff-after.txt; tail -3 pytest-gis.log editmode.log` -> obejrzeć pary (837235, 381800, 297817, 3281350, 275528, 3678296, 494288, 1801374) -> wpisać Results do `docs/adr/0127-g3b-low-readability.md` -> `git add` generated + commit -> `robocopy artifacts\g3b-lowread C:\Users\matma\Documents\Claude\kamion\artifacts\g3b-lowread /E` -> raport końcowy.

## 6. Wznowienie s13 (~16:55)
Cykl 2 zakonczony: EditMode 382/382, pytest gis+gate3 802 passed / 1 failed (stara asercja "LOD1 = two boxes" w test_street_r9 - poprawiona na budzet kratownicy <= 300 tris), SBS Low overcast+clear 20 kadrow G3-B, draws G3-B min/med/max -17/-1/+11 (stats-diff-after.txt). Scalono main bedc52d12 bez konfliktow (generated ours) -> b69cc5a8d.
W TLE: `run-all-2.ps1 -Name final -Tag 3` (build 3 -> fidelity -> pytest || import -> SBS -> EditMode), znacznik `all-3.done`.
NASTEPNY KROK: po `all-3.done`: `cd artifacts/g3b-lowread; BASE=baseline-newpose OUT=pairs-final bash make-pairs.sh final; BASE=baseline-newpose LIGHT=Low-clear OUT=pairs-final-clear bash make-pairs.sh final; BASE=baseline-newpose python stats-diff.py final > stats-diff-final.txt; tail -3 pytest-gis.log editmode.log` -> Results w ADR 0127 -> commit generated -> robocopy do main.
