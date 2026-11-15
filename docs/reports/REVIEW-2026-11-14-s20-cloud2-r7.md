# Przegląd R7 sky-weather-bialystok (chmura #2, PR #60) — s20, 2026-11-14

**Werdykt: SCAL z erratą.** Dane klimatyczne i słoneczne są rzetelne. Sprawdziłem u źródła 12 liczb i wszystkie się zgadzają. Opisy 11 obejrzanych kadrów są zgodne z obrazem, z jednym wyjątkiem (c21, §2). Teza „pod pełnym zachmurzeniem nie ma ciepłego pasa” jest dobrze udokumentowana, ale **nie dotyczy błędu w grze**: koralowy pas pojawia się w `LP_Dusk` (`overcast: 0.2`), a nie przy pełnym zachmurzeniu. **Hipotezę przyczyny (`HorizonColorExposed` → kolor mgły) obalają rendery**: pas jest kierunkowy, a kolor mgły jest jeden dla wszystkich kierunków (§3). Hipoteza ma w pakiecie status WORKING_VALUE („niesprawdzona”), dlatego nie blokuje scalenia. README §„Koralowy pas” p. 4 i opis PR trzeba jednak poprawić (errata E1), żeby nie skierowały poprawki w złe miejsce.

- Gałąź `origin/research/cloud2-sky-weather-bialystok` @ `c53e2549a`. `git diff --shortstat origin/main...`: 24 pliki, +5195, wszystkie w `research/cloud2/sky-weather-bialystok/` ✓.
- Manifest: 628 wierszy, id unikalne. Nic nie scalono, nic nie scommitowano, PR bez komentarza. Raport nie jest scommitowany.
- Pakiet nie ma wewnętrznej recenzji (`REVIEW.md`), choć wymaga jej CLOUD2-PROMPT. Ten przegląd ją zastępuje.

## 1. Kompletność wg CLOUD2-PROMPT (R7)

| Wymóg | Wynik | Dowód |
|---|---|---|
| Zachmurzenie i usłonecznienie per miesiąc (IMGW) | **TAK** | Tabela miesięczna i normy 1991–2020. Zachmurzenie i dni pochmurne zgadzają się z klimat.imgw.pl (§4) |
| Wysokość słońca w kluczowych porach | **TAK** | `out/sun_table.csv`, 12 dat. Niezależnie przeliczyłem 8 wartości (§4) |
| Typowe niebo pochmurne: opis + zdjęcia CC | **TAK** | 15 kadrów N = 8 (CC0, Rakoon) z parowaniem do terminu stacji |
| Mgła/zamglenie | **TAK** | Dni z mgłą, widzialność p10/mediana per miesiąc, przelicznik MOR → parametr gry |
| Liczby do profilu nieba/mgły + odniesienie do ADR 0192 | **TAK z błędem** | Tabela rekomendacji jest dobra. Hipoteza przyczyny jest błędna (§3) |
| manifest/sources/README/audit/fetch.py | **TAK z błędem** | 3 z 35 kadrów nie pobierają się (zły host Panoramax, E3) |
| Samokontrola 20 %, jawny seed | **TAK** | `Random(20261114).sample(sorted(ids), 126)` daje ten sam zbiór ✓. Niespójne liczby w JSON (E5) |
| Licencje, zakaz Google | **TAK** | CC0 ×26, CC BY-SA ×9 (z dopiskiem „referencja, nie tekstura”), IMGW z wymaganą formułą źródła. Nie ma Google/Bing/Apple/Yandex. UA ogólny (`research-fetch/1.0`) ✓ |
| Tylko własny katalog | **TAK** | diff jak wyżej |

## 2. Co obejrzałem sam (11 zdjęć + 2 wycinki 3× + 3 rendery gry)

