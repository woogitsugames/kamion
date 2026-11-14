# Przegląd M60 (P17 zmierzch: niebo, oświetlenie ulic trasy, zapalone okna) — s20, 2026-11-14

**Werdykt: FIX.** Część dokumentowa jest uczciwa:
- cytaty UM Białystok (28.07.2023 i 18.08.2026) zgadzają się ze świeżo pobranymi stronami;
- tabela klas M/P (POLAB) jest spójna;
- luki per ulica oznaczono uczciwie jako UNVERIFIED;
- 37 kadrów Commons ma licencje, daty i GPS zgodne z API;
- h0 da się odtworzyć (±0,3°), seed audytu jest odtwarzalny, Google nie użyto, duplikatów nie ma.

Oddanie ma jednak błędy, które wpłynęłyby na kalibrację, i nie spełnia kryteriów kadrowych:
- **Tabela 1, kolumna „wieś” (pogrubiona) jest błędna o rząd wielkości.** Przy −6° podaje 60 lx, a AMS (P17-002) i seria miejska z tej samej pracy dają 3,5 lx. Sama praca Spitschan 2016 mówi, że obie lokalizacje zgadzają się aż do zmierzchu nawigacyjnego.
- **Opisy kadrów odbiegają od obrazu.** Liczby zapalonych okien są zawyżone, „12 latarni = 12 plam” to kadr we mgle, a w P17-100 nie ma latarni. Zdania są szablonowe.
- **Fałszywe „brak czasu w EXIF”** dla trzech jedynych kadrów bloków o zmierzchu (083/084/087).
- **Brak odsetka okien.** Zadanie wymagało liczby zapalonych do wszystkich widocznych.
- **Brak luminancji i barwy horyzontu** po obu stronach Słońca.
- **Pole `kierunek_deg` jest puste w 37/37 kadrach** (zamiast UNVERIFIED).
- **Pliki w ZIP-ie mają po 1920 px** (36/37), choć README mówi o ≤ 1600 px.
- **Audyt nie obejrzał ponownie żadnego obrazu.**

Blok poprawek: `docs/owner/MISTRAL-FIXES-12.md` § M60-FIX. Nic nie scalono, nic nie scommitowano, PR #57 bez komentarza.

## 1. Zakres i metoda

- **Gałąź.** `origin/research/mistral-p17-dusk-lighting` @ `46a0fdd13` (2 commity). `git diff --stat main...` pokazuje 5 plików wyłącznie w `research/mistral/p17-dusk-lighting/`: README, manifest (109 wierszy: niebo 35, ulica 33, okna 19, kadr 22), sources, audit, `.gitignore`. Pliki obejrzano przez `git archive` w scratchu.
- **ZIP.** Dostarczył go właściciel, lider rozpakował do `research/_incoming/mistral-p17-dusk-lighting-files/files/`. Sha256 ZIP-a (`93CDDD14…4914`) jest **zgodny z README**. 37 plików, md5 unikalne (0 duplikatów).
  - **36/37 plików ma 1920 px na dłuższym boku** (np. 1920×1080, 1920×3413). Wyjątek: `Osiedle` 1632 px. Kryterium „JPG ≤ 1600 px” nie jest spełnione.
- **Kadry.** Metadane wszystkich 37 pobrałem z Commons API (licencja, autor, DateTimeOriginal, GPS, sha1 — wszystkie sha1 unikalne).
  - Obejrzane w ≤ 960 px (24): P17-073, 074, 075, 076, 077, 079, 080, 081, 083, 084, 085, 086, 087, 088, 089, 090, 092, 099, 100, 103, 104, 105, 106, 109.
  - Wycinki z plików ZIP: 077, 105, 103, 106, 073.
  - h0 przeliczyłem z EXIF (CET/CEST wg reguły UE) i GPS. Różnica wobec manifestu wynosi ≤ 0,33°, w tym 2023-10-27 jako CEST ✓.
