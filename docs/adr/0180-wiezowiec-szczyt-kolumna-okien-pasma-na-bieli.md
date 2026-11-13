# ADR 0180 — wieżowiec przy Kwadracie: gładki szczyt z jedną kolumną okien, długa elewacja z pasmami okien na bieli (reguła `facades`)

Status: ACCEPTED warunkowo (r2, 2026-11-13, s19): recenzja `docs/reports/REVIEW-2026-11-13-s19-0180-r2.md` — SCAL
warunkowo (warunek: ten ADR opisuje r2). Runda r1 (s18): recenzja `docs/reports/visual/REVIEW-2026-11-13-s18-0180.md`. Źródło: `docs/reports/visual/REVIEW-2026-11-13-s17-0171.md`, P1 kadrów
`sbs-g3-a-177786140912399` / `178689077481862`: „ściana szczytowa dostała pełną siatkę ~6×12 punktowych okien. Na
zdjęciu szczyt jest gładki, piaskowy, z jedną kolumną okien, a długa elewacja ma poziome pasma okien na bieli”.

## 1. Ustalenia (zmierzone)

Budynek `bdot:2BE4B431-CA0F-1BF0-E053-CC2BA8C0D140` (BDOT10k: 11 kondygnacji, „siedziba firmy”; LoD1 2024 41,81 m;
kondygnacja 3,69 m z `storey_plan`). Obrys BDOT10k: szczyty SW / NE 16,09 / 16,41 m (azymut normalnej 208° / 28°),
ściana SE 18,42 + 6,39 + 10,93 m z uskokami 1,8 / 1,4 m (118°), ściana NW 9,73 + 11,59 + 9,60 + 6,18 m (298°).
Kamery SBS stoją ok. 150 m na południe: widać szczyt SW (z lewej) i ścianę SE (z prawej).

Zdjęcia tylko jako referencja (Mapillary richlv 177786140912399 / 178689077481862, 2020-08-15, CC BY-SA 4.0 — w
rejestrze `docs/LICENSES.md`; wycinki 4× z `Data/raw/mapillary`):

- **Szczyt SW**: gładka piaskowa ściana, JEDNA kolumna dwudzielnych okien w białych ramach, po jednym na kondygnację
  (9 widocznych, dolne zasłania wiata stacji), oś kolumny na 0,52 ± 0,04 szerokości ściany (pomiar w obu zdjęciach),
  szerokość okna 2,0 ± 0,3 m i wysokość ok. 0,45 kondygnacji (stosunki pikseli do krawędzi 16,09 m i podziałki
  kondygnacji). Napis na szczycie to marka — nie odtwarzamy.
- **Ściana SE**: biała, na każdej kondygnacji cienka ciemna linia z oknami pod nią (11 linii; okna ok. 0,33
  podziałki kondygnacji); każde pasmo to krótki odcinek przy narożniku południowym (0,03–0,20 długości 37 m) i długi
  odcinek od 0,30. Uskoków obrysu BDOT (1,8 m) na zdjęciu nie widać.
- Ściany NE i NW: brak otwartego zdjęcia.

Stan po 0171 (`ribbon: false, bands: false`): ta sama siatka okien punktowych na każdej ścianie, jeden ton
`plaster_beige` — generator biurowca nie miał pojęcia „inna elewacja na szczycie niż na ścianie długiej”.
Przy okazji zmierzone na `T_facade_far_BaseColor.png`: „gładki” pasek atlasu dalekiej elewacji `FAR_PLAIN_V =
(0,65; 0,95)` ma od v 0,88 krawędź płyty balkonowej pierwszego rzędu (196–206 / 255 zamiast 187) — wysoki pojedynczy
quad to ukrywa, mały kawałek ściany między oknami pokazałby pasek.

## 2. Decyzja

