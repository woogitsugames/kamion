# R7 sky-weather-bialystok — klimat światła Białegostoku: niebo, słońce, mgła

Data: 2026-11-14 · gałąź `research/cloud2-sky-weather-bialystok` · wierszy manifestu: **628** (SOURCED 67, ESTIMATED 556, WORKING_VALUE 5) ·
obejrzanych kadrów: **35** w manifeście (41 pobranych i obejrzanych w 960 px, 6 odrzuconych: wnętrza/plakat) + 56 kandydatów Panoramax na stykówce ·
samokontrola: **126 wierszy (20,1 %), seed 20261114: 124 PASS / 2 FAIL (oba skorygowane)**; przebieg 1: 118/8 — wykrył błąd narzędzia (niżej) ·
pliki do pobrania przez `fetch.py`: 84 pliki, **16,98 MB** (sha256 zweryfikowane, exit 0).

Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy.
Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały przetworzone.

## Cel i metoda
Liczby do profilu nieba, słońca i mgły oraz dane do błędu „koralowy pas horyzontu” (ADR 0192, Otwarte P2-1).
1. **IMGW** (`tools_imgw.py`): dane miesięczne synop 1991–2023 i terminowe (co 1 h) 2014–2023 stacji BIAŁYSTOK (353230295 / 12295);
   normy oficjalne 1991–2020 z klimat.imgw.pl (`tools_normy.py`); zachmurzenie w porze zachodu/zmierzchu (`tools_twilight.py`).
2. **Słońce** (`tools_sun.py`): własna implementacja algorytmu NOAA Solar Calculator (wzory w nagłówku pliku), kontrola pakietem astral 3.2 (≤ 1 min, ≤ 0,1°).
3. **Zdjęcia**: Commons (seria CC0 z datą i godziną w nazwie, autor Rakoon) i Panoramax (CC BY-SA 4.0, azymut z API). Każdy kadr sparowany
   z wysokością słońca (NOAA) i **obserwacją stacji z najbliższego terminu** (N, widzialność, kod pogody, chmury) — kolumny `imgw_*` manifestu.
4. **Literatura**: WMO CIMO Guide rozdz. 9 (MOR), CIE general sky (tabela 15 typów z otwartego pakietu rcaiman), abstrakty prac Lee/Hernández-Andrés/Hulburt (DOI).

## Tabela miesięczna (stacja BIAŁYSTOK)
Zachmurzenie, usłonecznienie, mgła, śnieg, wilgotność: średnie 1991–2020 przeliczone z CSV (ESTIMATED; zgodne z normami oficjalnymi IMGW — SOURCED, R7-001…007).
Widzialność i udziały N: terminy dzienne 06–15 UTC z lat 2014–2023 (ESTIMATED).

| mies. | zachm. [okt] | usłon. [h] | usłon. [h/dobę] | dni z mgłą | dni z zamgl. | dni z pokr. śn. | wilg. [%] | wid. mediana [km] | wid. p10 [km] | wid. < 1 km [% term.] | N = 8 [%] | N ≥ 7 [%] | N ≤ 2 [%] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I | 6,45 | 38,2 | 1,23 | 5,7 | 24,5 | 19,6 | 88 | 8,4 | 2,1 | 3,7 | 59,8 | 79,4 | 6,5 |
| II | 6,15 | 57,2 | 2,02 | 4,5 | 22,9 | 17,8 | 85 | 12,6 | 2,6 | 3,0 | 48,3 | 69,4 | 11,5 |
| III | 5,25 | 120,5 | 3,89 | 4,2 | 22,2 | 10,0 | 78 | 22,4 | 6,0 | 0,8 | 32,2 | 53,9 | 18,3 |
| IV | 4,59 | 183,4 | 6,11 | 2,4 | 17,5 | 1,3 | 70 | 31,8 | 13,2 | 0,1 | 21,9 | 42,5 | 19,9 |
| V | 4,40 | 254,8 | 8,22 | 1,7 | 13,6 | 0 | 71 | 33,6 | 20,3 | 0,0 | 16,3 | 34,0 | 20,2 |
| VI | 4,55 | 259,3 | 8,64 | 1,1 | 12,5 | 0 | 73 | 34,2 | 22,3 | 0,0 | 12,5 | 29,6 | 21,6 |
| VII | 4,42 | 261,7 | 8,44 | 1,6 | 14,3 | 0 | 75 | 33,8 | 17,7 | 0,1 | 13,1 | 30,1 | 13,4 |
| VIII | 4,06 | 251,4 | 8,11 | 2,2 | 18,4 | 0 | 77 | 33,2 | 16,3 | 0,0 | 13,2 | 28,1 | 22,9 |
| IX | 4,54 | 160,4 | 5,34 | 3,8 | 21,9 | 0 | 82 | 30,8 | 11,0 | 0,3 | 19,2 | 37,5 | 22,9 |
| X | 5,22 | 101,2 | 3,26 | 6,6 | 24,3 | 0,6 | 86 | 20,4 | 4,4 | 1,7 | 34,9 | 55,5 | 16,4 |
| XI | 6,50 | 38,4 | 1,28 | 8,1 | 25,3 | 5,0 | 90 | 8,9 | 2,2 | 3,0 | 62,2 | 82,1 | 5,2 |
| XII | 6,56 | 28,9 | 0,93 | 6,1 | 26,3 | 14,4 | 90 | 8,3 | 1,7 | 4,5 | 64,5 | 81,0 | 5,9 |
| rok | 5,22 | 1755 | — | 48,2 | 243,9 | 68,8 | 80,5 | 26,9 | 4,0 | 1,4 | 33,1 | 51,8 | 15,4 |

