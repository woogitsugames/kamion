# M51 — p10-greenery-3: zieleń ulic osiedla przy Al. Tysiąclecia (Białystok)

Kontynuacja: `research/g7-street-greenery/` (G7) i `research/gptpro/p10-street-greenery-2/` (P10-2).
Gałąź: `research/mistral-p10-greenery-3` (od najnowszego `main`). Id wpisów: `M51-NNN`.
Autor: Vibe (GLM), data dostępu źródeł: 2026-11-13, raport po polsku.
**Wersja 2 (M51-FIX)** po przeglądzie: naprawa rejestracji ortofoto (odbicie N–S), przypisanie kadrów do prawdziwych ulic wg reguły ≤25 m od osi, żywopłoty liczone wyłącznie z obejrzanych kadrów, zwarta zieleń jako osobna warstwa, data ortofoto z GetFeatureInfo.
**Wersja 3 (M51-FIX-2, 2026-11-14)** po przeglądzie s19 (`docs/reports/REVIEW-2026-11-13-s19-mistral-m51-m53-m50v2.md` §3): (1) M51-214 usunięty, M51-112 = brak żywopłotu; (2) brakujące kadry M51-119…126 / odcinki 219…222 pobrane z Commons i obejrzane, opisy poprawione, **ZIP v3** z mapą plików `ZAWARTOSC_v3.txt`; (3) nowe kategorie „szpaler/zadrzewienie” (219, 227, 231) i „rabata ozdobna” (221, 222, 226, 229, 230), 232 = 1,0–1,5 m — **13 odcinków żywopłotu, próg ≥ 20 niespełniony**; (4) nakładki north-up z WMS, skala px/300 m; (5) filtr nie-roślinności `tools/filter_nonveg.py`: −14 obiektów (autobus z przeglądu usunięty), **5244 korony**; (6) M51-301 = 2520 / 2724, liczby spójne.

## Zakres i wyniki w skrócie

| Zadanie | Wynik | Status |
|---|---|---|
| 1. Letnie zdjęcia (VI–VIII) 9 ulic | 18 kadrów (M51-101…118) + 15 kadrów uzupełniających (M51-119…133) przypisanych do **prawdziwych ulic wg geotagu ≤25 m od osi** (aleja, Motoszko, Sokólska, Kombatantów, Andersa); kierunek **UNVERIFIED** (Commons: 0/33 plików z GPSImgDirection). **Skidelska/Wileńska/Łańcucka: 0 kadrów z wnętrza ulicy** | uczciwie — luka zdjęciowa nie została zamknięta (patrz Luki) |
| 2. Żywopłoty ≥ 20 odcinków | po M51-FIX-2: **13 odcinków żywopłotu/pasa krzewów** (+ 3 szpalery/zadrzewienia i 5 rabat ozdobnych — osobne kategorie, nieliczone); M51-214 usunięty; każdy z **obejrzanego kadru** (rejestr `hedge_viewings.json`) | **próg ≥20 NIE spełniony (13/20)** |
| 3. Detekcja koron kafla [776971, 595199, 779019, 597247] | `crowns.geojson` — **5244 korony** (po naprawie odbicia N–S i filtrze nie-roślinności M51-FIX-2: −14 autobusów/pojazdów/dachów); osobna warstwa `compact_greenery.geojson` (771 poligonów zwartej zieleni r>6,5 m); `%` środków na zieleń w 3 oknach 300×300 m: **100/99,8/100** (próg >80% ✓); data ortofoto **z GetFeatureInfo: 2024-05-27** | gotowe |
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

