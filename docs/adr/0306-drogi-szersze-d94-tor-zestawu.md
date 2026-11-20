# ADR 0306 — Drogi szersze niż w realu (D94): +0,25 m/pas, poszerzenie na łukach, łuki wylotów ronda kompaktowego, kontrola toru zestawu 16,5 m

Status: Proposed (agent `road-widen-s24`, gałąź `road-widen-s24`), 2026-11-19 / 20. Decyzja właściciela **D94** (docs/11).
Powiązane: ADR 0301 (pasy z ortofoto — baza), 0095 / 0077 (`lane_edges`, `center_offset`), 0233 (`lane_follow`),
0218 / 0274 / 0289 (rondo Knyszyn, tor naczepy), 0280 (pierścień 12,50/5,30, osie naczepy 6,32 / 7,63 / 8,94 m),
0300 (route_obstacles), PTB2022 (Dz.U. 2022 poz. 1518) § 17 ust. 5 i § 58 ust. 3.

## Kontekst
Właściciel (D94, 19.11): jezdnie mają być szersze niż w realu, „bo będzie ludziom ciężko”; przykład — wlot ronda
DK65/DW671 w Knyszynie wymusza lekki wjazd na przeciwny pas. Decyzja: **każdy pas +0,25 m** względem pomiaru
(ortofoto / OSM / BDOT, ADR 0301), **wloty / wyloty rond i skrzyżowań oraz łuki krawężników** tak, by zestaw 16,5 m
mieścił się bez wjazdu na przeciwny pas. Układ (liczba pasów, przebieg, położenie) bez zmian.

PTB2022 nie podaje wzoru poszerzenia na łuku ani promienia łuku krawężnika — tylko wymaganie wynikowe: pas na łuku
„powinien umożliwiać przejazd pojazdu miarodajnego” (§ 17 ust. 5), skrzyżowanie „umożliwiające przejazd pojazdu
miarodajnego bez utrudnień dla ruchu innych pojazdów” (§ 58 ust. 3); tekst przeczytany 2026-11-19 na
api.sejm.gov.pl/eli/acts/DU/2022/1518/text.html. Dlatego kryterium jest tor jazdy naszego zestawu, nie liczba z przepisu.

## Decyzja
Wszystko poniżej to **GAMEPLAY_WIDEN** (nie fakt pomiarowy), WORKING_VALUE.
1. **Jeden parametr** `roads/standards.py: GAMEPLAY_LANE_WIDEN_M = 0.25`, stosowany raz w `network.load` po wszystkich
   overrides (`network.gameplay_widen`): `lane_w` +0,25, `width` + liczba pasów × 0,25, zmierzone `lane_edges` (ADR
   0095/0301) — lewa opaska bez zmian, każdy pas +0,25; `width_profile` i autorskie `edge_line_spacing` + pasy × 0,25;
   `center_offset` bez zmian; ślad w `provenance.gameplay_widen_m`. Projektowany pas wlotu ronda kompaktowego
   (`lane_w_m`) też +0,25; pierścień jednopasowy Knyszyna 5,00 → 5,25 m. `GAMEPLAY_LANE_WIDEN_M = 0` daje przekroje
   zmierzone (QA z ortofoto, `combo_lane_check --widen 0`).
2. **Poszerzenie pasa na łuku** (`network.curve_widen`): dwukierunkowe 2-pasowe GP / G / Z bez `lane_edges`, łuki
   R < 200 m: pas ≥ 2,48 m (koła napędowe) + 2 × (offtracking + 0,10 m), offtracking ustalony zestawu
   `network.offtrack_ss(R)` (z `swept_path.Combination`, ≈ 40/R dla R ≥ 40 m — stara polska reguła), maks. 1,0 m/pas,
   rampa ~20 m, nie bliżej 15 m od węzła ≥ 3 ani 40 m od szwu kafla; sekcje dostają `lane_follow` (ADR 0233), więc oba
   pasy i oś rosną symetrycznie.
3. **Rondo kompaktowe** (`compact_roundabout`): łuki krawężników wlotu / wylotu co najmniej
   `TRUCK_ENTRY_R_MIN_M = 12` / `TRUCK_EXIT_R_MIN_M = 15` m (autorskie 6 / 8 m w Knyszynie podniesione regułą, notatka w
   raporcie ronda); zdjęcie drona właściciela nr 9 pokazuje tam szerokie łuki — kierunek zgodny z rzeczywistością.
