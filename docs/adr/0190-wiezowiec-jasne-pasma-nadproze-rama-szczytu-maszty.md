# ADR 0190 — wieżowiec przy Kwadracie: jasne okna pasm pod ciemną linią nadproża, białe ramy kolumny szczytu, maszty na dachu (override `roof_masts`)

Status: przyjęty (scalony do main 2026-11-14, `baae5f0e0`; status zaktualizowany 2026-11-16); pierwotnie: PROPOSED (s20, 2026-11-14; do recenzji visual-critic). Źródło: `docs/reports/REVIEW-2026-11-13-s19-0180-r2.md` (P2-3, P2-4, P2-5, „skok LOD
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
  ramie (pomiar komórek atlasu), na zacienionej ścianie bez kontrastu. Przyczyna „ramy tylko po prawej” w `stretch-02`
  (kadr Low) nie została ustalona — nie odtwarzałem jej na r2; po zmianie na komórkę `off` 2 rama jest po obu stronach
  w `stretch-02` i w kadrach krytyka telefonu. „Jasne kwadraciki pod 2 oknami NE” to jednostki klimatyzacji z zestawu
  elewacji (`facade_kit`, komórka `ac`, LOD0) — na zdjęciu szczytu SW też wiszą dwie pod oknami 4. i 5. od góry; zostają.
- **Ton szczytu.** Zdjęcia: mediana sRGB szczytu (216, 208, 177) w 5 polach (213–218 / 204–211 / 172–184); render r1
  (225, 211, 179). Różnica ≤ 9 na kanał — mniejsza niż rozrzut między polami zdjęcia; `plaster_beige` bez zmian
  (wspólny materiał wielu budynków).
- **„Skok LOD NW”.** Tier Low dostaje LOD0 budynków tylko w chunkach do 60 m od trasy startowej
  (`RegionImporter.LowBuildingsLod0M`), poza tym LOD1; który LOD pokazywały kadry recenzji r2 — nie ustalałem. Kamera `stretch-02` stoi w (663, −517),
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
   0,12; dotyczy tylko LOD0) — na zdjęciach ramy są niemal w licu tynku. Obejrzane na High z 60 m
   (`r2/z/LH-sw60-gable.jpg`): rama po obu stronach, wąski cień ościeża.
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

Łańcuch (sloty heavy / unity, `artifacts/tower2-0190/tools/full.ps1`): baza i r1 na kodzie sprzed scalenia main
(A/B budżetu), r2 po `git merge origin/main`: `build_world` exit 0 → import exit 0 → vqa Low-clear 48 kamer → kamery
wieżowca (`tower_cameras.json`: 4 ściany z 60 m i 200 m, z południa 150 m, dach × 2, kadry krytyka telefonu
`g3a_eye_s0012` / `s0062`) Low clear + overcast i **High clear** → SBS Low **42 + 42 pary**
(`sbs-r2/pairs/Low-clear|Low-overcast`). Dowody (poza gitem): `artifacts/tower2-0190/` w katalogu głównym.