- **Literatura.** Pełny tekst Spitschan 2016 (Europe PMC, PMC4895134) oraz dwie strony bialystok.pl. AMS Glossary zwrócił 403 — cytat P17-001/002 przyjmuję z manifestu, niesprawdzony ponownie. Nie sprawdzałem ponownie: Schmude 2024, Koomen 1952, Faid 2024, Krieg 2026, Jechow 2019, Nachtlichter 2025, ZDM Kraków, TED, Yunex, POLAB, Lipnik.
- **OSM.** `Data/raw/osm/podlaskie-261108.osm.pbf`, pyosmium, `highway=street_lamp` w bbox miasta, ways ulic przycięte do bbox, lampy ≤ 25 m od osi, odstęp do najbliższego sąsiada.
- **Gra.** ADR 0191/0192, `SkyModel.cs` (`CivilTwilightEndLux`, `TwilightFactorAt`), `LightingPreset.cs` (dusk −6°, EV100 3,7), `StreetLamps.cs` (włączanie 3°→1°, `NightFloorLux` 1, zasięg 45 m), `StreetLampOptics.cs` (RA 2,4 h, RS 1,5 h, ogon S 0,25 / R 1,5), `NightWindows.cs` (udziały, 15 cd/m²).

## 2. Kryteria akceptacji M60

| Kryterium (MISTRAL-TASKS-9 § M60) | Wynik |
|---|---|
| 1. Tabela: h0 → Ev [lx] (bezchmurnie i pochmurnie), luminancja zenitu **i horyzontu (od Słońca i przeciwnie)**, CCT horyzont vs zenit | **CZĘŚCIOWO / BŁĄD.** Seria miejska i AMS są dobre. **Seria „wieś” jest błędna** (§3.1), a CCT liczono z tej samej serii, więc też jest wątpliwe. Zenit zgadza się z AMS (0,29 cd/m² ↔ ~1 lx przy E≈πL, OK rzędem). **Brak luminancji horyzontu i CCT horyzontu** (jest jedno zdanie jakościowe z abstraktu Lee 1994), a tego braku nie ma w „Lukach”. Pochmurny zmierzch uczciwie oznaczono UNVERIFIED |
| 2. Ulice trasy: klasa / Lm / Uo / h / rozstaw / źródło / LED-kiedy / próg włączania | **CZĘŚCIOWO.** Klasy, Lm, Uo i h per ulica są UNVERIFIED, uczciwie, z opisem prób (Marketplanet, BIP-skany). Rozstawy OSM mają n=1–4, a Tysiąclecia i Wysockiego nie dają się odtworzyć (§5). **„Trasa generalska = Andersa + Maczka przez rondo Putry” to wniosek Mistrala.** Strona UM nie wymienia Andersa ani Maczka, a wiersz ma status SOURCED. Przetarg 2023 nie dowodzi, że LED zamontowano. Barwy LED (K) nie podaje żadne źródło |
| 3. Okna: liczba z metodą (literatura) + ≥ 10 zdjęć, **policz zapalone / wszystkie widoczne**, h0 z EXIF | **NIE.** Literatura (Nachtlichter) jest jakościowa. W kadrach są tylko liczby zapalonych, bez mianownika, a README §Luki 6 przyznaje „odsetek wyłącznie jakościowo”. Liczby są zawyżone w kadrach pełnych lampek świątecznych (§3.2). Dla 083/084/087 wpisano „brak czasu w EXIF — h0 nie policzone”, a EXIF jest: **083 h0 ≈ −5,7°, 084 ≈ −6,5°, 087 ≈ −4,3°** (087 bez GPS, Warszawa przybliżona). To jedyne kadry bloków przy h0 gry |
| 4. ≥ 10 zdjęć ulic Białegostoku o zmierzchu/nocą: plamy, barwa, halo | **CZĘŚCIOWO.** Jest 22 kadry, ale prawie wszystkie to deptak Lipowa i Rynek Kościuszki z ozdobnymi latarniami i iluminacją świąteczną (grudzień), a nie arterie trasy C. Opisy są szablonowe („N latarni HPS, plamy+halo, N okien”) i w kilku miejscach sprzeczne z obrazem (§3.2) |
| Każdy kadr OBEJRZANY, WGS84, `kierunek_deg` albo UNVERIFIED, data i godzina | **NIE.** `kierunek_deg` jest pusty w 37/37 (EXIF nie ma GPSImgDirection, więc powinno być UNVERIFIED). P17-109 opisano jako „poza Białymstokiem”, mimo tytułu „Streetlamps in Białystok” |
| Samokontrola ≥ 20 %, jawny seed | **CZĘŚCIOWO.** Seed 20261113 → te same 22 id w tej samej kolejności ✓. Audyt sprawdza tylko HTTP, cytat i status. **Nie obejrzał ponownie żadnego kadru** (sam to przyznaje). P17-077 („20–30 okien”) i P17-106 („plamy+halo”) przeszły, choć są błędne |
| Licencje, zakaz Google | **TAK.** Rakoon CC0 / CC BY 3.0, Raf24 CC BY 4.0, BY-SA (Borawski, Klisowski, gustawkaz, Bromaski) jako referencja. Prasa i strony firm użyte jako fakty. Mapillary i Google nie użyte |
| Zmiany tylko w `research/mistral/p17-dusk-lighting/`, ZIP + sha | **TAK** (ZIP zgodny z sha). **≤ 1600 px — NIE** |

