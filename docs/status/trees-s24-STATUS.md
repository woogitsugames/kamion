# STATUS trees-s24 (drzewa przydrożne i lasy, ADR 0308)

- 14:55 Worktree `trees-s24` (-CopyDerived, prywatna kopia `Data/raw/derived`). Generator: `tools/blender/world/make_trees.py`
  + `tools/worldgen/streetscape/leaf_textures.py`; rozmieszczenie `streetscape/{vegetation,tree_rows,forest_hlod}.py`.
  Podgląd Blender stanu „przed": `artifacts/trees-s24/preview/before_broadleaf.png` (korony = kilka kulistych kęp na gołych
  konarach; tekstury liści = okrągłe pompony). Render „przed" (import knyszyn + dk65-05, High clear) w tle.
  NASTĘPNY KROK: `cat artifacts/trees-s24/unity-before-knyszyn.status artifacts/trees-s24/unity-before-dk65.status`; obejrzeć `artifacts/trees-s24/vqa-before-*/`
- 15:45 „Przed" obejrzane (`artifacts/trees-s24/vqa-before-{knyszyn,dk65}/`, montaże `small/before*_m*.jpg`). Trzy źródła „brokułów":
  (1) drzewa biblioteki = kilka kulistych kęp na gołych konarach, karty liści = okrągłe pompony; (2) drzewa ogrodowe Knyszyna
  (3243 szt.) = skrzyżowane karty z ciemnym rdzeniem; (3) świerki = stos poziomych talerzy. Zrobione: `leaf_sprays.py` (atlasy
  gałązek 2×2), `make_trees.grow_crown` (lipa/klon/brzoza/olsza + topola), świerk z obrotem konarów, drzewa ogrodowe na High jako
  instancje biblioteki (`plantings.library_instance`), test `tests/gis/test_trees_0308.py` (10 passed), wpis LICENSES.
  LOD0 tris: lipa 3128–3272 → 3272–3354, klon 2450–2520 → 2916–2996, brzoza 3380–3534 → 2936–2976, olsza 4024–4130 → ~3100.
  Wypiek biblioteki + runda 1 (build_world knyszyn → import → render) w tle.
  NASTĘPNY KROK: `cat artifacts/trees-s24/bake-r1.status artifacts/trees-s24/round-r1.status`; obejrzeć `artifacts/trees-s24/vqa-r1-*/`
- 16:45 STOP (limit tygodniowy, polecenie lidera). STAN:
  * Wypiek biblioteki r1 GOTOWY (`artifacts/trees-s24/bake-r1.log`, exit 0): `trees.glb`, `trees_lod2.glb`, `trees_meta.json`,
    impostory sosna/brzoza/olsza/klon/lipa/świerk + NOWA topola (`impostor_tree_poplar_{0,1}*`), `forest_edge_*`/`forest_canopy_*` — w commicie.
  * Runda 1 W TLE (nie czekam): `artifacts/trees-s24/round.ps1 -Tag r1` = build_world knyszyn (start 15:39, log
    `artifacts/trees-s24/world-knyszyn-r1.log`) → import knyszyn + render → import dk65-05 + render. Status: `artifacts/trees-s24/round-r1.status`
    (`exit=0` = komplet), rendery `artifacts/trees-s24/vqa-r1-{knyszyn,dk65}/`. NIEOBEJRZANE — runda 1 nie jest oceniona.
  * NIEZWERYFIKOWANE kompilacją: zmiany C# (EdgeSides/WorldStreamer/WorldEdgeBuilder + test) — pierwszy import rundy 1 je skompiluje;
    błąd kompilacji = `import ... failed` w `unity-r1-knyszyn.status` i log `artifacts/logs/import-region-knyszyn-*.log`.
  * Brzoza: atlas z komórkami 0–1 wzniesionymi / 2–3 zwisającymi jest w KODZIE (`leaf_sprays.UPRIGHT_CELLS`, `grow_crown`), ale
    `leaves_birch.png` w repo i wypiek r1 są jeszcze ze starego układu (same witki) → runda 2 musi przegenerować atlas i wypiec brzozę.
  * ZIELONA ŚCIANA DK65 (zgłoszenie właściciela, owner-02): przyczyna ustalona analizą kodu i siatki kafli (NIE potwierdzona renderem):
    to nie las, tylko fartuch terenu (apron) kafla po przekątnej. Korytarz idzie schodkami 06 → 07 (W) → 08 (N od 07 = NW od 06);
    06 i 08 nie mają wspólnego boku, więc szew między nimi nigdy się nie „otwiera", a ćwiartka narożna fartucha 06 (połowa `Apron_N`,
    maska „las" = ciemna zieleń, zgrubna wysokość) leży w kaflu 08 nad jezdnią; krawędź ukośna na zrzucie = podział narożnika po
    przekątnej (`EdgeSides.ApronSide`). To samo dotyczy sektorów `far_*`. Takie schodki: 02/04, 06/08, 08/10, 11/knyszyn.
    Poprawka w gałęzi: `EdgeSides.ApronCorner/ApronPieceVisible/FarSectorVisible`, importer tnie fartuch na 8 części (+ `Apron_NE/SE/SW/NW`),
    streamer chowa narożnik i sektor dali przy gotowym kaflu po przekątnej; stare importy (bez narożników) chowają cały bok fartucha
    (działa bez reimportu, możliwa pusta smuga dalej od drogi — pełna poprawka po reimporcie kafli).
  * NIE ZROBIONE: skrajnia koron nad jezdnią (plan: przejście `vegetation.road_clearance` w `stage.py` — drzewo, którego korona
    o podstawie < 4,7 m wchodzi nad jezdnię > 0,3 m, jest zmniejszane do promienia = odległość od krawędzi + 0,3 m albo usuwane;
    promień/H i pień/H z `make_trees.CROWN`); liczby budżetu przed/po (`artifacts/trees-s24/compare_stats.py`); SBS z referencją;
    visual-critic; pełny pytest tests/gis; EditMode Win64; uzupełnienie ADR 0308 (sekcje WYNIKI_PLACEHOLDER / OTWARTE_PLACEHOLDER
    + punkt o fartuchu); wierzba (głowiasta) — brak modelu; kopia dowodów do main `artifacts/trees-s24/`.
  NASTĘPNY KROK (z katalogu worktree `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\trees-s24`):
  `cat artifacts/trees-s24/round-r1.status artifacts/trees-s24/unity-r1-*.status` → gdy `exit=0`:
  `uv run --no-project python artifacts/trees-s24/compare_stats.py artifacts/trees-s24/vqa-before-knyszyn/stats.txt artifacts/trees-s24/vqa-r1-knyszyn/stats.txt`
  (to samo dla `-dk65`), obejrzeć `vqa-r1-*/{dk65-inlet-south,dk65-outlet-nw,gardens-tykocka-eye,drive-north,rev-mid,route-s0786}.png` obok `vqa-before-*`.
  Runda 2: `uv run --project tools/worldgen tools/worldgen/streetscape/leaf_sprays.py --only birch` →
  `blender -b --factory-startup -P tools/blender/world/make_trees.py -- --reuse-bakes --rebake birch --rebake-forest mixed,broadleaf` →
  `pwsh artifacts/trees-s24/round.ps1 -Tag r2 -NoWorld`. Testy: `uv run --project tools/worldgen pytest tests/gis/test_trees_0308.py -q`
  (10 passed bez testu meta; test `meta` uruchomić po wypieku), potem `pwsh scripts/unity-slot.ps1 -Acquire -Owner trees-s24; pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64; pwsh scripts/unity-slot.ps1 -Release -Owner trees-s24`.
  Sprzątanie worktree: `Data/raw/derived` to PRYWATNA KOPIA (37 GB) — knyszyn przebudowany tu NIE jest w main (lider i tak przebuduje po scaleniu).