4. **Kontrola toru zestawu** `tools/worldgen/qa/combo_lane_check.py` (+ `qa/combo_topview.py`): dla każdego kafla
   korytarzy z `route_links.json` (trasa kafla / łącznik, ostatnie 45 m poprzedniego kafla doklejone) i każdego łącznika
   (ronda Knyszyna) oś przednia na środku pasa, tractrix ciągnika i naczepy (model ADR 0218/0280), krawędzie opon co 1 m
   klasyfikowane po **najwyższym** trójkącie zbudowanego kafla: `opposite` (za osią jezdni dwukierunkowej o > 0,10 m,
   pojazd wzdłuż drogi, poza wylotami skrzyżowań), `kerb` (krawężnik / chodnik / pobocze), `apron` (dozwolony fartuch
   ronda), `off_hard` (trawa, wyspa). Opcja `--swing`: najlepszy „swing” kierowcy (przesunięcie toru w obrębie własnego
   pasa / skrzyżowania, ten sam kształt co autorskie `swing` łączników) — przyjmowany tylko, gdy poprawia całą trasę.
   `KAMION_DATA_ROOT` = inny checkout (np. main dla „przed”). Powierzchnia klasyfikowana na poziomie jezdni pod osią
   przednią (wiadukt nad trasą / droga pod wiaduktem to inny poziom, `LAYER_M` 2 m) — bez tego Kleeberga pod wiaduktem
   dawała 663 / 347 fałszywych punktów.
5. **Jezdnia jednokierunkowa rośnie w prawo** (`network.gameplay_widen`): środek przesuwa się w prawo o połowę wzrostu
   D94, najwyżej `GROW_RIGHT_MAX_M` 0,5 m; profil położenia z ortofoto (ADR 0095) zostaje symetryczny. **Podłoga BDOT
   ADR 0301 zaliczana do D94**: pasy, które ADR 0301 już poszerzył ponad BDOT o ≥ 0,25 m, nie rosną dalej (DK8 w C).
   Wersje pośrednie (C, fidelity wyspy „absent_on_ortho” przy trasie; main 1): symetrycznie 4, całe w prawo 2 (ale
   marking_off 6 — jezdnia na chodnikach / wiadukcie), w prawo ≤ 0,5 m 3.
6. **L / D**: górny limit pasa z BDOT z powrotem std + 0,25 (L 3,00; ADR 0301 dał 3,50), klasa D (service, living_street)
   w ogóle bez szerokości BDOT (standard klasy): BDOT liczy zatoki i podjazdy, kolejne krawędzie jednej drogi wychodziły
   5,5 / 6,5 / 7,0 m, a tory pasów przez skrzyżowania wpadały na krawężniki (C: lane_blind_end 54 → 57 po ADR 0301).
7. **Rondo kompaktowe — narożniki** między ramionami zamykane promieniem `TRUCK_CORNER_R_M = 16` m (było `NOSE_R_M` 4 m):
   przy 4 m naczepa ścinała krawężnik narożnika SE przy wlocie DK65 od Białegostoku, przy 12 m nadal na trasie kontrolnej
   DK65 S → Tykocka E (przejazd playerem 19.11: naczepa 2,4 s na krawężniku; combo_lane_check 53 pkt). Kształt bliższy
   zdjęciu drona nr 9 (szerokie łuki).
9. **Testy GIS na geometrii zmierzonej**: `tests/gis/conftest.py` ustawia `GAMEPLAY_LANE_WIDEN_M = 0` na całą sesję
   (testy porównują generator z pomiarem / autorskimi wartościami); reguły D94 testuje `test_road_widen_0306.py`
   (ustawia 0,25). Domyślna wartość generatora: `GAMEPLAY_LANE_WIDEN_DEFAULT_M = 0.25`.
8. Autorski `swing` łącznika `knyszyn-rynek-to-dk65-w` usunięty (po regule pogarszał: krawężnik 59 → 23 pkt bez niego).

## Wyniki
Tor zestawu (`qa/combo_lane_check.py`, oś przednia na środku pasa; punkty opon przeciwny pas / krawężnik / poza
nawierzchnią; „przed” = kafle main, `--widen 0`, `artifacts/road-widen-s24/before/final_swing.json`):