**Usunięte po obejrzeniu (11 odcinków z pierwotnych 18):** M51-201 (luźne krzewy przy płotach, nieciągłe — nie żywopłot), 202 (brak żywopłotu — kadr źródłowy obejrzany), 203 (brak), 206 (brak), 208 (duplikat pasa z M51-207 — ten sam plik), 209/210 (brak w kadrze), 211 (pomnik/krzyż, brak), 213 (barierki, brak), 216 (ten sam plik co kadr M51-117 — brak żywopłotu; ujednolicono), 217 (**ekran akustyczny obrośnięty** 3–4 m — nie żywopłot). Przegląd kazał usunąć 6 (201, 207, 211, 213, 214, 217); po niezależnym obejrzeniu każdego kadra usunięto 11, a 207 (pas swobodnych krzewów — nie ekran, zweryfikowane) i 214 **zostawiono** z opisem. **M51-FIX-2:** M51-214 **usunięty** — kadr M51-112 (Commons 20220725_123946) obejrzany ponownie: po prawej trawnik z zaparkowanymi samochodami przed blokiem, żywopłotu brak (ten sam błąd zgłoszony w s17 i s19).

**Wynik po M51-FIX-2 — 21 wierszy odcinków (M51-204…233, bez 214) w 3 kategoriach** (kolumna `obiekt` w manifeście); kategorie ustalone po obejrzeniu każdego kadra 2026-11-14 (Read na JPG z Commons, ZIP v3):

| kategoria | odcinki | liczba |
|---|---|---|
| **żywopłot / pas krzewów** (liczony do progu) | 204, 205*, 207, 212, 215, 218, 220, 223, 224, 225, 228, 232, 233 | **13** |
| szpaler/zadrzewienie (NIE żywopłot) | 219 (zarośla wierzbowe >3 m), 227 (rząd drzew iglastych za parkingiem), 231 (zadrzewienie >6 m za placem zabaw) | 3 |
| rabata ozdobna (NIE żywopłot) | 221, 222 (nasadzenia przy elewacji), 226 (rabata mieszana z trawami), 229 (przedogródek: krzewy + byliny), 230 (nasadzenia przy elewacji) | 5 |

Żywopłoty / pasy krzewów wg ulic:

| ulica / lokalizacja | odcinki | typy | wysokości |
|---|---|---|---|
| Aleja Tysiąclecia PP | 204, 207, 212, 215 | liściaste ×2, pas swobodnych krzewów ×1, żywotnik ×1 | 1,2–3,0 m |
| Michała Motoszko | 205* | liściasty | 1,0 m |
| Sokólska | 218, 223, 224, 225 | liściaste ×2, iglaste (żywotnik) ×2 | 1,2–2,0 m |
| Kombatantów | 232 | liściaste zarośla przy siatce (M51-FIX-2: wysokość 1,0–1,5 m, nie 2,5–3) | 1,0–1,5 m |
| Generała W. Andersa | 220, 233 | luźne krzewy ×1, liściasty ×1 | 0,8–1,0 m |
| wnętrze kwartału (poza progiem 25 m) | 228 | grupa swobodnych krzewów | 1,0–1,5 m |

\* M51-205: geotag 27,8 m od osi Motoszko — **poza progiem 25 m**, atrybucja ESTIMATED (ujawnione w uwagach i w audycie).

**Uczciwy wynik progu:** **13 odcinków żywopłotu/pasa krzewów < 20 — próg „≥ 20 odcinków” NIE jest spełniony** (z przypisaną ulicą ≤ 25 m: 11). Wcześniejsze „22” liczyło fałszywy odcinek 214, rabaty i zadrzewienia. Uwagi z przeglądu s19 nieprzeliczone w M51-FIX-2 (kadry nie były w zakresie zadania): 212 (iglaki >3 m — raczej drzewa), 215 (żywopłotu i ekranu nie widać wyraźnie), 218 (masa drzew/krzewów za ogrodzeniem, nie formowany żywopłot) — pozostają liczone, ale **UNVERIFIED co do typu**; przy ich odrzuceniu zostaje 10. Domknięcie progu wymaga nowych letnich kadrów z wnętrza ulic osiedla (Luki, p. 1).

Razem z **G7-P01…P12** (wiosna 2024, ulice osiedla: Wołkowyska, Kowieńska, Grodzieńska, Wileńska, Lidzka, Racławicka, Łańcucka) — łącznie **25 odcinków żywopłotu przyulicznych/przyposesyjnych** (12 wiosennych G7 + 13 letnich M51, wszystkie z obejrzanych kadrów).

