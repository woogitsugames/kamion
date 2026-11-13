# Integracja świata s16 — `bialystok-industrial-c` (2026-11-13)

Gałąź `world-int-s16` z `origin/main` 55e66520d (po 0146, 0152, 0156, Mistral r4/r5). Jedna pełna regeneracja: zestawy PBR →
`build_world` (z grafem tras, krok M27) → `export-route` → `fidelity/run.py` → `import-region` → `ImpostorTrimBake.RunBatch` →
testy → kamery kontrolne → pary SBS. Generatory bez zmian. Dowody: `artifacts/world-int-s16/` (logi, `before/` i `after/`
kamery kontrolne, `budget-low.txt`, `cmp/`, `pairs/Low-overcast`, `pairs/Low-clear`).

## Łańcuch i liczby

| Krok | Wynik |
|---|---|
| `build_all.py` (zestawy PBR, wszystkie tiery) | exit 0, 516 s |
| `build_world.py` | exit 0, 623 s; 64 GLB: 498 MiB High / 169 MiB Low (main: 498,9 MiB chunków — bez zmian); `fallback=True` w logu: **0** (Megascans: 15 zasobów, 957 zamian odwodnienia, 320 propów) |
| — spójność dróg | **65** (`arrow_no_exit` 7, `lane_blind_end` 54, `marking_off_carriageway` 2, `obstacle_in_lane` 2; na trasie `lane_blind_end` 1) — jak main |
| — ściany terenu > 0,15 m | **4**, max 0,345 m — jak main |
| — far_field | High 118 588 / Low 24 548 |
| — overrides | 105 zastosowanych, 0 nieaktualnych |
| — graf tras GPS (KRTG) | przebudowany w `build_world`; plik identyczny z main (już zregenerowany przy Mistral r5) |
| `export-route.py` | 1199 punktów, 2398 m — `route_start.json` bez zmian |
| `fidelity/run.py` | exit 0, 255 s; zmieniły się tylko skróty wejść (`barrier_audit.py`, `build_world.py`, `standards.py`); IoU miejsc, lane_into_island (0 na trasie), krawędź vs ortofoto bez zmian |
| `import-region.ps1` | `IMPORT_RESULT: OK chunks=64 corridor=41 tiers=Low+High` (import odpalił ponownie `build_all.py`: „2 missing for Medium” — znane, nie blokuje) |
| `ImpostorTrimBake.RunBatch` | 18 impostorów, średnio 37 % quada, 0 pominiętych |
| pytest `tests/gis -q` | **935 passed, 4 xfailed**, 0 failed (15 min). Dotąd czerwone na main: `test_every_gate3_sign_is_placed`, `test_report_not_stale` — **zielone** |
| EditMode `scripts/test.ps1` | **467/467 passed** |

Zmienione pliki generowane: `streetscape_qa.json`, `world_manifest.json`, `far_field_qa.json`, `fidelity_qa.json`,
`viaduct_putry_underdeck.spec.json`, `bialystok-industrial-c-far-field.manifest.json`, `props_meta.json`, `street_props.glb`
(LFS; zmiany znaków M24/M25 i słupów). Różnica jest mała, bo 0146 (`acf5a411e`) zregenerował już większość na drzewie main 700517b22.

### xfail M29 (`tests/gis/test_barrier_ends.py`)
Audyt po regeneracji: `deck_run_ends_free` **32 → 2** (z 42 biegów), `rail_row_overlaps` 0, `closure_overlaps_lt_0_5m` 1.
Nie spadło do 0, więc xfail zostaje; zaktualizowałem tylko opis (liczby zmierzone). Pozostałe wolne końce pomostu:
`c:w177895177 L bridge` (E 669,4 N −781,9, wiadukt Bieżeństwa) i `c:w240542867 R approach` (E −739,6 N 74,1, łącznica DK8).
Para zapór edge-west (Maczka × trunk_link, 0,20 m) — zgodnie z opisem, osobne zadanie w C# `WorldEdgeBuilder`.

### Po scaleniu origin/main (Mistral r6, 68e5fc39f) w trakcie integracji
r6 zmienia `roads/standards.py` (`SHOULDER_W["GP"]` 1,25 → 0,75) i `roads/network.py` (stała 0,75 → `SHOULDER_W["GP"]`) —
wartość w profilu bez zmian, ale oba pliki są wejściami `fidelity_qa`. Merge bez konfliktów, ponownie `build_world` →
`export-route` → `fidelity`: **GLB, manifest, QA, graf tras identyczne bajtowo z pierwszym przebiegiem** (te same liczby: 65 / 4 /
far_field 118 588 / 24 548 / 498+169 MiB); zmieniły się tylko skróty wejść w `fidelity_qa.json`. Import Unity nie wymagał powtórki.
EditMode na scalonym drzewie: **467/467**. pytest gis na scalonym drzewie: **971 passed, 4 xfailed, 0 failed** (14:46; xfail: 2× M29, `p21_hatch` czeka na właściciela, `test_target_edge_p95` cel ADR 0075). Walidator świata M37 (`validate/run.py`, `--prev` = raport w repo): 558 znalezisk, 56 error — identycznie jak raport w repo (`artifacts/world-int-s16/validator/`).

