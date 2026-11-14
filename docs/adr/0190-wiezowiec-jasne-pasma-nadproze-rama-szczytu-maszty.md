# ADR 0190 — wieżowiec przy Kwadracie: jasne okna pasm pod ciemną linią nadproża, białe ramy kolumny szczytu, maszty na dachu (override `roof_masts`)

Status: PROPOSED (s20, 2026-11-14; do recenzji visual-critic). Źródło: `docs/reports/REVIEW-2026-11-13-s19-0180-r2.md` (P2-3, P2-4, P2-5, „skok LOD
NW”), ADR 0180 §4. Gałąź `tower2-0190` (main fd5f124a7 scalony; poprawka `FAR_PLAIN_U` z ADR 0184 wzięta ze
scalenia, nie powielona).

## 1. Kontekst (zmierzone)

Budynek `bdot:2BE4B431-CA0F-1BF0-E053-CC2BA8C0D140` (11 kondygnacji, 41,81 m). Referencje: Mapillary richlv
177786140912399 / 178689077481862 (2020-08-15, CC BY-SA 4.0, `docs/LICENSES.md`), ortofoto GUGiK 2024-05-27 (0,25 m).

- **Pasma SE (P2-3).** Na obu zdjęciach (wycinki 3×) okna pod każdą ciemną linią są tak jasne jak ściana, ciemnych
  jest tylko kilka szyb na pasmo; ciemna jest cienka linia nad pasmem. W r2 pasmo było mieszanką komórek `off` 0 / 2 /
  4 (beżowa roleta, czyste szkło, biała żaluzja) bez linii nadproża: luminancja 85–130 przy ścianie 150.
  Pomiar atlasu (`T_facade_atlas_BaseColor`): komórka `off` 4 — ciemne szkło do 0,30 wysokości, biała żaluzja (163)
  od 0,33; `off` 2 — biała rama (199), szkło 36–117; `off` 0 — beż 145. Atlas dalekich rzędów: ściana 187, żaluzja 172.
- **Kolumna szczytu (P2-4).** r2 użyło `variants: [4]` opisanego jako „czyste szkło” — to biała żaluzja w szarej
  ramie. Rama „tylko po prawej” w `stretch-02` to ościeże 0,12 m widziane pod kątem (jedno ościeże zasłonięte), nie
  rama okna. „Jasne kwadraciki pod 2 oknami NE” to jednostki klimatyzacji z zestawu elewacji (`facade_kit`, komórka
  `ac`) — na zdjęciu szczytu SW też wiszą dwie pod oknami 4. i 5. od góry; zostają.
- **Ton szczytu.** Zdjęcia: mediana sRGB szczytu (216, 208, 177) w 5 polach (213–218 / 204–211 / 172–184); render r1
  (225, 211, 179). Różnica ≤ 9 na kanał — mniejsza niż rozrzut między polami zdjęcia; `plaster_beige` bez zmian
  (wspólny materiał wielu budynków).
- **„Skok LOD NW”.** Tier Low rysuje wyłącznie LOD1 budynków (`chunk_*.low.glb` nie zawiera warstwy `buildings`),
  LOD0 jest tylko na High — recenzja r2 oglądała więc w obu obrazach LOD1. Kamera `stretch-02` stoi w (663, −517),
  wieżowiec w (577, −562): patrzy z ENE i widzi szczyt NE oraz ścianę **SE**, nie NW (tak samo `a184_tower_p` z ADR
  0184 = SE, `a184_tower_n` = NW). „Kod kreskowy z beżowymi roletami” to pasma SE (komórka `off` 0) — usunięte
  razem z P2-3. Podgląd programowy obu LOD-ów (`artifacts/tower2-0190/tools/elev2.py`, `elev-base.jpg`) i rendery
  Low / High (`r2/tower-*/t190_nw_60.png`): NW ma ten sam plan okien na LOD0 i LOD1 (rzędy `office_d`, te same
  przęsła). Białych łat NW-LOD1 w silniku nie ma (kamery `t190_nw_*`, `a184_tower_n`).