Pobrałem zdjęcia przez `fetch.py --only img`: 32 z 35 OK, sha256 zgodne. Trzy brakujące pobrałem z poprawionych URL-i (E3), sha256 też zgodne. Oglądałem każde zdjęcie osobno, ≤ 960 px.
- **c04, c07, c25** (N = 8, słońce 1–4°): niebo jednolicie białe lub niebieskoszare, bez ciepłej barwy ✓. Na c07 wiadukt przy rondzie Bieżeństwa z czerwonym gzymsem ✓.
- **c13** (−4,5°, N = 8): granat z fioletowym odcieniem ✓. **c14** (−3,7°): bladoniebieskoszare ✓. **c31** (+3,7°, N = 7): jasnoszare, przy dole ledwie widoczny różowokremowy odcień ✓.
- **c16** (+0,9°, N = 6): kremowa i brzoskwiniowa poświata nisko za chmurami ✓.
- **c32** (−3,2°, N = 2, lato): od góry kremowe, niżej łososiowe, przy horyzoncie szarofioletowe ✓. Zmierzyłem najniższy pas nieba: sRGB ≈ (247–254, 219–232, 222–230), **nasycenie ≈ 10 %**. Opis „kolory podbite obróbką” jest trafny, więc to górna granica nasycenia.
- **c22 / c23** (−7,1°, N = 0): kobalt / granat ✓. Kierunek obu kadrów jest UNVERIFIED, a c22 pokazuje tylko wąski wycinek nieba. Te kadry **nie dowodzą**, że w sektorze słońca przy −7° nie ma poświaty (E6).
- **c21** (−1,5°, N = 1), wycinek 3× nisko nad dachami po prawej: piksele (183–189, 199–205, 224–230), czyli R < G < B. Pas jest bladoniebieski z co najwyżej lawendowym odcieniem. **„Pastelowy różowo-liliowy pas” nie zgadza się z obrazem** (E2). Ma to znaczenie, bo README §2 używa c21 jako dowodu ciepłego pasa przy pogodnym zmierzchu.
- **Rendery gry** (`artifacts/night-int-0191-0192/final/High-dusk/`): `route-putry-approach`, `driver-andersa-to-putry`, `chase` + wycinek 3× pasa (§3).

## 3. Kod: `SkyModel.HorizonColorExposed()` — opis potwierdzony, przyczyna obalona

**Opis R7 jest zgodny z kodem:**
- `SkyModel.cs:251–261` uśrednia `Radiance()` z 32 azymutów w kierunku (sin a, 0,05, cos a), czyli przy wysokości 2,86°.
- `EnvironmentLighting.cs:136–137` przypisuje wynik do `fog` i `m_FogExposed`, a ten kolor trafia do:
  - `_SkyFogColor` (dla shadera nieba: niebo poniżej horyzontu `Sky.shader:211` i podstawa chmur `:198`);
  - `RenderSettings.fogColor` (`:178`);
  - `WorldAtmosphere.Push` (`:66`, `:185`);
  - horyzontu kostki odbić (`SkyModel.cs:394`).

**Pełne zachmurzenie (teza R7 o N = 8):** `LP_Overcast` ma `overcast: 1`.
- Wtedy `Radiance()` pomija gałąź chroma (`if (Overcast < 1f)`) i zwraca `AdaptedWhite · L` dla każdego azymutu, a `BuildChroma/ApplyTwilightChroma` w ogóle się nie wykonują (`:155`).
- Uśrednianie nie może więc dodać ciepła. Teza R7 jest zgodna z grą, ale nie dotyczy błędu. Rekomendacja „dla `LP_Overcast` zero składowej ciepłej” jest już spełniona i nic nie zmienia.
- Błąd jest w `LP_Dusk`: słońce −6°, azymut 300°, `overcast: 0.2`, `whiteBalanceAdaptation: 0`.

**Przyczyna (hipoteza R7) — obalona przez rendery:**
- Kolor mgły to jedna stała na preset, taka sama we wszystkich kierunkach. Gdyby to on tworzył pas, najniższe niebo i daleki plan byłyby koralowe w każdej kamerze o zmierzchu.
- Pomiar (sRGB, wiersze pełnej klatki 2340×1080):
  - `route-putry-approach`, y = 455–470: koral tylko w x ≈ 900–1300 (174,123,122), (189,119,113). Na tej samej wysokości y przy x ≈ 1500 jest (100,100,114), a przy x ≈ 2100 (63,79,117). Ta sama wysokość y oznacza ten sam kąt nad horyzontem (kamera bez przechyłu), a barwa jest różna. To nie jest jeden kolor mgły.
  - `driver-andersa-to-putry`, y = 440–480: koral (216,131,123), (194,109,93) w jednej kolumnie x ≈ 1060, obok granat. Na miniaturze to wąska łuna w osi drogi, w stronę słońca.
  - `chase`, `kwadrat-park-gate`, `trailer-34` (inne kierunki): przy horyzoncie (42–60, 63–80, 97–120), czyli błękit. Nie ma koralu.