| Punkt | Wynik (zmierzony / obejrzany) |
|---|---|
| P2-3 pasma SE — **częściowo** | `t190_se_200`, luminancja ściany 154: przeszklenie pasma baza 96 → r1 109 → **r2 121** (p90 147) na Low; High **125** (p90 176 > ściana 156); overcast 125 przy ścianie 161. Najciemniejszy wiersz pasma (nadproże) 91 (Low), 59 (High). Okna nie są jaśniejsze od ściany: światła z żaluzją sięgają jej poziomu, średnią obniżają żebra blachy, ramy i 38 % świateł z ciemnym szkłem. Beżowych rolet brak. `r2/z/se200-s150.jpg`, `r2/z/LH-se60.jpg` |
| P2-4 kolumna szczytu | biała rama po obu stronach okna, ciemne szkło; czytelna w kadrach krytyka telefonu `g3a_eye_s0012` / `s0062` na Low i High (`r2/z/gable-s0012-s0062.jpg`; przed: szare prostokąty bez kontrastu) oraz w `stretch-02` (`r1/z/st02-ba.jpg`). Ton szczytu w słońcu: mediana (227, 212, 180) wobec zdjęcia (216, 208, 177) |
| P2-5 maszty | 8 struktur na obu LOD-ach, widoczne z 150 m i w parach SBS (`r2/photo-vs-r2-s150.jpg`, `r2/before-r2clear-r2overcast-s150.jpg`, `sbs-r2/pairs/Low-overcast/sbs-g3-a-178689077481862.jpg`) |
| NW Low ↔ High | ten sam raster i ton okien, bez białych łat, bez rur (`r2/z/LH-nw60.jpg`) |
| kreski narożnika | znikają na obu tierach (porównanie `r1/z/s150-ba.jpg`, `r1/z/st02-ba.jpg`) |
| testy | `tests/gis/test_tower_0190.py` 10 nowych; pełny `pytest tests/gis`: **1115 passed, 2 xfailed** (`logs/pytest-gis.log`; po `fidelity/run.py`, exit 0); EditMode: **581 total, 580 passed, 0 failed, 1 skipped** (`logs/editmode.log`) |

Który LOD rysuje dana kamera Low (chunk 6_6 leży przy trasie: LOD0 z bliska, LOD1 dalej) — nie rozdzielałem w
kadrach; zgodność obu siatek sprawdza podgląd programowy (`elev-r2.png`: LOD0 nad LOD1) i testy.

Porównanie ze zdjęciami (Mapillary 177786140912399 / 178689077481862): zgodne — sylwetka z masztami, gładki szczyt z
jedną kolumną biało obramowanych okien, ściana SE w poziome cienkie ciemne linie z jasnymi oknami pod nimi. Różni się:
ściana SE w renderze clear jest w cieniu (154) zamiast w słońcu (ok. 249 na zdjęciu) — kierunek słońca, poza zakresem;
napis na szczycie (marka) nie jest odtwarzany; wysoki maszt na zdjęciu ma odciągi i więcej anten.

## 5. Otwarte

- Recenzja visual-critic r2 (ten ADR jest PROPOSED do jej wyniku); zrzuty z telefonu (APK Low na A16).
- **P2-3 do końca**: okno jaśniejsze od ściany wymaga nowej komórki atlasu (biała roleta / jasne odbicie nieba,
  albedo ≥ ściany) w `facade_atlas` i rzędzie dalekim, albo zmiany w shaderze dalekiej elewacji — zmiana tekstur
  wspólnych dla wszystkich budynków, osobne zadanie. Żebra blachy z 200 m dają pionowe prążki (aliasing mipów).
- Słupki między światłami z żaluzją: LOD0 ich nie ma (komórka blachy nie ma ramy) — z bliska na High pasmo żaluzji
  jest ciągłe na kilka świateł.
- Maszty: pozycje ±2 m, odsunięcia, liczba anten — UNVERIFIED (sesja zdjęciowa właściciela, pkt 6); bez odciągów,
  drabin kablowych i oświetlenia przeszkodowego.
- Reguła ogólna biur: para rur spustowych w miejscu styku dwóch współliniowych krawędzi obrysu (inne budynki) —
  scalić współliniowe krawędzie przed rozstawieniem rur.
- NW: stolarka antracytowa (`office_d`, wybór haszowany) przy białej stolarce szczytów i SE — brak zdjęcia NW;
  ewentualny override rodziny stolarki.
- `new-agent-worktree.ps1` nie kopiuje `art-source/world/materials/<set>/<tier>/*.png` ani
  `artifacts/sbs-gate3/rectified` — pierwszy import przebudowuje 159 zestawów PBR (ok. 90 min), a SBS nie składa par.
- Komentarz override `g3a-office-tower-colour` w `overrides.yaml` przypisuje „ramę po jednej stronie” ościeżu —
  to hipoteza, nie ustalenie; poprawić przy najbliższej regeneracji (zmiana pliku zmienia `sources_sha256` manifestu).
- SE w cieniu w oświetleniu clear, ton szczytu (Δ ≤ 11 / kanał) — bez zmian, jak w ADR 0180.
