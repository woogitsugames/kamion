# K69 (blok M69) — nocne ulice Białegostoku: oprawy latarni, rozstaw, barwa i kształt pul światła

Sesja chmurowa s21, 2026-11-15. Gałąź `research/night-lamps-s21`. To uzupełnienie M60 (C60, `origin/research/cloud-p17-dusk-lighting`) oraz ADR 0191 i 0192.
Zakresu M60 nie powtarzam: nie ma tu nieba, luksów zmierzchu, norm EN 13201, okien ani ponownego pomiaru rozstawu z ortofoto na Andersa, Maczka, Tysiąclecia i Sokólskiej. Te liczby tylko przywołuję jako SOURCED_SECONDARY.

Pliki w katalogu:
- `manifest.csv` — 84 wiersze K69-001…084. Kolumny są takie jak w bloku M69, a na końcu dopisałem 3 kolumny wymagane przez COMMON: `plik`, `url_pliku`, `sha256_pliku`.
- `sources.md`, `audit_20_percent.json`.
- `osm-street-lamps.json` (334 KB) — zamiast `overpass-result.json`, bo Overpass był niedostępny (szczegóły niżej).
- `osm_spacing.csv` i `osm_spacing_summary.json`.
- `files/` — 32 JPG ≤ 1600 px, 6,1 MB.
- `tools/` — skrypty pobierania i obliczeń. `gen_frames.py` i `build_manifest.py` odtwarzają manifest.

Statusy w manifeście: SOURCED, SOURCED_SECONDARY, ESTIMATED, VERIFIED_WIZJA, UNVERIFIED.

## 1. Zapytanie OSM i rozstawy

**Zapytanie.** Overpass (overpass-api.de, kumi, private.coffee, mail.ru) 15.11.2026 ok. 09:30–09:50 UTC zwracał przez proxy reset połączenia, 502 albo 504. Treść zapytania jest w `tools/q_lamps.overpassql` i `tools/q_lamps_only.overpassql`.
Zamiast tego użyłem OSM API 0.6 `/map` w kaflach 0,01° (`tools/osm_tiles.py`):
- bbox 53.095–53.165 N, 23.120–23.215 E;
- pobranie 15.11.2026, 09:4x–09:54 UTC;
- wynik: **1443 węzły `highway=street_lamp`**.

**Metoda** (`tools/osm_spacing.py`):
- Latarnię przypisuję do najbliższej nazwanej drogi, jeśli leży ≤ 25 m od jej osi (bez footway, cycleway, service).
- Rząd to strona osi way (L, P albo oś przy |t| < 2 m).
- Odstęp liczę między kolejnymi latarniami na tym samym way i w tym samym rzędzie.
- Odstępy poza zakresem 5–80 m odrzucam (luka w mapowaniu).

**Wynik: 16 ulic z ≥ 10 parami** (kryterium ≥ 8 odcinków spełnione). Wszystkie wartości SOURCED (OSM, obliczenie), w metrach.

| ulica | n par | min / mediana / max | p25–p75 | układ (z OSM) |
|---|---|---|---|---|
| Kazimierza Wielkiego | 75 | 9,4 / 25,0 / 49,2 | 24,5–25,4 | jednostronny |
| Lipowa | 53 | 9,7 / 20,4 / 41,1 | 19,8–20,7 | obustronny (deptak, ozdobne) |
| gen. J. Bema | 28 | 8,8 / 30,2 / 66,8 | 28,4–33,4 | obustronny |
| kard. S. Wyszyńskiego | 27 | 9,4 / 33,5 / 40,0 | 29,3–34,5 | głównie jednostronny |
| Zwycięstwa | 24 | 7,8 / 45,1 / 53,6 | 30,0–49,3 | obustronny |
| M. Skłodowskiej-Curie | 21 | 19,7 / 40,5 / 45,3 | 35,2–42,6 | obustronny |
| św. Rocha | 19 | 25,7 / 38,1 / 46,2 | 31,3–41,8 | obustronny |
| Ryska | 17 | 11,7 / 28,6 / 42,6 | 25,3–34,5 | obustronny |
| al. J. Piłsudskiego | 16 | 25,2 / 40,1 / 45,5 | 29,9–45,0 | jednostronny (rząd) |
| Nowowarszawska | 13 | 19,9 / 36,4 / 65,2 | 33,2–40,0 | jednostronny |
| Młynowa | 13 | 19,4 / 24,4 / 74,8 | 22,1–29,8 | jednostronny |
| Podlaska | 12 | 26,3 / 27,9 / 32,5 | 27,3–30,0 | jednostronny |
| Antoniukowska | 12 | 18,8 / 30,1 / 50,6 | 29,6–32,9 | obustronny |
| Nowy Świat | 11 | 13,1 / 29,8 / 56,9 | 18,7–32,7 | jednostronny |
| Jurowiecka | 11 | 23,7 / 30,0 / 35,6 | 29,1–34,8 | jednostronny |
| Legionowa | 10 | 14,4 / 27,6 / 31,4 | 26,2–30,1 | jednostronny |

