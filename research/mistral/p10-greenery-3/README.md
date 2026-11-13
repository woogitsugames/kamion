# M51 — p10-greenery-3: zieleń ulic osiedla przy Al. Tysiąclecia (Białystok)

Kontynuacja: `research/g7-street-greenery/` (G7) i `research/gptpro/p10-street-greenery-2/` (P10-2).
Gałąź: `research/mistral-p10-greenery-3` (od najnowszego `main`). Id wpisów: `M51-NNN`.
Autor: Vibe (GLM), data dostępu źródeł: 2026-11-13, raport po polsku.
**Wersja 2 (M51-FIX)** po przeglądzie: naprawa rejestracji ortofoto (odbicie N–S), przypisanie kadrów do prawdziwych ulic wg reguły ≤25 m od osi, żywopłoty liczone wyłącznie z obejrzanych kadrów, zwarta zieleń jako osobna warstwa, data ortofoto z GetFeatureInfo.

## Zakres i wyniki w skrócie

| Zadanie | Wynik | Status |
|---|---|---|
| 1. Letnie zdjęcia (VI–VIII) 9 ulic | 18 kadrów (M51-101…118) + 15 kadrów uzupełniających (M51-119…133) przypisanych do **prawdziwych ulic wg geotagu ≤25 m od osi** (aleja, Motoszko, Sokólska, Kombatantów, Andersa); kierunek **UNVERIFIED** (Commons: 0/33 plików z GPSImgDirection). **Skidelska/Wileńska/Łańcucka: 0 kadrów z wnętrza ulicy** | uczciwie — luka zdjęciowa nie została zamknięta (patrz Luki) |
| 2. Żywopłoty ≥ 20 odcinków | **22 odcinki** (M51-204…233), każdy z **obejrzanego kadru** (36 kadrów przeanalizowanych, rejestr `hedge_viewings.json`); 11 fałszywych odcinków usuniętych po obejrzeniu | gotowe (próg ≥20 spełniony) |
| 3. Detekcja koron kafla [776971, 595199, 779019, 597247] | `crowns.geojson` — **5258 koron** po naprawie odbicia N–S; osobna warstwa `compact_greenery.geojson` (771 poligonów zwartej zieleni r>6,5 m); `%` środków na zieleń w 3 oknach 300×300 m: **100/99,8/100** (próg >80% ✓); data ortofoto **z GetFeatureInfo: 2024-05-27** | gotowe |
| 4. Projekt zieleni Al. Tysiąclecia (Strabag 2021/22) | bez zmian — dane przetargowe i nasadzenia **SOURCED** (74 drzewa, 109 krzewów, 20 600 m² trawników, ~385 mb ekranów); **gatunki/obwody/rozstaw — UNVERIFIED** | częściowo — zgodnie z „jeśli dostępne" |

## Zadanie 1 — letnie zdjęcia ulic osiedla (M51-FIX)

**Kryteria:** lato VI–VIII (liście), ≥ 2 kadry/ulica, data + azymut, WGS84 (6 miejsc), sezon i pora_dnia, JPG ≤ 1600 px.

**Reguła przypisania (poprawiona po przeglądzie):** kadr należy do ulicy X tylko gdy **geotag ≤ 25 m od osi X** (osie: `roads.graph.json`, OSM/BDOT10k, EPSG:2180). Azymut kamery **nie jest** wyznaczany „w stronę osi ulicy" — Commons nie podaje GPSImgDirection (zweryfikowane API: **0/33 plików serii letnich**), więc kierunek wszystkich kadrów = **UNVERIFIED**. Jedyne potwierdzenie lokalizacji z treści: kadr M51-118 — wiat przystankowy z napisem „353 SOKÓŁSKA / AL. TYSIĄCLECIA PP" (opisane w uwagach).

**Prawdziwe położenie 18 kadrów (M51-101…118) po przeliczeniu ≤25 m od osi:**

