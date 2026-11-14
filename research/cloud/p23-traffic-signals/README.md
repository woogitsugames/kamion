# M66 — sygnalizatory świetlne w Białymstoku: tarcze, komory, daszki, warianty (cloud p23)

Stan: 2026-11-14. Wiersze `C66-001…C66-108` w `manifest.csv` (30 przepis, 35 skrzyżowanie [18 skrzyżowań + 17 wariantów], 12 wymiar, 31 kadr).
Zdjęcia i PDF-y nie są w gicie — `python3 -I fetch.py` pobiera 33 pliki (74 568 231 B) do `files/` i sprawdza sha256 (sprawdzone na czystym katalogu: 0 błędów).

## 1. Wniosek o tarczach (ekranach kontrastowych)

**Tarcza kontrastowa w Białymstoku: MIESZANIE — zależnie od położenia głowicy, zgodnie z przepisem.**

- **Głowice NAD jezdnią (wysięgnik / rama): tarcza jest.** 15 z 18 skrzyżowań w próbie (15/15 tam, gdzie głowicę nad jezdnią widać od przodu lub od tyłu); 2 skrzyżowania UNVERIFIED (widok z boku; wysięgnik poza kadrem — w tym P11-063 Mickiewicza/Kuronia), 1 bez głowic nad jezdnią w kadrze.
  Tarcza jest **czarna, prostokątna, większa od zestawu komór** (ok. 2× szersza), najczęściej z **białą obwódką** (10 skrzyżowań); na 2 skrzyżowaniach ul. Piastowskiej czarna bez widocznej białej obwódki; na 3 — ażurowa (rzędy pionowych szczelin); na 1 — owalna (ESTIMATED).
- **Głowice OBOK jezdni (na maszcie / słupku): tarczy nie ma** — 11 z 11 skrzyżowań, na których głowicę boczną obejrzano w powiększeniu; 0 przypadków głowicy bocznej z tarczą.
- **Białej tarczy nie widziano nigdzie.** Biała prostokątna tarcza w grze (uwaga z przeglądu P11-063) jest niezgodna zarówno z kadrami, jak i z Dz.U. („Ekran musi być barwy czarnej z białą obwódką”, s. 715). Żółtej odblaskowej obwódki (wspomnianej w bloku zadania) też nie stwierdzono — w kadrach i w przepisie obwódka jest biała.
- Przepis: ekran jest **wymagany** dla sygnalizatora nad jezdnią („Integralnym elementem sygnalizatora mocowanego nad jezdnią jest ekran kontrastowy”, zał. 3 pkt 3.3.5.6, s. 715), a obok jezdni tylko **dopuszczony**. Wymiary z rys. 10.28 a (s. 802): **850 × 1400 mm** (Ø300 nad jezdnią; 650 × 1400 obok jezdni), biała obwódka **40 mm**, czarny margines **20 mm**, naroża **R70**; dla Ø200: 520 × 1040 mm.
- Zastrzeżenie próby: 18 skrzyżowań z 151 skupisk OSM `highway=traffic_signals` (12 %), dobór wg dostępności kadrów (głównie arterie), lata 2018–2026; próba nie jest losowa.

Zalecenie dla `StreetFurniture` (do decyzji lidera): głowica na wysięgniku = czarna tarcza 850 × 1400 mm z białą obwódką 40 mm (20 mm od krawędzi), pochylona 5–10° ku jezdni; głowica na maszcie = bez tarczy; wszystkie komory czarne z daszkami.

## 2. Przepisy (Dz.U. 2019 poz. 2311, zał. 3 — tekst jednolity; obowiązujący)