- **Białe pionowe kreski na narożnikach i w ścianie NW** (ADR 0184 §4, `a184_tower_n`; widać je też na zrzutach z
  telefonu `g3a_eye_s0012`): rury spustowe z ocynku. Reguła biur wiesza rurę 0,35 m od każdego końca każdej
  krawędzi obrysu > 8 m — tu 8 rur: para przy każdym narożniku i para 0,7 m od siebie w środku ściany NW, gdzie
  stykają się dwie współliniowe krawędzie BDOT. Zdjęcia: ściany SW i SE oraz narożnik S bez rur zewnętrznych.
- **Kolumna szczytu na telefonie** (`docs/reports/REVIEW-2026-11-14-s20-gate3-phone.md`, P2-4: „ledwo widoczna,
  w LOD1 brak”): wycinki 1:1 zrzutów A16 — kolumna jest w obu kadrach, ale szara żaluzja `off` 4 na zacienionej
  ścianie khaki nie ma kontrastu.
- **Dach (P2-5).** Zdjęcia (z południa, ok. 150 m): wysoki maszt kratowy za szczytem SW ok. 0,3 jego szerokości od
  narożnika W, niższy maszt z antenami panelowymi przy narożniku S, cztery krótkie maszty z antenami bębnowymi wzdłuż
  krawędzi SE, anteny panelowe przy narożnikach W i E. Wysokości z proporcji pikseli do ściany 41,8 m: 9,5 m i 6,5 m
  (±15 %), krótkie ok. 3 m. Ortofoto (budynek pochylony o (+15,7; −2,7) m na 41,8 m wysokości): skupisko jasnych
  obiektów nad końcem SW dachu i kilka wzdłuż krawędzi SE — zgodne ze zdjęciami, pozycji pojedynczych masztów nie
  rozdziela.

## 2. Decyzja

1. **Światła pasma `glazing: light`** (`frontage.BAND_LIGHTS`, `band_lights`): 62 % biała żaluzja opuszczona, 28 %
   okno `off` 4 (żaluzja w 2/3), 10 % czyste szkło `off` 2; udziały WORKING_VALUE. Wybór haszowany per światło,
   jedna lista dla obu LOD-ów (8. pole krotki `facade_windows`). Żaluzja opuszczona: żadna komórka okna w atlasie nie
   jest jaśniejsza niż 172 / 255 (pomiar wszystkich `w1`/`w2`/`w3`/`off`/`bwin`), a komórka `off` 4 dała w silniku
   (r1, Low) 109 przy ścianie 154 — dlatego żaluzją jest najjaśniejsza biała żebrowana powierzchnia atlasu, wnętrze
   komórki blachy trapezowej `balf` 1 (202 / 255; w atlasie dalekim 213 przy neutralnej ścianie 187):
   `frontage.BLIND_CELL`, `blind_rect` (LOD0, atlas elewacji), `blind_far_uv` (LOD1, ten sam wycinek w rzędzie
   `balcony_1` atlasu dalekiego — bez nowej tekstury i materiału).
2. **Linia nadproża `lintel_m`** (`frontage.facade_lintels`): ciemny pas nad każdym pasmem, 5 cm poza pasmo z obu
   stron; LOD0 = profil 8 cm przed licem (czoło, spód, wierzch), LOD1 = jeden quad 6 cm przed licem (bez
   z-fightingu), materiał `hall_flashing` (okapnik attyki — rysowany już na obu LOD-ach). Wieżowiec: 0,15 m. Czym
   jest ta linia (żaluzja przeciwsłoneczna czy cień szczeliny) — ze zdjęć nie wynika: WORKING_VALUE.
3. **Kolumna szczytu:** `variants: [2]` (biała rama, czyste szkło), `reveal_m: 0.06` (nowe pole reguły; domyślnie
   0,12) — rama jest w komórce atlasu po obu stronach, a płytkie ościeże nie zasłania jej z ukosa.
