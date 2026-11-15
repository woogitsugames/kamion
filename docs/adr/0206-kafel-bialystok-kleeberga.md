# ADR 0206 — drugi kafel Białegostoku na trasie D64: `bialystok-kleeberga` (DK8/DK65 Maczka zachód + Kleeberga)
Status: Proposed (agent world-builder, s20, gałąź `bialystok-dk65-t2-0206`, baza `origin/bialystok-dk65-0203` @ 42d3c47f6),
2026-11-15. Scalać **po** 0203 (plan trasy, `junction_topview.py`, region `bialystok-maczka`).
Powiązane: D63, D64 (`docs/11`), ADR 0203 (plan 17 kafli), ADR 0166/0174 (potok regionu ≠ C).

## Kontekst
Plan ADR 0203 (`docs/reports/map/dk65_route_plan.json`) rezerwuje kafel (−2,0) `bialystok-kleeberga`, bbox EPSG:2180
772875,595199 – 774923,597247, km 3,58–5,80 wariantu A (2219 m trasy). To pierwszy wolny kafel po `bialystok-maczka`
w stronę Knyszyna. Zawartość: zachodni koniec Gen. Maczka (DK8/DK65, 2×2/2×3, krótki most km 4,07), łuk w Gen.
Kleeberga z **przejazdem DK8 w wykopie pod rondem prof. Szymańskiego** (OSM `tunnel=yes layer=-1`, way 23982181 i
76073122, po 77 m), łącznice km 5,19–5,27 i **wiadukt Kleeberga** (km 5,45–5,61) nad rondem ulicy niższej klasy.
Węzeł rozjazdu do ronda Pamięci Męczeństwa Kresowian (węzeł 2504239797) leży 23 m za zachodnią krawędzią — w kaflu
`bialystok-knyszynska`.

## Decyzja
1. Region `bialystok-kleeberga` dopisany do `tools/worldgen/regions.py` (bbox/id z planu 0203, origin = środek kafla,
   powiat 2061); `Data/Regions/bialystok-kleeberga/`: `route_endpoints.json` (wejście 774923,596185.7 way 249740774,
   wyjście 772875,595511.6 way 261104557), `overrides.yaml` (pusty — patrz niżej), `junction_checks.authored.json`
   (8 punktów, obie jezdnie), `control_cameras_place.authored.json` (5 kamer z oczu kierowcy).
2. Potok: `ingest` → `build_region` (670 węzłów, 766 krawędzi, 1865 budynków LoD1/LoD2) → `build_world --context`
   (nowy region nie ma `generated/osm_context.json`; bez `--context` build_world kończy się FileNotFoundError) →
   `export-route` → `import-region` (64 chunki) → scena `World_bialystok-kleeberga`.
3. **Drogi najpierw — porównanie z ortofoto GUGiK 2024 0,25 m** (narzędzia w `artifacts/bialystok-dk65-t2-0206/`):
   - `junctions/j1…j8.jpg` — ortofoto | widok z góry z trójkątów GLB, 8 węzłów (szwy E/W, łącznice km 3,85/3,89,
     most km 4,07, łącznice km 4,35, rondo Szymańskiego, łącznice km 5,19–5,27, wiadukt Kleeberga).
   - `lanes/sheet_00…04.jpg` — 56 kadrów 60×34 m w połowie każdej krawędzi trunk/trunk_link (liczenie linii P-1/P-7b);
     `lanes/zz_*.jpg` — powiększenia (szew z maczka, 774330, wiadukt).
   - `line_profile.py` — profil jasności w poprzek jezdni (±15 m, uśrednienie po 12 m): linie krawędziowe 2-pasowych
     jezdni Kleeberga/Maczka w odstępie 7,2–7,5 m (wygenerowane 7,5 m, BDOT10k), 3-pasowych ~11,0 m (wygenerowane
     10,75–11,5 m). `lane_widths.json` (pomiar asfaltu z 0203) jest wiarygodny tylko na Maczka (zielony pas dzielący);
     na Kleeberga pas dzielący jest utwardzony z barierą i pomiar skleja obie jezdnie (30 m) — nie używać.
   Wynik: liczba pasów OSM zgodna z ortofoto na wszystkich krawędziach trunk z jednym wyjątkiem (pkt „otwarte” 2);
   układ łącznic, rond i wiaduktów zgodny topologicznie. Szew z `bialystok-maczka` (x = 774923): te same drogi,
   pasy i kierunki po obu stronach (test). **Overrides pasów: 0** — nie było rozbieżności, którą obecny schemat
   overrides oddaje lepiej niż OSM.