| odcinek | przed | po |
|---|---|---|
| rondo Knyszyn DK65 → DW671 W (korytarz Tykocin) | 0 / 23 / 5 | 0 / 5 / 0 (ze swingiem kierowcy 0 / 0 / 0) |
| rondo Knyszyn DK65 → DK65 W | 0 / 16 / 0 | 0 / 0 / 0 |
| trasa kontrolna knyszyn (DK65 S → Tykocka E, 1. zjazd) | 0 / 80 / 0 (12 m: 53 na narożniku SE) | 0 / 56 / 0 (29 na rondzie; ze swingiem 0) |
| Tykocin DW671 → Rynek | 109 / 0 / 0 | 7 / 0 / 0 (ze swingiem 0) |
| Rynek Knyszyn → rondo (2 łączniki) | 42–45 / 18–63 / 0 | 29–33 / 0 / 0 (przeciwny pas: skręty w ulicach Rynku) |
| kleeberga, dk65-05, knyszyn-s, knyszyn-w | 0 / 0 / 0 | 0 / 0 / 0 |

Przejazd playerem (build Windows, GTX 1070 High 60 fps, `-stream 1 -route_to tykocin -telemetry 1`, 20.11): łącznik
DK65 → DW671 W przez rondo (lewo 275°, 30 km/h): w promieniu 45 m od środka ronda ciągnik i prawe koła naczepy cały czas na
asfalcie, ciągnik ≤ 0,85 m od linii łącznika, lewe koła naczepy 5,8 s na fartuchu (kostka, zaprojektowany), 0 wyjątków.
Przejazd trasą kontrolną przy narożnikach 12 m: naczepa 2,4 s na krawężniku narożnika SE → narożniki 16 m (r8).
Rzut z góry przed / po: `artifacts/road-widen-s24/top/knyszyn_before_after_lc_960.jpg`; render High
`artifacts/road-widen-s24/top_vqa_after_vs_before.jpg` (narożniki ronda jak na zdjęciu drona nr 9).

## Konsekwencje
- Każdy kafel zmienia się przy najbliższej przebudowie (szersze pasy wszędzie, łuki); szwy zgodne dopiero, gdy obie strony
  są przebudowane tym samym kodem (seam_taper liczy sąsiada tym samym `network.load`).
- `route_start.json` każdego przebudowanego kafla trzeba wyeksportować ponownie (środek pasa przesuwa się o 0,125 m na
  pas), potem `streaming/route_links.py`.
- Testy mierzonych szerokości (ADR 0301, 0220, 0233 …) porównują z `GAMEPLAY_LANE_WIDEN_M = 0` albo z bazą + delta.

## Kafel C (CI lidera po ADR 0301)
road_consistency (r6): lane_blind_end 44 (ratchet 55; main 57), marking_off_carriageway 3 (3; main 4), obstacle_in_lane 2
(2), arrow_no_exit 8 (8; main 7) — w ratchetach. Na trasie 2 (ROUTE_MAX 1; main 3): pętla parkingu w435369082 (E -208
N -287, przy trasie od ADR 0301) + znana brama zajezdni. fidelity: wyspy „absent_on_ortho” przy trasie r6 3 (main 1),
edge p95 1,33 m (main 2,09). r7 (obecny kod: podłoga BDOT zaliczana do D94): wyspy 1 (= main), edge p95 1,63 m, ale
lane_blind_end 45, marking_off 6, obstacle 3, na trasie 3 — oba warianty łamią część ratchetów; wybór dla lidera.

## Testy
pytest `tests/gis/test_road_widen_0306.py` 12, 0274 / 0301 / lane_edges zielone; pełne `tests/gis` (19.11, przed
przejściem suite na geometrię zmierzoną) 64 / 2570 czerwone, powtórka 64 po zmianie: 15 — kafle przebudowane w worktree
obok nieprzebudowanych sąsiadów (szwy, łącznik jeroniki), katalog regionów (fala w main), zebry / ściany terenu / most w C,
wyspy i trasa C (wyżej). EditMode Win64 (20.11): 1329 / 1 — `RegionSelectTests` katalog routeLengthM (fala w main).

## Otwarte
- Wyspy fidelity C i pętla parkingu przy trasie (powyżej) — jeśli r7 nie zamknie, reguła „rośnij od sąsiedniej jezdni”
  (geometria, po zbudowaniu łańcuchów) zamiast stałego „w prawo”.
- Łączniki z Rynku Knyszyna: skręty w ulicach Rynku przechodzą przez oś (32–37 pkt) — narożniki L/D bez reguły D94
  (wierność zabudowy).
