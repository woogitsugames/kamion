# ADR 0186 — Dojlidy: zieleń i kadr P11-063 (Mickiewicza / Kuronia)
Status: Proposed (agent world-builder, s20, gałąź `dojgreen-0186` = main + `origin/horizon-0170`), 2026-11-13/14.
Poprzednik: ADR 0179, recenzja `docs/reports/REVIEW-2026-11-13-s19-0179.md` (P11-063: N/P — „inny kadr, brak
zielonej ściany”). Zakres: tylko region `bialystok-dojlidy`; las przy lotnisku (ADR 0187) nietknięty.

## Kontekst
Recenzja s19 0179, kadr P11-063 (CC0, Rakoon 2024-06-23): (1) kępa drzew narożnika to jedna sadzonka, (2) krzewy to
osobne kule liści, przez które widać auta, (3) maszt sygnalizacji stoi w środku kadru, a na zdjęciu przy prawej
krawędzi. Przyczyny znalezione w danych, nie w wyglądzie:
- **Kamera.** ADR 0174/0179 stawiały kamerę w punkcie GPS z Commons (lokalnie −46,5 381,8) i celowały 82° w centroid
  hali Kuronia 2. Punkt GPS leży na pasie rozdziału Mickiewicza. Resekcja z pięciu obiektów kadru (x w kadrze
  1600 px, f = 1255 px dla hFOV 65°) względem ortofoto 2024 / BDOT10k — narożnik W hali Kuronia 2 (47,8 337,4; x 1160),
  szafa sterownicza (−15,3 371,0; x 1102), maszt wysięgnikowy w pasie rozdziału (−35,5 368,0; x 1492), pień bliższego
  drzewa (−13,0 372,5; x 1037), para drzew za nim (−2,0 379,5; x 840) — daje **pozycję −67,0 393,5, azymut 100,0°**,
  reszty ≤ 0,2° (rozwiązanie z trzech pierwszych punktów trafia w oba drzewa na 0,2°). Kamera stała 23 m od
  właściwego miejsca i była obrócona o 18°. Pochylenie 8° (horyzont na y 630/900; było 10°). Pozycja masztu z
  ortofoto ±1,5 m przesuwa wynik o kilka metrów wzdłuż osi widzenia — WORKING_VALUE ±4 m.
- **Maszt w środku kadru** nie istnieje w terenie: reguła `junctions.build_junctions` uznaje skrzyżowanie za
  sterowane, gdy węzeł sygnalizacji OSM leży ≤ 25 m od jego środka. Zawrotka w pasie rozdziału (węzeł OSM
  3541204205) leży 20 m przed linią zatrzymania skrzyżowania z Kuronia, więc dostała 2 maszty i 3 słupy — dokładnie
  tam, gdzie stała kamera. Zdjęcie i ortofoto: przy zawrotce nie ma sygnalizacji.
- **Drzewa narożnika** (`tree_groups`, linia): wszystkie odrzucone przez regułę „3 m od nawierzchni” (trawnik między
  chodnikami); w kadrze została samosiejka 6 m.
- **Krzewy**: dwa rzędy instancji `tree_shrub` co 1,9–2,5 m — z definicji osobne korony na pniach.

## Decyzja
1. **Kamera `photo_P11-063`**: `pos_en [-67.0, 393.5]`, `heading_deg 100`, `pitch_deg 8` (dane; `basis` opisuje
   resekcję; test `test_camera_063_looks_at_the_frame` liczy x pięciu obiektów z pozycji kamery).
2. **`tree_groups.points_en`** (`vegetation.py`, opt-in): pnie wskazane pojedynczo `[E, N]` albo `[E, N, wysokość]`,
   `height_m: [lo, hi]` dla punktów bez własnej wysokości. Odmowa tylko na samej jezdni / nawierzchni / budynku
   (siatka `hard` = maska przed dylatacją 3 m, nowy parametr `place(..., hard=None)`), raport `points_refused`;
   wskazany pień wygrywa przerzedzanie 1,8 m z drzewem reguły. Narożnik: 4 klony/lipy — 10,5 m (zmierzone na
   zdjęciu: 190 px szerokości korony z 58 m ≈ 8 m, wysokość ≈ 10,5 m) i 9,0–9,8 m (WORKING_VALUE, częściowo zasłonięte).
3. **Gatunek nasadzeń `thicket`** (`plantings.SPECIES` + profil `thicket`, opt-in): zarośla jako jedna bryła —
   ciemny rdzeń od gruntu (−5 cm), powłoka liści alfa, krzewy co 1,1–1,7 m jako garby boku 0,4 m, `gap_p = 0`
   (brak brakujących roślin → nic nie prześwituje), zaokrąglony bark, luźne pędy 0,3–0,65 m. Tekstury grabu z
   istniejącego zestawu żywopłotów — **bez nowych materiałów**. Pas krzewów P11-063: 7 zachodzących na siebie
   mas 2,3–3,2 m (oś z ADR 0179, szer. 3,8–4,8 m) jako `kind: plantings` zamiast dwóch rzędów `tree_shrub`.
4. **Nadpisanie węzła `set: {signalized: false | true}`** (`junctions.py`, opt-in) — zawrotka `n3541204205` nie jest
   sterowana. **Maszt w pasie rozdziału** jako `gate3_signal` (−35,5 368,0; ramię nad jezdnią w stronę SW).

Region C: żadnego z tych wpisów nie ma w jego danych (`test_region_c_uses_none_of_it`), kod bez wpisu idzie starą
ścieżką.