- **Ulice trasy C mają w OSM prawie zerowe pokrycie:**
  - Kombatantów: 2 pary, 32,6–33,5 m;
  - Andersa, Maczka, Kuronia, Mickiewicza, Dywizjonu 303: mniej niż 3 latarnie na ulicę.
- Dla trasy przywołuję C60 (ortofoto, SOURCED_SECONDARY):
  - Andersa 41,6 m, n = 6, pas dzielący;
  - Maczka 40,4 m, n = 6;
  - Al. Tysiąclecia (odcinek południowy) 34,8 m, n = 7;
  - Sokólska 32,4 m, n = 5.
- Rozstaw na Kuronia, Mickiewicza, Dywizjonu 303 i Wysockiego jest **UNVERIFIED**. Pas ortofoto na Kuronia nie trafił w oś na zakręcie.

**OSM a ortofoto a kadry.** Ulic, które da się porównać w obu źródłach, jest mało:
- Kombatantów: OSM 32,6–33,5 m, C60 32,6 m — zgodne.
- Kadry 2019 z Maczka i Tysiąclecia (Panoramax) pokazują słupy dwuramienne w pasie dzielącym, co jest zgodne z „rzędem w pasie dzielącym” w C60. Odstępu w kadrach nie mierzyłem.

**Tagi OSM** (n = 1443):
- `lamp_mount=bent_mast` 701, `straight_mast` 256, `angled_mast` 4;
- `light:count=1` 348, `=2` 213, `=3` 23, `=4` 10.
- `lamp_type=sodium` 21 i `light:method=led` 4 to dane nieaktualne po wymianach 2023–2025. Nie używać ich jako barwy.

## 2. Typy opraw (bez marek)

h oznacza wysokość punktu świetlnego. Wartości bezwzględnej h nie ma w żadnym dokumencie: warunki ZDM 2024, s. 4 pkt 12: „określenie wysokości słupów, długości wysięgników … leży w gestii Wykonawcy”. Gra przyjmuje GP 11 m — WORKING_VALUE.

| typ | gdzie | sylwetka | kadry |
|---|---|---|---|
| **T1** dwuramienna łukowa w pasie dzielącym (czasem przy krawędzi) | Maczka, Andersa przy rondzie Putry, Al. Tysiąclecia | jasnoszary/biały słup stożkowy; rozwidlenie ok. 0,9 h; ramiona wznoszą się łukiem i kończą płaską, wydłużoną głowicą lekko uniesioną. Wysięg ramienia **0,13–0,17 h** (ESTIMATED: 145/880 i 115/880 px w 3eba62ce, perspektywa). Głowica ok. 0,07 h | 10 (Panoramax 2019) |
| **T2** jednoramienna łukowa przy krawędzi | Tysiąclecia, Putry, Kalinowskiego, Kołłątaja, Lipowa (2006) | jak T1, jedno ramię nad jezdnią | 8 |
| **T3** ozdobna jednoramienna (pastorał / łabędzia szyja) | Lipowa (deptak), pl. NZS | ciemny smukły słup, zwisająca oprawa | 3 |
| **T4** ozdobna wielokulowa (2–4 kule) | Rynek Kościuszki | niskie słupy z 2 albo 3–4 kloszami kulistymi | 3 |
| T5 parkowa post-top | osiedle przy Swobodnej | szary słup ok. 4–5 m (ESTIMATED, niska pewność), klosz grzybkowy | **1 kadr — typ niekompletny** |

