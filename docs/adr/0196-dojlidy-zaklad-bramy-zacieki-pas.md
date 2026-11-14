# ADR 0196 — Dojlidy: zakład przy Kuronia 2 jako bryły, bramy segmentowe, zacieki bez powtórzeń, pas 09R/27L w kadrze
Status: Proposed (agent world-builder, s20, gałąź `dojind-0196`), 2026-11-13. Do scalenia przez lidera.
Poprzednik: ADR 0179 + recenzja `docs/reports/REVIEW-2026-11-13-s19-0179.md` (P2: dominanta P11-063, bramy P11-094,
zacieki co moduł, brak kadru pasa startowego). Zakres: tylko region `bialystok-dojlidy`; region C bez zmian.
Sąsiednie zadania (nie ruszane): `dojbld-0185` (bryła/okładzina hali północnej, Kuronia 3, ogrodzenia),
`dojgreen-0186` (zieleń, kadr 063), `forest-0187` (las).

## Kontekst
1. Zakład przy Kuronia 2 (BDOT10k jeden obrys 11 215 m², LoD1 12,72 m) był jedną jasną halą z grafitowym pasem.
   Kadry CC0 P11-005, P11-059, P11-063 (obejrzane w pełnej rozdzielczości) i ortofoto 2024 pokazują co innego: hala
   właściwa jest **grafitowa** na całej wysokości, a jasne ściany widziane z ulicy to niskie przybudówki przed nią;
   na narożniku zachodnim stoją dwa ciemne, wyższe bloki (noszą tablice firmy — nie odtwarzane).
2. Na ścianie północnej hali północnej (P11-094) brakowało dwóch bram segmentowych.
3. Zacieki pod attyką: warstwa `parapet_runoff` ma okres 24 m, więc ściana 133 m pokazywała tę samą grupę smug 5,5 raza.
4. „30 153 m² pasa” nie miało dowodu w kadrze; pas nie miał oznakowania.

## Decyzja
1. **Kuronia 2 = hala + 5 `building_part`** (mechanizm 0179; wpis 0179 `kuronia2-hall-dark-band` zastąpiony):
   hala 12,72 m `hall_wall_graphite` bez pasów; blok narożny (14 × 7 m) i drugi blok frontowy (8 × 10 m) **9,0 m**
   jako ciemne ramy (pas górny 2,6 m i słupy narożne `hall_flashing`, ciemny parter) wokół jasnego pola z oknami; wnęka między nimi, skrzydło biurowe wzdłuż ściany SW (10,1 m głębokości z ortofoto) i przybudówka
   wzdłuż Kuronii (8,3–8,5 m) **7,2 m**: jasny tynk nad ciemnym parterem, pasmo okien na piętrze skrzydła. Obrysy =
   prostokąty z ortofoto przycięte obrysem BDOT10k. Bez nazwy, logo i tablic.
   Wysokości 9,0 / 7,2 m odczytane z proporcji w kadrach (P11-005: blok 222 px wobec 190 px przybudówki; P11-059:
   przybudówka 120 px wobec 195 px hali 12,72 m) — **UNVERIFIED ±1 m, do potwierdzenia przez M63**.
2. **Nowy rodzaj `kind: wall_gates`** (`buildings_mesh.wall_gates` / `gate_openings`): bramy podane punktem E/N,
   przypinane do najbliższej ściany hali (≤ 2 m) — przeżywają przecięcie obrysu przez `building_part` innego agenta.
   Otwór z ościeżem na LOD0 i LOD1, wypełnienie = istniejący materiał `dock_door` (bez nowego materiału). Brama bez
   ściany w zasięgu albo niemieszcząca się na ścianie = błąd buildu. Dane: 2 bramy 4,5 × 5,0 m na ścianie N hali
   północnej, 14,7 m i 53,8 m od narożnika NE (namiary z kadru P11-094, ±2 m; rozmiar **UNVERIFIED, M63**).