| ulica (wg geotagu) | kadry | odległości od osi |
|---|---|---|
| Aleja Tysiąclecia PP | 101–103, 106, 107, 109–112, 114, 117 | 1,6–20,9 m |
| Michała Motoszko | 108 | 0,0 m (na osi) |
| Sokólska | 113 (0,5 m), 116 (6,7 m), 118 (8,0 m) | ≤8 m |
| Kombatantów | 115 | 22,4 m |
| **poza progiem 25 m** (referencja, bez ulicy) | 104 (27,8 m od Motoszko), 105 (39,5 m od alei) | >25 m |

**Uczciwy wniosek:** kadry serii spacerowej 25.07.2022 i pozostałych serii letnich zostały wykonane **przy alei i sąsiednich ulicach (Motoszko, Sokólska, Kombatantów, Andersa), nie wewnątrz ulic osiedla**. Dla **Skidelskiej, Wileńskiej i Łańcuckiej: 0 kadrów z wnętrza ulicy** — poprzednie przypisanie (7/4/7 kadrów) było błędne i zostało wycofane. Klatki przy wlotach (np. M51-101 — wlot Skidelskiej, geotag 5,0 m od osi alei / 8,0 m od osi Skidelskiej) pokazują wloty z alei.

**Kadry uzupełniające (M51-119…133):** 15 kadrów przyulicznych z serii Rakoon, każdy obejrzany, z „co widać" w uwagach, ulicą z OSM i odległością geotagu od osi:
- spacer 25.07.2022 (M51-119…126): 123952 (14,4 m od osi alei), 132358 (10,4 m), 132511 (14,7 m), 132717 (0,1 m) — aleja; 125403 (14,9 m), 125410 (20,7 m), 125414 (11,6 m), 125438 (20,7 m) — Andersa;
- 26.06.2024 (M51-127…129): 103406 (2,3 m), 103407 (2,9 m), 103414 (3,4 m) — Sokólska;
- 29.07.2023 (M51-130…132): 105311 (0,1 m), 105353 (2,2 m) — Kombatantów; 105858 (16,4 m) — Andersa;
- 11.07.2020 (M51-133): 065239 (3,3 m) — Kombatantów, **CC BY 3.0 (referencja, nie tekstura)**.

**Sumarycznie kadry letnie per ulica (33):** aleja ×15, Sokólska ×6, Andersa ×5, Kombatantów ×4, Motoszko ×1, poza progiem 25 m ×2 (M51-104, 105). Pełna lista dodatkowych serii z przypisaniem: `extra_series.json` (59 kadrów w bbox osiedla; obejrzane dodatkowo kadry bez żywopłotu — np. 131152, 131202, 125821, 105303, 105958 — służą jako kontekst/rejestr obejrzeń `hedge_viewings.json`).

**Źródła odpytane (bez Google):** Panoramax (0 kadrów w bbox osiedla — potwierdzone), KartaView (na osiach 9 ulic **0 kadrów**; sekwencja przywlotowa 1155711 z 23.03.2018 — obrazy niedostępne, serwer `storage7.openstreetcam.org` zwraca **HTTP 502**; testy 2026-11-13 trzykrotne), Wikimedia Commons (seria spacerowa 25.07.2022 — 41 kadrów w bbox, wszystkie pobrane i przeanalizowane w zakresie zielonym), Openverse (bez trafień), Mapillary — nie odpytano (brak tokenu).
**Licencja KartaView: CC BY-SA 4.0 (referencja, nie tekstura)** — ujednolicono w całym raporcie i manifeście.

## Zadanie 2 — żywopłoty (M51-FIX: ≥20 odcinków z obejrzanych kadrów)

**Definicja odcinka (bez zmian):** front jednej posesji (lub jedna strona kadru) widoczny na konkretnym zdjęciu; odczyt wizualny (Vibe `analyze_image`, **jeden kadr na wywołanie**, 2026-11-13); wysokość **ESTIMATED ±0,3–0,5 m** z odniesieniem (płot 1,2–1,5 m; siatka 1,5 m; samochód ~1,4 m). **Nowe (M51-FIX): odcinek może istnieć tylko jeśli jego kadr został realnie obejrzony** — rejestr wszystkich 36 obejrzeń z werdyktem: `hedge_viewings.json`.