4. **Błąd krytyczny znaleziony kamerą place (r2): DK8/DK65 zablokowana pod rondem Szymańskiego.** OSM: obie jezdnie
   DK8 `tunnel=yes layer=-1` (77 m), rondo na gruncie; generator nie zna tuneli, conform terenu bierze WYŻSZĄ drogę
   na węzeł, a NMT trzyma grunt ronda między jezdniami → siatka kolizji terenu (`terrain_lod2`, 4 m) 0,27–4 m nad
   jezdnią DK8 przy obu łukach ronda (`probe_lod2.py`). Poprawka w dwóch częściach (**zmiany wspólnego kodu**):
   - nowy klucz override `set: {bridge: true}` (`tools/worldgen/roads/network.py`, `apply_edge_overrides`): odcinek
     naziemny niesiony jako pomost (profil z prześwitem nad drogą niżej, przekrój mostowy, bez conform terenu);
     użyty dla łuków ronda 257353773/74 (`overrides.yaml`). Sam w r3 nie wystarczył (teren nadal 0,54 m nad jezdnią:
     podnosiła go płyta skrzyżowania ronda i chodniki);
   - `tools/worldgen/roads/build_world.py: keep_tunnel_cut` — po conform terenu węzły w promieniu 9 m od osi dróg
     `tunnel` (bez `building_passage`, service, living_street, ścieżek) schodzą do poziomu tej drogi − 0,35 m
     (cięcie ograniczone do osi samych krawędzi tunelowych, nie całych łańcuchów 842/849 m; drogi wyżej położone
     dalej niż 7 m od osi zachowują teren). r4: 970 węzłów, max obniżenie 6,31 m. Regiony C/Dojlidy/maczka nie mają
     takich dróg (C: tylko `building_passage`) → funkcja zwraca {} i nic nie zmienia.

## Budżet (wycinek kafla; A = maczka 0203, B = ten kafel)
| | maczka (0203) | kleeberga (0206) |
|---|---|---|
| build_world | 2158 s | 2608–2913 s (r1–r4, do 3 jobów heavy równolegle) |
| import-region | — | ~540–620 s, 64 chunki, korytarz 33 |
| WORLD_MEMORY Low | 153,0 MB | 156,7 MB |
| WORLD_MEMORY High | 420,3 MB | 356,8 MB |
| 7 kamer trasy Low (drawsEst / tris) | 93–586 / 150–387k | 75–405 / 169–346k |
| 7 kamer trasy High (drawsEst / tris) | — | 71–990 / 341k–1,12M (r2) |
| 5 kamer place Low | — | 215–383 / 220–408k |

## Walidacja
- `tests/gis/test_kleeberga_0206.py` (7): pomost ronda zastosowany, DK8 bez pomostu; kafel = zachodni sąsiad maczka i zgodny z planem 0203, szew z maczka
  (te same drogi/pasy/kierunki), końce trasy na węzłach brzegowych, overrides z uzasadnieniem, brak dróg
  `proposed/construction/motorway`, punkty kontrolne w kaflu.
- visual-qa r1 Low (7 kamer trasy co ~317 m + 2 rondo z góry), r2–r4 Low+High z 5 kamerami place
  (`control_cameras_place.authored.json`): razem 14 kamer świata. Arkusze: `vqa-r4/{route,place}_{Low,High}.jpg`.
- Przejezdność bez telefonu: `route_sweep.py` (r4) — trasa D64 w kaflu 2165 m, co 2 m, przesunięcia −3…+3 m,
  5345 próbek: **0 przeszkód 0,3–4,5 m nad kolizją jezdni** (wszystkie materiały LOD0 + `terrain_lod2`), skok
  kolizji na osi ≤ 0,10 m, 14 próbek bez kolizji jezdni (krańce ±3 m przy zwężeniach — do sprawdzenia przy
  przejeździe A16). `probe_lod2_r4.txt`: brak terenu < 4,5 m nad DK8 pod rondem (r2: 0,27 m, r3: 0,54 m).
- EditMode r2: 580/581 (1 skip). pytest gis r2: 1163 ok, 1 fail `test_dojbld_0185::test_fence_mesh_mips…` —
  na main oznaczony xfail w 3f625052c, którego nie ma w bazie 0203; po scaleniu znika.
- Końcowo (kod r4): EditMode 580/581 (1 skip); pytest gis 1163 ok + ten sam 0185; `fidelity_qa.json` regionu C
  odświeżony (`fidelity/run.py`): zmieniły się tylko 2 hashe wejść (build_world.py, network.py) — metryki C bez zmian,
  co potwierdza, że poprawka nie rusza innych regionów.
- visual-critic: NIE uruchomiony (subagent nie tworzy subagentów) — do zlecenia przez lidera na `vqa-r4/*.jpg`.

## Otwarte (backlog do szlifu)
1. **Rondo Szymańskiego nad wykopem** — przejezdne (pkt 4), ale z grubsza: wyspa środkowa i chodniki ronda nad
   wykopem nie mają konstrukcji (wyspa otwarta na wykop, widoczna z góry; od spodu jezdnia ronda jest jednostronna),
   duża gładka ściana oporowa przy łącznicy na prawo od jezdni zachodniej. Docelowo etap „tunel / płyta nad wykopem”
   (ściany portali, strop) w `tools/worldgen/roads`.
2. Way 606396484 (Maczka, jezdnia wschodnia, 110 m): OSM `lanes=3`, ortofoto: 2 pasy na zachodniej ~55 %, trzeci
   pas (zwalniający do łącznicy 1410715799) dopiero na wschodniej części. Overrides nie mają „pasa od t do t”
   (profil szerokości zachowuje układ najszerszego przekroju) — zostaje 3 na całej długości (WORKING_VALUE).
3. Oś OSM Kleeberga (301702369) ~0,9 m na prawo od środka jezdni (profil linii) — poniżej progu poprawki „z grubsza”.
4. Szew zachodni: łącznica 668340275/561326924 w ortofoto przylega do jezdni (pas wydzielony linią), w generacji
   ma zielony pas rozdzielający; dokończyć razem z kaflem `bialystok-knyszynska` (węzeł rozjazdu jest tam).
5. Budynki LoD1 i roślinność bez szlifu (D63/D64).