## 3. Błędy merytoryczne

### 3.1 Tabela 1, „wieś” (P17-008…012, P17-018…020)

| h0 | „wieś” M60 | „miasto” M60 (P17-013…017) | AMS (P17-001…004) | Koomen 10×/2° od miasta −6° |
|---|---|---|---|---|
| −4° | 312 | 36,1 | — | ~35 |
| −6° | **60** | 3,5 | **3,5–2** | 3,5 |
| −8° | 6,0 | 0,49 | — | ~0,35 |

- Spitschan i in. 2016 (pełny tekst): pomiary obu lokalizacji „largely agree in these two measurement sites up to nautical twilight”, a miasto jest jaśniejsze dopiero od ok. −8° (światło sztuczne). Seria M60, w której wieś jest 17× jaśniejsza od miasta przy −6°, przeczy więc i AMS, i samej pracy. Uwaga P17-013 („przy −8° miasto ~12× ciemniejsze niż wieś”) jest fizycznie odwrócona.
- Spadek „wsi” −4→−6° wynosi tylko 5,2× (Koomen: 10×/2°). Najpewniej czas lub h0 surowych pomiarów wiejskich przesunięto o ~2–3°: strefa czasowa albo czas lokalny vs UTC (UNVERIFIED, przyczyny nie badałem).
- **Do gry nie wolno brać tej kolumny ani CCT 11 100 / 15 100 / 20 200 K.**
- Wartości to całkowanie suplementu przez Mistrala, a nie liczby z tekstu pracy, więc status powinien być **ESTIMATED**, nie SOURCED.

### 3.2 Kadry — opis Mistrala a obraz