Plik: API ELI Sejmu `DU/2019/2311/text/I/D20192311-c2.pdf` (381 stron = s. 526–906 dziennika; sha256 w manifeście). Strony podane wg numeracji Dziennika Ustaw (nagłówek „– NNN –”). Wartości z rysunków i z tabeli 7.1 (raster) odczytano z renderów stron (obejrzane; rys. 10.28 dodatkowo w 600 dpi).
Nowelizacje po tekście jednolitym (2021 poz. 438 i 2066, 2022 poz. 2377, 2026 poz. 132) przejrzano: w zał. 3 zmieniono tylko rys. 10.3 oraz pkt 3.3.5.2–3.3.5.3 (sygnalizatory akustyczne/wibracyjne) — ekrany, komory i tabela 7.1 bez zmian.
Nie powtarzamy M50-033…039 (`research/mistral/p9-furniture-3`): wysokości 4,5–5,5 m, LZW, szerokości ekranów 850/650/520; **nowe**: pełne wymiary ekranów z rysunków, barwa i obowiązek ekranu, komory, daszek, średnice wg typów, skrajnie z tabeli 7.1 (w M50-039 były UNVERIFIED).

| id | element | parametr | wartość | jedn. | punkt / strona |
|---|---|---|---|---|---|
| C66-001 | ekran kontrastowy – tarcza | definicja / barwa | czarna z białym obrzeżem; prostokąt lub owal; za sygnalizatorem |  | pkt 1.2 (definicje), s. 701 (SOURCED) |
| C66-002 | ekran kontrastowy – tarcza | czy wymagana – nad jezdnią | TAK (integralny element sygnalizatora nad jezdnią) |  | pkt 3.3.5.6, s. 715 (SOURCED) |
| C66-003 | ekran kontrastowy – tarcza | czy wymagana – obok jezdni | NIE (dopuszczona w uzasadnionych przypadkach; wtedy mniejsza) |  | pkt 3.3.5.6, s. 715 (SOURCED) |
| C66-004 | ekran kontrastowy – tarcza | barwa i obwódka | czarna z białą obwódką |  | pkt 3.3.5.6, s. 715 (SOURCED) |
| C66-005 | ekran kontrastowy – tarcza | szerokość wg średnicy soczewek | 850 (Ø300 nad jezdnią); 650 (Ø300 obok jezdni, zalecane; nad jezdnią gdy brak skrajni); 520 (Ø200, zalecane) | mm | pkt 3.3.5.6, s. 716 (SOURCED) |
| C66-006 | ekran kontrastowy – tarcza prostokątna S-1/S-3 Ø300 | wymiary (szer. × wys.), obwódka, narożniki | 850 (650*) × 1400; biała obwódka 40; czarny margines zewnętrzny 20; promień naroża R70 | mm | rys. 10.28 a, s. 802 (SOURCED) |
| C66-007 | ekran kontrastowy – tarcza prostokątna Ø200 | wymiary (szer. × wys.) | 520 × 1040; obwódka 40; margines 20; R70 | mm | rys. 10.28 b, s. 803 (SOURCED) |
| C66-008 | ekran kontrastowy – tarcza owalna Ø300 | wymiary (szer. × wys.) | 850 (650*) × 1400; obwódka 40; margines 20 | mm | rys. 10.29, s. 803 (SOURCED) |
| C66-009 | ekran kontrastowy – tarcza S-2 (z komorą strzałki) | wymiary | 1000 (800*) × 1400; wycięcie narożne 400 (320*) szer.; obwódka 40; margines 20; R70 | mm | rys. 10.30, s. 804 (SOURCED) |
| C66-010 | ekran kontrastowy – tarcza kwadratowa S-4/S-7 | bok ekranu b wg wymiaru sygnału a | a 600 → b 850; a 450 → b 650; a 300 → b 520 | mm | rys. 10.31 (tabela), s. 804 (SOURCED) |
| C66-011 | komora sygnałowa – obudowa | barwa | czoło: czarna lub ciemnozielona; tył: czarna, ciemnozielona lub szara |  | pkt 3.3.2 lit. a, s. 708 (SOURCED) |
| C66-012 | komora sygnałowa – sygnalizator | liczba komór | 1–4, wyjątkowo 5 (+ ew. kwadratowa komora wyświetlacza czasu) | szt. | pkt 3.3.2, s. 707 (SOURCED) |
| C66-013 | komora sygnałowa – daszek (osłona) | długość części wystającej | ≥ 200 (zalecenie) | mm | pkt 3.3.2, s. 709 (SOURCED) |
| C66-014 | S-1 – soczewka | średnica | 300 (S-1); 200 (S-1a – dla kierujących rowerami) | mm | pkt 3.2.2, s. 702 (SOURCED) |
| C66-015 | S-1 – soczewka | dopuszczenie Ø200 obok jezdni | 200 – gdy sygnalizacja nie jest jedyna/pierwsza w miejscowości i v ≤ 60 km/h | mm | pkt 3.2.2, s. 702–703 (SOURCED) |
| C66-016 | S-2 – sygnalizator z sygnałem dopuszczającym skręcanie | liczba komór / soczewka strzałki | 4 lub 5 komór; soczewka strzałki 200 | mm | pkt 3.2.3, s. 703 (SOURCED) |
| C66-017 | S-3 – sygnalizator kierunkowy | średnica soczewek | 300 (S-3); 200 (S-3a) | mm | pkt 3.2.4, s. 703 (SOURCED) |
| C66-018 | S-5 / S-6 – sygnalizator dla pieszych / rowerzystów | średnica soczewek | 200 | mm | pkt 3.2.7, s. 704 (SOURCED) |
| C66-019 | sygnalizator pomocniczy – soczewka | średnica | 90–100 | mm | pkt 3.2.2, s. 703 (SOURCED) |
| C66-020 | wysokość / skrajnia – sygnalizator obok jezdni na maszcie | skrajnia pionowa (min / zalecana / maks) | 2,0 / 2,2 / 2,7 | m | tabela 7.1 lp. 1, s. 757 (SOURCED) |
| C66-021 | wysokość / skrajnia – sygnalizator nad jezdnią | skrajnia pionowa (min / zalecana / maks) | normalna 4,5 / 4,7 / 5,5; podwyższona 5,5 / 5,5 / 6,0 | m | tabela 7.1 lp. 5–6, s. 757 (SOURCED) |
| C66-022 | wysokość / skrajnia – sygnalizator obok jezdni | skrajnia pozioma od krawędzi jezdni (min / zalecana / maks) | v ≤ 60 km/h: 0,5 / 0,7 / 2,0; v > 60 km/h: 0,75 / 0,9 / 2,0 (prosta i łuki R ≥ 100 m) | m | tabela 7.1 lp. 3, s. 757 (SOURCED) |
| C66-023 | ustawienie – sygnalizator nad jezdnią | pochylenie ku nadjeżdżającym | 5–10 | ° | pkt 7.2.2, s. 755 (SOURCED) |
| C66-024 | lokalizacja – sygnalizator podstawowy / dodatkowy | zasada | podstawowy po prawej stronie każdego wlotu; dodatkowy nad wlotem lub po lewej |  | pkt 7.3.1, s. 758 (SOURCED) |
| C66-025 | S-5 – przycisk dla pieszych | wysokość montażu | 1,2–1,35 (na maszcie/słupie); osobny słupek ≥ 1,5 wys. | m | pkt 3.3.5.1, s. 712 (SOURCED) |
| C66-026 | wyświetlacz czasu – komora kwadratowa | bok / wysokość cyfr | 300 / ≥ 210 | mm | pkt 3.3.3.2, s. 711 (SOURCED) |
| C66-027 | S-5 – sygnalizator akustyczny | forma | nie jako dodatkowa komora zblokowana z S-5 |  | Dz.U. 2022 poz. 2377, § 1 pkt 3 lit. a (nowe brzmienie pkt 3.3.5.2 zał. 3), s. 15 (SOURCED) |
| C66-028 | aktualność aktu – zał. 3 po tekście jednolitym | nowelizacje | 2021 poz. 438 (tylko zał. 1); 2021 poz. 2066 (zał. 3: tylko rys. 10.3); 2022 poz. 2377 (zał. 3: pkt 3.3.5.2 i 3.3.5.3); 2026 poz. 132 (zał. 1, 2, 4) – ekrany, komory i tab. 7.1 bez zmian |  | API ELI Sejmu: DU/2019/2311 → „Nowelizacje po tekście jednolitym” (SOURCED) |
| C66-029 | sygnały dla ciężarówek – — | osobny sygnalizator | BRAK w zał. 3 (s. 691–806: 0 wystąpień rdzenia „ciężar”) |  | całość (przeszukanie warstwy tekstowej) (UNVERIFIED) |
| C66-030 | wytyczne WR-D / GDDKiA dot. sygnalizacji – — | tarcza kontrastowa | nie sprawdzono |  | — (UNVERIFIED) |