- **Wniosek pewny:** pas jest kierunkowy, więc **nie pochodzi z koloru mgły**.
- **Wniosek prawdopodobny (WORKING_VALUE recenzenta, z pikseli po tonemappingu, bez uruchomienia modelu):** pas to łuna w sektorze słońca w LUT kopuły (`ChromaAt`).
  - `ApplyTwilightChroma` (`SkyModel.cs:707–734`) celowo zostawia ciepły kolor zachodu (LUT liczony dla słońca w kształcie +0,5°) w obszarze `glow`: γ < 15–75°, v < 0,15–0,6. Niebieski cel zmierzchu dostaje tylko (1 − glow), a w niskim pasie B jest obniżane tylko o 15 %.
  - Próba z ADR 0192 („0 zmian”) dotyczyła `SuppressTwilightMagenta`. Funkcja wychodzi wcześnie, gdy `min(R,B) − G ≤ 0`. Na ekranie kolor (179,127,127) ma G = B, a (189,119,113) ma B < G. Jeśli w liniowym LUT jest podobnie, funkcja nie dotyka tej łuny, co tłumaczyłoby brak zmian. Wartości w LUT nie odczytałem, a samej próby nie widziałem (została cofnięta).
- `HorizonColorExposed` może dodatkowo lekko ocieplać daleki plan przy 20 % udziału pogodnego nieba. Pasa jednak nie tworzy. Tego nie mierzyłem: nie odczytałem wartości `fog` dla `LP_Dusk`, bo testu nie uruchamiałem (zakaz Unity w recenzji).

**Co R7 daje dla poprawki P2-1 (status: wniosek recenzenta, WORKING_VALUE):**
- Łuna przy pogodnym zmierzchu istnieje naprawdę (c32, c16), więc sama łuna nie jest błędem.
- Jakościowo łuna w grze jest **wyraźnie bardziej nasycona i „koralowa”** niż pastelowe pasy na zdjęciach:
  - gra: nasycenie sRGB 29–52 %;
  - c32: ≈ 10 %, ale jasność 247–254, czyli przy granicy przepalenia, a przepalenie zaniża nasycenie. Liczba nie jest więc progiem docelowym.
- Na żadnym kadrze R7 nie widać sektora słońca przy −6° (E6). Dlatego nie podaję docelowej wartości ani krzywej wygaszania.
- Kierunek zmian: osłabić lub odbarwić `glow` w `ApplyTwilightChroma` dla głębszego słońca i ocenić na `route-putry-approach` i `driver-andersa-to-putry`.
- **Rozstrzyga zdjęcie właściciela** (koniec zmierzchu cywilnego, w stronę słońca, N ≤ 2) — §7.

## 4. Liczby zweryfikowane u źródła (12)