| Kadr | M60 | Co widać (recenzent) | Ocena |
|---|---|---|---|
| 073 (h0 −3,8°, pl. Niepodległości) | HPS, 20–30 okien | Niebo niebieskie, bez różu przy horyzoncie. Wysokie maszty z oprawami **białawymi** (rdzeń przepalony, otoczka blado-brzoskwiniowa, barwa nierozstrzygalna); jedna oprawa pomarańczowa w lewym górnym rogu. Okna: kilkanaście–20 ✓. Plam na jezdni nie widać (światło nieba dominuje) | barwa nadinterpretowana |
| 074 (−4,6°, Lipowa) | 5–7 okien | Lampki świąteczne na drzewach, oprawy HPS pomarańczowe. Zapalone 1–3 okna | zawyżone |
| 075 (−5,1°) | „biurowiec z bankiem” | Blok mieszkalny z bankiem na parterze; 2 zapalone okna na piętrze | typ błędny |
| 076 (−8,5°, Rynek) | „kilka latarni LED (białe)”, 20–30 okien | Białe to **girlandy i iluminacja świąteczna**, nie latarnie; latarnie ozdobne ciepłe. Okna ~6–10 | ✗ |
| 077 (−7,4°, Lipowa) | 4 HPS, **20–30 okien** | Lampki świąteczne, pierzeja w cieniu; w wycinku z 1920 px **żadne okno pięter nie jest zapalone** | ✗ (w próbie audytu — PASS) |
| 079 (−12,1°) | LED „plamy na śniegu”, 4–5 okien | **Latarni w kadrze nie ma.** Niebo zachmurzone pomarańczowo-brązowe, śnieg pomarańczowy (łuna HPS). Okna ~6/32 | opis latarni ✗, okna ✓ |
| 080 (−14,3°) | ≈10 okien | Latarnia parkowa biała (post-top). Okna ~16/110, w tym **pion klatki: 4/5 zapalonych** | zaniżone |
| 081 (−18,8°) | 6–8 okien | Niebo pomarańczowo-brązowe (chmury + łuna). Okna ~14/60, jedno niebieskie (TV) | zaniżone |
| 083 (Mokotów, EXIF 2008-04-29 20:34, **h0 ≈ −5,7°**) | „brak czasu w EXIF”, 50–100 okien | Niebo granatowe, horyzont szaroniebieski, **bez różu**. HPS na arterii z plamami. Blok ~45/250 okien | EXIF ✗ |
| 084 (Skorosze, EXIF 2008-03-26 18:37, **h0 ≈ −6,5°**) | „brak czasu w EXIF”, 50–100 | Długi czas naświetlania (smuga samolotu), niebo przesycone. Bloki ~60/250 | EXIF ✗ |
| 085 (newcity) | 2 HPS, 50–60 okien | Zdjęcie architektoniczne HDR, fontanna, ~1/3 pięter biura zapalona. HPS niewidoczne | latarnie ✗ |
| 086 | 1 okno | 1–2 z ~14 ✓ | ✓ |
| 087 (Biała, EXIF 2025-02-04 16:53, **h0 ≈ −4,3°**) | „brak czasu”, 4 HPS, 10–15 | Niebo niebieskie z chmurami, **bez różu**. Świeci 1 latarnia (ciepła). Na jezdni **plam nie widać**. Okna ~10/70 | EXIF ✗, latarnie ✗ |
| 088 (−8,9°) | „wyraźne PLAMY”, 5–6 okien | Ozdobne HPS, bruk oświetlony dość równo, łagodne plamy. Okna 0–2 | przesadzone |
| 089 (−3,7°, pochmurno) | plamy + halo, 5–6 okien | Latarnie świecą ✓ (włączone przy −3,7°). Mokra jezdnia; plam nie odróżnisz od odbić | plamy ✗ |
| 090 (−6,0°) | 8 HPS, plamy | Ozdobne HPS, mokry bruk, ciągłe pasmo światła wzdłuż pierzei, niebo granatowe | ✓ (bez „plam”) |
| 092 (−8,4°, śnieg) | 5 HPS, plamy | Ozdobne latarnie ciepłobiałe (nie typowo pomarańczowe), śnieg jasny dość równo | ✓ częściowo |
| 099 (−29,5°) | „ponad 20 opraw LED” | Girlandy żarówkowe nad straganami | ✗ (to nie oprawy) |
| 100 (−15,2°) | „1 latarnia LED (biała), plamy” | **W kadrze nie ma latarni**; świecą stropówki biura i witryna Rossmanna | ✗ |
| 103 (−3,3°) | 2 HPS świecą, plamy na jezdni | Wycinek 1920 px: **wysokie oprawy drogowe nie świecą**, świecą 2 niskie lampy przy budynku. Plam brak. Przy horyzoncie od strony Słońca, pod chmurami, **ciepły brzoskwiniowy pas** | ✗ (to dowód „włączone przy −3,2°” z README) |
| 104 (−6,9°) | plamy + słabe halo, 10–15 okien | Odbicia na mokrej jezdni; plam brak; okna 1–3 | zawyżone |
| 105 (−7,2°) | 8 HPS, plamy + halo, **20–30 okien** | Wycinek: zapalone okna pięter 0–1; reszta to iluminacja świąteczna | ✗ |
| 106 (−15,8°) | „12 latarni = 12 plam” + halo | **Gęsta mgła.** Halo to rozpraszanie we mgle, nie cecha oprawy; nawierzchnia oświetlona równo, plam nie widać (wycinek). Dwuramienne maszty, barwa sodowa | ✗ (dowód nr 1 w README) |
| 109 (EXIF 2013-09-11 07:28) | „by night”, „poza Białymstokiem” | **Dzień** (h0 ≈ +13°, o ile zegar aparatu był dobry). Pomarańczowe klosze ozdobne; to nie oprawa drogowa | ✗ |

**Wynik.** Obejrzano 24 kadry. 083 i 084 mają opis zgodny z obrazem, błędny jest tylko EXIF. Zgodnych lub prawie zgodnych jest 6: 073, 080, 081, 086, 090, 092 (080 i 081 zaniżone co do okien). 4 są przesadzone: 074, 075, 088, 104. 12 ma opis sprzeczny z obrazem (076, 077, 079, 085, 087, 089, 099, 100, 103, 105, 106, 109). Wniosek README „pod KAŻDĄ latarnią HPS jasna plama” opiera się na 106 (mgła) i 092 (śnieg), więc nie wynika z kadrów.

## 4. Dokumenty