1. **Nowy klucz override budynku `facades`** (authored_override w `overrides.yaml`, przeżywa reimport; tylko typ
   `office` bez `frontage`): lista reguł per kierunek ściany. Pola: `facing` (jak we `frontage`, ±30°),
   `min_len_m` / `max_len_m` (wybór krawędzi obrysu po długości — stabilne względem BDOT, bez współrzędnych),
   `windows: ribbon | column | blank`, `sill_m` / `head_m` (nad podłogą kondygnacji), `spans` (ułamki ściany dla
   pasm), `u` i `window_w_m` (kolumna), `wall_material`, `from_storey`. Pierwsza pasująca reguła wygrywa; ściany bez
   reguły (uskoki 1,4–1,8 m) zostają przy regule haszowanej i kolorze budynku. Walidacja (`frontage.facade_rules`):
   nieznany kierunek / typ / materiał bez wariantu `__far_*` / złe `spans` = błąd autora, nie cichy fallback.
2. **Jedno źródło prostokątów dla obu LOD-ów** (`frontage.facade_windows`): LOD0 wycina je jako otwory z komórkami
   atlasu elewacji (`buildings_mesh.authored_openings`: pasmo = komórki `off` rzędu `ribbon`, kolumna = okno rzędu
   `office`, drzwi wejściowe pod kolumną albo w środku ściany głównej), LOD1 rysuje je jako quady atlasu dalekich
   rzędów w gładkim pasku tego samego materiału `<ściana>__far_<rodzaj>` (`frontage.lod1_facade`: kolumny quadów bez
   nakładania się — brak z-fightingu, bez geometrii otworów). Gładki pasek autorskich ścian: v 0,65–0,85 (pkt 1).
3. **Pasmo biegnie od filara do filara** (0,4 m od końca krawędzi), dzielone na światła ok. 1,5 m
   (`ribbon_lights`), zamiast rastra 3 m — krawędź 6,39 m dostaje pasmo 5,6 m, a nie 3 m.
4. **Override wieżowca** `g3a-office-tower-colour`: `wall_material: plaster_white`; szczyty SW / NE: `column`,
   `u: 0.52`, okno 1,8 × 1,6 m, `plaster_beige`; ściany SE / NW: `ribbon`, parapet 1,0 m, nadproże 2,3 m; krawędź SE
   18,42 m: `spans: [[0.06, 0.40], [0.60, 1.0]]` (stan r1 — zastąpiony w pkt 5). WORKING_VALUE: wymiary okien (szacunek z pikseli), cała elewacja NE
   i NW (kopie przeciwległych, confidence low).

5. **Runda r2** (recenzja s18 0180: P1 biały pionowy pas uskoku BDOT na SE, P2 pasma rozbite, ciemne szklenie,
   okna szczytu za małe). Override `g3a-office-tower-colour` po r2:
   - `footprint_open_m: 3.3` — autorskie wyprostowanie obrysu: otwarcie morfologiczne w `buildings_mesh.load`
     (`buffer(-d).buffer(+d)`, narożniki ścięte, potem `simplify(0.15)`) usuwa występy węższe niż 6,6 m. Występ BDOT
     6,4 × 1,8 m na ścianie SE znika; SE = jedna krawędź 37,12 m. Uzasadnienie: żadne zdjęcie ani ortofoto
     2024-05-27 nie pokazuje uskoku; jako pryzmat 42 m ściana 1,8 m była nasłonecznionym białym pasem na całą
     wysokość. confidence medium (czym uskok BDOT jest przy gruncie — nieznane).
   - `wall_material: plaster_beige` (kolor budynku); SE: `windows: ribbon`, `glazing: light` (jasne okna rzędu
     `office` obok siebie, jedno okno na światło, w materiale `plaster_white__far_ribbon` — wszystkie `__far_*`
     mapują ten sam atlas, więc bez nowego draw), `wall_material: plaster_white`, `min_len_m: 30`,
     `spans: [[0.03, 0.20], [0.30, 1.0]]` (krótki odcinek przy narożniku S + długie pasmo, jak na zdjęciach).
   - Szczyty SW / NE: `column`, `u: 0.52`, okno 2,0 m (było 1,8), parapet 0,9 m, nadproże 2,5 m, `variants: [4]`
     (komórka atlasu z czystym szkłem, nie rolety); ościeże okien autorskich 0,12 m (było `REVEAL_ETICS`).
   - NW: bez reguły (ortofoto 2024-05-27, przechył budynku: bladożółta ściana z regularną siatką okien punktowych,
     ok. 11 rzędów) = haszowane okna punktowe w kolorze budynku `plaster_beige`.
   - Walidacja reguł: nieznane `glazing` / `variants` bez okna w rzędach grupy = błąd autora.
   - Trójkąty wieżowca r2: **LOD0 4553, LOD1 747** (r1: 4076 / 650; baza 8504 / 300).