- 17:30 WZNOWIONE (właściciel odwołał STOP). ZIELONA ŚCIANA — PRZYCZYNA POTWIERDZONA DANYMI (korekta wpisu wyżej: fartuch to tylko
  ryzyko poboczne): `far_field.py` przypisywał cały drzewostan dali do sektora jego CENTROIDU. `audit_far_sectors.py`: dk65-07 ma
  47 ha lasu rysowanego z `far_east`, a leżącego na północ od kafla (e −505…1614, n 1024…1605 = południowe 580 m dk65-08).
  Po zwolnieniu dk65-06 bok E kafla 07 się zamyka → `far_east` wraca → kopiec podszytu + kurtyny stoją w 08 (zgadza się z DIAG
  krytyka t=1738). To samo: dk65-11 104 ha (E→N), tykocin-07 35 ha, -08 27 ha, -09 25 ha, industrial-c 14 ha, maczka 6,5 ha.
  POPRAWKI (commit 8bd… + wcześniejsze): (a) `far_field.split_by_sector` — drzewostan cięty po granicach sektorów;
  dk65-07 po regeneracji: trójkąty poza własnym sektorem `far_east` 20,3 % → 0 %, `far_south` 11,9 % → 0 % (`audit_far_glb.py`;
  High 53 508 → 60 137 tris, Low 12 446 → 13 101, limit Low 27k); (b) streamer chowa sektor dali / fartuch także przy gotowym
  kaflu PO PRZEKĄTNEJ i gdy sam kafel jeszcze się aktywuje (`coveredSides`); (c) fartuch cięty na 8 części (narożniki);
  (d) `vegetation.road_clearance` — korona z podstawą < 4,7 m nie wchodzi nad jezdnię > 0,3 m (test, 12 passed).
  WYMAGA po scaleniu: regeneracja dali KAŻDEGO kafla (`uv run --project tools/worldgen python tools/worldgen/streetscape/far_field.py --region <id>`,
  < 2 min/kafel) + reimport. Manifesty dk65-07 cofnięte (derived tylko w prywatnej kopii).
  Runda 1 nadal w tle (build_world knyszyn od 15:39 wg zegara maszyny).
  NASTĘPNY KROK: `cat artifacts/trees-s24/round-r1.status artifacts/trees-s24/unity-r1-*.status`
- 18:20 Runda 1 OBEJRZANA (`artifacts/trees-s24/sbs/*-before-vs-r1b.jpg`, kopia w main): drzewa liściaste i ogrodowe bez „brokułów" —
  zwarte, płatowe korony; kompilacja C# OK (import przeszedł). Budżet High (edytor, `compare_stats.py`): knyszyn 64 kamery
  draws 18 390 → 18 452 (+0,3 %), tris sceny 55,26 M → 54,67 M (−1,1 %), tris instancji 1,306 M → 1,490 M (+14 %);
  dk65-05: draws ±0, tris sceny ±0, tris instancji +4,0 %. Usterki r1: świerk przy drodze nadal jak talerze; korony nad jezdnią
  (dk65-outlet-nw) — skrajnia nie była jeszcze w tym buildzie świata.
  Runda 2 W TLE: świerk = konary jako kalenica ze zwisającymi gałązkami (te same 4 tris/konar), wypiek `bake-r3`, build_world knyszyn
  ze skrajnią, import + render obu kafli (`round.ps1 -Tag r2`).
  NASTĘPNY KROK: `cat artifacts/trees-s24/round-r2.status artifacts/trees-s24/unity-r2-*.status` → `bash artifacts/trees-s24/sbs.sh r2` (z katalogu artifacts/trees-s24)