Normy oficjalne IMGW 1991–2020 (SOURCED): zachmurzenie 6,5/6,2/5,3/4,6/4,4/4,6/4,4/4,1/4,5/5,2/6,5/6,6 (rok 5,2); usłonecznienie rok 1755,3 h;
dni pochmurnych 135,7/rok (I 20,4; XII 20,4; VIII 4,1), dni pogodnych 33,1/rok; temp. 7,7 °C; opad 610,2 mm; dni z pokrywą śnieżną 68,7.
Mediana widzialności w dzień przy N ≥ 7: zima (XI–II) 7,4 km, lato (V–VIII) 31,4 km; przy N ≤ 2: 17,4 / 32,9 km. Przy N = 8 dominują Sc (CL=5, 41 %) i St neb (CL=6, 32 %; zimą 42 %),
mediana podstawy chmur 240 m (zima 200 m, lato 570 m). Pełne tabele: `out/`.

## Tabela słońca (53,13 N, 23,16 E; rok 2026; ESTIMATED — obliczone NOAA; czas lokalny CET/CEST)
wys./az. = wysokość pozorna i azymut geograficzny [°]; pod horyzontem wysokość geometryczna.

| data | 8:00 | 12:00 | 16:00 | 20:00 | wschód | zachód (az.) | koniec zm. cyw. (az.) | koniec zm. żegl. | wys. w poł. | dzień [h] | min/dobę słońce 0–10° |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 21 I | 3,3/130 | 16,9/185 | −2,0/239 | −36,7/287 | 07:27 | 15:51 (237) | 16:30 (245) | 17:13 | 17,1 | 8,39 | 194 |
| 21 II | 11,0/125 | 26,3/185 | 6,3/244 | −28,7/293 | 06:33 | 16:50 (254) | 17:26 (261) | 18:06 | 26,4 | 10,29 | 154 |
| 21 III | 21,1/120 | 37,0/188 | 14,3/251 | −20,5/301 | 05:28 | 17:42 (272) | 18:17 (279) | 18:58 | 37,2 | 12,24 | 140 |
| 21 IV | 23,5/102 | 48,5/170 | 31,1/247 | −3,8/296 | 05:15 | 19:38 (292) | 20:16 (299) | 21:05 | 48,8 | 14,38 | 145 |
| 21 V | 30,4/97 | 56,8/170 | 37,5/253 | 3,0/301 | 04:20 | 20:29 (307) | 21:15 (316) | 22:23 | 57,1 | 16,15 | 159 |
| 21 VI | 32,1/93 | 59,8/167 | 40,7/254 | 6,2/302 | 04:00 | 20:58 (313) | 21:50 (324) | 23:21 | 60,3 | 16,96 | 170 |
| 21 VII | 29,1/94 | 56,7/166 | 39,0/251 | 4,3/299 | 04:27 | 20:39 (307) | 21:25 (316) | 22:33 | 57,3 | 16,20 | 160 |
| 21 VIII | 23,0/101 | 48,5/169 | 31,7/246 | −3,3/295 | 05:18 | 19:42 (291) | 20:20 (299) | 21:08 | 48,9 | 14,40 | 146 |
| 21 IX | 15,2/110 | 37,3/174 | 20,7/241 | −14,2/291 | 06:11 | 18:29 (272) | 19:03 (279) | 19:44 | 37,5 | 12,29 | 141 |
| 21 X | 7,0/118 | 26,1/177 | 9,9/237 | −24,8/286 | 07:05 | 17:19 (253) | 17:54 (260) | 18:34 | 26,1 | 10,23 | 154 |
| 21 XI | 6,0/135 | 16,3/192 | −5,5/244 | −40,5/293 | 07:02 | 15:24 (237) | 16:03 (244) | 16:46 | 17,0 | 8,36 | 194 |
| 21 XII | 1,8/134 | 13,1/188 | −6,8/239 | −41,4/287 | 07:39 | 15:12 (230) | 15:54 (238) | 16:39 | 13,5 | 7,54 | 232 |

