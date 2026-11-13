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
   hala 12,72 m `hall_wall_graphite` bez pasów; blok narożny (14 × 7 m) i drugi blok frontowy (8 × 10 m) grafitowe
   **9,0 m**; wnęka między nimi, skrzydło biurowe wzdłuż ściany SW (10,1 m głębokości z ortofoto) i przybudówka
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
   warstwy między jej „cichymi” kolumnami (10 miejsc, gdzie w ±0,25 m nie ma smugi — szew nie tnie żadnej smugi;
   zmierzone na teksturze High: maks. 0,004 przy średniej warstwy 0,017). Bloki (1,6–4,4 m) układane w kolejności
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
   lotniska z OSM, oczy 1,7 m nad NMT, azymut 261° (wzdłuż pasa na zachód), obiektyw 30° (pas ma stąd 0,56°
   wysokości), widoczność nad NMT sprawdzona (teren 3–10 cm pod promieniem).

## Czy to wygląda jak trawiasto-asfaltowe lotnisko aeroklubu (OSM aeroway + ortofoto)
- OSM: `958211700` runway 09R/27L asphalt 1350 × 30 m (oś local −1446,3 −227,2 → −115,7 −192,3 — zgodna z obrysem
  0179 co do 1 m; w kaflu wschodnie 919 m); `303368859` runway 09L/27R **grass** 860 m (wschodnia połowa w kaflu,
  ~150 m na N od asfaltu); hangary, płyta, drogi kołowania i lądowiska śmigłowców leżą **poza kaflem** (E < −1024).
- Ortofoto: pas trawiasty nie ma oznakowania ani znaczników — w grze zostaje łąką `open_ground` (zgodne).
  Asfalt ma pełne oznakowanie — dodane (pkt 4).

## Budżet (A/B) i wyniki
Patrz sekcja „Wyniki” niżej (uzupełniana po buildzie).

## Walidacja
- `tests/gis/test_dojind_0196.py` (10 testów): region C bez nowych rodzajów; ścieżka bez tabeli = stary quad;
  bloki pokrywają ścianę, szwy na cichych kolumnach, ta sama kolumna tekstury co 24 m na < 10 % ściany (było 100 %);
  bramy (przypięcie, usunięcie okna reguły, błąd bez ściany); farba pasa w obrysie asfaltu, CCW, lift;
  dane Kuronia 2 (hala grafitowa + 5 części, bez nakładania, suma pól = BDOT ±40 m²), brak nazw firm w danych.

## Otwarte
- Wysokości części Kuronia 2, rozmiar i położenie bram: UNVERIFIED do M63 / sesji zdjęciowej właściciela.
- Kuronia 2: czerwona linia między parterem a piętrem, czerwony daszek wejścia, urządzenia na dachu przybudówki,
  okładzina kasetonowa bloków (teraz blacha trapezowa `hall_wall_graphite`).
- Oznaczenie „27 L” na pasie; pas trawiasty 09L/27R bez wyróżnienia w trawie (koszona murawa).
- `runoff_shuffle` w regionie C: jeden wpis `facade_rules` w `overrides.yaml` C przy najbliższej regeneracji lidera
  (zmieni chunki z halami > 24 m).
