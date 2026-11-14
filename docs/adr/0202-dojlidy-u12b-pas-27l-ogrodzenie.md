# ADR 0202 — Dojlidy: ogrodzenie łańcuchowe U-12b zamiast słupków U-12c, pas 09R/27L z „27 L”, zielone ogrodzenie lotniska

Status: Proposed (agent world-builder, s20, gałąź `dojfix-0202`), 2026-11-14. Do scalenia przez lidera.
Poprzednicy: ADR 0183 (słupki z łańcuchem), ADR 0196 (farba pasa). Podstawa: recenzja cloud M58
`docs/reports/REVIEW-2026-11-14-s20-cloud-m58.md` §5 i paczka `research/cloud/p15-dojlidy-details/` z erratą.
Zakres: tylko region `bialystok-dojlidy`. Nie ruszane: zieleń (`dojgreen-0186`), brama szpitala (`hospgate-0189`),
`stage.py` / `props.py` / `export.py` (zmieniają je obie gałęzie Argona).

## Kontekst
1. ADR 0183 wziął wysokość słupków z przepisu dla **U-12c** (słupki blokujące, 0,6–0,8 m). Na P11-063 stoi **U-12b**
   (ogrodzenie łańcuchowe). Dz.U. 2019 poz. 2311 zał. 4 pkt 5.4, s. 843 (cytat w recenzji M58 §4; aktu nie czytałem
   ponownie): „Wysokość tych ogrodzeń powinna wynosić 1,10 m. Rozstaw słupków powinien wynosić 1,5 m lub 2,0 m”.
   Pomiar M58: 1,17 / 1,19 m (ESTIMATED), rozstaw 1,90–2,04 m na ortofoto 0,05 m, rząd 13,99 m.
2. Farba pasa (0196) była z ortofoto 0,25 m: brak piątej kreski osi i „27 L”, szerokości zawyżone.
3. Kolor ogrodzenia lotniska wynikał z hasha klucza OSM.
4. M58 (C58-056): NMT z 2018 r. ma wały 2–3 m wzdłuż pasa, których na ortofoto 2025 nie ma.

## Decyzja
### A. Ogrodzenie łańcuchowe (`tools/worldgen/streetscape/chain_bollards.py`)
| stała | było (0183) | jest | źródło |
|---|---|---|---|
| `POST_H_M` | 0,80 | **1,10** | przepis U-12b; pomiar M58 1,17 / 1,19 m mieści go w błędzie |
| `BAY_M` | 1,60 | **2,00** | przepis (1,5 lub 2,0) + ortofoto 0,05 m |
| `BANDS` | ułamki 22/21/25/21/11 % | B 0–0,25, C 0,25–0,50, B 0,50–0,75, C 0,75–1,00, B 1,00–1,10 m | przepis (pasy 25 cm, dolny biały); P11-063: górny biały krótki |
| ucha / zwis | 0,75 / 0,37 m; 0,14 / 0,13 m | 1,03 / 0,51 m; 0,20 / 0,18 m (te same ułamki × 1,10) | P11-063, WORKING_VALUE; zalecenie „do 0,10 m” nie odpowiada zdjęciu |
| malowanie łańcucha | pół przęsła czerwone, pół białe | **całe przęsło jednobarwne**, kolor zmienia się co przęsło, górny i dolny w przeciwnej fazie | P11-063 (7 przęseł, wycinki `view/p063-posts-{a,b}.jpg`), P11-076 |