## Uwaga dla lidera: import w main był stary
`game/Assets/_Generated/World/bialystok-industrial-c` w main jest z **2026-11-12 14:03** (log `import-region-…-173604` w
main ma 17:36). APK `kamion-0.1.0-fbb610dd30.apk` i wcześniejsze z main zawierały świat sprzed 0141 r6d/0144/0132/0146/M24.
Po scaleniu tej gałęzi trzeba zrobić `import-region` w main przed APK. „Przed” w tabeli budżetu = ten stary import.

## Budżet Low (kamery kontrolne Low-clear, przed = import main 14:03, po = ta integracja)

Suma: draws (renderer + cienie + instancje) i trójkąty (renderer + instancje). Pełna tabela z rozbiciem: `artifacts/world-int-s16/budget-low.txt`.

| Kamera | draws przed → po | trisK przed → po |
|---|---|---|
| driver-andersa-to-putry | 533 → 537 (+4) | 315 → 304 (−3,5 %) |
| route-onramp-andersa | 764 → 761 (−3) | 276 → 281 (+1,8 %) |
| route-onramp-andersa-above | 665 → 664 (−1) | 283 → 270 (−4,6 %) |
| route-putry-approach | 530 → 534 (+4) | 319 → 301 (−5,6 %) |
| route-putry-entry-signs | 475 → 476 (+1) | 209 → 201 (−3,8 %) |
| g3a-eye-s0262 | 771 → 727 (−44) | 319 → 320 (+0,3 %) |
| g3a-rondo-bie-approach | 510 → 472 (−38) | 296 → 297 (+0,3 %) |
| g3b-eye-s1482 | 503 → 511 (+8) | 306 → 294 (−3,9 %) |
| g3b-rondo-putry-approach | 500 → 497 (−3) | 307 → 290 (−5,5 %) |
| stretch-01 / 02 / 03 / 04 | 852→796 / 982→884 / 772→727 / 677→687 (+10) | +1,6 / −1,7 / +0,3 / +0,6 % |
| stretch-05-docks | 902 → 880 (−22) | 318 → 299 (−6,0 %) |
| fire-station-route | 496 → 509 (**+13**) | 265 → 258 (−2,6 %) |
| fire-station-abeam / above / ref7197 | −10 / +6 / −14 | −0,8 / 0,0 / −0,6 % |
| photo-biezenstwa-ground | 538 → 500 (−38) | 0,0 % |
| biezenstwa-above | 598 → 604 (+6) | +1,0 % |
| putry-above | 400 → 416 (**+16**) | −3,8 % |
| dk8-dk19-exit | 171 → 158 (−13) | 162 → 169 (+4,3 %) |
| kwadrat-park-gate | 778 → 774 (−4) | +0,8 % |
| edge-east / north / south / west | −3 / −7 / −3 / −15 | +2,4 / **+7,6** / 0,0 / +4,5 % |
| chase / trailer-34 / truck-rear34 | −36 / −26 / −12 | +0,3 / +0,6 / +0,8 % |
| kabina (cab-*, 11 kamer) | od −42 do +4 | +0,5 … +2,2 % |
| truck-* / trailer-side (6 kamer) | +2 … +5 | +1,1 … +1,8 % |

Draws instancji osobno rosną na kamerach trasy o +1…+15 (np. driver-andersa 157 → 172, g3b-eye 169 → 183,
fire-station-route 210 → 223, route-putry-approach 178 → 188), trójkąty instancji +1…+5 k — nowe/zmienione propy (znaki M24/M25,
słupy, bariery 0146). Renderer draws spadają mocniej, więc suma na trasie: od −44 do +13. Najgorsze: putry-above +16
(kamera z lotu ptaka) i fire-station-route +13. Trójkąty powyżej +2 %: tylko kamery tła (edge-north +7,6 %, edge-west +4,5 %,
dk8-dk19-exit +4,3 %, edge-east +2,4 %) i cab-seat +2,2 %. To pomiar edytora (szacunek przed SRP batching); telefon jest prawdą — APK Low na A16.