- **Pochylenie oprawy.** W kadrach 2019 głowice są lekko uniesione, 0…+10° (ESTIMATED).
- Dokumenty ZDM dopuszczają regulację uchwytu: 0…−20° na wysięgniku i 0…+20° na szczycie słupa (2023) oraz 0…−15° / 0…+15° (2024).
- Klosz ma być **płaski, ze szkła hartowanego**, czyli z pełnym odcięciem — zgodnie z założeniem ADR 0191.

## 3. Nocne kadry (20, a–f w manifeście)

Kadry: Panoramax 5, Openverse/Flickr 6, Commons (Rakoon, CC0) 9. Wszystkie obejrzane w ≤ 960 px, część także w wycinkach.

Najważniejsze obserwacje:
- **Barwa do 2020 włącznie:** sodowa pomarańczowa na wszystkich ulicach śródmieścia (Lipowa 2006/2020, Młynowa 2019, pl. NZS, Kalinowskiego, Kołłątaja 2020). Rynek jest ciepłożółty (ozdobne).
- **Osiedle przy Swobodnej, 13.11.2026:** latarnie parkowe w neutralnej lub zimnej bieli.
- **Brak kadrów LED z trasy C.** Nocnych kadrów Andersa, Maczka i ronda Putry po 2023 nie znalazłem: Panoramax nie ma nocnych sekwencji, Commons — patrz luki.
- **Kształt pul:**
  - Na **suchej** nawierzchni przy oprawach bocznych (T2/T3) jezdnia i chodnik są oświetlone **ciągle**: jaśniej pod oprawą, ale bez ciemnych przerw (ov_10c97958, cm_014, cm_016, cm_017). Ułamek jezdni ≈ 1.
  - Wyraźne „pulsowanie” jasności w rytmie słupów widać tylko na **mokrej** jezdni (cm_kol, Kołłątaja: ułamek 0,6–0,8, jezdnia po stronie słupów jaśniejsza; ov_88e3040d). Są to głównie odbicia, nie pule rozproszone.
  - Pojedyncza oprawa parkowa (pnx_c1a5e40e) daje krąg na trawie i asfalcie o promieniu ok. 1–1,5 h, który zanika płynnie.
- **Długości i szerokości plamy z kadrów nie da się zmierzyć.** Brak kadru z góry na suchą jezdnię nocą z znanym h, więc ten parametr jest UNVERIFIED.
- **Halo:**
  - silne tylko we mgle i w opadzie (cm_014, ov_10c97958) — promień ok. 0,2–0,3 wysokości słupa;
  - w powietrzu suchym słabe lub średnie;
  - „gwiazdy” w ov_88e3040d, ov_10510274 i ov_e85fe0c9 to dyfrakcja przysłony albo filtr, nie cecha oprawy;
  - odblaski obiektywu przy LED post-top: pnx_c1a5e40e.
- **Chodnik / DDR:** na wszystkich kadrach chodnik oświetlają te same oprawy. Osobnego światła DDR nie widać na żadnym kadrze.
- **Włączenie:** przy −4,4° (pnx_3e13253b) latarnia świeci, co jest zgodne z C60.

## 4. Barwa — dokumenty ZDM (SOURCED)

Warunki techniczne ZDM do przetargów na „Dostawę i montaż opraw oświetleniowych” pobrałem z platformy e-zamówień (publiczna, bez logowania; `tools/ezam.py`). Skany obejrzałem jako rendery 110 dpi.

| ulica | dokument | CCT ulica | CCT przejścia | inne |
|---|---|---|---|---|
| gen. Andersa, al. 1000-lecia PP, gen. Maczka | ZDM-VII.7021.1.14.2023 (postęp. 93688), s. 1 pkt 2a | **4000 K** | — | Ra ≥ 70; ≥ 130 lm/W; klosz płaski hartowany; redukcja 70 % 22–5; przed wymianą oprawy 70–250 W |
| W. Wysockiego | ZDM-VII.7021.1.4.2024 (120561), s. 1 pkt 2a–b | **4000 K** | **5700 K** | jw. |
| A. Mickiewicza, J. Kuronia, Dywizjonu 303 | ZDM-VII.7021.1.7.2024 (122716), s. 1 pkt 2a–b | **4000 K** | **5700 K** | parkowe 4000 K, ≥ 119 lm/W; przejścia 100 % całą noc |