**Usunięte po obejrzeniu (11 odcinków z pierwotnych 18):** M51-201 (luźne krzewy przy płotach, nieciągłe — nie żywopłot), 202 (brak żywopłotu — kadr źródłowy obejrzany), 203 (brak), 206 (brak), 208 (duplikat pasa z M51-207 — ten sam plik), 209/210 (brak w kadrze), 211 (pomnik/krzyż, brak), 213 (barierki, brak), 216 (ten sam plik co kadr M51-117 — brak żywopłotu; ujednolicono), 217 (**ekran akustyczny obrośnięty** 3–4 m — nie żywopłot). Przegląd kazał usunąć 6 (201, 207, 211, 213, 214, 217); po niezależnym obejrzeniu każdego kadra usunięto 11, a 207 (pas swobodnych krzewów — nie ekran, zweryfikowane) i 214 (niski strzyżony żywopłot 1,0–1,2 m) **zostawiono** z uczciwym opisem.

**Wynik — 22 odcinki (M51-204…233):**

| ulica / lokalizacja | odcinki | typy | wysokości |
|---|---|---|---|
| Aleja Tysiąclecia PP | 204, 207, 212, 214, 215 | liściaste ×3, pas swobodnych krzewów ×1, żywotnik ×1 | 1,0–3,0 m |
| Michała Motoszko | 205* | liściasty | 1,0 m |
| Sokólska | 218, 223, 224, 225 | liściaste ×2, iglaste (żywotnik) ×2 | 1,2–2,0 m |
| Kombatantów | 232 | liściasty | 2,5–3,0 m |
| Generała W. Andersa | 219, 220, 233 | pas swobodny ×1, luźne krzewy ×1, liściasty ×1 | 1,0–4,0 m |
| kwartały między aleją a Andersą (poza progiem 25 m — uczciwie oznaczone) | 221, 222, 226, 227, 228, 229, 230, 231 | liściaste ×7, iglasty ×1 | 0,5–6 m |

\* M51-205: geotag 27,8 m od osi Motoszko — **poza progiem 25 m**, atrybucja ESTIMATED (ujawnione w uwagach i w audycie).

Razem z **G7-P01…P12** (wiosna 2024, ulice osiedla: Wołkowyska, Kowieńska, Grodzieńska, Wileńska, Lidzka, Racławicka, Łańcucka) — łącznie **34 odcinki przyuliczne/przyposesyjne**, z czego **22 letnie, wszystkie z obejrzanych kadrów** (próg ≥20 ✓).

## Zadanie 3 — odtwarzalna detekcja koron (M51-FIX: rejestracja, zwarta zieleń, filtr nie-roślinności)