- Instancja ma tylko obrót wokół pionu, więc naprzemienność = **drugi prototyp** `bollard_rw_chain_b` (górny biały,
  dolny czerwony) obok `bollard_rw_chain` (górny czerwony, dolny biały); ten sam materiał i atlas. `apply` układa je
  na przemian od pierwszego słupka; nowy klucz override `first_upper: red | white` (domyślnie `red`; błędna wartość →
  `stale`). Prefiks `bollard` zachowany (osadzanie, polityka LOD bez zmian w C#).
- `STRIP_SHADE`: lita łata rdzenia LOD0 / taśm LOD1 dla bieli 0,80 → 0,97 farby (czerwień zostaje 0,80). Render r2
  z 4 m: biały łańcuch ginął na bruku — rdzeń ~150 sRGB przy bruku ~143, karty ogniw ~250.
- Override `mickiewicza-kuronia-chain-posts-p11-063`: linia M58 `[[780013.35, 590461.80], [780018.27, 590448.69]]`
  = 8 słupków, 7 przęseł × 2,00 m = 14,0 m (było 11,2 m), ok. 2 m bliżej jezdni; pierwsze przęsło od północy z
  czerwonym łańcuchem u góry (P11-063). `confidence` low → medium (pięć słupków zmierzonych w recenzji leży
  0,01–0,13 m od linii).
- **Nowy wpis `mickiewicza-east-verge-paved-at-chain-posts`** (`paved_area`, `sidewalk_paving`, pas 43 × ~5 m). Powód
  z renderu r1 i sondy `probe.py`: na prawdziwej linii świat miał trawnik (krawężnik → ~4 m trawy → chodnik), słupki
  osiadły 0,2–0,4 m poniżej darni. Ortofoto i P11-063: chodnik jest utwardzony od krawężnika. Wpis jest własnym
  blokiem 0202; w `origin/dojgreen-0186` żaden wpis nie leży bliżej niż 11,7 m od rzędu (`near_row.py`).

### B. Pas 09R/27L (`streetscape/runway_paint.py`, wpis `krywlany-runway-paint`)
- Linie krawędziowe 0,9 → **0,85 m**, oś linii 14,05 → **14,55 m** od osi pasa; poprzeczki progów 1,0 → **1,25 m**,
  sięgają linii krawędziowych (`half_span_m` 14,125); trzon strzałki i linia osiowa 0,45 → **0,35 m**; groty
  3,3 → 3,1 m co 5,5 m, ostrza 2,1 m od poprzeczki (s 15,8 i 210,1).
- **Piąta kreska osi s 0,5–27,9** w trzech kawałkach (0,5–10,15; 15,8–17,775; 19,025–27,9), które kończą się na
  farbie środkowego grotu i poprzeczki 09R — bez podwójnej, współpłaszczyznowej farby.
- **„27 L”**: nowy klucz `designator` — znaki z osi kresek (`GLYPHS`: „2”, „7”, „L”) rozciągnięte na pole
  `s_m` × `width_m`, farba grubsza wzdłuż pasa niż w poprzek (`stroke_m: [0.8, 1.7]`), siatka cięta co 2 m i
  kładziona na powierzchni jak reszta farby (`marking_white`, warstwa `markings`). „27” s 845,9–855,4, „L”
  s 860,9–870,4 (M58 − 422,6), stopy znaków ku końcowi E, „2” na S i „7” na N od osi (±2,6 m), „L” w osi.
  Kształt znaków, grubość kreski i położenie poprzeczne cyfr: z ortofoto 2024 0,25 m (±0,3 m), **WORKING_VALUE** —
  nie cytuję normy lotniczej.
- **Groty jako pełne strzałki** (`arm_m: 4.5`, ramiona ~0,7 m): 0196 rysował kontur 0,14 m, a ortofoto pokazuje
  pełne groty z wcięciem od tyłu. Poza listą zadania; wyszło na nakładce `view/paint_09R_s.jpg`.

### C. Ogrodzenie lotniska
`kind: fence_style`, `fence_green` dla dróg OSM 483199984, 483199985, 542255310. Uczciwie: hash już dawał zieleń obu
drogom leżącym w kaflu (1518 m + 1493 m), więc obraz się nie zmienia — wpis przypina kolor, żeby nie zależał od
klucza. Droga 483199985 leży poza kaflem: `streetscape_qa.json → fences.style_stale: [483199985]` jest oczekiwane.

### D. Wały z NMT 2018 — sprawdzone, **nie ma czego spłaszczać**
- Teren gry to `gugik-nmt-2025-bialystok-dojlidy`: wszystkie arkusze mają w manifeście `akt_data` 2025-04-18.
- Przekroje w poprzek osi co 60 m, ±120 m (`berms.py`, `berms.json`): pas leży na wyprofilowanej grzędzie — spadek
  ok. 2 % w obie strony do ±75–80 m (−1,3…−2,4 m względem osi), dalej płasko. Żadnego grzbietu 70 m na N ani
  50–65 m na S od osi, także przy zachodniej krawędzi kafla (s 20 i 80), gdzie M58 brał próbkę.
- Jedyne grzbiety o wyniosłości > 0,8 m w ±260 m: 0,9–2,0 m, 172–218 m na S od osi, s 610–840. To wąski, kręty wał
  w zaroślach za drogą techniczną (`view/nmt-south-ridge-hillshade.jpg`, `view/ortho-south-ridge.jpg`), poza łąką
  lotniska; na ortofoto 2024 rośnie na nim pas drzew. To on jest „zielonym kopcem” przed lasem w kadrze
  `krywlany_runway` (uwaga z recenzji 0196). Nie spłaszczam: nie jest to wał z M58, a ortofoto mu nie przeczy.

## Budżet (A/B) — Low, overcast, 1920 × 1080, edytor (nie telefon)
A = scena z `main` przed zmianą, B = r3, te same kamery (`cameras.json`). `stats.txt` w `A-Low-overcast/` i `r3-Low-overcast/`.
BUDGET_TABLE
Prototypy: `bollard_rw_chain` i nowy `bollard_rw_chain_b` po 270 / 79 trójkątów (LOD0 / LOD1, bez zmian), `bollard_rw`
78 / 15. Koszt naprzemienności: +1 draw instancjonowany na LOD w kadrze z rzędem, instancji i trójkątów tyle samo
(8). Farba pasa: 2672 → 2796 trójkątów w warstwie `markings` (+124). Pas bruku: +249 trójkątów w kadrze. Wobec
`docs/06` §6 (hipoteza Samsung A ≤ 300–400 draws, ≤ 400–600 tys. trójkątów) bez zmiany. Telefon: nie mierzone (bez adb).

## Wizualnie (3 pętle build → import → render; kadry obejrzane przez agenta, `visual-critic` u lidera)
| Dowód | Zgodne | Rozbieżne / otwarte |
|---|---|---|
| `sbs/sbs-P11-063-row-photo_A_r3low_r3high.jpg` (zdjęcie / A / r3 Low / r3 High, ten sam wycinek) | 8 słupków w tych samych kolumnach kadru co na zdjęciu, pięć pasów, łańcuchy jednobarwne na przęsło z naprzemienną fazą, słupki na bruku za krawężnikiem | słupki proste (na zdjęciu kilka krzywych do ~5°); krawężnik świata biegnie 6° skośnie do rzędu (3,3 m od słupka 1, 1,6 m od słupka 8; w terenie tuż przy nim) — geometria jezdni, nie 0202 |
| `sbs/sbs-P11-063-photo13m-r3-low.jpg` (cały kadr) | rząd w tym samym miejscu i skali | dwa maszty sygnalizacji na pierwszym planie i brak zarośli — zakres 0186 |
| `view/r3-bollards-close-4m.jpg`, `view/r3H-bollards-close-4m.jpg` | stopy na bruku, pasy 25 cm, czerwone i białe przęsła | WHITE_NOTE |
| `view/paint_27L_s.jpg`, `view/paint_09R_s.jpg`, `view/paint_27thr_s.jpg` (farba z generatora na ortofoto) | „27 L” w tych samych miejscach i w tym samym zwrocie co na ortofoto; kreska osi przez grot i poprzeczkę 09R; poprzeczki do linii krawędziowych | cyfry bez szeryfu „7”; kształt WORKING_VALUE |
| `view/paint-A-vs-r3.jpg`, `view/r3-krywlany-runway-paint.jpg` (14 m nad osią) | „27 L” czytelne od wschodu: „2” po lewej, „7” po prawej, „L” bliżej, stopą w prawo | asfalt w łaty i idealnie biała farba — jak w recenzji 0196 |
| `view/fence-A-vs-r3.jpg` | ogrodzenie bez zmiany (było zielone z hasha) | blada, jednolita wstęga ogrodzenia z daleka = „turkusowy pas” z recenzji 0196 |

Kamera `bollards-photo-13m`: id zostaje, poza dopasowana na nowo (`cams.py`). 0183 ustawił słupek 1 w 13 m, bo zakładał
0,80 m. Teraz pozycja i azymut wynikają z kolumn słupków 1–4 na zdjęciu (x = 630 / 750 / 858 / 966 z 1600 px,
f = 1230 px ASSUMED) i zbudowanych pozycji; reszty dopasowania ≤ 1,8 px, słupek 1 w **20,4 m** (M58: ok. 19 m).
Wysokość słupków jest wtedy kontrolą, nie wejściem: 1,10 m daje 66,8 → 61,6 px wobec 72 → 64 px na zdjęciu, 1,17 m
dałoby 71,1 → 65,5 px. Zdjęcie potwierdza więc pomiar M58 (ok. 1,17 m); w grze zostaje wartość z przepisu, ok. 6 %
niżej. Nie stroiłem wysokości do zdjęcia.

## Walidacja
- `tests/gis/test_chain_bollards_0183.py`: linie 85–86 (U-12c 0,6–0,8 m, przęsło = 2 × wysokość) zastąpione
  wartościami U-12b; nowe `test_0202_each_chain_is_one_colour_and_bays_alternate`,
  `test_0202_dojlidy_row_is_the_m58_line`.
- `tests/gis/test_dojind_0196.py`: zakres pola linii krawędziowych 0,9 → 0,85 m; nowe
  `test_0202_runway_designator_27l_reads_from_the_east` (strona „2” / „7”, stopa „L”, pole znaku wypełnione),
  `test_0202_runway_widths_and_fifth_dash`, `test_0202_aerodrome_fence_is_green`.
PYTEST_NOTE
- EditMode (`scripts/test.ps1 -Platform EditMode`, 22:26): 581 total, **580 passed, 0 failed**, 1 skipped (Ignored).
- `streetscape_qa.json → furniture.chain_bollards`: 8 słupków, 7 przęseł, 14,0 m, `end_shift_m` 0,0, `max_step_m` 0,032;
  słupki osadzone 159,07–159,16 m na `sidewalk_paving` (`probe.json`).
- Zrzut z telefonu: brak (bez adb w zadaniu) — `docs/06` §5 pkt 2 do spełnienia przez lidera przed bramką.

Zdjęcia właściciela: `art-source/world/refs/` nie istnieje w repo; referencje = kadr CC0 P11-063 i ortofoto GUGiK.
Odtworzenie: `artifacts/dojfix-0202/chain.ps1 -Tag rN [-Baseline] [-High]` (build → kamery → import → render),
`tests.ps1`, `probe.py`, `verge.py`, `berms.py`, `overlay.py`, `cams.py`.

## Otwarte
- Wysokość 1,10 (przepis) wobec ~1,17 m (pomiar, potwierdzony kadrem) — decyzja lidera / pomiar właściciela.
- Krawężnik wschodniej jezdni Mickiewicza w świecie leży 1,6–3,3 m od rzędu i 6° skośnie; w terenie słupki stoją
  tuż za nim. Pas bruku 0202 zamyka trawnik tylko na 43 m przy rzędzie — dalej na północ trawnik zostaje (0179).
- Słupki krzywe, drugi (dalszy) rząd z kadru, rzędy przy Dywizjonu 303 i przy bramie E (M58 §1.2–1.3; końce UNVERIFIED).
- Region C: biblioteka mebli ma jeden prototyp więcej — REGION_C_NOTE
- „09 R” leży poza kaflem. Żółte linie kołowania, szare krzyże, oprawy przy końcu E, drut kolczasty na ogrodzeniu,
  brama E — backlog (M58 §2.2, §3).
- Kolizja z Argonem przy scalaniu: obie gałęzie zmieniają `overrides.yaml` Dojlid i `generated/*`; wpisy 0202 to blok
  `chain_bollards`, `krywlany-runway-paint` i dwa nowe wpisy na końcu pliku. Po scaleniu: regeneracja Dojlid.