3. **Zacieki bez powtórzeń — `kind: facade_rules`, `runoff_shuffle: true`** (opt-in na region). Tylko siatka
   (TEXCOORD_1), bez zmiany shadera i tekstury: górna strefa ściany (4 m × skala długości) jest cięta na bloki
   warstwy między jej „cichymi” kolumnami (miejsca, gdzie w ±0,25 m nie ma smugi — szew nie tnie żadnej smugi;
   zmierzone na teksturze High: 10 takich miejsc, maks. 0,008 przy średniej warstwy 0,017; użyte 6, bo 10 bloków
   dawało +30 % trójkątów LOD1). Bloki (2,3–6,1 m, średnio 4 m) układane w kolejności
   z hasha budynku, nigdy ten sam dwa razy z rzędu, połowa odbita lustrzanie, każdy z własną długością smug
   (× 0,65–1,25), 20 % bloków tylko z krótkimi smugami (× 0,3). Skala u = 1 (szerokości smug bez zmian). Poniżej
   strefy smug ściana zostaje jednym quadem. LOD0 i LOD1 używają tej samej tabeli.
4. **Oznakowanie pasa — `kind: runway_markings`** (`streetscape/runway_paint.py`): pasy wzdłuż osi próbkowane co 2 m
   w obu kierunkach, kładzione na powierzchni placu + `MARKING_LIFT`, materiał `marking_white` na warstwie `markings`
   (decal z offsetem głębi jak oznakowanie dróg — bez z-fightingu, bez nowego materiału). Dane z ortofoto 2024
   (0,25 m): linie boczne 0,9 m (krawędzie zewn. 29 m), 10 strzałek progu przesuniętego 40 m co 57,7 m, 2 poprzeczki
   progu z 5 grotami, 4 odcinki linii osiowej. Nie rysowane: oznaczenie „27 L”, wyblakłe szare krzyże, linia
   kołowania na płycie do zawracania.
5. **Kamera `krywlany_runway`** — nowy plik `control_cameras_place.authored.json` (kamery miejsc bez zdjęcia;
   osobny plik, żeby nie kolidować z kamerami foto innych agentów): local 21,1 / −121,0, 0,6 m za linią ogrodzenia
   lotniska z OSM (narożnik NE), oczy 1,7 m nad NMT, azymut 252,5°, obiektyw 14° (pas leży 145–1050 m stąd,
   depresja 0,31–0,96°); 83 % pasa widoczne nad NMT, w sektorze kadru jedna sosna przy lewej krawędzi (sprawdzone na
   instancjach drzew). W tym samym pliku kamery QA: `krywlany_runway_paint` (14 m nad osią pasa — dowód oznakowania)
   i `kuronia2_front` (poza zdjęcia P11-005).

## Czy to wygląda jak trawiasto-asfaltowe lotnisko aeroklubu (OSM aeroway + ortofoto)
- OSM: `958211700` runway 09R/27L asphalt 1350 × 30 m (oś local −1446,3 −227,2 → −115,7 −192,3 — zgodna z obrysem
  0179 co do 1 m; w kaflu wschodnie 919 m); `303368859` runway 09L/27R **grass** 860 m (wschodnia połowa w kaflu,
  ~150 m na N od asfaltu); hangary, płyta, drogi kołowania i lądowiska śmigłowców leżą **poza kaflem** (E < −1024).
- Ortofoto: pas trawiasty nie ma oznakowania ani znaczników — w grze zostaje łąką `open_ground` (zgodne).
  Asfalt ma pełne oznakowanie — dodane (pkt 4).