| # | Liczba R7 | Źródło / metoda recenzenta | Wynik |
|---|---|---|---|
| 1 | Zachmurzenie 1991–2020: 6,5/6,2/5,3/4,6/4,4/4,6/4,4/4,1/4,5/5,2/6,5/6,6, rok 5,2 | klimat.imgw.pl `ZACHM`, wiersz BIAŁYSTOK 12295 | ✓ identyczne |
| 2 | Usłonecznienie rok 1755,3 h | `USL` | ✓ (miesiące w tabeli README: E4) |
| 3 | Dni pochmurne 135,7 (I 20,4; XII 20,4; VIII 4,1) | `D_POCHMURNE` | ✓ |
| 4 | 21 XII: słońce w południe 13,5°, zachód 15:12 az. 230°, koniec zm. cyw. 15:54 az. 238° | własny algorytm słoneczny (niezależny od NOAA/astral) | ✓ 13,44° geom. (+refrakcja); 15:12 / 230°; 15:55 / 238° |
| 5 | 21 VI: 60,3° | jw. | ✓ 60,31° |
| 6 | 21 XI 8:00: 6,0°/135°; 21 I 16:00: −2,0°/239°; 21 IV 20:00: −3,8°/296° | jw. | ✓ 5,9/135; −2,0/239; −3,8/296 |
| 7 | XI–I koniec zm. cyw. az. 238–245° | jw. | ✓ 238 / 244 / 245 |
| 8 | c07: 2020-11-02 14 UTC N = 8, wid. 3900 m | surowy `s_t_295_2020.csv` (NOG, WIDO) | ✓ (HPON 210 m) |
| 9 | c13: 2020-11-06 15 UTC N = 8, wid. 9000 m | jw. | ✓ |
| 10 | c01: 2020-11-10 07 UTC N = 0, wid. 130 m; c03: 11-21 08 UTC N = 8, 480 m; c16: 11-19 14 UTC N = 6, 23 370 m | jw. | ✓ wszystkie |
| 11 | Cytat „overcasts make daylight bluer” (Lee & Hernández-Andrés 2005) | OpenAlex, doi:10.1364/AO.44.005712 | ✓ dosłownie w abstrakcie |
| 12 | σ = 2,996/V (MOR, 5 %) vs 3,912/V (2 %) → V_gry = 1,306·V_IMGW | ln 20 / ln 50 | ✓ |

Dodatkowo sprawdziłem surowe dane terminowe XI–II w dzień z lat 2014–2023 (12 020 terminów):
- wśród terminów z N ≤ 2 tylko 8 z 868 ma widzialność < 1 km (mgła zapisana jako N = 0);
- wśród 430 terminów z widzialnością < 1 km kod N = 9 (niebo niewidoczne) wystąpił 31 razy.

`tools_imgw.py` (l. ~276–284) zalicza N = 9 do `nog78` (warunek `nog >= 7`). Do średnich zachmurzenia bierze tylko N ≤ 8. Udziały N w tabeli nie są więc istotnie zafałszowane przez mgłę ✓.

## 5. Co R7 daje grze (pliki, liczby)

| Element gry | Dziś | Wg R7 | Działanie |
|---|---|---|---|
| Koralowy pas `LP_Dusk` (ADR 0192 P2-1) | pas kierunkowy w sektorze słońca, nasycenie 29–52 % (prawdopodobnie `glow` w LUT) | łuna przy pogodnym zmierzchu istnieje, ale jest pastelowa (c32, c16) | rendering-perf: `ApplyTwilightChroma`, osłabić lub odbarwić `glow` dla głębszego słońca; cel ustalić ze zdjęcia właściciela. **Nie** traktować `HorizonColorExposed` jako przyczyny (§3) |
| `LP_Dusk` azymut 300° | IV/VIII | XI–I: 238–245° (koniec zm. cyw.) | jeśli preset ma być „typowym zimowym zmierzchem”: azymut 240°, a `overcast` ≥ 0,8 (N ≥ 7 w 79–82 % wieczorów XI–I). Decyzja właściciela (sezon gry) |
| `LP_Clear` `visibilityKm: 20` (słońce 42° = IV/IX) | MOR ≈ 15,3 km | mediana IV 31,8 km, IX 30,8 km (MOR) → parametr gry ≈ 40 km | WORKING_VALUE: 20 → ~40 km albo opisać 20 km jako „zamglony dzień” |
| `LP_Overcast` `visibilityKm: 8`, słońce 41° | MOR ≈ 6,1 km | lato pochmurne 31,4 km (→ 41 km gry), zima pochmurna 7,4 km (→ 9,7 km gry) | spójność: słońce 41° to wiosna/lato, a 8 km to zimowa mgiełka. Wybrać sezon presetu |
| Mgiełka ADR 0080 (≈ 2,4 km) | stała | 11,6 % terminów XI–II, 0,2 % V–VIII | tylko jako stan zimowy |