Bez nowych materiałów i tekstur: `plaster_white`, `plaster_beige`, `plaster_white__far_ribbon`,
`plaster_beige__far_office` chunk 6_6 rysuje już na obu LOD-ach (inne budynki).

Odrzucone: `frontage` z listą 11 przeszkleń na ścianę (prawdziwe otwory i szkło na LOD1: nowy materiał szkła w LOD1
chunku 6_6 i kilka tysięcy trójkątów); nowe rzędy atlasu dalekiej elewacji z jasnymi pasmami (zmiana tekstury
wspólnej dla wszystkich bloków i biur); poprawka `FAR_PLAIN_V` w regule ogólnej (zmienia piksele wszystkich budynków
— osobne zadanie).

## 3. Walidacja

Runda r1: `build_world` exit 0, import exit 0, vqa Low-clear exit 0, SBS Low clear + overcast 42 + 42 pary
(`scripts/sbs-low-pairs.ps1`, preflight OK). Baza = ta gałąź przed zmianą, przebudowana i wyrenderowana tym samym
łańcuchem (`artifacts/tower-0180/tools/base.ps1`). Dowody (poza gitem): `artifacts/tower-0180/` w katalogu głównym —
`sbs-r1/pairs/Low-clear|Low-overcast`, `before-after-Low-clear|overcast.jpg` (0171 nad 0180), `tower-zoom-r1-clear-overcast.jpg`,
`tower-ne-gable-stretch-02.jpg`, `tower-lod1-elevations-SW-SE-NW-NE.png` (podgląd programowy LOD1), `r1/budget-vs-base.txt`,
`r1/pixel-diff-vs-base.txt`, `base/`, `tools/`, `logs/`.

| Wielkość | Wynik (zmierzony) |
|---|---|
| draws, tier Low, 48 kamer kontrolnych | **+0 we wszystkich 48** |
| trójkąty w kamerach | min −2,09 % (cab-grain), maks. +0,16 % (cab-materials) |
| prymitywy LOD1 / LOD0 budynków (65 chunków, `primdiff`) | netto 0 |
| trójkąty wieżowca | LOD0 8504 → 4076; LOD1 300 → 650 (LOD1 budynków regionu +350, ok. +0,37 %) |
| kamery kontrolne baza → r1, piksele z \|Δ\| > 25 | stretch-02 6,1 %, kwadrat-park-gate 1,5 %, pozostałe 46 ≤ 0,76 % (mediana 0,0 %) |
| testy | `test_buildings_0180` 10 nowych; z 0171 / 0167 / g3b_frontage / world_v31 59 zielonych; pełny `tests/gis`: 1076 zielonych + 2 czerwone w przebiegu równoległym z przebudową świata (`test_report_not_stale` — `fidelity_qa.json` odświeżone `fidelity/run.py`; `test_export_is_deterministic` — wyścig z przebudową chunku 6_6); oba powtórzone po przebudowie: zielone (`logs/pytest-determinism.log`, 4 passed; `test_road_fidelity` 9 passed) |

Obejrzane (pętla wizualna): `sbs-g3-a-178689077481862` Low-clear i `177786140912399` Low-overcast oraz `stretch-02`
(ściana NW + szczyt NE z 40 m). Szczyt: gładki, piaskowy, jedna kolumna okien po jednym na kondygnację; średni sRGB
szczytu w słońcu (225, 211, 179) wobec zdjęcia (217, 209, 177). Ściana długa: jasna z poziomymi pasmami (krótki odcinek
przy narożniku + długi), bez kratki; w renderze clear jest w cieniu — ściana między pasmami (158, 158, 151), zdjęcie
w słońcu (249, 248, 246). Uskok obrysu BDOT (ściana 1,8 m zwrócona na SW) jest w renderze w słońcu i rysuje jasny
pionowy pas na zacienionej ścianie SE — na zdjęciu (obie ściany w słońcu, biel prześwietlona) niewidoczny.
Z-fightingu ani szczelin nie widać w żadnym z obejrzanych kadrów.