- **bialystok.pl 28.07.2023:** 8 mln zł ✓, 4 650 opraw ✓, „Alei 1000-lecia PP”, „W. Wysockiego”, „tzw. trasie generalskiej”, „Wasilkowskiej”, „gen. Kleeberga” ✓, 19 mln 620 tys. zł do 2025 ✓. **Andersa i Maczka nie są wymienione**, a temperatury barwowej nie ma.
- **bialystok.pl 18.08.2026:** „ponad 6 900 opraw” w latach 2024–2025 ✓. Ciołkowskiego/Zaułek Podlaski 382 latarnie ✓, ~400 tys. zł ✓. Brak K, ściemniania i progu.
- **Klasy M/P (POLAB):** wartości zgodne z EN 13201-2:2015 (M1–M6, P1–P6) ✓. Lipnik (ME4b/ME5, h 9 m, moduł 46–48 m) to droga wiejska starej normy, **nie stosować do arterii trasy C**. Mistral pisze to w uwagach, ale w README §2 przywołuje Lipnik w wierszach ulic trasy jako „przykład urzędowy: 9”.

## 5. OSM (PBF 2026-11-08)

| Ulica | M60 | Recenzent (lampy ≤ 25 m od osi, odstęp do najbliższego sąsiada) |
|---|---|---|
| Andersa | ≈ 31,7 m (1 para) | 3 lampy: 31,7 / 31,7 / 154 m ✓ (n = 1 para) |
| Kombatantów | 31,2–33,4 m | 6 lamp: 31,3 / 32,3 / 32,6 / 32,6 m (+ 12,4 m, para naprzeciw) ✓ |
| Al. Tysiąclecia | ≈ 11,3 m (mediana) | 4 lampy: **38,9 / 38,9 / 39,0** + 339 m — **11,3 nie odtworzone** |
| Wysockiego | ≈ 16,1 m | 2 lampy: **48,3 m** — **nie odtworzone** |
| Maczka / Sokólska / rondo Putry | 0 / 1 / 0 | 0 / 0 / — ✓ (luka OSM) |

Pokrycie OSM na trasie jest bardzo słabe (n ≤ 6 na ulicę). Odtwarzalne wartości 31–39 m zgadzają się z regułą gry (najbliższy sąsiad p50 28,9 m, `standards.LAMP` 30–36 m). **Zmiany w grze nie są potrzebne.**

## 6. Porównanie z grą — konkretne kalibracje