Przeliczenia widzialności zakładają gęstość mgły = 3,912 / V. W kodzie jest jeszcze mnożnik `fogDensityScale` (`EnvironmentLighting.cs`), którego wartości w scenach nie sprawdzałem.

## 6. Errata (blok do wklejenia autorowi; nie blokuje scalenia)

```
R7 sky-weather-bialystok — errata po przeglądzie lidera (REVIEW-2026-11-14-s20-cloud2-r7.md)
E1 (P1) README §„Koralowy pas” p. 4 i opis PR #60: hipoteza „HorizonColorExposed → kolor mgły” jest
   obalona renderami (artifacts/night-int-0191-0192/final/High-dusk: route-putry-approach y 455–470 koral
   tylko x 900–1300, przy x 1500 (100,100,114); driver-andersa-to-putry koral tylko w osi; chase/kwadrat/
   trailer-34 błękit). Kolor mgły jest jeden dla wszystkich kierunków, a pas jest kierunkowy.
   Przepisz p. 4: „HorizonColorExposed nie tworzy pasa (rendery). Prawdopodobna przyczyna (WORKING_VALUE
   recenzenta, niesprawdzona w Unity): obszar glow w LUT kopuły (ApplyTwilightChroma), łuna bardziej
   nasycona niż na zdjęciach pogodnego zmierzchu”. Usuń „dla LP_Overcast zero składowej ciepłej” (przy
   overcast = 1 model i tak nie ma chroma — SkyModel.cs:155, 233–237).
E2 (P2) R7-572 (c21): „pastelowy różowo-liliowy pas” → „bladoniebieskie, nisko lekko lawendowe;
   R < G < B (≈ 185,202,227)”; pas_ciepły = „nie / bardzo słaby lawendowy”. Popraw README §2
   (c21 nie jest dowodem ciepłego pasa).
E3 (P2) url_pliku R7-552, R7-553, R7-555: host panoramax.openstreetmap.fr/derivates → 404.
   Poprawne (sha256 zgodne):
   https://panoramax.mapcomplete.org/derivatives/96/6a/c3/e0/2731-4033-bf9a-67aa21ada5c6/sd.jpg
   https://panoramax.mapcomplete.org/derivatives/cb/cb/62/c5/9ef0-46a2-8ec7-4979ed543543/sd.jpg
   https://panoramax.mapcomplete.org/derivatives/c1/a5/e4/0e/4a83-4807-a13b-30d39b9bceab/sd.jpg
E4 (P2) README tabela, kolumna usłonecznienie: wartości własne odbiegają od norm oficjalnych (USL) o
   1,6–4,8 h (III 120,5 vs 122,1; IV 183,4 vs 185,7; VII 261,7 vs 256,9; IX 160,4 vs 161,8). Wpisz normy
   oficjalne (SOURCED) albo usuń słowo „zgodne”.
E5 (P2) audit_20_percent.json: „kadry_w_probie_obejrzane_ponownie: 8” vs README „13”; „wszystkie 3 FAIL”
   vs n_FAIL = 2. Ujednolić.
E6 (P2) README §2 p. 1–2 „nigdy” i c22/c23 „przy −7° w kadrze sam błękit”: kierunki Commons są
   UNVERIFIED, c22 pokazuje wąski wycinek nieba. Dopisz: „nie wiadomo, czy kadr obejmuje sektor słońca”.
   „Nigdy” → „w 15/15 kadrach zimowych N = 8 (kierunki niezweryfikowane) i wg Lee 2005”.
```

## 7. Uwagi procesowe
- Brak `REVIEW.md` w katalogu pakietu (wymóg CLOUD2-PROMPT). Ten przegląd go zastępuje.
- `audit.py` wymaga `astral` i `rdata`. Nie uruchamiałem go; słońce sprawdziłem własnym kodem (§4).
- Do pracy przy zmierzchu w grze przydałoby się zdjęcie właściciela o końcu zmierzchu cywilnego w stronę słońca przy N ≤ 2, zimą. Z otwartych źródeł takiego kadru nie ma.