- Po przebudowie C w main: złote trasy nawigacji (`dotnet run -c Release --project tools/nav-runner/Runner -- --write-golden`,
  EditMode `Nav0168Tests.Exit_GoldenRoutes` 5 vs 4 manewry) i katalog regionów (`scripts/export-region-catalog.py`).
- Recenzja `visual-critic` renderów Knyszyna — do zlecenia przez lidera.

## Decyzja właściciela 20.11 — właściwa poprawka (G1, walidacja w toku)
Stałe „w prawo” zastępuje geometria nieposzerzonych jezdni: odległości krawędzi do równoległych dróg po obu stronach,
wliczając drogi parkingowe i serwisowe na tym samym poziomie. Wzrost idzie od bliższego sąsiada; istniejąca szczelina
w odległości do 12 m jest rezerwowana w całości (WORKING_VALUE, nie pomiar ortofoto). Przy braku miejsca po obu
stronach sekcja dostaje mniejsze poszerzenie, zapisane w provenance. Bez sąsiadów wzrost symetryczny.
Snapshot przed mutacjami zapewnia niezależność od kolejności i chroni szczelinę również między dwiema rosnącymi jezdniami.
Reguła obejmuje profile położenia z ortofoto. Podłoga BDOT nie zastępuje już GAMEPLAY (punkt 5 historyczny).

### Parking w435369082 (G2)
Przyczyna niezależna od przesunięcia jezdni: wyszukiwanie przecięcia krawędzi i wyrównanie nosa separatora sięgało
za zakręt pętli serwisowej, dając przycięcia ramion 40,44 / 81,57 m i krawężnik na przejeździe.
Klasa D kończy wyszukiwanie i przycięcie przed pierwszym odchyleniem stycznej o >45° (WORKING_VALUE).
Odcinek za zakrętem pozostaje wstęgą drogi; nos jest lokalny. Przycięcia wynoszą 13,15 / 13,00 m.
Plan na ortofoto GUGiK HR sprawdzony, bez Unity. Regresja wymaga poprawnego poligonu i przejezdnego starego punktu błędu.

### Wspólny budżet (G3, po niezależnej recenzji)
Planowanie obejmuje także drogi dwukierunkowe obok drogi głównej. Nadwyżka szczeliny ponad rezerwę jest dzielona
po połowie między obu sąsiadów; nie wolno wydać jej dwukrotnie. Porównanie używa lokalnych width_profile
oraz center_offset_profile. Jedynie topologicznie wspólna, nakładająca się nawierzchnia skrzyżowania jest pomijana.

### Pierwszy pełny pomiar geometrii (G1 C, 20.11 10:21)
marking_off_carriageway 6→0; obstacle_in_lane 3→2; lane_blind_end 45→46 (limit55); na trasie3→2.
Stary punkt krawężnika parkingu zniknął, ale przejazd przeciwny przez scalone dwa T jest nadal błędny (None,
E -210,68 N -279,71). Wariant diagnostyczny z zachowaniem dwóch osobnych węzłów lepiej odtwarza obrys z ortofoto.
Fidelity i kontrola Knyszyna w toku; bramki nie są jeszcze zamknięte.

### Ponowny pomiar położenia DK8 (diagnoza przed G2)
Starszy `dk8-placement-b` ustawia centrum w238861874 0,55 m w prawo od OSM na podstawie niskiej pewności pomiaru
krawędzi. Pomiar białych linii na GUGiK HR istniejącym ortho_lane_fit, po dopuszczeniu ponownego pomiaru samych
center-only overrides, daje 17/29 użytecznych profili, 2 pasy we wszystkich 17, MAD granic 0,09/0,05/0,10 m i
centrum +0,02 m. Profile N180/220/260 obejrzane, niezależny przegląd PASS (`dk8-placement-strips.png`).
Plan G2: skorygować sam pomiar centrum; nie przepisywać wykrytych szerokości ani liczby pasów z całego fit.
Reprodukcja diagnostyczna (bez zapisu danych): `uv run --project tools/worldgen python -c "import sys;
sys.path.insert(0,'tools/worldgen/qa'); import ortho_lane_fit as F; F.LANE_KEYS=('lane_edges','lanes','width','lane_width');
F.fit(['bialystok-industrial-c'],step=10,out='artifacts/road-widen-s24/fit-placement-diagnostic',dry=True)"`.