- Udzielenie zamówień: TED 658997-2023 i 769998-2024 (Kuronia, Mickiewicza, Dywizjonu 303; 17.12.2024).
- **Data montażu i stan w terenie w 2026 są UNVERIFIED.** Jedyne kadry z tych ulic są dzienne, z 2019, sprzed wymiany.
- **Spójność dokumentów i kadrów: NIE da się sprawdzić**, bo kadry nocne trasy są sprzed wymiany i pokazują sód. Kadry 2006–2020 ze śródmieścia: sód — spójne z „oprawami o mocach 70, 100, 150, 250 W” do demontażu.
- Źródło barwy jest dla **7 ulic** (kryterium ≥ 4 spełnione).

## 5. Liczby do kalibracji (ADR 0191/0192)

| parametr | trasa C | ogólnie Białystok | metoda / źródło | gra / ADR dziś | różnica |
|---|---|---|---|---|---|
| rozstaw słupów [m] | Andersa 41,6; Maczka 40,4; Tysiąclecia 34,8; Sokólska 32,4; Kombatantów 32,6–33,5 | mediany 20–45; typowo 25–40 (16 ulic) | ortofoto (C60) / OSM | `standards.LAMP` GP 36, G 33, Z/L 30; NN p50 28,9 | GP na Andersa i Maczka o 4–6 m za krótki; reszta mieści się w rozrzucie OSM |
| wysokość punktu świetlnego [m] | UNVERIFIED | UNVERIFIED (T5 ok. 4–5, niska pewność) | dokumenty: „w gestii Wykonawcy” | GP 11, G 10, Z 9, L 8 | brak danych do zmiany |
| wysięgnik | 0,13–0,17 h na ramię (≈ 1,4–1,9 m przy h = 11, ESTIMATED); T1 dwa ramiona w pasie dzielącym | T2 jedno ramię | sylwetka 3eba62ce | 0191: pozycja głowicy z `M_lamp_glass`, RC = 1,5 h po stronie jezdni | zgodne co do układu. Sprawdzić `lamp_double_*` w pasie dzielącym Andersa/Maczka (C60) |
| pochylenie | 0…+10° (ESTIMATED, 2019) | — | kadry; regulacja 0…−20° (ZDM) | — | po LED: UNVERIFIED |
| długość plamy (wzdłuż) | UNVERIFIED z kadrów | na suchej nawierzchni ciągła — brak przerw | kadry | RA = 2,4 h (±2,4 h, ogon do 3,6 h) | dla S/h = 41,6/11 = 3,8 ślad 0191 (4,8 h) nakłada się — zgodne z „ciągłą” jezdnią w kadrach |
| szerokość plamy (w poprzek) | UNVERIFIED | ułamek jezdni ≈ 1 (sucho, T2/T3); 0,6–0,8 (mokro, Kołłątaja) | kadry | RC 1,5 h / 0,7 h za słupem | zgodne jakościowo |
| kontrast pod oprawą / między | — | sucho: łagodny, bez czarnych dołów; mokro: wyraźne pulsowanie (odbicia GGX) | kadry | min/szczyt 0,44–0,49 | **rozważyć mniejszy kontrast dyfuzyjny**, a pulsowanie zostawić odblaskowi (0191 pkt 4, High) |
| barwa | **4000 K** (Andersa, 1000-lecia, Maczka, Wysockiego, Kuronia, Mickiewicza, Dywizjonu 303); przejścia **5700 K** | śródmieście do 2020 sód; osiedla 2026 neutralna biel | dokumenty ZDM (SOURCED) | `k_Led` (1; 0,93; 0,82) ≈ 3000–3500 K (ocena C60); DK8 LED „UNVERIFIED” | **k_Led chłodniej (~4000 K)**; nowy kolor 5700 K dla przejść; w ADR 0191 zmienić „UNVERIFIED” na „przetarg 2023 (4000 K), montaż UNVERIFIED” |
| redukcja nocna | 100 % do 22:00, **70 % 22–5**, 100 % od 5:00 | jw. | ZDM | brak | opcjonalnie I0 × 0,7 w nocnym presecie po 22:00 (przejścia 100 %) |
| klosz | płaski hartowany (full cut-off) | — | ZDM | odcięcie ~67–74° | zgodne |
| halo | słabe w suchym powietrzu; silne tylko we mgle | jw. | kadry | glare 3°, K = 0,4 | zgodne. Mocniejsze halo tylko przy mgle (overcast/fog) |