Runda r2 (s19): `build_world` exit 0, import exit 0, vqa Low-clear exit 0, SBS Low clear + overcast **42 + 42 pary**
(`artifacts/tower-0180/sbs-r2/pairs/Low-clear|Low-overcast`). Budżet baza → r2 (`artifacts/tower-0180/r2/budget-vs-base.txt`):

| Wielkość | Wynik r2 (zmierzony) |
|---|---|
| draws, tier Low, 48 kamer kontrolnych | **+0 we wszystkich 48** |
| trójkąty w kamerach | min −1,65 % (cab-grain), maks. +0,20 % (cab-materials) |
| trójkąty wieżowca | LOD0 4553, LOD1 747 |
| piksele \|Δ\| > 25 baza → r2 (recenzja r2) | stretch-02 5,38 %, kwadrat-park-gate 1,16 %, reszta ≤ 0,73 %; tylko kamery z wieżowcem |
| testy | `pytest tests/gis -k "building or tower"` i EditMode — wyniki w live `artifacts/live/tower-0180.md` (s19) |

Wynik recenzji r2 (visual-critic, s19): **SCAL warunkowo**, brak P0 / P1 wizualnych. P1 r1 naprawione: biały
pionowy pas na SE zniknął w obu kadrach i obu oświetleniach — luminancja wierszy ściany SE w 177786 z 237–255 (r1,
clear) do maks. ok. 155 (152–161, poziom ściany). Pasma SE ciągłe (krótki odcinek + jedno długie). Szklenie pasm
85–130 (r1: 46–78). Z 150 m budynek jest rozpoznawalny jako ten ze zdjęcia.

## 4. Otwarte (P2, z recenzji r2)

- **NW: skok wyglądu LOD0 ↔ LOD1** — LOD0 = poziome rzędy haszowanych okien z beżowymi „roletami” („kod kreskowy” z
  40 m), LOD1 = siatka wysokich ciemnych okien podwójnych. Jeden wzór dla obu LOD-ów (np. reguła NW przez
  `facade_windows`); rolety ograniczyć do `variants` z czystym szkłem.
- **NW LOD1: białe łaty u góry** (3 górne kondygnacje, przerwy między kolumnami okien i prawa krawędź). Ściana NW
  idzie ogólną ścieżką LOD1 (bez reguły); hipoteza UNVERIFIED: ten sam jasny pasek `FAR_PLAIN_V` > 0,88 (pkt 1
  ustaleń) — poprawka w regule ogólnej zmienia wszystkie budynki, osobne zadanie. Nie naprawione w r2 (koszt > 1 runda).
- **Okna szczytu**: rama tylko z jednej strony; jasny kwadracik pod 2 oknami NE (kondygnacje ok. 5 i 7 od góry) —
  sprawdzić UV komórki `variants: [4]` i sąsiada w atlasie (bleeding). Z 150 m okna to szare kwadraty bez białej ramy.
- **Szkło pasm SE ciemniejsze od ściany** — na zdjęciu okna jasne, ciemna tylko linia nadproża (nowa komórka atlasu;
  razem z ekspozycją SE).
- **Szczyt SW kremowy zamiast oliwkowego** w clear — albedo `plaster_beige` w stronę oliwki albo wariant dla budynku.
- **Maszty i anteny na dachu** — brak (osobne zadanie).
- **SE w cieniu** (ok. 150 vs ok. 249 na zdjęciu) — kierunek słońca / ekspozycja poza zakresem.
- Szczyt SW w LOD1 ma 10 okien, NE 11 (brak okna parteru SW — prawdopodobnie wejście / wiata; do potwierdzenia).

## 5. Otwarte (z r1, aktualne)

- Zrzuty z telefonu (APK Low na A16).
- Elewacje NE i NW oraz parter: bez otwartego zdjęcia (sesja zdjęciowa właściciela, pkt 6).
- `FAR_PLAIN_V` do 0,95 w regule ogólnej (pkt 1 ustaleń) — jaśniejszy pasek u góry gładkich quadów LOD1 bloków i biur.
- `generated/` po scaleniu: przebudowa świata + powtórka SBS Low.
