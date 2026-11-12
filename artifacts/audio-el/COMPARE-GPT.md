# Porównanie z niezależną analizą GPT (248 WAV ElevenLabs) — ADR 0137

Źródła: GPT `C:\Users\matma\Documents\Claude\kamion-audio-review-20261112\` (`selections.json`, `engine-refined.md`;
folder nie był modyfikowany). Moje dane: `artifacts/audio-el/analysis/analysis.csv`, `rpmtest.csv`
(`tools/audio/el_rpmtest.py`), `prepare.txt`, `verify/`. Wersja 2026-11-12.

## 1. Czy pętle mają różne obroty? — **Nie.** (zgodnie z GPT, mocniej rozstrzygnięte)

Test drabiny zapłonów R6 (`el_rpmtest.py`): dla każdej pętli liczę wyrazistość harmonicznych k·f, k = 1…6, w dB
ponad lokalnym tłem widma Welcha (tolerancja 1,5 %). Raz przy f = obroty z promptu / 20, raz przy zmierzonej linii
dominującej. Pętla „jest na” danych obrotach, gdy ≥ 3 z 6 harmonicznych wystają ≥ 6 dB.

| Obroty w prompcie | plików | drabina przy obrotach z promptu (≥3/6) | drabina przy zmierzonych | mediana zmierzonych [obr/min] |
|---:|---:|---:|---:|---:|
| 600 | 16 | 0 | 3 | 883 |
| 900 | 16 | 1 | 5 | 1071 |
| 1200 | 16 | 1 | 2 | 991 |
| 1500 | 16 | 0 | 6 | 995 |
| 1800 | 16 | 0 | 4 | 1227 |
| 2100 | 16 | 0 | 3 | 995 |

- Tylko **2 z 96** plików mają drabinę przy obrotach z promptu: `ENG_EXT_ON_1200 (4)` (60,1/120,1/180,9 Hz)
  i jeden 900. Średnio przy obrotach z promptu wystaje 0,1–0,9 z 6 harmonicznych (losowe trafienia w tło).
- Linia dominująca (20–120 Hz) we wszystkich ID leży przy 36–72 Hz, mediana 933 obr/min. Korelacja prompt → pomiar
  r = 0,24. Teza GPT, że EXT_OFF_1500/1800/2100 mają maksima 44–47 Hz, potwierdza się: moje pomiary dla v1–v4 to
  883/933/960/996, 866–1108 i 879–937 obr/min.
- **Wniosek:** banki z nazw ID nie różnią się obrotami. Dlatego gra nie używa ID jako komórek. Każda komórka bierze
  stabilną pętlę z wyraźną linią z całej puli perspektywy/obciążenia i przestraja ją offline do obrotów siatki.
  `el_verify` mierzy ton po przestrojeniu: ±2,5 % od obr/min / 20 w 24/24 komórkach.
- Zastrzeżenie: większość pętli to szumowy pomruk z 1–2 liniami tonalnymi, nie pełna drabina silnika. Tylko 23/96
  ma ≥ 3 harmoniczne nawet przy zmierzonej linii. „Obroty” to więc odczuwalna wysokość tonu, nie prawdziwy rząd
  zapłonów. Wartości > 2000 obr/min w tabeli niżej oznaczają pliki bez linii 20–120 Hz: miernik złapał wtedy
  pasmo 120–145 Hz, które ma niemal każdy plik. Takie pliki nie wchodzą do siatki (filtr wyrazistości ≥ 9 dB).

## 2. Stabilność i szwy — zgodnie

GPT: szwy pętli silnika bez alarmów, ranking stabilności w centach. U mnie: skok szwu < 1 × p99,9 w 96/96. Po
obróbce (crossfade 40 ms) `el_verify` daje 0 FAIL. Moje okna 1 s mierzą słabą linię z szumem (mediana 9 %), a analiza
GPT (korelacja widma, 2 s, ±500 centów) jest tu dokładniejsza. Dlatego jej ranking posłużył do korekty wyboru:
- `ENG_CAB_OFF_1200 (4)` (u GPT najmniej stabilny w ID, koszt 366) grał w 4 komórkach kabina/bez obciążenia.
  Teraz gra tylko w 1800/2100, gdzie potrzebny jest jego wysoki ton (1426 obr/min). Komórki 1200/1500 przeszły na
  `ENG_CAB_OFF_1800 (3)` (u GPT najlepszy w ID; 1218 obr/min, ×0,99/×1,23).
- Próba odwrotna: `ENG_EXT_OFF_1200 (2)` (u GPT najlepszy w ID, 30 centów) zamiast `ENG_EXT_OFF_900 (4)` dla
  zewnątrz/bez obciążenia 1800/2100. **Odrzucona:** nie ma linii 20–120 Hz (wędruje o 18,8 %), silna linia 133 Hz
  jest dwuznaczna (k = 2 czy 3) i `el_verify` dał FAIL tonu > 4 %. Stabilność widma według GPT to nie to samo co
  użyteczna linia do strojenia.

## 3. Zdarzenia i C–G

GPT zaleca regenerację/odsłuch dla: TURBO_SPOOL (zgoda, R3), GEAR_UPSHIFT_CAB, BRAKE_SERVICE_HISS, CAB_DOOR_OPEN,
CAB_WIPERS_LOOP, warunkowo CAB_INDICATOR_LOOP. Pliki C–G nie są wpięte w 0137, więc dopisuję je do
`docs/owner/ELEVENLABS-REGEN-01.md` (sekcja R6) na podstawie dowodów GPT. Moje metryki ich nie podważają: brak
przesterowania, szwy pętli < 1, poza `REVERSE_BEEPER_LOOP (4)` (GPT wybiera v2 — zgoda). Kierunkowskaz ~3 kliknięcia/s
to tik + tok przy 1,5 cyklu/s, czyli zgodnie z promptem; gra i tak używa przekaźnika zsynchronizowanego z lampami
(osobne tik/tok). Opóźnione ataki (CAB_SWITCH 0,15 s, CAB_DOOR_OPEN 0,92 s, SUSP_BUMP 0,47 s) obcina `trim_silence`
w `el_prepare.py` przy wpinaniu, więc nie ma potrzeby regeneracji tylko z tego powodu.

## 4. Tabela ID po ID

„Mój wybór” dla pętli silnika = które warianty danego ID grają w których komórkach siatki (`ext_on_1500` itd.).
| ID | GPT wybór (ranking) / status | Mój wybór / użycie w grze | Zgodność i powód |
|---|---|---|---|
| `ENG_CAB_OFF_1200` | v3 (3,1,2,4) — umiarkowane wahania tonu | v3: cab_off_0600; v4: cab_off_1800, cab_off_2100 · zmierzone obr/min: v1 702, v2 728, v3 808, v4 1426 | ten sam wariant używany; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_CAB_OFF_1500` | v1 (1,2,3,4) — wynik niejednoznaczny | nieużyty bezpośrednio · zmierzone obr/min: v1 1002, v2 2646, v3 2791, v4 2117 | ID nieużyty: żaden wariant nie wygrał rankingu (ton/stabilność/przestrojenie) dla żadnej komórki; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_CAB_OFF_1800` | v3 (3,2,4,1) — wynik niejednoznaczny | v3: cab_off_1200, cab_off_1500 · zmierzone obr/min: v1 1778, v2 1297, v3 1218, v4 2667 | ten sam wariant używany; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_CAB_OFF_2100` | v4 (4,2,3,1) — stabilny w granicach pomiaru | v2: cab_off_0900 · zmierzone obr/min: v1 1378, v2 1045, v3 1372, v4 2934 | inny wariant: siatkę układam po zmierzonym tonie z całej puli perspektywy/obciążenia, nie po ID; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_CAB_OFF_600` | v2 (2,1,4,3) — wynik niejednoznaczny | nieużyty bezpośrednio · zmierzone obr/min: v1 717, v2 878, v3 2421, v4 888 | ID nieużyty: żaden wariant nie wygrał rankingu (ton/stabilność/przestrojenie) dla żadnej komórki; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_CAB_OFF_900` | v4 (4,3,2,1) — stabilny w granicach pomiaru | nieużyty bezpośrednio · zmierzone obr/min: v1 1540, v2 798, v3 891, v4 1008 | ID nieużyty: żaden wariant nie wygrał rankingu (ton/stabilność/przestrojenie) dla żadnej komórki; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_CAB_ON_1200` | v1 (1,4,3,2) — stabilny w granicach pomiaru | v1: cab_on_0600, cab_on_0900 · zmierzone obr/min: v1 887, v2 1114, v3 2774, v4 1164 | ten sam wariant używany; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_CAB_ON_1500` | v2 (2,3,4,1) — wynik niejednoznaczny | v3: cab_on_1200 · zmierzone obr/min: v1 868, v2 1162, v3 1220, v4 833 | inny wariant: siatkę układam po zmierzonym tonie z całej puli perspektywy/obciążenia, nie po ID; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_CAB_ON_1800` | v4 (4,3,2,1) — stabilny w granicach pomiaru | v4: cab_on_1800 · zmierzone obr/min: v1 767, v2 1236, v3 1001, v4 1300 | ten sam wariant używany; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_CAB_ON_2100` | v4 (4,2,1,3) — stabilny w granicach pomiaru | v4: cab_on_1500, cab_on_2100 · zmierzone obr/min: v1 796, v2 1089, v3 1413, v4 1449 | ten sam wariant używany; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_CAB_ON_600` | v1 (1,3,4,2) — wynik niejednoznaczny | nieużyty bezpośrednio · zmierzone obr/min: v1 1284, v2 825, v3 835, v4 928 | ID nieużyty: żaden wariant nie wygrał rankingu (ton/stabilność/przestrojenie) dla żadnej komórki; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_CAB_ON_900` | v2 (2,1,3,4) — umiarkowane wahania tonu | nieużyty bezpośrednio · zmierzone obr/min: v1 813, v2 2233, v3 1181, v4 853 | ID nieużyty: żaden wariant nie wygrał rankingu (ton/stabilność/przestrojenie) dla żadnej komórki; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_EXT_OFF_1200` | v2 (2,3,4,1) — stabilny w granicach pomiaru | nieużyty bezpośrednio · zmierzone obr/min: v1 508, v2 1238, v3 1026, v4 956 | ID nieużyty: żaden wariant nie wygrał rankingu (ton/stabilność/przestrojenie) dla żadnej komórki; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_EXT_OFF_1500` | v3 (3,1,4,2) — stabilny w granicach pomiaru | v3: ext_off_0900, ext_off_1500; v4: ext_off_0600, ext_off_1200 · zmierzone obr/min: v1 893, v2 986, v3 933, v4 883 | ten sam wariant używany; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_EXT_OFF_1800` | v4 (4,1,2,3) — stabilny w granicach pomiaru | nieużyty bezpośrednio · zmierzone obr/min: v1 2763, v2 926, v3 939, v4 881 | ID nieużyty: żaden wariant nie wygrał rankingu (ton/stabilność/przestrojenie) dla żadnej komórki; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_EXT_OFF_2100` | v3 (3,4,2,1) — stabilny w granicach pomiaru | nieużyty bezpośrednio · zmierzone obr/min: v1 966, v2 866, v3 884, v4 892 | ID nieużyty: żaden wariant nie wygrał rankingu (ton/stabilność/przestrojenie) dla żadnej komórki; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_EXT_OFF_600` | v2 (2,4,3,1) — stabilny w granicach pomiaru | nieużyty bezpośrednio · zmierzone obr/min: v1 961, v2 1004, v3 879, v4 872 | ID nieużyty: żaden wariant nie wygrał rankingu (ton/stabilność/przestrojenie) dla żadnej komórki; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_EXT_OFF_900` | v3 (3,1,2,4) — stabilny w granicach pomiaru | v4: ext_off_1800, ext_off_2100 · zmierzone obr/min: v1 928, v2 2490, v3 1290, v4 1108 | inny wariant: siatkę układam po zmierzonym tonie z całej puli perspektywy/obciążenia, nie po ID; drabina R6 przy obrotach z promptu ≥3/6: 1/4 |
| `ENG_EXT_ON_1200` | v2 (2,4,3,1) — wynik niejednoznaczny | v4: ext_on_1200, ext_on_1800 · zmierzone obr/min: v1 1258, v2 940, v3 951, v4 1195 | inny wariant: siatkę układam po zmierzonym tonie z całej puli perspektywy/obciążenia, nie po ID; drabina R6 przy obrotach z promptu ≥3/6: 1/4 |
| `ENG_EXT_ON_1500` | v4 (4,3,1,2) — stabilny w granicach pomiaru | nieużyty bezpośrednio · zmierzone obr/min: v1 1093, v2 989, v3 911, v4 2677 | ID nieużyty: żaden wariant nie wygrał rankingu (ton/stabilność/przestrojenie) dla żadnej komórki; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_EXT_ON_1800` | v4 (4,2,1,3) — stabilny w granicach pomiaru | nieużyty bezpośrednio · zmierzone obr/min: v1 1013, v2 1038, v3 1254, v4 1304 | ID nieużyty: żaden wariant nie wygrał rankingu (ton/stabilność/przestrojenie) dla żadnej komórki; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_EXT_ON_2100` | v4 (4,3,1,2) — stabilny w granicach pomiaru | nieużyty bezpośrednio · zmierzone obr/min: v1 912, v2 1024, v3 904, v4 948 | ID nieużyty: żaden wariant nie wygrał rankingu (ton/stabilność/przestrojenie) dla żadnej komórki; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_EXT_ON_600` | v3 (3,1,2,4) — stabilny w granicach pomiaru | v1: ext_on_0600, ext_on_0900 · zmierzone obr/min: v1 874, v2 924, v3 896, v4 848 | inny wariant: siatkę układam po zmierzonym tonie z całej puli perspektywy/obciążenia, nie po ID; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `ENG_EXT_ON_900` | v3 (3,1,2,4) — wynik niejednoznaczny | v3: ext_on_1500, ext_on_2100 · zmierzone obr/min: v1 1259, v2 863, v3 1315, v4 1034 | ten sam wariant używany; drabina R6 przy obrotach z promptu ≥3/6: 0/4 |
| `AIR_COMPRESSOR_LOOP` | v4 (4,1,3,2) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v4: -38.5 LUFS, szczyt -22.5 dBFS, szew 0.33 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `AIR_DRYER_PURGE` | v2 (2,1,4,3) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v2: -19.9 LUFS, szczyt -0.0 dBFS, szew 0.28 — UWAGA: szczyt -0.0 dBFS |
| `AIR_PARKING_APPLY` | v4 (4,2,1,3) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v4: -24.4 LUFS, szczyt -2.3 dBFS, szew 0.01 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `AIR_PARKING_RELEASE` | v4 (4,3,1,2) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v4: -16.6 LUFS, szczyt -1.6 dBFS, szew 0.11 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `AMB_INDUSTRIAL_DAY` | v1 (1,4,3,2) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v1: -44.3 LUFS, szczyt -27.2 dBFS, szew 0.52 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `AMB_PASSING_CAR` | v3 (3,2,1,4) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v3: -32.4 LUFS, szczyt -15.5 dBFS, szew 0.15 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `AMB_WIND_CAB_80` | v1 (1,4,2,3) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v1: -17.2 LUFS, szczyt -3.7 dBFS, szew 0.43 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `AMB_YARD_LOGISTICS` | v1 (1,2,4,3) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v1: -43.1 LUFS, szczyt -21.5 dBFS, szew 0.05 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `BRAKE_ROLL_LOOP` | v1 (1,2,3,4) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v1: -42.1 LUFS, szczyt -23.5 dBFS, szew 0.31 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `BRAKE_SERVICE_HISS` | v4 (4,3,2,1) — regeneracja / dokładny odsłuch | nie wpinałem (poza zakresem 0137) | moje metryki dla v4: -51.1 LUFS, szczyt -31.8 dBFS, szew 0.89 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `BRAKE_SQUEAL_STOP` | v1 (1,3,4,2) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v1: -47.7 LUFS, szczyt -26.1 dBFS, szew 0.05 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `CAB_DOOR_CLOSE` | v1 (1,3,4,2) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v1: -24.6 LUFS, szczyt -1.3 dBFS, szew 0.02 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `CAB_DOOR_OPEN` | v1 (1,2,4,3) — warunkowy / nowa generacja | nie wpinałem (poza zakresem 0137) | moje metryki dla v1: -34.5 LUFS, szczyt -5.8 dBFS, szew 0.04 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `CAB_INDICATOR_LOOP` | v3 (3,1,2,4) — warunkowy / nowa generacja | nie wpinałem (poza zakresem 0137) | moje metryki dla v3: -49.3 LUFS, szczyt -25.6 dBFS, szew 0.01 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `CAB_RAIN_ROOF_LOOP` | v3 (3,1,2,4) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v3: -39.5 LUFS, szczyt -20.3 dBFS, szew 0.50 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `CAB_SWITCH` | v2 (2,3,4,1) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v2: -24.5 LUFS, szczyt 0.0 dBFS, szew 0.01 — UWAGA: szczyt 0.0 dBFS |
| `CAB_WIPERS_LOOP` | v2 (2,4,3,1) — warunkowy / nowa generacja | nie wpinałem (poza zakresem 0137) | moje metryki dla v2: -28.4 LUFS, szczyt -7.0 dBFS, szew 0.09 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `ENG_IDLE_CLATTER` | v2 (2,1,3,4) — wybór roboczy | v2: idle_clatter_loop, idle_clatter_cab_loop | ten sam wariant — zgodnie |
| `ENG_START_CAB` | v1 (1,3,4,2) — wybór roboczy | v3: start_cab | inny — ja: v3 ma krótki ton ~5 kHz przy 2,4–3 s (sygnał z deski, o który prosił prompt); GPT go nie potwierdził i wybrał v1 — do odsłuchu |
| `ENG_START_EXT` | v3 (3,2,1,4) — wybór roboczy | v3: start_ext | ten sam wariant — zgodnie |
| `ENG_STOP_EXT` | v1 (1,4,2,3) — wybór roboczy | v3: stop_ext, stop_cab | inny — ja: v3 ma szerokopasmowe tyknięcia 1,7–2,3 s (prompt: „small metallic tick”); GPT nie potwierdził ticku w v1 — mój wybór właśnie z tego powodu |
| `EXHAUST_BRAKE_LOOP` | v4 (4,3,2,1) — wybór roboczy | v3: ebrake_ext_1000, ebrake_cab_1000, ebrake_ext_1400, ebrake_cab_1400, ebrake_ext_1800, ebrake_cab_1800, ebrake_ext_2200, ebrake_cab_2200 | inny — ja: v3 ma czystą drabinę 72,5/142,8/216,8 Hz (1443 obr/min) — potrzebna do strojenia siatki 1000–2200; v4 (GPT) ma rozproszone linie 82/86/95/129 Hz bez jednoznacznej podstawy |
| `GEARBOX_WHINE_LOOP` | v2 (2,4,1,3) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v2: -41.9 LUFS, szczyt -23.4 dBFS, szew 0.48 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `GEAR_DOWNSHIFT_CAB` | v3 (3,4,1,2) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v3: -33.5 LUFS, szczyt -5.8 dBFS, szew 0.00 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `GEAR_UPSHIFT_CAB` | v1 (1,4,2,3) — regeneracja / dokładny odsłuch | nie wpinałem (poza zakresem 0137) | moje metryki dla v1: -36.1 LUFS, szczyt -13.8 dBFS, szew 0.11 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `HORN_AIR` | v2 (2,1,4,3) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v2: -16.2 LUFS, szczyt -3.2 dBFS, szew 0.37 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `RETARDER_LOOP` | v4 (4,1,3,2) — wybór roboczy | v1: retarder_loop, retarder_cab_loop | inny — ja: v1 ma stałą linię ~4 kHz (wycie łopatek) + 124/186 Hz; GPT: v4 (632 Hz, mniejszy skok szwu). Szew i tak robiony od nowa — do odsłuchu |
| `REVERSE_BEEPER_LOOP` | v2 (2,3,4,1) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v2: -31.8 LUFS, szczyt -20.7 dBFS, szew 0.24 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `SUSP_BUMP` | v3 (3,4,1,2) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v3: -35.5 LUFS, szczyt -13.5 dBFS, szew 0.02 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `TRAILER_COUPLE` | v4 (4,2,1,3) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v4: -30.4 LUFS, szczyt -6.7 dBFS, szew 0.00 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `TRAILER_RATTLE_LOOP` | v4 (4,1,3,2) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v4: -41.8 LUFS, szczyt -18.2 dBFS, szew 0.02 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `TURBO_SPOOL` | v2 (2,4,1,3) — regeneracja / dokładny odsłuch | żaden | zgodnie: brak rosnącego gwizdu, przegenerować (REGEN-01 R3 jako pętla) |
| `TURBO_WASTEGATE` | v2 (2,4,1,3) — wybór roboczy | v4: turbo_wastegate, turbo_wastegate_cab | inny — ja: v4 ma pasma „flutter” po wyrzucie (prompt); GPT: v2 najczystszy wyrzut, flutter niepotwierdzony — do odsłuchu, różnica drugorzędna |
| `TYRE_ASPHALT_50` | v2 (2,4,3,1) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v2: -37.3 LUFS, szczyt -20.1 dBFS, szew 0.00 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `TYRE_ASPHALT_80` | v4 (4,3,2,1) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v4: -41.4 LUFS, szczyt -24.1 dBFS, szew 0.19 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `TYRE_GRAVEL_15` | v2 (2,1,3,4) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v2: -29.6 LUFS, szczyt -4.6 dBFS, szew 0.08 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `TYRE_PAVERS_20` | v2 (2,3,1,4) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v2: -40.8 LUFS, szczyt -11.8 dBFS, szew 0.01 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
| `TYRE_WET_60` | v4 (4,3,2,1) — wybór roboczy | nie wpinałem (poza zakresem 0137) | moje metryki dla v4: -43.9 LUFS, szczyt -26.9 dBFS, szew 0.11 — bez zastrzeżeń; przyjmuję wybór GPT do wpięcia |