Uwagi: (a) tekst pkt 3.3.5.6 odsyła do „rysunków 10.23–10.27”, a ekrany są na rys. 10.28–10.32 — niespójność w samym akcie; (b) w tym akcie S-6 = sygnalizator dla rowerzystów, S-1a/S-3a = dla kierujących rowerami, **S-7 = żółta strzałka nakazu opuszczenia pasa** (nie rowerowy); (c) osobnego sygnalizatora dla ciężarówek w zał. 3 nie ma (wynik negatywny wyszukiwania, UNVERIFIED dla rysunków).

## 3. Skrzyżowania (18) — pozycja = środek skupiska węzłów OSM

| id | skrzyżowanie | lat, lon | tarcza nad jezdnią | opis tarczy | głowice boczne bez tarczy | konstrukcja | kadry |
|---|---|---|---|---|---|---|---|
| C66-062 | Al. Jana Pawła II / Wysoki Stoczek | 53.141019, 23.100731 | TAK | czarna prostokątna, biała obwódka wyraźna | TAK | 2 proste wysięgniki poziome z rury na słupach (rama niepełna); maszt boczny okrągły szary |  C66-031 |
| C66-063 | Al. Piłsudskiego / Sienkiewicza | 53.134877, 23.163143 | TAK | czarna prostokątna, biała obwódka wyraźna; pochylona ku jezdni | TAK | rama: belka z rury na 2 słupach z kołnierzami; 6 głowic |  C66-032, C66-033 |
| C66-064 | Piastowska / Towarowa / Piasta | 53.135342, 23.196029 | TAK | czarna prostokątna, bez widocznej białej obwódki (wycinek 5×) | TAK | 2 łukowe wysięgniki z dwóch stron jezdni |  C66-034 |
| C66-065 | Piastowska / Mieszka I / Sybiraków | 53.132632, 23.193457 | TAK | czarna prostokątna, bez widocznej białej obwódki (wycinek 5×) | TAK | łukowy wysięgnik; głowica boczna przy słupie betonowym |  C66-035 |
| C66-066 | Piastowska / Chrobrego / mjr. Szendzielarza | 53.129114, 23.188946 | TAK | czarna prostokątna, cienka jasna obwódka | UNVERIFIED (za małe w kadrze) | 2 łukowe wysięgniki stykające się nad jezdnią |  C66-036 |
| C66-067 | Rondo Żołnierzy Wyklętych (Piastowska / Kazimierza Wielkiego) | 53.140429, 23.200786 | TAK | czarna prostokątna, biała obwódka | TAK | rama/wysięgniki z rury na grubych słupach; słupek boczny z głowicą na szczycie |  C66-037, C66-038, C66-039 |
| C66-068 | gen. Sosabowskiego / 42 Pułku Piechoty | 53.143551, 23.190866 | TAK | czarna prostokątna, biała obwódka wyraźna | UNVERIFIED (nie powiększano) | wysięgnik prosty z 1 głowicą |  C66-040, C66-041 |
| C66-069 | gen. Sulika / Dolistowska | 53.138843, 23.212029 | TAK | czarna prostokątna, biała obwódka wyraźna, narożniki zaokrąglone | TAK | ramy z rur (słup + belka pozioma) |  C66-042, C66-043 |
| C66-070 | Jurowiecka / Fabryczna | 53.136919, 23.163105 | TAK | czarna prostokątna, jasna obwódka | UNVERIFIED | prosty wysięgnik z rury |  C66-044 |
| C66-071 | Sienkiewicza / Jurowiecka | 53.136044, 23.165084 | TAK | czarna prostokątna, biała obwódka | UNVERIFIED | łukowy wysięgnik |  C66-045, C66-046 |
| C66-072 | Al. Tysiąclecia PP / Sokólska / Kombatantów | 53.150754, 23.154708 | TAK | czarna prostokątna, biała obwódka; od tyłu pełna blacha | TAK | łukowy wysięgnik, tablice pasów na prętach nad belką |  C66-047, C66-048 |
| C66-073 | Al. Tysiąclecia PP / Radzymińska / Bitwy Białostockiej | 53.145649, 23.157261 | TAK | owalna (kształt kapsuły), ciemna z jasną obwódką – kształt ESTIMATED z wycinka 5× | UNVERIFIED | łukowy wysięgnik |  C66-049 |
| C66-074 | Rondo Putry (Al. Tysiąclecia PP / gen. Andersa) | 53.159019, 23.151591 | TAK | czarna prostokątna, biała obwódka; pod estakadą wariant żaluzjowy | TAK | maszty z łukowym wysięgnikiem; wg ADR 0172 (ortofoto 2024) 1 maszt z wysięgnikiem ~8,8 m, 2 głowice na wysięgniku + 1 na maszcie |  C66-050, C66-051, C66-052, C66-053 |
| C66-075 | Antoniuk Fabryczny / Swobodna | 53.150292, 23.112660 | TAK | ażurowa (pionowe szczeliny), widziana od tyłu; obwódka UNVERIFIED | UNVERIFIED | ciemnoszary okrągły maszt, łukowy wysięgnik |  C66-054 |
| C66-076 | Kołłątaja / Swobodna | 53.144375, 23.105828 | UNVERIFIED | widok z boku – cienka krawędź blachy za komorami | UNVERIFIED | maszt z łukowym wysięgnikiem |  C66-055 |
| C66-077 | Swobodna / Łagodna | 53.147266, 23.108080 | BRAK GŁOWIC NAD JEZDNIĄ W KADRZE | — | TAK | słupki smukłe ocynkowane; maszt boczny |  C66-056 |
| C66-078 | Pogodna / Składowa / Żeromskiego / Transportowa | 53.113670, 23.129837 | TAK | czarna ażurowa (rzędy pionowych szczelin), narożniki zaokrąglone; widziana od tyłu – obwódka UNVERIFIED | TAK | 2 łukowe wysięgniki; słupek boczny ocynkowany |  C66-057, C66-058, C66-059, C66-060 |
| C66-079 | Mickiewicza / Kuronia / Dywizjonu 303 | 53.105460, 23.185033 | UNVERIFIED | wysięgnik wychodzi poza kadr | TAK | maszt z łukowym wysięgnikiem |  C66-061 |

