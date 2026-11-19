# ADR 0306 — Drogi szersze niż w realu (D94): +0,25 m/pas, poszerzenie na łukach, łuki wylotów ronda kompaktowego, kontrola toru zestawu 16,5 m

Status: Proposed (agent `road-widen-s24`, gałąź `road-widen-s24`), 2026-11-19. Decyzja właściciela **D94** (docs/11).
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
7. **Rondo kompaktowe — narożniki** między ramionami zamykane promieniem `TRUCK_CORNER_R_M = 12` m (było `NOSE_R_M` 4 m):
   naczepa ścinała krawężnik narożnika przy wlocie DK65 od Białegostoku; kształt zgodny ze zdjęciem drona nr 9.
8. Autorski `swing` łącznika `knyszyn-rynek-to-dk65-w` usunięty (po regule pogarszał: krawężnik 59 → 23 pkt bez niego).

## Wyniki
Tor zestawu (`qa/combo_lane_check.py`, oś przednia na środku pasa; punkty opon przeciwny pas / krawężnik / poza
nawierzchnią; „przed” = kafle main, `--widen 0`, `artifacts/road-widen-s24/before/final_swing.json`):

| odcinek | przed | po |
|---|---|---|
| rondo Knyszyn DK65 → DW671 W (korytarz Tykocin) | 0 / 23 / 5 | 0 / 3 / 0 (ze swingiem kierowcy 0 / 0 / 0) |
| rondo Knyszyn DK65 → DK65 W | 0 / 16 / 0 | 0 / 0 / 0 |
| Tykocin DW671 → Rynek | 109 / 0 / 0 | 7 / 0 / 0 (ze swingiem 0) |
| Rynek Knyszyn → rondo (2 łączniki) | 42–45 / 18–63 / 0 | 32–37 / 0–59 / 0 (przeciwny pas: skręty w ulicach Rynku) |
| kleeberga, dk65-05, knyszyn-s, knyszyn-w | 0 / 0 / 0 | 0 / 0 / 0 |

Rzut z góry przed / po: `artifacts/road-widen-s24/top/knyszyn_before_after_lc_960.jpg`; render High
`artifacts/road-widen-s24/top_vqa_after_vs_before.jpg` (narożniki ronda jak na zdjęciu drona nr 9).

## Konsekwencje
- Każdy kafel zmienia się przy najbliższej przebudowie (szersze pasy wszędzie, łuki); szwy zgodne dopiero, gdy obie strony
  są przebudowane tym samym kodem (seam_taper liczy sąsiada tym samym `network.load`).
- `route_start.json` każdego przebudowanego kafla trzeba wyeksportować ponownie (środek pasa przesuwa się o 0,125 m na
  pas), potem `streaming/route_links.py`.
- Testy mierzonych szerokości (ADR 0301, 0220, 0233 …) porównują z `GAMEPLAY_LANE_WIDEN_M = 0` albo z bazą + delta.

## Otwarte
(uzupełnione na końcu)