4. **Override `roof_masts`** (authored_override, przeżywa reimport; `frontage.roof_mast_specs` / `roof_masts`):
   lista struktur `{kind: lattice | pole, facing, u, inset_m, height_m, side_m, sectors, dishes, aim_deg}`
   zakotwiczonych do ściany o danym kierunku (ułamek długości + odsunięcie w głąb dachu — bez współrzędnych).
   Maszt kratowy: 4 nogi, pierścienie, przekątna na pole i ścianę, iglica; anteny panelowe 0,28 × 0,12 × 2,0 m,
   bębny radiolinii 0,6 m (WORKING_VALUE, typowe klasy sprzętu; bez oznaczeń operatorów). LOD1 zachowuje wszystkie
   struktury (sylwetka dachu z 150 m): grubsze nogi, połowa pól, bez pierścieni, bębny jako pudełka. Materiały:
   `downpipe` (ocynk) i `plaster_white` — chunk 6_6 rysuje oba na obu LOD-ach.
   Wieżowiec: 8 struktur (2 kratowe 9,5 m / 6,5 m, 4 maszty z bębnami, 2 z panelami). Liczba i rodzaje ze zdjęć;
   pozycje wzdłuż ścian ±2 m, odsunięcia i liczba anten na maszcie: **UNVERIFIED**.
5. `frontage.lod1_facade` bierze gładki pasek z `FA.FAR_PLAIN_U` (zalecenie ADR 0184 §3).
6. **Override `downpipes: false`** (authored_override budynku typu `office`): bez rur spustowych na elewacjach
   (dach płaski za attyką — odwodnienie wewnętrzne; NW / NE bez zdjęcia: WORKING_VALUE). Reguła ogólna (pary rur na
   współliniowych krawędziach innych biur) bez zmian — patrz Otwarte.

Odrzucone: nowa komórka atlasu „jasne okno” i nowy rząd atlasu dalekiego (zmiana tekstur wspólnych dla wszystkich
bloków i biur, w toku ADR 0184); zmiana albedo `plaster_beige` (różnica do zdjęcia w granicach rozrzutu pomiaru);
reguła NW przez `facade_windows` (brak skoku do naprawienia — pkt 1).

## 3. Budżet (A/B, tier Low)

| Wielkość | Wynik (zmierzony) |
|---|---|
| draws, tier Low, 48 kamer kontrolnych, baza → r1 (ten sam kod poza tą zmianą) | **+0 we wszystkich 48** |
| trójkąty w kamerach, baza → r1 | min +0,00 %, maks. **+0,38 %** (`cab-grain` 200 957 → 201 711); `stretch-02` +0,22 % |
| trójkąty wieżowca | LOD0 4553 → **5307**, LOD1 747 → **1179** (maszty +982 / +448, nadproża +132 / +44, rury −360 / −60) |
| manifest świata po scaleniu main (main → r2) | zmieniony tylko chunk 6_6: `buildings` 19 944 → 20 698 (+754), `buildings_lod1` 3372 → 3804 (+432); pozostałe 64 chunki bit w bit |
| nowe materiały / tekstury | 0 (maszty `downpipe` + `plaster_white`, nadproże `hall_flashing`, żaluzja = istniejące atlasy) |

A = baza: gałąź przed tą zmianą (8145d1d68 = main + 0184), przebudowana i wyrenderowana tym samym łańcuchem
(`artifacts/tower2-0190/tools/full.ps1 -Tag base`); B = r1 (ta zmiana na tej samej bazie). r2 (po scaleniu main i
zamianie komórki żaluzji) ma tę samą geometrię co r1 (te same liczby trójkątów) — zmieniły się tylko UV świateł.
`artifacts/tower2-0190/r1/budget-vs-base.txt`. Telefon: niezmierzony (bez adb w tym zadaniu).

## 4. Walidacja

VALIDATION_PLACEHOLDER

## 5. Otwarte

OPEN_PLACEHOLDER