## Budżet (A/B) — Low, overcast, 1920×1080, edytor (nie telefon)
„Przed” = `artifacts/dojlidy-vis-0179/Low-overcast-photo/stats.txt` (0179), „po” = `r4-Low-overcast/stats.txt` (po scaleniu
`origin/main` fd5f124a7 — różnica obejmuje też zmiany main). Szacunek edytora przed batchingiem.
| Kadr | draws przed → po | trójkąty przed → po |
|---|---|---|
| photo_P11-063 | 317 → 323 (+6) | 333 897 → 342 810 (+2,7 %) |
| photo_P11-094 | 195 → 199 (+4) | 288 046 → 292 547 (+1,6 %) |
| photo_P11-001 | 335 → 341 (+6) | 462 860 → 471 466 (+1,9 %) |
| photo_P11-056 | 125 → 126 (+1) | 158 580 → 159 781 (+0,8 %) |
| krywlany_runway / _paint / kuronia2_front (nowe) | 61 / 54 / 207 | 194 853 / 119 189 / 347 683 |
Geometria budynków całego kafla (offline, ten sam kod z wpisami 0196 i bez): LOD0 467 487 → 476 480 (+1,9 %),
LOD1 47 375 → 54 581 (+15,2 %; z tego zacieki ≈ +6 tys., części Kuronia 2 ≈ +1,2 tys.), materiały LOD0 43 → 45,
LOD1 48 → 50 (w chunku Kuronia 2). Farba pasa: 2 672 trójkąty w warstwie `markings`.
Werdykt wobec `docs/06` §6 (hipoteza Samsung A: ≤ 300–400 draws, ≤ 400–600 tys. trójkątów w kadrze): wszystkie kadry
mieszczą się; najcięższy P11-001 (341 / 471 tys.) był 335 / 463 tys. przed zmianą. +15 % trójkątów LOD1 budynków to
+7 tys. w całym kaflu (1–3 tys. w kadrze). Pomiar na telefonie: brak (bramka lidera).

## Wizualnie (pętla: 4 buildy / importy / rendery; kadry obejrzane przez agenta, ocena `visual-critic` u lidera)
| Dowód | Zgodne | Rozbieżne / otwarte |
|---|---|---|
| `sbs-r4/sbs-P11-005.jpg` (kamera `kuronia2_front` w pozie zdjęcia P11-005) | grafitowa hala w tle, biała przybudówka wzdłuż Kuronii, dwa ciemne bloki-ramy z jasnym polem i oknami na narożniku, długie niskie białe skrzydło z pasmem okien nad ciemnym parterem | brak czerwonej linii i daszku, tablic (świadomie), urządzeń na dachu; ramy płaskie (bez wysunięcia attyki); białe ogrodzenie panelowe z morą na pierwszym planie (zakres 0185) |
| `sbs-r4/sbs-P11-063.jpg` | po prawej ciemna, wyższa część + niska biała zamiast jednej jasnej hali z pasem | kadr nadal przesunięty (sygnalizator w środku — zakres 0186), przez to dominanta przy krawędzi |
| `sbs-r4/sbs-P11-094.jpg`, `view/r4-094-{top,gates}.jpg`, `view/r1-094-top-ba.jpg` (przed / po) | dwie bramy segmentowe na ścianie N; smugi pod attyką w nieregularnych odstępach, bez widocznych szwów | bramy bez obróbki/odbojnic; rozmiar UNVERIFIED |
| `view/r4-runway.jpg` (`krywlany_runway`, oczy 1,7 m przy płocie, 14°) | pas = ciemna wstęga asfaltu w łące (ok. 30 px wysokości przy 1080p — szacunek z pomniejszenia, niemierzone), las w tle | z 1,7 m oznakowania nie widać (kąt 0,3–1,0°) — tak jest też w terenie; dlatego druga kamera |
| `view/r4-runway-paint.jpg` (`krywlany_runway_paint`, 14 m nad osią, QA) | linie boczne, strzałki progu przesuniętego w osi, płyta do zawracania | asfalt pasa ma łaty materiału `asphalt_worn` (jak place) — za „zniszczony” dla pasa z 2018 r. |
| `view/paint_{w,mid,e}.jpg` | farba z generatora nałożona na ortofoto: poprzeczki, groty, strzałki i linie zgodne co do ~1 m | „27 L” nie rysowane |
Odrzucone renderem: kamera pasa r1 (30°, zły azymut — pas 3 px przy krawędzi), r2 (wschodnie ogrodzenie w osi pasa —
zasłania las między ogrodzeniem a płytą); bloki frontu jako jednolite grafitowe pudełka (r3) → ramy z jasnym polem (r4).

