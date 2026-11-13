# Integracja świata s16b — końcowa regeneracja `bialystok-industrial-c` (2026-11-13)

Gałąź `world-int-s16b` z `origin/main` 227c2b6f7 (scalone 0153, 0154, 0155, 0159, 0160). Jedna pełna regeneracja wg łańcucha
z `WORLD-INTEGRATION-2026-11-13-s16.md`: zestawy PBR → `build_world` (z grafem tras) → `export-route` → `fidelity/run.py` →
`import-region` → `ImpostorTrimBake.RunBatch` → testy → kamery kontrolne → pary SBS. Generatory bez zmian.
Dowody: `artifacts/world-int-s16b/` (repo główne): `logs/`, `pairs/Low-overcast|Low-clear` (42 + 42, ≤ 960 px), `cmp/`
(0160 nad s16b), `view/` (kamery kontrolne), `budget-low.txt`, `stats-Low-clear.txt`, `stats-High-clear.txt`.

## Łańcuch i liczby

| Krok | Wynik |
|---|---|
| `build_all.py` (zestawy PBR) | exit 0, 452 s (`asphalt_detail_photo` pominięty: brak zdjęcia źródłowego w worktree, jak dotąd) |
| `build_world.py` | exit 0, 504 s; `fallback=True` w logu: **0** |
| — spójność dróg | **65** (`arrow_no_exit` 7, `lane_blind_end` 54, `marking_off_carriageway` 2, `obstacle_in_lane` 2; na trasie `lane_blind_end` 1) — jak 0159 / 0160 |
| — ściany terenu > 0,15 m | **4**, max 0,345 m — bez zmian |
| — far_field | High 118 588 / Low 24 548 — bez zmian |
| — zieleń (0154) | żywopłoty 4, 94,3 m², `stale: []` — **już były w `generated/` main** (bez różnicy) |
| `export-route.py` | 1199 punktów, 2398 m — `route_start.json` bez zmian |
| `fidelity/run.py` | exit 0, 217 s; `fidelity_qa.json` zmienione tylko skróty wejść |
| `import-region.ps1` | `IMPORT_RESULT: OK chunks=64 corridor=41 tiers=Low+High` |
| `ImpostorTrimBake.RunBatch` | 18 impostorów, średnio 37 % quada, 0 pominiętych |
| pytest `tests/gis -q` | **1001 passed, 3 xfailed, 0 failed** (16:14); `test_every_gate3_sign_is_placed` **zielony** |
| EditMode `scripts/test.ps1` | **493 / 493 passed** |

Zmienione pliki (wobec main 227c2b6f7): `generated/streetscape_qa.json` (znaki `gate3_sign`: A-30 ×2 na `at_en` 0160 —
E −255,3 N −205,8 i E −262,8 N −216,3; nowe `andersa-slip-merge-a7` E −360,6 N −165,7 i `andersa-link-median-d1`),
`generated/world_manifest.json` (hash `overrides.yaml`, liczba prototypów propów 1472 → 1474, skróty `street_props`),
`generated/fidelity_qa.json` (skróty wejść), `art-source/world/props/street_props.glb` (LFS; prototypy A-7 i D-1).
Chunki GLB i reszta `generated/` identyczne z main — czyli w main brakowało tylko znaków 0160; zieleń 0154 i bariery 0159
już tam były.

## Pary SBS (Low-overcast + Low-clear, 42/42 każda)
Render `0029eb520b`, `pwsh scripts/sbs-low-pairs.ps1` (preflight OK). Pierwsze złożenie par przerwało się, bo worktree nie miał
`artifacts/sbs-gate3/rectified` (zdjęcia porównawcze, poza gitem) — skopiowane z main, pary złożone ponownie `-SkipRender`.
Surowych renderów 0159 / 0160 nie ma (tylko pary JPG), więc porównanie = średnia różnica bezwzględna połowy renderu z dolnym
wierszem par `g3a-0160/pairs-final` i `barriers-0159/pairs` (`tools/pairdiff.py`), potem oglądanie.

Obejrzane (pary + zestawienia 0160 nad s16b w `cmp/`):
- **Znaki 0160 w kadrze:** 275528 — oba A-30 z tabliczką po obu stronach portalu (jak w 0160, x ≈ 0,17 / 0,82); 1528935 — A-7
  ostrzem w dół przy włączeniu łącznicy; 4312632 — D-1 w pasie dzielącym przy x ≈ 0,33, nadal widoczny prawie z boku (Open z 0160).
- **Różnice vs 0160** (MAE overcast; reszta < 2): 751431 (7,0) — ściana z wielokątnych paneli z fugami zamiast kamienia, jak
  na zdjęciu; 962702 (3,7) i 810896 (3,1) — bariera W na pierwszym planie; 3678296 (2,5) — bariera w pasie dzielącym;
  482392 — bariera W biegnie po skosie od lewej jak na zdjęciu (koniec „kikuta w powietrzu” z recenzji s16). To commity
  0159 after4, których render 0160 nie zawierał. **Poprawy, nie regresje.**
- **Vs 0159** (duże MAE na 177786, cm92458760, 1528935, 1259231, 201270, cm109685822, 339463, 4312632, 504348, 3970163,
  2818555) — to nowe pozy 0160; obejrzane 1801374 i 182011 (pozy bez zmian): bez różnic, ciemne słupki ekranów 0159 zostały.
- 494288 (ekran na łuku): ciemne słupki, ekran, czerwona kapa — jak 0159.
- 297817: bez zmian vs 0160.
- Plamy słońca (0155): na kamerach Low-clear/High-clear (route-putry-approach, g3b-eye-s1482, photo-biezenstwa-ground) cienie
  ciągłe, bez plam.

Nie zrobiono: niezależny `visual-critic` (ocena powyżej jest moja), zrzuty z telefonu.

## Budżet Low (48 kamer kontrolnych, Low-clear, vs `artifacts/barriers-0159/budget-low.txt` kolumny „po”)
Pełna tabela: `artifacts/world-int-s16b/budget-low.txt` (draws = renderer + cienie + instancje; szacunek edytora przed SRP batching).
- draws: od **−2** (fire-station-ref7197) do **+3** (route-putry-approach: instancje 163 → 166 — nowe znaki); +2 putry-above,
  +1 driver-andersa / fire-station-above / -route / g3b-rondo-putry-approach; reszta 0 lub −1.
- trójkąty: **+0,0 %** na 47 kamerach, **+0,3 %** putry-above (z lotu ptaka).
Zgodne z 0160 (max +3 draws / +0,3 % tris vs 0159). Telefon jest prawdą — APK Low A16 po scaleniu (lider).

## Gotowość
Gotowe do scalenia: `generated/*` i `street_props.glb` z tej gałęzi zastępują wersję z 0159 (`--ours` w 227c2b6f7).
Po scaleniu w main: `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` (import w main nie odpowiada tej regeneracji),
potem `visual-critic` na `artifacts/world-int-s16b/pairs` i APK Low A16.

## Co otwarte
1. 4312632: tarcza D-1 widziana prawie z boku (zdjęcie ok. 45°) — obrót tarczy w pasie dzielącym (0160 Open).
2. Pozostałe Open z 0160 (pozy C 1259231 / 182011, 149248 tablica za duża, cm109685822 `yard_behaton`, cm92458760 klomb/EC).
3. `asphalt_detail_photo` w `build_all.py` pomijany bez zdjęcia źródłowego `Data/photos/nowe/...` (jak w poprzednich integracjach).