### G2 — dwa lokalne T i korekta pomiaru centrum
Zachowujemy dwa osobne skrzyżowania serwisowe, jeśli całe aktualne grupy składają się wyłącznie z klasy D,
nie zawierają pierścienia/compact i dzieli je fizycznie ≥2 szerokości jezdni (WORKING_VALUE). Sprawdzamy wszystkie
węzły grup, także wcześniej wchłonięte; odległość euklidesowa wyklucza zakręcony łącznik wracający obok siebie.
Finalny solver dzieli krótki łącznik między dwa lokalne łuki. Ten mechanizm usuwa długi skrót Hermite'a przez parking.
Wprowadzono osobno zweryfikowaną korektę dk8-placement-b -0,55→+0,02 m. Szerokość i liczba pasów pozostają te same.
Równe dostępne luzy po obu stronach zachowują centrum. Ratchety bez zmian.

### Sprostowanie identyfikacji krawędzi (G2b)
Wcześniejsza identyfikacja dk8-placement-b jako krawędzi przy wyspie N219 była błędna. w238861874 zaczyna się na
N335,85; projekcja prób N180/220/260 zatrzymywała się na końcu tej krawędzi. Opisy tych próbek i decyzja zmiany b
są WYCOFANE; b wraca do -0,55. To błąd diagnostyki, nie generatora. Kolejny skrypt kontroluje zakres i podpisuje
rzeczywistą stację. Preview z błędnym wyborem nie rozpoczął generacji (czekał w kolejce).
Właściwy odcinek to w882366266 N146,58..335,85, override dk8-placement-a. Fitter: 9/15 profili, 2 pasy we wszystkich9,
MAD0,07/0,07/0,05m, centrum -0,18m zamiast -0,50. Profile z rzeczywistych N180,001/219,979/260,008 pokazują linię
między pasami -0,30/-0,10/-0,05m od OSM. Korygujemy tylko położenie a; szerokość i liczba pasów nie zmieniają się.
Dowód zastępujący błędny rzut: `artifacts/road-widen-s24/dk8-correct-edge-strips.png`.

### Podgląd G2b przed pełną przebudową
Na tej samej referencji sheet0,25m2024 główny komponent DK8 zmienia się absent→partial (udział drogi0,706→0,482;
powierzchnia545,4→508,9m²). Pozostały mały absent przyN120 jest27m od trasy. Obejrzane oba rzuty DK8 i parkingu:
zachowany rzeczywisty separator oraz dwa lokalne T. Bez zmian klasyfikatora, źródła referencji i ratchetów.
Pełna przebudowa i ponowne QA nadal wymagane.

### G3 — pełna ochrona medianu i poprawna domena próbkowania QA
Wybieramy najbliższą równoległą jezdnię osobno na każdej stronie/stacji PRZED zastosowaniem reguły separatora.
Kandydat z obwiedni STRtree musi spełniać również faktyczny dystans≤40m; sam obrys długiego zakrętu nie dowodzi
bliskości jezdni. Przeciwbieżne oneway (bez pierścieni rond) rezerwują CAŁY bazowy median, także >12m. Dla innych
sąsiadów nadal chroniona jest bliska szczelina, a nadwyżka ponad12m dzielona na pół. 12m nie jest pomiarem ortofoto.
Dla parkingu pozostający błąd nie był zamknięciem asfaltu: trim8,911+3=11,911m przekraczał L10,745m krótkiego ramienia.
Polyline klipował środek do końca, a normalna Hermite'a wypychała skrajną próbkę poza cap. QA ogranicza target do
istniejącej drogi z marginesem1m (WORKING_VALUE wobec maks.0,9m skrajnej próbki), zachowując look-ahead3m na długich
ramionach. Jedna target_s jest używana w fan_l, wyborze pasa, q_end/c_out/q1/z1. Nie zmieniamy geometrii tylko pod
błędny cel QA, nie pomijamy przypadku i nie zmieniamy klasyfikatora ani ratchetów. Test na rzeczywistych trójkątach
obejmuje krótkie zakrzywione i długie ramię, bez przeszkody i z prawdziwym krawężnikiem: falseNone znika, kerb zostaje.
Dodatkowe regresje: median20m z blokadą parkingową pozostaje20m (przed19m), bliższy sąsiad przed dalszym przeciwnym,
odległa droga z nakładającą się obwiednią nie przesuwa jezdni. 10 nowych testów PASS. Pełne G3 QA w toku.