## Walidacja
- Ścieżka bez tabeli zacieków w `wall_with_openings` jest dosłownie starym kodem (region C bit w bit).
- `tests/gis/test_dojind_0196.py` (10 testów): region C bez nowych rodzajów; ścieżka bez tabeli = stary quad;
  bloki pokrywają ścianę, szwy na cichych kolumnach, ta sama kolumna tekstury co 24 m na < 20 % ściany (było 100 %);
  bramy (przypięcie, usunięcie okna reguły, błąd bez ściany); farba pasa w obrysie asfaltu, CCW, lift;
  dane Kuronia 2 (hala grafitowa + 5 części, bez nakładania, suma pól = BDOT ±40 m²), brak nazw firm w danych.

- Pełny `pytest tests/gis` po scaleniu `origin/main` (14.11 17:14, 932 s): **1112 passed, 3 failed, 2 xfailed**.
  - `test_world_v31::test_forest_trees_reference_their_cell`, `test_p1_0161::test_ring_mast_survives_the_carriageway_clearing`
    — nieaktualna kopia `Data/raw/derived/bialystok-industrial-c` w worktree (13.11 14:16, main zregenerował C 14.11 04:54);
    po skopiowaniu danych z main: oba pliki testów 30/30 zielone.
  - `test_road_fidelity::test_report_not_stale` — `fidelity_qa.json` regionu C nieaktualny wobec `build_world.py`
    (ta gałąź dodaje w nim kamery miejsc) → lider: `fidelity/run.py --region bialystok-industrial-c` po scaleniu.
  - `test_export_is_deterministic` zielony: build regionu C tym kodem = sha256 każdego chunku z zacommitowanego
    manifestu main (test porównuje świeży build z manifestem sprzed buildu).
- EditMode (`scripts/test.ps1 -Platform EditMode`, 17:29): 581 total, **580 passed, 0 failed**, 1 skipped (Ignored).
- Zrzut z telefonu: brak (bez adb w zadaniu) — `docs/06` §5 pkt 2 do spełnienia przez lidera przed bramką.

Zdjęcia właściciela: `art-source/world/refs/` nie istnieje w repo — brak; referencje = kadry CC0 P11 i ortofoto.
Odtworzenie liczb: `artifacts/dojind-0196/ab.py` (geometria LOD0/LOD1 z wpisami 0196 i bez), `overlay.py` (farba na
ortofoto), `chain.ps1 -Tag rN` (build → import → render), `sbs.sh`, `tests.ps1`.

## Otwarte
- Wysokości części Kuronia 2, rozmiar i położenie bram: UNVERIFIED do M63 / sesji zdjęciowej właściciela.
- Kuronia 2: czerwona linia między parterem a piętrem, czerwony daszek wejścia, urządzenia na dachu przybudówki,
  okładzina kasetonowa bloków (teraz blacha trapezowa `hall_wall_graphite`).
- Oznaczenie „27 L” na pasie; pas trawiasty 09L/27R bez wyróżnienia w trawie (koszona murawa); asfalt pasa z łatami
  `asphalt_worn` (osobny, czystszy zestaw = nowy materiał → decyzja lidera).
- `wall_gates` przerywa build, gdy ściana pod bramą przestanie być halą (np. `building_part` 0185 z `frontage` na
  ścianie N hali północnej) — po scaleniu z 0185 sprawdzić build; bramy są pozycyjne, więc zwykłe przecięcie obrysu
  ich nie psuje.
- `game/Assets/_Project/UI/Resources/CabDisplay/Nav/bialystok-dojlidy_route.bytes(.meta)` powstaje przy build_world,
  nie jest w gicie (tak jak po 0179) — decyzja lidera.
- `runoff_shuffle` w regionie C: jeden wpis `facade_rules` w `overrides.yaml` C przy najbliższej regeneracji lidera
  (zmieni chunki z halami > 24 m).