- **Dane:** ortofotomapa GUGiK, **data z GetFeatureInfo (nie z pamięci): 2024-05-27**, GSD 0,25 m, PL-1992, zgłoszenie DFT.7201.011.2024, arkusze N-34-107-C-b-1-1/-1-2, N-34-107-A-d-3-3/-3-4 (surowe odpowiedzi GFI: `orto_metadata.json`). Kafel zadania [776971, 595199, 779019, 597247] (EPSG:2180) = 4 kafle 1024×1024 m.
- **Naprawiona rejestracja (M51-FIX):** wcześniejsza wersja **czytała kafle lustrzanie odbite N–S** (wiersz 0 = południe). Poprawka: wiersz 0 = **północ** (N = n0+1024−wiersz·0,25). Weryfikacja niezależna: centroidy jasnych dachów z `buildings.geojson` trafiają na jasne piksele tylko po poprawce (mean V 141,7 vs 120,8 bez); odcinki dróg mają ExG 0,0026 (poprawnie) vs 0,0277 (pod odbiciem). Skrypt: `tools/detect_crowns.py` (poprawiony).
- **Maska dwu-progowa:** korony: ExG > 0,12 AND G > 60 (jasne, rozłączne korony); **zwarta zieleń: ExG > 0,06** (ciemny baldachim, las, skarpy) — osobna warstwa.
- **Wynik — korony:** `crowns.geojson`, **5258 koron** (2520 iglaste / 2738 liściaste), r 0,71–6,49 m (mediana 1,15 m), każda z `orto_data=2024-05-27` (źródło: GFI).
- **Nowa warstwa — zwarta zieleń:** `compact_greenery.geojson` — **771 poligonów** (closing 5×5, komponenty r > 6,5 m, kontur marching-squares + Douglas-Peucker tol 1,5 m; poprawiony krytyczny błąd offsetu globalnego — poligony były przesunięte ~1 km). Największy poligon 99 178 m²; zadrzewiona skarpa przy Al. Tysiąclecia uchwycona (27 poligonów przecina okno W1). Bez sztucznego górnego limitu promienia — las i skarpy nie są „koronami".
- **Filtr nie-roślinności (kształt+jasność):** pojazd (aspect>3,0 & fill>0,72 & v_std<3,5 & v_mean>100), dach (fill>0,85 & v_std<3,5 & v_mean>115); pierwsza wersja bez kryterium gładkości fałszywie odrzucała rzędy drzew przy torowisku — poprawione po weryfikacji wizualnej. Ostatecznie odrzucono **1 obiekt** (r 0,71 m, niejednoznaczny jasny prostokąt) — znikomy.
- **Kontrola rejestracji w 3 oknach 300×300 m (`tools/overlays_check.py`, nakładki PNG w ZIP):** W1 skarpa (68 koron): **100%** środków na zieleni (ExG>0,06); W2 max korony (439): **99,8%**; W3 max zwarta (28): **100%**; średnia ważona **99,8%** (próg >80% ✓). QA wizualne: okręgi nakładek leżą na koronach (powiększenie W2 potwierdzone — brak trafień na dachach); drobne wtrącenia zabudowy w warstwie zwartej zieleni przy lewej krawędzi kafla Z0166 — udokumentowane jako ograniczenie warstwy.
- **Porównanie z P10 (po poprawce flipa, `comparison_p10.json`):** P10-2xx (n=37): mediana Δ pokrycia **−54 p.p.**, zgodne |Δ|≤15 p.p.: **5/37**, spadki >30 p.p.: **26**, wzrosty: **2**; suma koron P10=445 vs **M51=58**; mediana maski M51 62%. P10-3xx (młode nasadzenia, 13 okien): P10=64 vs **M51=24** na 100 m. **Przyczyny różnic są metodologiczne, nie rejestracyjne:** detektor P10 celowo łapie ciemny baldachim (LUMA_MAX 118) i liczy krzewy jako korony; M51 wymaga jasnych, rozłącznych koron r≥0,7 m — dlatego na odcinkach z krzewami/trawnikiem pokrycie P10 jest wyższe. Różnice w 2 oknach (wzrost M51) wynikają z poprawnie zarejestrowanych nasadzeń przy jezdni. `street_agg.json`: agregacja koron per ulica (bufor 8 m).
- **Ważne:** warstwa `plot_canopy.json` z P10 jest poprawnie zarejestrowana (42,4% ExG>0,06 vs 29,6% po odbiciu) — jej detektor celowo liczy ciemny baldachim.

## Zadanie 4 — projekt zieleni Al. Tysiąclecia (Strabag 2021/22)

**SOURCED (karta postępowania BIP UM Białystok, 2026-11-13):** postępowanie **ZDM-X.271.16.2018.JZ**, „Rozbudowa Alei Tysiąclecia Państwa Polskiego w Białymstoku od ul. Wileńskiej do terenu kolejowego przy ul. Poleskiej wraz z infrastrukturą techniczną" (formuła D&B), wykonawca **STRABAG Sp. z o.o.**, 32 883 642,97 zł brutto; komunikat UM 31.01.2022: **74 drzewa, 109 krzewów**, 20 600 m² trawników i skarp, ~385 mb ekranów akustycznych.
**UNVERIFIED — gatunki, obwody, rozstaw:** SIWZ (20 s.) i postanowienie RDOŚ (17 s., CCITT G4→PNG, własny dekoder) to skany bez warstwy tekstowej; dokumentacja projektowa nieopublikowana na BIP.

## Pliki