V–VII: brak nocy astronomicznej (min. wysokość −13,4° 21 VI). Presety gry: `LP_Clear` (42°, az. 200°) = 6–7 IV lub 4–6 IX ok. 13:27 CEST;
`LP_Dusk` (−6°, az. 300°) = 21 IV / 21 VIII; w XI–I koniec zmierzchu cywilnego ma azymut 238–245°.

## „Koralowy pas horyzontu” — co mówią dane i zdjęcia
1. **Pod zachmurzeniem całkowitym nie ma ciepłego pasa — nigdy.** 15 kadrów z N = 8 wg stacji + 2 kadry Panoramax z XI 2026: 0 z ciepłą barwą nieba,
   także przy słońcu 1–4° nad horyzontem (c07 — wiadukt przy rondzie Bieżeństwa, c08, c09, c25) i o zmierzchu (c04, c13, c14, c30: niebo jednolicie
   niebieskoszare → granatowe; ciepło tylko od latarni). Literatura: „overcasts make daylight bluer” (Lee & Hernández-Andrés 2005, doi:10.1364/AO.44.005712).
2. **Ciepły pas istnieje tylko przy niskim słońcu i przejaśnieniach, w sektorze słońca, i jest pastelowy**: c16 (słońce 0,9°, N = 6: wąski brzoskwiniowy pas
   nad dachami), c32 (lato, słońce −3,2°, N = 2: łososiowo-brzoskwiniowy pas, a **przy samym horyzoncie szarofioletowa warstwa zamglenia**), c21 (słońce −1,5°,
   N = 1: pastelowy różowo-liliowy pas). Przy N = 7 (c17, c31) tylko ledwo widoczny kremowy odcień. Przy słońcu −7° i N = 0 (c22, c23) w kadrze już sam błękit/granat.
3. **Jak często**: przy końcu zmierzchu cywilnego N ≥ 7 w 79–82 % wieczorów XI–I (N ≤ 2: 7–9 %); latem (VI–VIII) N ≤ 2 w 29–38 %, N ≥ 7 w 24–32 %.
   Zimowy zmierzch w Białymstoku to w 4 przypadkach na 5 jednolity niebieskoszary bez barw.
4. **Hipoteza przyczyny w grze (WORKING_VALUE, niesprawdzona renderem):** `SkyModel.HorizonColorExposed()` (SkyModel.cs:251–261) uśrednia radiancję nieba z 32 azymutów
   na wys. ok. 2,9° i ta jedna barwa jest kolorem mgły (EnvironmentLighting.cs:136) — o zmierzchu ciepły sektor słońca barwi więc zamglony daleki plan we wszystkich
   kierunkach. Na zdjęciach warstwa przy horyzoncie jest szarofioletowa/niebieskoszara, a ciepło leży NAD nią i tylko po stronie słońca. Propozycja: barwę mgły
   o zmierzchu liczyć bez sektora słońca (np. ±60°) albo kierunkowo; dla `LP_Overcast` i zmierzchu pochmurnego — zero składowej ciepłej.

## Rekomendacje dla profilu nieba i mgły (status jawny)
| parametr | wartość | status |
|---|---|---|
| σ mgły, pogodny dzień letni (V = 32,9 km) | 9,1·10⁻⁵ 1/m (barwa horyzontu: 4,5 % na 500 m) | ESTIMATED (σ = 2,996/V, WMO MOR) |
| σ, pochmurny dzień letni (V = 31,4 km) | 9,5·10⁻⁵ 1/m (4,7 % na 500 m) | ESTIMATED |
| σ, pogodny dzień zimowy (V = 17,4 km) | 1,7·10⁻⁴ 1/m (8,2 % na 500 m) | ESTIMATED |
| σ, pochmurny dzień zimowy (V = 7,4 km) | 4,0·10⁻⁴ 1/m (18 % na 500 m) | ESTIMATED |
| σ, zamglony dzień zimowy (p10, V = 2,1 km) | 1,4·10⁻³ 1/m (51 % na 500 m) | ESTIMATED |
| σ, pochmurno — cały rok (V = 13,6 km) | 2,2·10⁻⁴ 1/m (10 % na 500 m) | ESTIMATED |
| przelicznik na parametr „visibility” gry (wzór 3,912/V z ADR 0010) | V_gry = 1,306 · V_IMGW (widzialność IMGW ≈ MOR, próg 0,05) | SOURCED (WMO) + obliczenie |
| mgiełka ADR 0080 (≈ 2,4 km, 55 % na 500 m) | występuje w 11,6 % terminów dziennych XI–II i 0,2 % V–VIII — to stan „zamglony dzień zimowy”, nie letni | ESTIMATED |
| niebo pochmurne: barwa | neutralna szarość do lekko niebieskawej, bez ciepłego pasa | WORKING_VALUE (zdjęcia + Lee 2005) |
| niebo pochmurne: gradient | St neb/mgła: CIE typ 5–3 (horyzont/zenit 1,0–0,67); typ 1 (0,335 ≈ 1:3, Moon–Spencer, obecny model gry) dla grubej warstwy bez mgły | WORKING_VALUE |
| mgła gęsta (stacja 130–480 m, kadry c01–c04) | brak linii horyzontu, niebo = tło; pod słońce cała mgła kremowa, poza tym neutralna/niebieskawa | SOURCED (kadry) |
| opad śniegu przy wid. 1,07–1,2 km (c26, c27) | obiekty na ok. 500 m to blade zarysy; niebo ≈ jasność śniegu | SOURCED (kadry; odległości nie mierzono) |