Maszty: rura okrągła, szara (ocynk); wyjątek C66-075 — maszt ciemnoszary/malowany. Przekroju wielokątnego nie stwierdzono. Długość wysięgnika znana tylko dla Ronda Putry (8,8 m, ADR 0172). Sygnalizatory dla pieszych, przyciski, kamery i szafki — kolumny „wartość”/„uwagi” w manifeście (wiersze C66-062…079).
Trasa C: są Rondo Putry (C66-074), Al. Tysiąclecia/Sokólska (C66-072), Al. Tysiąclecia/Radzymińska (C66-073), Mickiewicza/Kuronia (C66-079, P11-063). **Brak kadrów** dla: Sokólska/Wysockiego, Al. Tysiąclecia/Maczka, gen. Andersa (poza rondem) — patrz luki.

## 4. Warianty → liczba wystąpień → przykładowy kadr

| wariant | liczba skrzyżowań (z 18) | przykładowy kadr |
|---|---|---|
| tarcza prostokątna czarna z białą obwódką na głowicy NAD jezdnią | 10 | C66-031 |
| tarcza prostokątna czarna BEZ widocznej białej obwódki NAD jezdnią | 2 | C66-034 |
| tarcza ażurowa (pionowe szczeliny) NAD jezdnią | 3 | C66-057 |
| tarcza owalna z jasną obwódką NAD jezdnią (kształt ESTIMATED) | 1 | C66-049 |
| głowica boczna na maszcie/słupku BEZ tarczy | 11 | C66-037 |
| głowica boczna Z tarczą | 0 | brak przykładu w próbie |
| wysięgnik łukowy (rura gięta) z 1–2 głowicami | 11 | C66-047 |
| rama / prosty wysięgnik poziomy z rury | 6 | C66-032 |
| sygnalizator kierunkowy S-3 (strzałka w soczewce) | 8 | C66-034 |
| sygnalizator S-2 (dodatkowa komora strzałki obok) | 0 | brak przykładu w próbie |
| sygnalizator dla pieszych S-5, 2 komory | 3 | C66-056 |
| przycisk dla pieszych (żółta skrzynka na słupku) | 1 | C66-058 |
| sygnalizator dla rowerzystów S-6 / S-1a (rozpoznany jednoznacznie) | 0 | brak przykładu w próbie |
| tablice pasów ruchu przy głowicach nad jezdnią | 11 | C66-032 |
| kamera/czujnik na wysięgniku lub słupku | 6 | C66-051 |
| szafka przy skrzyżowaniu (sterownik? UNVERIFIED) | 2 | C66-057 |
| daszki na komorach (wszystkie obejrzane głowice) | 18 | C66-058 |