## Pary SBS i ocena D51 (Low-overcast, poza `sbs-poses-r2`; before = `artifacts/sbs-poses-r2/after`)
Pary ≤ 960 px: `artifacts/world-int-s16/pairs/Low-overcast/` i `…/Low-clear/` (42/42). Wpis w `sbs_recognition.json`
(nowa wersja `world-int-s16`, poprzednia r3 przeniesiona do `history`, skróty render/zdjęcie powiązane z pikselami).

| Kadr | Było | Teraz | Uzasadnienie |
|---|---|---|---|
| 494288 (G3-B, ekran na łuku) | R | **RECOGNISABLE** | Poza `sbs-poses-r2` po scaleniu 0146 trafia: łuk w lewo, szklany ekran po prawej, latarnie po lewej, czerwona kapa — układ jak na zdjęciu (na main był łuk w prawo). Odstaje: słupki ekranu jasnozielone zamiast grafitowych, ekran czyta się jak drobna siatka, bariera W z prześwitem zamiast ciężkiej mostowej (P1 z REVIEW-0146, nadal otwarte). |
| 482392 (G3-A, pod wiaduktem) | R | **RECOGNISABLE** | Pomost z czerwonymi pasami, podpory z czerwonym pasem, bariera W na skarpie — zgodne. **Doszedł niebieski znak ze strzałką** po prawej (brak w r3). Odstaje: kamera „bliżej” pomostu (pomost zajmuje więcej kadru), rytm bliskich podpór inny, bariera w kadrze krótsza. |
| 320326 (G3-A, przejście pod wiaduktem) | P | **RECOGNISABLE** (awans) | Teraz są D-3 i D-6 na wyspie, kostka i żwir w miejscu trawiastej wysepki — główne braki z r3 zamknięte (0144/0146 + `gate3_landmarks`). Odstaje: podpory kwadratowe zamiast okrągłych z czerwonym pasem, znaki trochę dalej w głąb. |
| 297817 (G3-B, prosta przy remizie) | R (0141) | **RECOGNISABLE** | Układ jezdni, remiza po lewej, latarnie, kominy EC na horyzoncie (widoczne w Low-clear), nowa latarnia dwuramienna po lewej jak na zdjęciu. Odstaje: horyzont niżej (pochylenie pozy), brak drzew po lewej (zdjęcie: duże liściaste). |
| 275528 (G3-B, portal Andersa) | R (0146) | **RECOGNISABLE** | Kratowy portal z dwiema tablicami w tym samym miejscu kadru, dwie jezdnie, las po obu stronach. Odstaje: **brak obu A-30 z tabliczką** w kadrze (P1 z REVIEW-0146: znaki stoją w świecie, ale poza kadrem pary), tablice nieco mniejsze. |

## Kamery kontrolne — co obejrzałem (before/after, `artifacts/world-int-s16/cmp/`)
- route-putry-approach: czerwona kapa i nowe ekrany 0146; na Low mniej koron drzew przy domach (0132 r4b: drzewa ogrodowe `tier: high` pomijane na Low) — zieleń ulic domów nadal za rzadka (D51 PARTIAL, znane).
- driver-andersa-to-putry, g3a-eye-s0262: znaki U-3a/D-6 mniejsze — wymiary M24 (prawidłowe).
- route-putry-entry-signs: A-7/C-12, sygnalizacja, ekran — bez regresji.
- putry-above (z lotu ptaka): skyline 0141 widoczny jako „pływające” bloki nad horyzontem — tylko z góry (P2).
- **Regresja P1 do sprawdzenia — g3b-eye-s1482** (`cmp/crop-g3b.jpg`, Low i High): bariera W po lewej przy portalu kończy się
  **wolnym wysięgiem ~3–4 m bez słupka**, uniesionym nad trawą; na main bariera biegła dalej na słupkach. Najpewniej skutek
  przycinania/łączenia końców barier (M29 #31 lub deduplikacja 0146). Pierwszy plan G3-B — do naprawy w generatorze barier
  (nie ruszałem generatorów w integracji).

## Co otwarte
1. P1 g3b-eye-s1482: wolny koniec bariery W bez słupka (wyżej).
2. M29: 2 wolne końce pomostu (lista wyżej) + para zapór edge-west (C# `WorldEdgeBuilder`).
3. P1 z REVIEW-0146: ekrany (siatka, miętowe słupki), bariera mostowa, A-30 w kadrze 275528, mur bez fug, kikut 810896.
4. `import-region` w main + APK Low A16 (lider).
5. visual-critic D51 na parach `pairs/` (ta ocena jest moja, nie niezależna).