## Zadanie 3 — odtwarzalna detekcja koron (M51-FIX: rejestracja, zwarta zieleń, filtr nie-roślinności)

- **Dane:** ortofotomapa GUGiK, **data z GetFeatureInfo (nie z pamięci): 2024-05-27**, GSD 0,25 m, PL-1992, zgłoszenie DFT.7201.011.2024, arkusze N-34-107-C-b-1-1/-1-2, N-34-107-A-d-3-3/-3-4 (surowe odpowiedzi GFI: `orto_metadata.json`). Kafel zadania [776971, 595199, 779019, 597247] (EPSG:2180) = 4 kafle 1024×1024 m.
- **Naprawiona rejestracja (M51-FIX):** wcześniejsza wersja **czytała kafle lustrzanie odbite N–S** (wiersz 0 = południe). Poprawka: wiersz 0 = **północ** (N = n0+1024−wiersz·0,25). Weryfikacja niezależna: centroidy jasnych dachów z `buildings.geojson` trafiają na jasne piksele tylko po poprawce (mean V 141,7 vs 120,8 bez); odcinki dróg mają ExG 0,0026 (poprawnie) vs 0,0277 (pod odbiciem). Skrypt: `tools/detect_crowns.py` (poprawiony).
- **Maska dwu-progowa:** korony: ExG > 0,12 AND G > 60 (jasne, rozłączne korony); **zwarta zieleń: ExG > 0,06** (ciemny baldachim, las, skarpy) — osobna warstwa.
- **Wynik — korony:** `crowns.geojson`, **5244 korony po M51-FIX-2** (2520 iglaste / 2724 liściaste; przed filtrem M51-FIX-2: 5258 = 2520 / 2738), r 0,71–6,49 m (mediana 1,15 m), każda z `orto_data=2024-05-27` (źródło: GFI).
- **Nowa warstwa — zwarta zieleń:** `compact_greenery.geojson` — **771 poligonów** (closing 5×5, komponenty r > 6,5 m, kontur marching-squares + Douglas-Peucker tol 1,5 m; poprawiony krytyczny błąd offsetu globalnego — poligony były przesunięte ~1 km). Największy poligon 99 178 m²; zadrzewiona skarpa przy Al. Tysiąclecia uchwycona (27 poligonów przecina okno W1). Bez sztucznego górnego limitu promienia — las i skarpy nie są „koronami".
- **Filtr nie-roślinności (kształt+jasność):** pojazd (aspect>3,0 & fill>0,72 & v_std<3,5 & v_mean>100), dach (fill>0,85 & v_std<3,5 & v_mean>115); pierwsza wersja bez kryterium gładkości fałszywie odrzucała rzędy drzew przy torowisku — poprawione po weryfikacji wizualnej. Ostatecznie odrzucono **1 obiekt** (r 0,71 m, niejednoznaczny jasny prostokąt) — znikomy.
- **M51-FIX-2 — skuteczny filtr nie-roślinności (`tools/filter_nonveg.py`, post-filtr na `crowns.geojson`):** filtr z detekcji usuwał 1 obiekt, a zielony autobus na jezdni Al. Tysiąclecia (ok. 53,1556 N, 23,1524 E; korona C01782, wydłużenie 4,5, 24 m²) pozostawał „koroną”. Nowe reguły: **(A)** środek na jezdni drogi głównej z OSM (osie `roads.graph.json` regionu bialystok-industrial-c = OSM Geofabrik + szerokość BDOT10k, pas = oś ± szerokość/2; Overpass API był nieosiągalny z kontenera 2026-11-14 — connection reset) **i** (wydłużenie PCA > 2 **lub** prostokątność > 0,80 **lub** jasność V > 140); **(B)** jasność bloba V > 140 w dowolnym miejscu (jasnozielony/turkusowy lakier i pokrycia — w kaflu tylko 13 takich koron, **13/13 obejrzane: nie-roślinność**). **Wynik: usunięto 14 obiektów** (A: 4, B: 10; lista z cechami: `nonveg_removed.geojson`): 7 zielonych autobusów lub ich fragmentów (w tym **C01782 — autobus z przeglądu: usunięty**, najbliższa pozostała korona ~48 m od podanego punktu), 5 zielonych/turkusowych pojazdów na parkingach, 2 turkusowe elementy dachów; **wszystkie 14 obejrzane** na wycinkach ortofoto north-up (`nonveg_check.png`) — żadna nie jest koroną. Odrzucona po obejrzeniu wersja 1: kryterium „małe wydłużone gładkie prostokąty poza jezdnią” trafiało w 14/14 przypadków w roślinność (ogródki działkowe, las), a osie `service/living_street` obejmują podwórka i dojścia (trawniki, krzewy) — dlatego nie są traktowane jako jezdnia. **Ograniczenie:** pojazdy ciemniejsze niż V 140 poza jezdnią drogi głównej nie są wykrywane (UNVERIFIED, ile ich zostało). Po filtrze: **5244 korony (2520 iglaste / 2724 liściaste)**; `comparison_p10.json` i `street_agg.json` przeliczone `tools/compare_with_p10.py` na nowym zbiorze.
- **Kontrola rejestracji w 3 oknach 300×300 m — M51-FIX-2 (`tools/overlays_check.py`, przepisany):** nakładki z ZIP v2 były bezwartościowe (obraz odwrócony N–S — wycinek mozaiki zapisany z wierszem 0 = południe; znaczniki w skali 4 px/m na obrazie powiększonym do 4800 px, więc tylko w lewym-górnym rogu). Teraz obraz okna pobierany wprost z **GUGiK WMS** (ORTO StandardResolution, CC BY 4.0; osiągalny 2026-11-14) w natywnej rozdzielczości 0,25 m — **north-up (wiersz 0 = północ)**; jedna skala dla obrazu i znaczników **s = rozmiar okna w px / 300 m** (1200 px → 4 px/m w ZIP v3; 960 px → 3,2 px/m w gicie: `overlays/w1_skarpa.png`, `w2_max_korony.png`, `w3_max_zwarta.png`, paleta 124 kolory + kolory znaczników, 540–650 KB); dodatkowo żółte osie dróg OSM (`roads.graph.json`) jako kontrola rejestracji i orientacji. **Kontrola wzrokowa (Read na PNG, 2026-11-14):** osie dróg leżą na jezdniach, znaczniki rozłożone na całym obrazie i leżą na zieleni — W1: drzewa/krzewy w ogrodach, skarpa N od bloków, drzewa na podwórkach (autobus na jezdni zniknął po filtrze z p. 5); W2: drzewa i krzewy w ogródkach działkowych i w zadrzewieniu przy torach; W3: jaśniejsze korony w drzewostanie iglastym; część znaczników trafia na jasne płaty trawnika (ExG bez modelu wysokości nie odróżnia trawnika od niskiej korony — skala UNVERIFIED). Warstwa zwartej zieleni (cyjan) ma znane artefakty — długie proste krawędzie przez jezdnię/zabudowę. **Odsetek środków koron na zieleni (ExG>0,06), przeliczony na obrazie WMS, po filtrze:** W1 (67 koron) **100 %**, W2 (439) **99,8 %**, W3 (28) **100 %**; ważony **99,8 %** (próg >80 % ✓). Kontrola: te same środki na obrazie odbitym N–S dają 25,4 / 50,3 / 53,6 % — rejestracja potwierdzona niezależnie od mozaiki detektora. Wyniki: `overlays_check.json`.
- **Porównanie z P10 (po poprawce flipa, `comparison_p10.json`):** P10-2xx (n=37): mediana Δ pokrycia **−54 p.p.**, zgodne |Δ|≤15 p.p.: **5/37**, spadki >30 p.p.: **26**, wzrosty: **2**; suma koron P10=445 vs **M51=60**; mediana maski M51 62%. P10-3xx (młode nasadzenia, 13 okien): P10=64 (suma szt./100 m) vs **M51=23** korony r 0,7–2,0 m w oknach (suma `m51_na_100m` = 14). *M51-FIX-2: plik przeliczony na zbiorze po filtrze; poprzedni `comparison_p10.json` był wygenerowany z wcześniejszego stanu koron (ponowne uruchomienie na 5258 koronach dawało 60, nie 58, w 2 oknach P10-2xx różnica o 1 koronę); filtr zmienił tylko P10-302 (−1, autobus) i `street_agg.json` (aleja 6→5, Andersa 3→2 korony w buforze 8 m).* **Przyczyny różnic są metodologiczne, nie rejestracyjne:** detektor P10 celowo łapie ciemny baldachim (LUMA_MAX 118) i liczy krzewy jako korony; M51 wymaga jasnych, rozłącznych koron r≥0,7 m — dlatego na odcinkach z krzewami/trawnikiem pokrycie P10 jest wyższe. Różnice w 2 oknach (wzrost M51) wynikają z poprawnie zarejestrowanych nasadzeń przy jezdni. `street_agg.json`: agregacja koron per ulica (bufor 8 m).
- **Ważne:** warstwa `plot_canopy.json` z P10 jest poprawnie zarejestrowana (42,4% ExG>0,06 vs 29,6% po odbiciu) — jej detektor celowo liczy ciemny baldachim.