## 6. Tabela „dla silnika” (ulica → …)

| ulica | układ | rozstaw mediana [m] | h [m] | barwa | ułamek jezdni / 1 oprawa | halo |
|---|---|---|---|---|---|---|
| gen. Andersa | T1 w pasie dzielącym + rzędy boczne (C60) | 41,6 (C60) | UNVERIFIED (gra 11) | 4000 K (dok.) | UNVERIFIED (brak kadru LED); jedna oprawa na jezdnię | słabe (sucho) |
| gen. Maczka | T1 w pasie dzielącym | 40,4 (C60) | UNVERIFIED | 4000 K (dok.) | UNVERIFIED | słabe |
| Al. Tysiąclecia PP | T1 w pasie dzielącym, T2 przy krawędziach (płn.) | 34,8 (C60, odc. płd.) | UNVERIFIED | 4000 K (dok.) | UNVERIFIED | słabe |
| rondo Putry | T1 + T2 + maszty sygnalizatorów | UNVERIFIED | UNVERIFIED | 4000 K? (Andersa/1000-lecia dok.; rondo nie wymienione) | UNVERIFIED | — |
| Sokólska | jednostronny | 32,4 (C60) | UNVERIFIED | UNVERIFIED | UNVERIFIED | — |
| Kombatantów | obustronny | 33 (OSM, n = 2) | UNVERIFIED | UNVERIFIED | UNVERIFIED | — |
| Wysockiego | UNVERIFIED | UNVERIFIED | UNVERIFIED | 4000 K, przejścia 5700 K (dok.) | UNVERIFIED | — |
| Kuronia, Mickiewicza, Dywizjonu 303 | UNVERIFIED | UNVERIFIED | UNVERIFIED | 4000 K, przejścia 5700 K (dok.) | UNVERIFIED | — |
| śródmieście (Lipowa, NZS, Kalinowskiego, Kołłątaja) | T2/T3 boczne; Lipowa obustronnie | 20–30 (OSM) | UNVERIFIED | sód do 2020; stan 2026 UNVERIFIED (przetargi 2024: Piłsudskiego, Sienkiewicza…) | ≈ 1 (sucho), 0,6–0,8 (mokro) | słabe; silne we mgle |

## 7. Luki

1. **Brak nocnych kadrów z trasy C po wymianie LED (2023–2025).** To najważniejsza luka. Rozwiąże ją sesja zdjęciowa właściciela, nocą, na Andersa, Maczka i rondzie Putry.
2. **Commons API zwracało HTTP 429 przez całą sesję**, tak samo `upload.wikimedia.org` przy większości miniatur. Kandydatów szukałem przez HTML kategorii miesięcznych: 567 plików z czasem w nazwie przy Słońcu < −6°. Obejrzałem 21 miniatur triage i 10 kadrów 960 px. NSZ i Lipowa 165443 przerwane (429).
3. Overpass niedostępny — zastąpiony API 0.6. KartaView i Mapillary nie były używane.
4. Wysokość montażu i wysięg w metrach: dokumenty nie podają liczb.
5. Typ T5 (post-top) ma 1 kadr.
6. Rozstaw na Kuronia, Mickiewicza, Dywizjonu 303 i Wysockiego nie jest zmierzony.

## 8. Samokontrola

Seed 20261115, próba 17/84 (20,2 %). Wynik: **14 PASS, 3 FIX**.
- K69-031: tag LED zapisany jako „4+1”.
- K69-039: w ov_88e3040d jasne łuki to ślady świateł aut, nie pule.
- K69-061: dwuramienna latarnia stoi przy prawej krawędzi jezdni, nie w pasie dzielącym.

Ponowne zapytanie OSM objęło 2 odcinki (Wyszyńskiego, Młynowa) plus Skłodowskiej. Ponownie obejrzałem 5 kadrów i sprawdziłem 1 cytat z dokumentu ZDM. Szczegóły w `audit_20_percent.json`.

## 9. Uzgodnienie z M60

- Z C60 przywołuję tylko rozstawy z ortofoto. Nie mierzę ich ponownie i nie powtarzam nieba, norm ani okien.
- Plik `20201215 170715 Lipowa…` z C60 świadomie pominąłem.
- Wszystkie nowe kadry Commons mają inne pliki niż C60: inne nazwy, a sha w manifeście.