## 5. Wymiary elementów (do modelu 3D)

| id | element | parametr | wartość | jedn. | status |
|---|---|---|---|---|---|
| C66-080 | tarcza nad jezdnią (JPII/Wysoki Stoczek) | proporcja wys./szer. | 1,60 (640 px / 400 px na wycinku A2) | — | ESTIMATED |
| C66-081 | tarcza nad jezdnią | szerokość białej obwódki | ~43 (20 px z 400 px szerokości × 850 mm) | mm | ESTIMATED |
| C66-082 | sygnalizator trójkomorowy Ø300 na słupku (Rondo Żołnierzy Wyklętych) | szerokość obudowy | ~370 (215 px przy widocznej soczewce 175 px = 300 mm) | mm | ESTIMATED |
| C66-083 | sygnalizator trójkomorowy Ø300 | wysokość zestawu 3 komór | ~1040 (605 px / 175 px × 300 mm) → ~345 na komorę | mm | ESTIMATED |
| C66-084 | komora | głębokość obudowy | UNVERIFIED | mm | UNVERIFIED |
| C66-085 | daszek tunelowy | długość | min. 200 wg zalecenia Dz.U. (wiersz przepisu); z kadrów: daszek ≈ 0,6–0,8 wysokości komory (widok boczny R2, Y3) | mm | ESTIMATED |
| C66-086 | tarcza | grubość / materiał | cienka płaska blacha (od tyłu szara lub ciemna), wariant pełny i ażurowy; grubość UNVERIFIED | mm | UNVERIFIED |
| C66-087 | słupek pod sygnalizatorem bocznym | średnica | ~100 (60 px / 175 px × 300 mm) | mm | ESTIMATED |
| C66-088 | słup ramy/wysięgnika | średnica | ~220 (130 px / 175 px × 300 mm) – słup dalej/bliżej niż głowica, więc ±30 % | mm | ESTIMATED |
| C66-089 | maszt z wysięgnikiem na Rondzie Putry (182011) | długość wysięgnika | 8,8 (±0,3) | m | SOURCED |
| C66-090 | jasnoszara szafka dwudrzwiowa z daszkiem (Pogodna) | wysokość × szerokość | ~1,3–1,5 × ~1,0–1,2 | m | ESTIMATED |
| C66-091 | komora / tarcza / daszek | wymiary katalogowe | nie pozyskano | mm | UNVERIFIED |