- Repo: `README.md`, `manifest.csv` (**60 wierszy M51**), `crowns.geojson` (5258 koron), `compact_greenery.geojson` (771 poligonów — nowe), `comparison_p10.json`, `street_agg.json`, `overlays_check.json` (nowe), `street_assignment.json` (przypisanie 18 kadrów ≤25 m — nowe), `new_frames_streets.json`, `extra_series.json`, `hedge_viewings.json` (36 obejrzeń z werdyktem — nowe), `orto_metadata.json` (GetFeatureInfo — nowe), `audit_20_percent.json` (nowe losowanie), `sources.md`, `tools/` (detect_crowns.py, compare_with_p10.py, overlays_check.py, assign_streets.py, audit_fix.py, tm2180.py).
- **Zdjęcia nie idą do gita** (`files/` w `.gitignore`). Pakiet **`mistral-p10-greenery-3-files-v2.zip`**: wszystkie JPG (18 kadrów M51-101…118 + 29 kadrów spaceru + 12 kadrów serii dodatkowych + kadry P10 wylane wcześniej — ≤1600 px) + **PNG nakładek 3 okien 300×300 m** + metadane (orto_metadata.json, dl_manifest, commons_meta, hedge_viewings.json). Karta do pobrania w wątku Vibe (PR nie przenosi plików binarnych).
- Licencje: CC0 (seria 2022/2023/2024 Rakoon), CC BY 3.0 (seria 2020-07-11 — „referencja, nie tekstura"), **CC BY-SA 4.0 (KartaView — referencja, nie tekstura)**, CC BY 4.0 (ortofoto GUGiK), ODbL (osie OSM), BIP (dokumenty urzędowe).

## Samokontrola (M51-FIX: nowe losowanie 20%, nowy seed)

`audit_20_percent.json` + skrypt `tools/audit_fix.py`: `random.Random(20261114).sample(ids, ceil(0.2*60))` = **12 próbek** (poprzedni seed 20261113 — zastąpiony). Kontrole: kadry — „co widać" w uwagach + **ulica z OSM z przeliczoną odległością geotagu od osi** (reguła ≤25 m; >25 m tylko z ujawnieniem „POZA progiem" w uwagach) + kierunek UNVERIFIED; odcinki — dodatkowo typ/gatunek, wysokość ESTIMATED z metodą, id zdjęcia; wiersze koron — **% środków koron na zieleń w 3 oknach (100/99,8/100%, próg >80%)**; wiersze BIP — status+licencja. **Wynik: 12/12 PASS.**

## Luki i dalsza praca (uczciwie)

1. **Skidelska, Wileńska, Łańcucka: 0 letnich kadrów z wnętrza ulicy** (poprzednio błędnie: 7/4/7). Wszystkie dozwolone źródła odpytane — Commons ma tylko serie przy alei/Sokólskiej/Motoszko/Andersa/Kombatantów. Pozostałe 6 ulic osiedla (Kowieńska, Lidzka, Wołkowyska, Grodzieńska, Racławicka, Świsłocka) — nadal brak letnich kadrów street-level; G7 (wiosna 2024) pozostaje jedynym street-level.
2. **KartaView outage**: `storage7.openstreetcam.org` HTTP 502 (testy 2026-11-13, trzykrotnie) — 51 kadrów sekwencji przywlotowych niepobranych; azymuty SOURCED z metadanych API zachowane, licencja CC BY-SA 4.0 (referencja, nie tekstura).
3. **OCR SIWZ/RDOŚ** (gatunki/obwody/rozstaw zadania 4) — skany w ZIP, do dokończenia przy dostępnym budżecie analizy obrazu.
4. **Kierunek kamery UNVERIFIED** we wszystkich kadrach Commons (brak GPSImgDirection); jedyny opisany z treści: lokalizacja M51-118 (wiat „353 SOKÓŁSKA / AL. TYSIĄCLECIA").
5. **Kwartalne odcinki żywopłotów (8/22)** leżą poza progiem 25 m od osi nazwanych ulic — oznaczone uczciwie w kolumnie uwagi i uwzględnione w audycie; wynikają z realnej geometrii spaceru (aleja↔Andersa), nie z błędu przypisania.