## Co już było w repo / co nowe
| temat | w repo | nowe w R7 |
|---|---|---|
| model nieba, niebo pochmurne CIE 1:3, mgła 3,912/V | ADR 0010 | parametry 5 typów „overcast” CIE, przelicznik MOR 2,996 vs 3,912, σ per sezon z danych |
| zmierzch = −6°, magenta, koralowy pas (otwarte) | ADR 0182, 0192 | zdjęcia zmierzchu z N i wysokością słońca, częstość zachmurzenia o zmierzchu, hipoteza z kodu |
| mgiełka przy gruncie 2,4 km | ADR 0080 | częstość takiej widzialności per sezon |
| klimat Białegostoku (zachmurzenie, usłonecznienie, mgła, widzialność), tabela słońca | brak (`research/` g5, g7, g10, mistral, gptpro — brak tematu) | całość |

## Luki
- Brak zdjęcia całego nieba (rybie oko) — gradient zenit/horyzont pod St/Sc nie zmierzony; wybór typu CIE to WORKING_VALUE.
- Kierunek kadrów Commons UNVERIFIED (brak azymutu w metadanych); 4 kadry bez współrzędnych. Czas zdjęć Commons przyjęty jako lokalny (założenie).
- Stacja IMGW leży na lotnisku (Krywlany), nie w miejscu zdjęć; parowanie do najbliższej pełnej godziny. Współrzędne stacji w manifeście przybliżone (UNVERIFIED).
- Usłonecznienie: braki od 2016 (33 miesiące ze statusem 8); liczniki dni ze zjawiskami brak od IV 2022; zachmurzenie nocne (19–05 UTC) brak od IV 2022
  (statystyki zmierzchu letniego opierają się głównie na 2014–2021).
- Kody ww/CL interpretowane wg pola tekstowego w danych; klucza WMO-No. 306 nie otwarto. Moon & Spencer 1942 nie otwarto (brak DOI); pełnych tekstów prac
  Applied Optics nie otwarto (tylko abstrakty). Norma ISO 15469 płatna — parametry ze źródła wtórnego (rcaiman, GPL-3).
- Kadry Panoramax z XI 2026 bez danych stacji (jeszcze nieopublikowane). Brak kadrów: letni dzień pochmurny, wschód słońca, mgła poza miastem (droga), noc pogodna.
- Samokontrola: 3 z 13 ponownie obejrzanych kadrów miały nieścisłe zdanie o subtelnym gradiencie jasności nieba przy horyzoncie (poprawione) — takie zdania
  w pozostałych opisach traktować ostrożnie; stwierdzenia o braku/obecności ciepłego pasa potwierdzone 13/13.
- Licencja IMGW: czy dane archiwalne to „dane o wysokiej wartości” (użycie w każdym celu) — UNVERIFIED; do gry trafiają tylko parametry pochodne.
- Hipoteza o barwie mgły niesprawdzona w Unity.

## Jak używać
`python3 -I fetch.py` (pobranie + sha256) → `python3 -I tools_imgw.py compute; python3 -I tools_normy.py; python3 -I tools_sun.py; python3 -I tools_twilight.py; python3 -I tools_checks.py`
→ `python3 -I build_manifest.py` → `python audit.py` (wymaga pakietów astral, rdata). CC BY-SA (Panoramax, c32) = referencja, nie tekstura.

## Errata lidera (s20, 2026-11-14)
Patrz `docs/reports/REVIEW-2026-11-14-s20-cloud2-r7.md` — errata obowiązuje przed użyciem danych.