Z przepisu (SOURCED, §2): soczewki Ø300 (S-1, S-3), Ø200 (S-5, S-6, S-1a, S-3a, strzałka S-2), Ø90–100 (pomocnicze); czoło komory czarne lub ciemnozielone, tył czarny/ciemnozielony/szary; daszek ≥ 200 mm (zalecenie); tarcze — §1.
Wygląd z kadrów: wszystkie obejrzane obudowy **czarne**; daszki tunelowe na każdej komorze; soczewka wyłączona w dzień = ciemna, prawie czarna; zapalona = jednolity krążek (wygląd LED; typ źródła światła UNVERIFIED); tarcza = cienka blacha na obejmach do belki, od tyłu szara lub ciemna, pełna albo ażurowa; tablice pasów ruchu na pionowych prętach nad belką albo na belce między głowicami.

## 6. Kadry (31 obejrzanych, 18 skrzyżowań)

26 × KartaView (CC BY-SA 4.0 — referencja, nie tekstura; pełna rozdzielczość 3072–4608 px), 5 × Wikimedia Commons (CC0; **miniatury 1920 px** — oryginały i miniatury 3840 px zwracały HTTP 429 dla naszego User-Agenta; URL oryginału i sha1 z Commons są w `uwagi`).
Każdy kadr obejrzany w 960 px; wykonano 48 wycinków z pełnej rozdzielczości (3×; dla dużych pól wynik ograniczony do 1500 px szerokości, czyli < 3×), z czego **obejrzano 40** (+ 3 wycinki 5× w audycie); 8 nieobejrzanych wycinków nie jest podstawą żadnego opisu. Spełnienie progów: z tarczą ≥ 5 → 26 kadrów (wszystkie poza C66-041, -055, -056, -058, -061); głowica bez tarczy potwierdzona wycinkiem ≥ 5 → 13 kadrów (C66-031, -032, -033, -034, -035, -037, -039, -043, -051, -053, -056, -058, -061); dla pieszych ≥ 3 → C66-031, C66-037, C66-056 (+ przycisk C66-058); na wysięgniku/ramie ≥ 3 → 29 kadrów (wszystkie poza C66-056, -058).
Kierunek: KartaView — pole `Heading` z API (skontrolowane namiarem kamera → węzeł OSM, różnica ≤ 27°, wartości w `uwagi`); Commons — brak GPSImgDirection → UNVERIFIED. Wszystkie kadry ≤ 40 m od węzła `highway=traffic_signals` (2,9–33,3 m; id i odległość w wierszu).
Marki/szyldy/reklamy widoczne w kadrach — tylko referencja, nie odtwarzamy.