## Zadanie 4 — projekt zieleni Al. Tysiąclecia (Strabag 2021/22)

**SOURCED (karta postępowania BIP UM Białystok, 2026-11-13):** postępowanie **ZDM-X.271.16.2018.JZ**, „Rozbudowa Alei Tysiąclecia Państwa Polskiego w Białymstoku od ul. Wileńskiej do terenu kolejowego przy ul. Poleskiej wraz z infrastrukturą techniczną" (formuła D&B), wykonawca **STRABAG Sp. z o.o.**, 32 883 642,97 zł brutto; komunikat UM 31.01.2022: **74 drzewa, 109 krzewów**, 20 600 m² trawników i skarp, ~385 mb ekranów akustycznych.
**UNVERIFIED — gatunki, obwody, rozstaw:** SIWZ (20 s.) i postanowienie RDOŚ (17 s., CCITT G4→PNG, własny dekoder) to skany bez warstwy tekstowej; dokumentacja projektowa nieopublikowana na BIP.

## Pliki

- Repo: `README.md`, `manifest.csv` (**59 wierszy M51** — po usunięciu M51-214 w M51-FIX-2), `ZAWARTOSC_v3.txt` (mapa ZIP v3 + SHA-256), `crowns.geojson` (5244 korony), `nonveg_removed.geojson` (14 usuniętych — M51-FIX-2), `nonveg_check.png` (wycinki 14 usuniętych), `compact_greenery.geojson` (771 poligonów — nowe), `comparison_p10.json`, `street_agg.json`, `overlays_check.json` + `overlays/*.png` (M51-FIX-2: north-up, 960 px), `street_assignment.json` (przypisanie 18 kadrów ≤25 m — nowe), `new_frames_streets.json`, `extra_series.json`, `hedge_viewings.json` (36 obejrzeń z werdyktem — nowe), `orto_metadata.json` (GetFeatureInfo — nowe), `audit_20_percent.json` (nowe losowanie), `sources.md`, `tools/` (detect_crowns.py, compare_with_p10.py, overlays_check.py, assign_streets.py, audit_fix.py, tm2180.py).
- **Zdjęcia nie idą do gita** (`files/` w `.gitignore`). **ZIP v2 (`mistral-p10-greenery-3-files-v2.zip`) był niekompletny** (przegląd s19 §3.4): brakowało kadrów M51-119…126 i odcinków M51-219…222 (Commons 20220725_123952, 123959, 124049, 125403, 125410, 125414, 125438, 132358, 132511, 132717), a `ZAWARTOSC_v2.txt` błędnie przypisywał `walk_*.jpg` do 119–126. **Zastępuje go ZIP v3 (M51-FIX-2): `p10-greenery-3_v3.zip`** (u lidera: `artifacts/m51-fix2/p10-greenery-3_v3.zip`, poza gitem) — `frames/M51-101…133.jpg` (33 kadry manifestu), `viewings/walk_*.jpg` + `viewings/extra_*.jpg` (36 kadrów z `hedge_viewings.json`, w tym 8 kadrów 125420, 125821, 131152, 131202, 131205, 131327, 131342, 131431), wszystkie pobrane ponownie z Commons (miniatura 1600 px, licencje z API: 65× CC0, 4× CC BY 3.0 — seria 2020-07-11), `overlays/*.png` (nakładki north-up, M51-FIX-2), `bip/` (SIWZ.pdf + 20 stron JPG, Załączniki 22.07.2020 ZIP + 17 stron postanowienia RDOŚ PNG), `metadane/` (manifest, hedge_viewings, orto_metadata, commons_meta_v3 z sha1 oryginałów, wyniki filtra nie-roślinności) i **`ZAWARTOSC_v3.txt`** (mapa plik → wiersz manifestu → kadr Commons). Nie odtworzono: 51 kadrów KartaView (brak listy wybranych kadrów w repo; nie są źródłem żadnego wiersza manifestu — tylko referencja) ani kadrów P10.
- Licencje: CC0 (seria 2022/2023/2024 Rakoon), CC BY 3.0 (seria 2020-07-11 — „referencja, nie tekstura"), **CC BY-SA 4.0 (KartaView — referencja, nie tekstura)**, CC BY 4.0 (ortofoto GUGiK), ODbL (osie OSM), BIP (dokumenty urzędowe).

## Samokontrola (M51-FIX: nowe losowanie 20%, nowy seed)

`audit_20_percent.json` + skrypt `tools/audit_fix.py`: `random.Random(20261114).sample(ids, ceil(0.2*60))` = **12 próbek** (poprzedni seed 20261113 — zastąpiony). Kontrole: kadry — „co widać" w uwagach + **ulica z OSM z przeliczoną odległością geotagu od osi** (reguła ≤25 m; >25 m tylko z ujawnieniem „POZA progiem" w uwagach) + kierunek UNVERIFIED; odcinki — dodatkowo typ/gatunek, wysokość ESTIMATED z metodą, id zdjęcia; wiersze koron — **% środków koron na zieleń w 3 oknach (100/99,8/100%, próg >80%)**; wiersze BIP — status+licencja. **Wynik: 12/12 PASS.**