| Element | Gra dziś | M60 + przegląd | Działanie |
|---|---|---|---|
| Ev przy −6° (`SkyModel.CivilTwilightEndLux`) | 3,4 lx, w komentarzu „UNVERIFIED: from memory” | AMS 3,5–2 lx (P17-002), Spitschan miasto 3,5 lx (P17-015) | **Wartość zostaje.** Komentarz zmienić na SOURCED (AMS + Spitschan 2016 miasto, mediana n=50). **Nie używać 60 lx z tabeli 1** |
| Ev przy −4° / −8° (`TwilightFactorAt`, log-liniowo 2,25 klx@0,5° → 3,4@−6°, ≈ 0,37×/°) | −4°: ≈ 25 lx; −8° (kres klampu): ≈ 0,46 lx | miasto 36,1 / 0,49 lx; Koomen 10×/2° | −8° ✓. −4° jest 30 % za ciemno. Opcjonalnie dodać węzeł −4° → 36 lx (dwa odcinki log-liniowe). WORKING_VALUE → ESTIMATED wg P17-013/017. Na preset dusk (−6°) nie wpływa |
| Luminancja zenitu −6° | z modelu nieba (dusk EV100 3,7) | ≈ 0,29 cd/m² (Schmude, przeliczenie ESTIMATED; zgodne rzędem z ~1–3 lx) | jako punkt kontrolny pomiaru LUT: zenit przy −6° ~0,3 cd/m² (±×3), dalej −10×/2°. Wymaga logu luminancji z `SkyModel` (nie sprawdzałem) |
| Pas koralowy horyzontu (ADR 0192 P2-1, otwarty) | koralowy pas y 450–480 na route_putry dusk | Kadry: −3,3° (103) ciepły **brzoskwiniowy** pas tylko od strony Słońca, pod chmurami; −3,8° (073), −4,3° (087), −5,7° (083) **bez różu**, horyzont szaroniebieski / lawendowo-niebieski. M60 nie dostarczył liczb horyzontu | przy −6° **0 koralu**. Od strony Słońca wąski (≤ ~5° nad horyzontem, ESTIMATED z 103) ciepły żółto-pomarańczowy pas, od strony przeciwnej szaroniebieski. Sprawdzić kandydata z ADR 0192 (`HorizonColorExposed` / far-field fog), bo LUT kopuły pas już zbija. Dowód: 083 i 087 jako referencje (BY-SA / CC BY, tylko porównanie) |
| Niebo pochmurne nocą / mgła | — | 079, 081 (2022, śnieg + chmury): niebo i śnieg **pomarańczowo-brązowe** (łuna HPS) | dla `overcast` nocą: niebo ciepłe, nie granatowe (stan 2022; po LED 2024–25 mniej pomarańczowe — UNVERIFIED) |
| Pule latarni (ADR 0191: RA 2,4 h, RS 1,5 h, I0 2500 cd, ogon) | min/szczyt 0,49 przy h9/S29 | Moje całkowanie śladu na pasie 0–7 m (ogon S 0,25 / R 1,5): Eavg 18,2 / 15,0 / 12,9 lx, Emin/Eavg 0,37 / 0,42 / 0,49 dla h/S = 9/29, 10/33, 11/36. Przy q0 = 0,07 (R3, **moje założenie**) L ≈ 1,3 / 1,05 / 0,9 cd/m², czyli **M2–M3** (P17-037/038: 1,5 / 1,0). Uwaga: Emin/Eavg z natężenia to nie Uo luminancji z normy | **I0 2500 cd zostaje.** Klasa ulic trasy jest UNVERIFIED, więc bez zmian. Gdyby dokumentacja dała M2 dla DK8/Andersa, I0 → ~2900 cd przy h 10/S 33. Przy h 9 / S 31,7 (Andersa OSM) Emin/Eavg spada do 0,27 — przy następnej regeneracji sprawdzić, czy reguła nie daje S > 3,3 h na arteriach |
| Widoczność pul o zmierzchu | dusk −6°: pule ~6:1 do tła (r5) | Fotometria: Ev nieba 3,5 lx vs Eavg pul 13–18 lx → **4–5:1**. Kadry: przy −3,3…−4,3° plam nie widać (087, 089, 073), przy −6…−7° umiarkowane (090), wyraźne dopiero przy ≥ −8° i na śniegu | pule przy −6° mają być widoczne, ale **łagodniejsze niż nocą**: kontrast ~4–5:1, nie ~6:1. Do oceny na telefonie (P1-5); toe 0,6 ewentualnie złagodzić. WORKING_VALUE |
| Podłoga nocna 1 lx (`NightFloorLux`, zasięg 45 m) | 1 lx do 45 m od wybranej oprawy, dalej 0 | 1 lx = Emin klasy P4 (P17-045); łuna miejska nocą 0,008–0,037 lx bezchmurnie, 0,038–0,23 lx w chmurach (P17-032, Krieg — niesprawdzone) | 1 lx w zasięgu ✓ (< Emin pul 4,5–6,8 lx). **Poza 45 m nie schodzić do 0**: resztka ~0,03 lx bezchmurnie / ~0,2 lx pochmurnie (łuna). WORKING_VALUE |
| Włączanie latarni (`StreetLamps.SetSunElevation`: 3°→1°) | latarnie pełne od +1° | 089 (−3,7°, pochmurno) i 073 (−3,8°) świecą; 103 (−3,3°): **oprawy drogowe jeszcze nie świecą**. Kraków: fotokomórka + zegar astronomiczny | sygnał (n = 3), że włączenie jest później niż +1°: ok. −2…−3,5°. Proponuję fade −2° → −3,5° (WORKING_VALUE). Dusk −6° bez zmian |
| Sód vs LED na trasie C | 0191: sód per materiał `*_sodium`, DK8 w świecie LED (UNVERIFIED) | M60: przetarg 2023 na Al. Tysiąclecia, Wysockiego i „trasę generalską” (bez nazw Andersa/Maczka i bez dowodu montażu); kadry HPS to deptak 2020–2023; 106 (arteria, 2023) sód | **dowodów nie wystarczy na zmianę**. Stan LED na DK8 nadal UNVERIFIED. Kadrów nie traktować jako dowodu „dominuje sód na trasie”. Barwa LED (K) — brak źródła; `k_Led` (1, 0,93, 0,82) zostaje |
| Okna — udział mieszkań (`NightWindows.BaseShares` x: 0,40 przy −6° → 0,50 przy −16°; ×0,75 w mieszkaniu + 0,06 pojedyncze → ≈ 0,33–0,43 okien) | WORKING_VALUE | Moje liczenie (ESTIMATED, ±50 % względnie, n = 7 kadrów bloków): 087 (−4,3°) ~14 %, 083 (−5,7°) ~18 %, 084 (−6,5°, długi czas) ~24 %, 079 (−12°) ~19 %, 080 (−14°) ~15 %, 081 (−19°) ~23 %, 086 ~14 %. **Wszystkie 14–24 %, żaden ≥ 30 %.** Nachtlichter: okna gasną w ciągu nocy | obniżyć mieszkania do **0,25 (−6°) → 0,28 (−16°)** zamiast 0,40 → 0,50, co daje ok. 0,19–0,27 na okno. Bez wzrostu późnym wieczorem. WORKING_VALUE z tym przeglądem jako ESTIMATED; po M60-FIX zastąpić liczbami z ≥ 15 kadrów |
| Okna — klatki (w: 0,35) | 0,35 | 080: pion klatki 4/5 zapalonych (n = 1) | sygnał wyżej (0,6–0,8), n = 1 — do M60-FIX, bez zmiany teraz |
| Okna — biura (y: 0,65 → 0,15) | 0,65 o zmierzchu | 085 (HDR, profesjonalne, h0 nieznane) ~1/3 pięter | bez zmian (n = 1, kadr nieneutralny) |
| Okna — barwa (2700/3200/4000/4500 K) | — | w kadrach dominują ciepłe 2700–3000 K, pojedyncze niebieskie (TV); Nachtlichter 39 % okien „pomarańczowych” (niesprawdzone) | ✓ zakres; ewentualnie dodać rzadki (≤ 3 %) chłodny migający ekran. Bez zmian |
| Okna — luminancja 15 cd/m² | WORKING_VALUE | M60 nic nie dostarcza (piksele RGB słusznie nie liczone jako luminancja) | bez zmian, luka |