## 7. Samokontrola (≥ 20 %)

`random.Random(20261114).sample(ids, 22)` z 108 wierszy (20,4 %). Ponownie otwarto 6 wylosowanych kadrów (960 px) i wycinki 5× dla wylosowanych skrzyżowań, sprawdzono HTTP wszystkich URL-i wylosowanych wierszy (200/206) i cytaty przepisów w warstwie tekstowej PDF. **4 poprawki** (szczegóły w `audit_20_percent.json`):
1. C66-065 / C66-035 (Piastowska/Mieszka I): „obwódka cienka” → **bez widocznej białej obwódki** (wycinek 5×);
2. C66-064 / C66-034 (Piastowska/Towarowa): „obwódka słabo widoczna” → **bez widocznej białej obwódki** (wycinek 5×) — skorygowano też tabelę wariantów (10 + 2 zamiast 11 + 1);
3. C66-049 / C66-073 / C66-095 (Al. Tysiąclecia/Radzymińska): „kształt niepewny” → **owalna (kapsuła), ESTIMATED** (wycinek 5×);
4. C66-051: „niebo o świcie” → „niskie słońce” (pory dnia nie da się ustalić z obrazu).

## 8. Kryteria akceptacji

| kryterium | wynik |
|---|---|
| jednoznaczny wniosek tarcza tak/nie/mieszanie z liczbą skrzyżowań i ułamkiem | TAK — mieszanie: nad jezdnią 15/18 (15/15 widocznych), obok jezdni 0/11 |
| ≥ 12 skrzyżowań w tabeli | TAK — 18 |
| ≥ 20 kadrów (≥ 5 z tarczą, ≥ 5 bez, ≥ 3 piesi, ≥ 3 wysięgnik) | TAK — 31 |
| wymiary komory i tarczy z dokumentu lub ESTIMATED | CZĘŚCIOWO — tarcza z Dz.U. (rysunki); komora tylko ESTIMATED (szer./wys.), głębokość i grubość tarczy UNVERIFIED; brak kart katalogowych |
| wszystkie warianty z p. 2 jako lista wariant → liczba → kadr | CZĘŚCIOWO — 17 wariantów; S-2, S-6/S-1a i głowica boczna z tarczą: 0 w próbie; średnice masztów tylko z 1 kadru; wysięgnik tylko 182011 |

