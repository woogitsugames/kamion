# STATUS g3b-r2 (ADR 0139)

## 1. Kod poprawek (2026-11-12 ~18:05)
Worktree `.claude/worktrees/g3b-r2`, galaz `g3b-r2` (z main a6cfe38a). Narzedzia skopiowane z g3b-lowread do `artifacts/g3b-r2/` (owner claude-g3b-r2). "Przed" = `.claude/worktrees/g3b-lowread/artifacts/g3b-lowread/final/renders`.
Kod: ekran wiaduktu `noise_glass_lined` haze 0.06->0.02, linie 22->44/v (okres 0,05 m), sila 0.45->0.30, duty 0.25->0.12, `haze_color` ciemniejszy (importer czyta); slupy Tysiaclecia `noise_post_dark` przez `post_mat` w 4 strefach; portal Andersa: `size_m` tablic 3,75x0,82 i 3,8x1,2 m + `beam_depth_m` 0,55 (odczyt z 275528; H wyjdzie ~6,4 m); slup WN: ramiona 3,3->4,3 m (ortofoto hi-res GUGiK `crops/ortho-pylon-hr.jpg`: 8,6 m koniec-koniec, os ramion azymut ~322 st. = zgodna z danymi; kadr 3678296 widzi je ~10 st. od osi -> roznica to poza SBS, nie swiat).
3281350: jedna tablica na zdjeciu z 2017, dwie na 2019/2020/2024 - stan nowszy zostaje (bez zmiany).
Testy: `tests/gis/test_g3b_r2.py` 4 passed 1 skipped (przed buildem), test_g3b_lowread zielony.
OTWARTE: artefakt "duchow" drzew na szybie - diagnoza wymaga Unity (PHONE_RUN aktywny od 17:34).
NASTEPNY KROK: `pwsh artifacts/g3b-r2/run-all-2.ps1 -Name after -Tag 1` (build -> fidelity -> pytest || import -> SBS Low overcast+clear -> EditMode), potem `cd artifacts/g3b-r2; BASE=../../../g3b-lowread/artifacts/g3b-lowread/final ...make-pairs`.

## 2. Build 1 OK (~17:55)
build_world 527 s exit 0; portal Andersa 14 m / H 6,1 m (tablice dolem 5,2-5,5 m), strefy stale 0; test_g3b_r2 5 passed. Regeneracja generated/* jeszcze nie scommitowana (po zielonym cyklu).
W TLE: import-1 -> SBS Low overcast -> SBS Low clear do `artifacts/g3b-r2/after/renders` (czeka na slot Unity / PHONE_RUN), znacznik `artifacts/g3b-r2/cycle1.done`.
NASTEPNY KROK: po `cycle1.done`: `cd artifacts/g3b-r2; BASE=../../../g3b-lowread/artifacts/g3b-lowread/final OUT=pairs-after bash make-pairs.sh after; BASE=../../../g3b-lowread/artifacts/g3b-lowread/final LIGHT=Low-clear OUT=pairs-after-clear bash make-pairs.sh after` -> obejrzec 494288 (duchy!), 810525, 1801374, 275528, 3678296.

## 3. Pary cycle1 obejrzane + diagnoza "duchow" (s14, 18:31)
Pary `pairs-after(+clear)` (20+20): 494288/810525 szklo czyste z cienkimi liniami, 1801374 slupy ciemne, 275528 tablice nizsze/wezsze jak na zdjeciu, 3678296 ramiona dluzsze (poza bez zmian).
"Duchy" drzew: `run-ghost.ps1` (ablacje Low overcast 494288): rq_a2c=0 i rq_msaa=1 bez zmiany, rq_hlod=0 usuwa -> to przeswity nieba w sylwetce lesnego HLOD (karty krawedzi) widziane przez szybe, NIE blad kolejnosci/alfy szyby. Przed 0139 mleczny film + grube linie robily z nich jasne plamy; po 0139 czytaja sie jak luki w koronach. Dowod: `crops/ghost-ablation-494288.jpg`.
NASTEPNY KROK: `git merge main` (generated/glb/meta --ours) -> `pwsh artifacts/g3b-r2/run-all-2.ps1 -Name final -Tag 2`.