## 7. Licencje, samokontrola, pliki

- **Licencje** sprawdzone na Commons API dla 37/37 ✓ (zgodne z manifestem). BY-SA jako referencja ✓. Google nie ma.
- **Duplikaty:** 0 (md5 37 plików ZIP-a, sha1 Commons 37 unikalnych).
- **Rozmiar:** 36/37 plików > 1600 px (1920 px).
- **Samokontrola:** seed odtwarzalny ✓, ale merytorycznie sprawdzono tylko żywotność URL. Ponownego obejrzenia nie było.

## 8. Dla lidera

- **Nie scalać** w obecnej postaci. Blok poprawek: `docs/owner/MISTRAL-FIXES-12.md` § M60-FIX.
- **Do gry od razu, bez czekania na FIX:**
  1. `CivilTwilightEndLux` 3,4 — tylko komentarz → SOURCED.
  2. **Nie przenosić do gry tabeli 1 „wieś” ani CCT 11–20 kK.**
  3. Pas koralowy przy −6° — cel to 0 koralu, ciepły wąski pas tylko od strony Słońca (083/087/103 jako porównanie).
  4. Udział okien mieszkań 0,40 → 0,50 jest za wysoki wobec 7 kadrów (14–24 %): kandydat 0,25 → 0,28.
  5. Podłoga nocna poza 45 m: resztka łuny ~0,03 / 0,2 lx zamiast 0.
  6. Włączanie latarni: kandydat −2° → −3,5°.

  Każdą zmianę wykonać z renderem `visual-qa` (dusk/night) i pomiarem na telefonie. I0 2500 cd i ślad 0191 są zgodne z klasą M2–M3, bez zmian.
- **Pliki recenzenta (tymczasowe, scratch sesji):**
  - `C:\Users\matma\AppData\Local\Temp\claude\65a86252f72ba2de\44810253-4f54-463a-b591-9868ed7d4a4f\scratchpad\m60\v\P17-*.jpg` (≤ 960 px);
  - `…\m60\k77.jpg`, `k103.jpg`, `k105.jpg`, `k106.jpg`, `c73.jpg` (wycinki);
  - `…\m60\meta.json` (metadane Commons);
  - `…\m60\chk.py` (h0).