## 9. Luki (uczciwie)

- **Trasa C niepełna:** brak otwartych kadrów dla Sokólska/Wysockiego, Al. Tysiąclecia/Maczka, Andersa (odcinek) i Dojlid poza P11-063; skan Commons (geosearch) objął 24 z 64 kafli (południe miasta do 53,12°N + część centrum) — limit 429; Panoramax: tylko 1 skupisko (Rondo Putry, 2019), nie użyto; Mapillary — nie (brak tokenu).
- **P11-063:** głowica na wysięgniku jest poza kadrem → tarcza na TYM skrzyżowaniu UNVERIFIED (reguła z próby: nad jezdnią będzie czarna tarcza; na maszcie widać głowicę bez tarczy).
- **Rondo Putry:** kadry 2018–2019 pokazują stan sprzed przebudowy (dwa maszty); stan 2024 wg ADR 0172 — nie mamy kadru po przebudowie.
- **BIP ZDM (zlecenia/przetargi na sygnalizacje), WR-D / wytyczne GDDKiA:** nie sprawdzono (czas) — typy masztów i sterowników z dokumentów zamawiającego UNVERIFIED.
- **Karty katalogowe / PN-EN 12368:** nie pozyskano → głębokość komory, grubość i materiał tarczy, konstrukcja opasek: UNVERIFIED.
- **Skrzynki sterowników:** 2 szafki widoczne, przeznaczenie niepotwierdzone, napisy nieczytelne. **Głośniki S-5:** 1 element niepewny (C66-056).
- Średnice masztów i wymiary komory: po jednym odczycie proporcją do soczewki (±15–30 %).
- Sezon: brak kadrów zimowych ze śniegiem i nocnych. Godzina w API KartaView bez strefy — pora dnia „dzień” z obrazu.
- Miniatury Commons: sha256 dotyczy miniatury 1920 px serwowanej 2026-11-14 (przy ponownym wygenerowaniu po stronie Commons suma może się zmienić; wtedy porównać z sha1 oryginału z `uwagi`).