## Luki i dalsza praca (uczciwie)

1. **Skidelska, Wileńska, Łańcucka: 0 letnich kadrów z wnętrza ulicy** (poprzednio błędnie: 7/4/7). Wszystkie dozwolone źródła odpytane — Commons ma tylko serie przy alei/Sokólskiej/Motoszko/Andersa/Kombatantów. Pozostałe 6 ulic osiedla (Kowieńska, Lidzka, Wołkowyska, Grodzieńska, Racławicka, Świsłocka) — nadal brak letnich kadrów street-level; G7 (wiosna 2024) pozostaje jedynym street-level.
2. **KartaView outage**: `storage7.openstreetcam.org` HTTP 502 (testy 2026-11-13, trzykrotnie) — 51 kadrów sekwencji przywlotowych niepobranych; azymuty SOURCED z metadanych API zachowane, licencja CC BY-SA 4.0 (referencja, nie tekstura).
3. **OCR SIWZ/RDOŚ** (gatunki/obwody/rozstaw zadania 4) — skany w ZIP, do dokończenia przy dostępnym budżecie analizy obrazu.
4. **Kierunek kamery UNVERIFIED** we wszystkich kadrach Commons (brak GPSImgDirection); jedyny opisany z treści: lokalizacja M51-118 (wiat „353 SOKÓŁSKA / AL. TYSIĄCLECIA").
5. **Wiersze odcinków z wnętrza kwartałów (8/21: 221, 222, 226–231)** leżą poza progiem 25 m od osi nazwanych ulic; po M51-FIX-2 tylko jeden z nich (228) jest liczony jako pas krzewów — reszta to rabaty lub zadrzewienia.
6. **Próg żywopłotów ≥ 20 niespełniony (13)** — patrz Zadanie 2.
