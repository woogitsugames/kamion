# Przegląd chmury #71 (M60 zmierzch, `research/cloud-p17-dusk-lighting`) i porównanie z Mistralem #57 — s20, 2026-11-14

**Werdykt #71: SCAL z erratą.**
- Opisy kadrów zgadzają się z obrazem: obejrzałem 19 z 24 (+2 wycinki 1920 px do przeliczenia okien) i nie znalazłem błędu merytorycznego.
- Metadane 24/24 zgadzają się z Commons API: licencja, EXIF, sha1, wysokość Słońca co do 0,1°.
- Rozstaw słupów z ortofoto da się odtworzyć: Maczka powtórzyłem niezależnie, wynik ~40 m.
- Cytaty sprawdzone u źródła: 6/6 (5 teraz, Spitschan w przeglądzie #57).
- `sun.py` jest poprawny (±0,06°).
- Zostały 3 błędy interpretacji w tabeli „Do porównania” (§4) — errata, nie blokada.

**Rekomendacja: scalić #71 jako główne źródło kalibracji ADR 0191/0192.** #57 (Mistral, przegląd = FIX) **nie scalać w całości**. M60-FIX zawęzić do dwóch rzeczy, których #71 nie ma:
1. seria miejska Spitschan 2016 (−4…−8°) jako ESTIMATED, bez kolumny „wieś”;
2. dokumenty UM Białystok (2023: 4 650 opraw, „trasa generalska”; 2026: > 6 900 opraw w latach 2024–25).

Sekcje okien i kadrów z #57 porzucić — #71 robi je poprawnie. Szczegóły w §5.

Nic nie scalono, nic nie scommitowano, PR #71 i #57 bez komentarza. Raport nie jest scommitowany.

## 1. Zakres i metoda

- **Gałąź i diff.** `origin/research/cloud-p17-dusk-lighting` @ `156667155` (3 commity). `git diff --name-only origin/main...` zwraca 14 plików, **wszystkie w `research/cloud/p17-dusk-lighting/`**: README, manifest (87 wierszy), sources, audit, STATUS, `sun.py`, `fetch.py`, `build_manifest.py`, `frames_meta.json`, `ortho_lamp_spacing.csv`, `tools/`. `.gitignore` wyklucza obrazy, ZIP i PDF ✓.
- **Kadry.** Własnym skryptem przez Commons API pobrałem metadane i miniatury 960 px wszystkich 24 plików z manifestu (`fetch.py` autora nie uruchamiałem).
  - Licencje 24/24 ✓, DateTimeOriginal 24/24 ✓, sha1 oryginału 24/24 = `sha1_oryginału` ✓.
  - Wysokość Słońca przeliczyłem z EXIF (CET/CEST wg reguły UE) i GPS: 24/24 zgodne z manifestem (różnica ≤ 0,1°).
  - Obejrzane (19 plików ≤ 960 px): C60-061…072, 075, 076, 077/078, 079, 083, 086, 087. Wycinki 1920 px do przeliczenia okien: 075, 076. Nieoglądane: 073/081 (ten sam plik), 074 (odrzucony), 080, 082, 084, 085.
- **Ortofoto.** `tools/strip.py` (przeczytany: tylko urllib, PIL, GUGiK WMS) uruchomiłem z katalogu recenzenta dla ul. Maczka (A 53.15942, 23.13476 → B 53.15933, 23.13045).
  - Słupy w pasie dzielącym (wyraźne cienie) przy s ≈ 21 / 61 / 101,7 / 141,5 / 181 m, czyli odstępy 40,3 / 39,8 / 39,5 m.
  - Wynik autora (20,8 / 61,3 / 101,5 / 141,5 / 181,0) **potwierdzony**.
- **Cytaty (6).** Schlyter radfaq (tabela E od −8° do +1°), Fotios i in. 2024 (PLoS ONE, PMC11469482), Novak i in. 2025 (CIE x051, PDF), Patat i in. 2006 (arXiv), TED API (pełnotekstowo 281034-2023), Spitschan 2016 (sprawdzony już w przeglądzie #57). Szczegóły w §3.
- **`sun.py`.** Sprawdziłem 4 daty z tabeli. Moim algorytmem (NOAA-ish) dla podanej godziny „koniec zmierzchu cywilnego” wychodzi −5,94 / −6,06 / −6,05 / −5,98° ✓.
- **Gra.** Sprawdzone pliki i stałe:
  - `SkyModel.cs`: `CivilTwilightEndLux` 3,4, log-liniowa `TwilightFactorAt` od ~2,25 klx przy 0,5°;
  - `StreetLamps.cs`: włączanie `InverseLerp(3°, 1°)`, I0 2500 cd, `k_Led` (1; 0,93; 0,82), `NightFloorLux` 1;
  - `StreetLampOptics.cs`;
  - `NightWindows.cs`: mieszkania 0,40→0,50, biura 0,65→0,15, 15 cd/m², włączanie 4°→−2°;
  - `tools/worldgen/roads/standards.py`: `LAMP` GP 11 m / 36 m, G 10/33, Z 9/30, L 8/30.

## 2. Kryteria akceptacji (blok M60 w MISTRAL-TASKS-9 + CLOUD-FABLE-PROMPT-S20)

| Kryterium | Wynik |
|---|---|
| 1. Tabela nieba: E przy −4…−8° bezchmurnie i pochmurnie, L zenitu i horyzontu (od Słońca i przeciwnie), barwa | **CZĘŚCIOWO, uczciwie.** E bezchmurnie jest dla −8…+1° (Schlyter — wtórne, ale ciągłe; Fotios/Muneer). L zenitu z Patata jako ESTIMATED. Pochmurnie, horyzont po obu stronach Słońca i CCT oznaczono UNVERIFIED (C60-011, 020, 024) i opisano w lukach ✓. Barwa nieba z 5 kadrów, słownie, bez RGB ✓ |
| 2. Ulice trasy: klasa / L / Uo / h / rozstaw / źródło / LED-kiedy / próg | **CZĘŚCIOWO, uczciwie.** Rozstaw z ortofoto dla 4 ulic + OSM dla Kombatantów, z metodą i współrzędnymi ✓. LED: Andersa, Maczka i Al. 1000-lecia w ogłoszeniu TED 281034-2023, które **sprawdziłem pełnotekstowo przez API** ✓; Wysockiego w 697205-2023 i 73896-2024 ✓. Klasa, h, CCT i próg dla ulic to UNVERIFIED, z opisem prób ✓ |
| 3. Okna: liczba z literatury + ≥ 10 kadrów (zapalone / widoczne, h0 z EXIF) | **TAK.** Novak 2025: 50 % maks., 6 cd/m² ✓. 13 zliczeń z mianownikiem, h0 z EXIF ✓. Przeliczyłem sam na wycinkach 1920 px: 076 — szczyt 3/4–5, elewacja ~4/22, niski budynek 2/5, razem 8–9/32 (autor 9/32 ✓); 075 — 6–9/40 (autor 8/40 ✓). 083, 079, 087 przy 960 px wiarygodne, nieprzeliczane |
| 4. ≥ 10 kadrów ulic Białegostoku o zmierzchu/nocą: plamy, barwa, halo | **TAK liczbowo (13), CZĘŚCIOWO co do trasy** — 3 kadry z Al. Tysiąclecia/Kombatantów, 1 z Wysockiego, reszta to śródmieście (autor sam to pisze) |
| Każdy kadr OBEJRZANY, WGS84, `kierunek_deg` albo UNVERIFIED, data i godzina | **TAK.** `kierunek_deg` = UNVERIFIED w 24/24 (EXIF nie ma azymutu) — zgodnie z blokiem |
| Liczby ze źródłem albo ESTIMATED z metodą, bez RGB jako luminancji | **TAK** |
| Samokontrola ≥ 20 % z seedem, ponowne obejrzenie | **TAK** (18/87, `Random(20261114)`, 8 kadrów obejrzanych ponownie) |
| Licencje, zakaz Google | **TAK.** Kadry CC0 (22) i CC BY 3.0 (2). Novak 2025 ma licencję **CC BY-NC** — używane są tylko liczby (fakty), więc to dopuszczalne; dopisać to w sources |
| JPG ≤ 1600 px / fetch.py + sha256 | **CZĘŚCIOWO.** `fetch.py` pobiera miniatury 1920 px (oryginały blokował HTTP 429). Zostaje tak, bo pliki nie idą do gita ani do gry |
| Zmiany tylko we własnym katalogu | **TAK** |

## 3. Weryfikacja liczb u źródła

| Wiersz | Wartość | Sprawdzenie | Ocena |
|---|---|---|---|
| C60-001…007 | E: 759 / 79,1 / 29,9 / 10,4 / 3,41 / 1,09 / 0,348 lx (0, −3…−8°) | radfaq: „-6.0 0.53 3.41” itd., wszystkie zgodne. Tabela na stronie **nie ma przypisanego źródła** (README podaje „Explanatory Supplement”, którego nie otwarto) | ✓, status wtórny poprawny |
| C60-008/009/010 | 355 / 4,3 / 0,001 lx | PMC11469482 Table 1 ✓; przypis „Definitions from Muneer” | ✓ |
| C60-016 | Paranal ~30 % ciemniej niż nizina | arXiv astro-ph/0604128, abstrakt ✓ | ✓. Przeliczenia mag/arcsec² → cd/m² (C60-012…015) nie powtarzałem |
| C60-037/039 | Andersa, Maczka w przetargu LED | TED API, pełny tekst, zapytania per numer: 281034-2023 zawiera „Andersa”, „Maczka” i „1000-lecia” ✓ (data 2023-05-12); 697205-2023 zawiera „Andersa” i „Wysockiego” ✓; 73896-2024 — „W. Wysockiego” ✓; 658997-2023 (udzielenie, 2023-10-30) zawiera „Maczka” ✓ | ✓ (montaż nadal UNVERIFIED — autor to pisze) |
| C60-055/056/058 | 50 % okien, 6 cd/m², reklamy 50 cd/m² | PDF CIE x051 (Novak i in. 2025), Výškovice/Ostrawa: wszystkie trzy zdania dosłownie ✓ | ✓ (licencja CC BY-NC — tylko liczby) |
| C60-047…049 | rozstaw 41,6 / 40,4 / 34,8 m | przeliczyłem z `ortho_lamp_spacing.csv` (mediany ✓); Maczka odtworzona z ortofoto ✓ | ✓ |

## 4. Errata do #71 (nie blokuje scalenia; poprawić przy okazji albo dopisać w ADR)

1. **„Gra za ciemna przy 0…−3°” (tabela „Do porównania”, `TwilightFactorAt`) — kierunek jest błędny dla 0…−2°.** Z kodu: E_gra(el) = 3,4 · e^(−0,999·(el+6)). Porównanie ze Schlyterem:

| el | +0,5° | 0° | −1° | −2° | −3° | −4° | −5° | −6° | −7° | −8° |
|---|---|---|---|---|---|---|---|---|---|---|
| gra [lx] | ~2250 | 1366 | 503 | 185 | 68 | 25,1 | 9,2 | 3,4 | 1,25 | 0,46 |
| Schlyter [lx] | 994 | 759 | 405 | 189 | 79,1 | 29,9 | 10,4 | 3,41 | 1,09 | 0,348 |
| gra/ref | **2,26** | **1,80** | 1,24 | 0,98 | 0,86 | 0,84 | 0,88 | 1,00 | 1,15 | 1,32 |

   Uwaga: 2250 lx przy 0,5° w grze to **samo niebo** (`e05 = (0,8 + 15,5·√sin 0,5°)·1000`, bez Słońca). Poniżej 0° gra nie ma światła bezpośredniego, więc porównanie z całkowitym E Schlytera jest poprawne dla el < 0°. Wdrażając tabelę, trzeba ją znormalizować do wartości modelu przy 0,5° albo zmienić `e05`, bo inaczej będzie skok 2250 → 994 lx.

   Gra jest **za jasna przy +0,5…−1°** (×1,2–2,3), **za ciemna o 12–16 % przy −3…−5°**, a przy −7…−8° znów za jasna. Spitschan (miasto, #57) daje −4° 36,1 lx i −8° 0,49 lx, więc obie serie różnią się od siebie o 20–40 %. Prawdziwy rozrzut źródeł przy −4° to 30–36 lx.

2. **„Stosunek horyzont/zenit w LUT: rząd 1–2× przy −5…−6°” jest sprzeczny z własnymi wierszami autora.** C60-018 (horyzont ~0,1 cd/m² po 30 min) i C60-012/013 (zenit 2,0 / 0,52 cd/m² przy −5/−6°) dają 0,05–0,2×. Wiersze Schlytera „(horiz)” to rząd wielkości bez azymutu Słońca. **Nie używać ich jako celu.** Celem może być tylko zenit: 0,3 (Schmude, #57) do 0,5–0,7 cd/m² (Patat + 30 %), czyli przedział ×2.
3. **Uwaga do wiersza Uo/Ul:** gra liczy min/szczyt E, a norma — min/średnia L. Autor to zaznacza ✓. Wniosek „0,20 (h 8/S 30) poniżej każdej klasy M” jest jednak porównaniem różnych wielkości, więc test trzeba dopiero napisać (patrz §6).
4. Drobne:
   - `sources.md`: dopisać licencję CC BY-NC dla Novak 2025.
   - C60-082 (47 %) słusznie oznaczono jako zawyżone. W statystyce mieszkań „6–28 %” go nie ma ✓.
   - Pliki `fetch.py` mają 1920 px, a blok M60 mówi „JPG ≤ 1600 px”. To ta sama usterka, którą wpisano #57 — tu formalnie też niespełnione. Nie blokuje, bo pliki nie idą do gita ani do gry.

## 5. Porównanie #57 (Mistral) i #71 (chmura)

| Obszar | #57 Mistral (przegląd: FIX) | #71 chmura | Lepsze / do scalenia |
|---|---|---|---|
| E(el), bezchmurnie | Spitschan miasto (całkowanie suplementu) 36,1 / 3,5 / 0,49 lx przy −4/−6/−8 + AMS; **kolumna „wieś” błędna ×17** | Schlyter −8…+1° (ciągła tabela, wtórna) + Fotios/Muneer 4,3 lx; spadek na stopień | **#71** jako tabela bazowa; **#57: tylko seria miejska** jako druga, niezależna (ESTIMATED) |
| E pochmurnie | UNVERIFIED | UNVERIFIED | — |
| L zenitu | 0,29 cd/m² przy −6° (Schmude, przeliczenie) | 0,52 → ~0,7 cd/m² (Patat + 30 %) | obie — przedział 0,3–0,7 |
| L i barwa horyzontu | brak | kadry: żółtawo-brzoskwiniowy pas przy horyzoncie, **róż/lawenda nad nim**, błękit górą; pochmurno — granat bez ciepła | **#71** (064, 071, 076, 086, 087 — opisy zgodne z obrazem) |
| Klasy EN 13201 | POLAB (zgodne) | performanceinlighting (zgodne) + kontrole | równoważne |
| Rozstaw słupów | OSM, n = 1–4; Tysiąclecia i Wysockiego nieodtwarzalne | **ortofoto GUGiK, n = 5–7, z współrzędnymi**, odtworzone przeze mnie (Maczka) | **#71** |
| LED na trasie | UM 2023 „trasa generalska” (bez nazw Andersa/Maczka) | **TED: Andersa, Maczka, 1000-lecia, Wysockiego wprost** | **#71**; dokumenty UM z #57 jako uzupełnienie (liczby opraw 4 650 / > 6 900) |
| Włączanie latarni | Kraków (fotokomórka + zegar), kadry −3,3° (nie świecą) / −3,7° (świecą) | kadr −3,1° (świecą), Augustów: 10 min po zachodzie | obie, spójne: włączenie **między ok. −2° a −3,5°** (przy −3,1° już świecą, przy −3,3° jedna arteria jeszcze nie) |
| Okna mieszkań | brak mianownika, liczby zawyżone; recenzent policzył 14–24 % (n = 7) | 13 zliczeń z mianownikiem: 6–28 %, typowo 20–28 %; literatura 50 % maks., 6 cd/m² | **#71** |
| Okna biur | n = 1 | zależne od godziny zegarowej (23–55 % w pracy, 3 % o 18:44) | **#71** |
| Kadry ulic | 22, w tym 12 sprzecznych z obrazem | 13 + 1 odrzucony, zgodne z obrazem | **#71** |
| Duplikaty między PR | — | wspólne pliki: C60-070 = P17-102, C60-071 = P17-094 (sha1) | przy scalaniu #57 usunąć te kadry |

**Decyzja proponowana:**
- **Scalić #71** (z erratą §4 w ADR / komentarzu).
- **#57: nie scalać w całości.** M60-FIX (`docs/owner/MISTRAL-FIXES-12.md`) zawęzić do dwóch zadań:
  - seria miejska Spitschan −4…−8° jako ESTIMATED (bez „wsi” i CCT 11–20 kK);
  - dokumenty UM Białystok 2023/2026 (opisane, bez wniosku „Andersa/Maczka”);
  - całą resztę (okna, kadry, rozstaw OSM, tabela ulic) usunąć z gałęzi #57, odsyłając do `research/cloud/p17-dusk-lighting/`.
- Jeśli właściciel woli nie angażować Mistrala, wystarczy zamknąć #57 i przenieść 2 liczby (Spitschan miasto −4° 36,1 lx, −8° 0,49 lx) do ADR jako ESTIMATED z odwołaniem do przeglądu #57.

## 6. Liczby kalibracji dla ADR 0191/0192 (i 0182)

Statusy: SRC = źródło sprawdzone; EST = szacunek z metodą; WV = WORKING_VALUE recenzenta.

| Parametr (plik) | Gra dziś | Cel / referencja | Status | Działanie |
|---|---|---|---|---|
| `SkyModel.CivilTwilightEndLux` | 3,4 lx (komentarz „UNVERIFIED from memory”) | 3,41 (Schlyter), 3,5 (Spitschan miasto, AMS), 4,3 (Muneer) | SRC | **wartość zostaje**, komentarz → SOURCED (C60-005/009, P17-002/015) |
| `TwilightFactorAt` (log-liniowo, ~0,37×/°) | 1366 lx przy 0°, 25 przy −4°, 0,46 przy −8° | Schlyter: 759 / 29,9 / 0,348; Spitschan: — / 36,1 / 0,49 | SRC (wtórne) / EST | zastąpić **tabelą** (Schlyter, 1° krok, −8…+1°) z interpolacją log-liniową między węzłami, znormalizowaną do `e05` przy 0,5° (patrz §4 pkt 1). Preset dusk (−6°) bez zmian; poprawia przejścia 0…−4° (zachód za jasny ×1,8). Test EditMode: E(el) w 10 węzłach ±20 % |
| Zenit przy −6° (LUT kopuły) | nieodczytany | 0,3–0,7 cd/m² (Schmude / Patat + 30 %); −10×/2° | EST | log luminancji zenitu w `SkyModel`, akceptacja przy −6° w przedziale 0,3–0,7 |
| Pas horyzontu (0192 P2-1, `SuppressTwilightMagenta`) | koralowy pas na `route_putry` | przy −5…−6°: **przy horyzoncie od Słońca żółtawo-brzoskwiniowy, róż/lawenda NAD nim**, góra niebieska; od strony przeciwnej — równy błękit jaśniejszy ku dołowi; pochmurno — granat bez ciepła | EST (kadry 064, 076, 087, 071, 086, 083) | cel: zero magenty przy samym horyzoncie; róż dopuszczalny tylko jako słabe pasmo ~5–15° nad horyzontem od strony Słońca. Porównanie renderu z C60-064 (CC0) |
| Włączanie latarni (`StreetLamps.SetSunElevation`: `InverseLerp(3°, 1°)`) | pełne od +1° | świecą przy −3,1° (C60-083), −3,7°, −4,1°, −5,4°; przy −3,3° jeszcze nie (P17-103); Augustów 10 min po zachodzie ≈ −1,5…−2,3° | EST/ANALOG | **fade −2° → −3,5°** (WV, jak w przeglądzie #57 — zastępuje wcześniejszą propozycję −1° → −3°). Dusk −6° bez zmian |
| Rozstaw GP (`standards.LAMP["GP"]`) | 36 m, h 11 | Andersa 41,6 m (n 6), Maczka 40,4 (n 6) — **słupy w pasie dzielącym**, Maczka z oprawami na obie jezdnie | EST (ortofoto, odtworzone) | dla Andersa/Maczka (GP z pasem dzielącym) **40 m + słup dwuramienny w pasie dzielącym** (override per ulica albo reguła „GP z pasem ≥ 4 m”). h 11 zostaje (UNVERIFIED) |
| Rozstaw G (33 m) | 33 | Al. Tysiąclecia płd. 34,8 (n 7, pas dzielący); OSM recenzenta #57: 38,9 (inny odcinek) | EST | bez zmian (±2 m); sprawdzić układ w pasie dzielącym |
| Rozstaw Z/L (30 m) | 30 | Sokólska 32,4 (n 5, niska pewność), Kombatantów 32,6 (OSM n 3; przegląd #57: 31,3–32,6) | EST | bez zmian |
| I0 2500 cd przy S/h 40/11 = 3,6 | min/szczyt 0,49 przy h9/S29 | przegląd #57: przy S/h > 3,3 Emin/Eavg spada do ~0,27; klasy M2–M3: Uo ≥ 0,40 | EST (całkowanie śladu 0191) | po zmianie rozstawu na 40 m **dodać test** `StreetLampOpticsTests`: min/średnia E na pasie ≥ 0,35 przy h 11 / S 40. Jeśli nie przejdzie — RA 2,4 → ~2,7 h (szerszy rozsył wzdłuż), a nie wyższe I0 |
| Strumień oprawy | 6,9 klm w dół (I0 2500) | analog BPN-T: ≥ 16,5 klm, 4000 K (parking 2026) | ANALOG | bez zmian (analog nie dotyczy ulic trasy) |
| Barwa LED `k_Led` (1; 0,93; 0,82) | ~3500 K (ocena) | kadry 2022–23: osiedla i parkingi biało-zimne; ZDM: brak | ANALOG / wizja | bez zmian; ewentualnie lekko chłodniej (0,97 / 0,90 → ~4000 K) po decyzji właściciela |
| Sód / LED na trasie | DK8 LED, śródmieście sód | TED 2023: Andersa, Maczka, 1000-lecia, Wysockiego → LED; Lipowa sodowa do 12.2022 | SRC (przetarg) | **zgodne**, bez zmian. ADR 0191: zamienić „stan UNVERIFIED” na „przetarg 2023 (281034-2023), montaż UNVERIFIED” |
| Podłoga nocna `NightFloorLux` 1 lx do 45 m | 1 lx / 0 dalej | kadry: między latarniami nigdy czarno (C60-061, 065); łuna 0,03 / 0,2 lx (przegląd #57) | EST | poza 45 m zostawić **0,03 lx (pogodnie) / 0,2 lx (pochmurno)**, nie 0 |
| Okna mieszkań (`NightWindows.BaseShares.x`) | 0,40 (−6°) → 0,50 (−16°) | zmierzch 6–28 % (#71, n 8), 14–24 % (przegląd #57, n 7); wieczór 22–27 %; literatura: 50 % = maksimum, nie wartość typowa | EST | **0,25 (−6°) → 0,28 (−16°)** (WV) |
| Rampa włączania okien | 4° → −2° | przy −3,1° tylko 6 %, przy −3,7…−4,1° już 20–28 % | EST | **+1° → −5°** (WV; #71 proponuje 0 → −8°; kompromis, bo przy −4° kadry mają już ~20 %) |
| Okna biur | 0,65 → 0,15 wg Słońca | 23–55 % w godzinach pracy, 3 % o 18:44 (czw.); zależne od zegara | EST | uzależnić od godziny zegarowej presetu: do 17:00 → 0,4; 17–19 → spadek do 0,1; po 19 → 0,05. Dusk listopadowy (16:10) = 0,4. WV |
| Okna klatek (0,35) | 0,35 | pion klatki świeci: C60-079 (3/3 kondygnacji), P17-080 (4/5) | EST n = 2 | **0,6** (WV) |
| Luminancja okna `MeanLuminance` | 15 cd/m² | 6 cd/m² (Novak 2025, bloki z firanami, Ostrawa) | SRC | **8 cd/m²** (WV: 6 zmierzone + zapas na mały ekran telefonu; ocenić na A16). Reklamy podświetlane 50 cd/m² |
| Barwa okien | 2700/3200/4000/4500 K per klasa | mieszkania: od ciepłej żółci po zimną biel, pojedyncze czerwone i niebieskie (zasłony, TV); biura: zimna biel | wizja | rozrzut CCT **w obrębie mieszkań** (2700–4000 K + ≤ 3 % kolorowych), biura 4000–4500 K |
| Glare / halo opraw (0192) | K 0,4, 3° | halo przy każdej oprawie, rośnie z wilgocią — efekt obiektywu telefonu | wizja | bez zmian (skala niemierzalna) |

Każdą zmianę wykonać z pętlą `visual-qa`: `WorldC` dusk i night, `route_putry_approach`, `chase`, Low/High. Na koniec zrzut z A16 i decyzja właściciela (P1-5 z 0182).

## 7. Dla lidera

- **#71 → SCAL z erratą** (§4: punkty 1–2 dopisać w ADR przy wdrażaniu; `sources.md` — licencja Novak). Przy scalaniu uruchomić `python3 research/cloud/p17-dusk-lighting/fetch.py` (24 pliki, ~13 MB, Commons dławi — skrypt ponawia).
- **#57 → nie scalać w obecnej postaci.** M60-FIX zawęzić (§5) albo zamknąć PR i przenieść 2 liczby Spitschana do ADR.
- **Do gry** — tabela §6. Najtańsze i najpewniejsze:
  1. `CivilTwilightEndLux` → SOURCED (tylko komentarz);
  2. okna mieszkań 0,25→0,28 i luminancja okna 8 cd/m²;
  3. włączanie latarni −2° → −3,5°;
  4. GP Andersa/Maczka 40 m w pasie dzielącym + test równomierności;
  5. `TwilightFactorAt` jako tabela.
- **Pliki recenzenta (scratch sesji, tymczasowe):**
  - `C:\Users\matma\AppData\Local\Temp\claude\65a86252f72ba2de\44810253-4f54-463a-b591-9868ed7d4a4f\scratchpad\c60\img\C60-*.jpg` + `meta.json`;
  - `…\ortho\Maczka_s0.jpg`, `Maczka_s1.jpg`;
  - skrypty `…\tools\c60fetch.py`, `…\tools\c60chk.py`.
