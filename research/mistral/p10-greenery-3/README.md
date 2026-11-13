# M51 — p10-greenery-3: zieleń ulic osiedla przy Al. Tysiąclecia (Białystok)

Kontynuacja: `research/g7-street-greenery/` (G7) i `research/gptpro/p10-street-greenery-2/` (P10-2).
Gałąź: `research/mistral-p10-greenery-3` (od najnowszego `main`). Id wpisów: `M51-NNN`.
Autor: Vibe (GLM), data dostępu źródeł: 2026-11-13, raport po polsku.

## Zakres i wyniki w skrócie

| Zadanie | Wynik | Status |
|---|---|---|
| 1. Letnie zdjęcia (VI–VIII) 9 ulic | 18 kadrów (M51-101…118) dla **Skidelskiej (7), Wileńskiej (4), Łańcuckiej (7)** z datą i azymutem; Skidelska i Świsłocka „bez zdjęcia" → **Skidelska ma dziś 7 letnich kadrów**; Świsłocka — potwierdzony brak | częściowo (6 ulic bez letnich street-level — patrz Luki) |
| 2. Żywopłoty ≥ 20 odcinków | **18 nowych letnich odcinków** (M51-201…218) z gatunkiem i wysokością ESTIMATED; razem z 12 wiosennymi odcinkami G7-P01…P12 → 30 odcinków przy ulicach zadania | −2 do progu (limit analizy obrazu 20/odpowiedź; kadry przygotowane do dokończenia) |
| 3. Detekcja koron kafla [776971, 595199, 779019, 597247] | `crowns.geojson` — **5259 koron** (2520 iglaste / 2739 liściaste), skrypt `tools/detect_crowns.py`, porównanie `comparison_p10.json` + `street_agg.json` | gotowe |
| 4. Projekt zieleni Al. Tysiąclecia (Strabag 2021/22) | Dane przetargowe i nasadzenia **SOURCED** (74 drzewa, 109 krzewów, 20 600 m² trawników, ~385 mb ekranów); **gatunki/obwody/rozstaw — UNVERIFIED** (dokumentacja projektowa nieopublikowana; SIWZ i RDOŚ to skany) | częściowo — zgodnie z „jeśli dostępne" |

## Zadanie 1 — letnie zdjęcia ulic osiedla

**Kryteria:** lato VI–VIII (liście), ≥ 2 kadry/ulica, data + azymut, WGS84 (6 miejsc), sezon i pora_dnia obowiązkowe, JPG ≤ 1600 px.

**Źródła odpytane (bez Google):** Panoramax (bbox osiedla: **0 kadrów** — potwierdzone `https://api.panoramax.xyz/api/search?bbox=23.147,53.148,23.156,23.158`), KartaView (POST `api.kartaview.org/1.0/list/nearby-photos/`; 664 pkt / 513 kadrów w buforze 450 m; na osiach 9 ulic **0 kadrów**, jedynie aleja/Andersa), Wikimedia Commons (geosearch 500 plików w r=1,2 km; wygrano serie), Openverse (bez trafień dla nazw ulic), Mapillary — **nie odpytano** (brak tokenu; nie zgadywano kluczy).

**Kluczowa seria: 25.07.2022, Rakoon, CC0** — spacer aleją 12:39–13:28 (54 kadry pobrane, 1920→1600 px). Pozycje = geotagi Commons; **Commons nie ma GPSImgDirection** → azymut **ESTIMATED**: kierunek od geotagu do najbliższego punktu osi ulicy (`roads.graph.json`), treść kadru zgodna z azymutem, ±30°, metoda w kolumnie `metoda` każdego wiersza manifestu.

- **Skidelska (M51-101…108, 7 kadrów):** wlot ul. Skidelskiej z alei (8–137 m od osi): domki jednorodzinne, niskie żywopłoty 0,5–1 m, młode palikowane drzewka (nasadzenia Strabag 2022), ekrany akustyczne, stacja Shell. **Luka zdjęciowa Skidelska zamknięta** (wcześniej: 0 zdjęć).
- **Wileńska (M51-109…112, 4 kadry):** wlot 30–53 m od osi: żywotniki 1,5–2 m, iglaki 10–15 m za nimi, krzyż przydrożny; wysoki żywopłot liściasty 2–2,5 m; strefa bloków.
- **Łańcucka (M51-113…118, 7 kadrów):** wlot z sygnalizacją; żywopłoty liściaste 1,2–1,5 m przy chodniku + ekran akustyczny (2020-07-11, CC BY 3.0 — referencja); 2021-06-08 — stan **przed przebudową** (parkowane auta, nowy blok, brak zieleni przyulicznej); 2023/2024 — stan po: żywotnik 1,2–1,5 m, młode palikowane nasadzenia, wysoki żywopłot liściasty ~2 m, czerwony przystanek.
- **Kowieńska, Lidzka, Wołkowyska, Grodzieńska, Racławicka:** w Panoramax/KartaView/Commons/Openverse **brak letnich zdjęć z poziomu ulicy** (Commons: 0 letnich w promieniu 450 m od osi; KartaView: sekwencja przy wlotach z 2018-03-23 jest marcowa i niedostępna — patrz Luki). Uzupełnienie z jedynego dostępnego street-level: **G7 (IV 2024, wiosna, CC0)** — kadry `g7-photo-01…12.jpg` w `research/g7-street-greenery/files/` (bez dublowania — patrz G7 manifest).
- **Świsłocka:** brak jakiegokolwiek zdjęcia z poziomu ulicy (wszystkie źródła odpytane; potwierdzona luka).
- **KartaView — sekwencja 1155711 (23.03.2018, heading SOURCED):** 142 kadry 5–140 m od wlotów wszystkich 9 ulic (metadane: `kv_wloty_test.json` w ZIP; azymuty z API — jedyne źródło z azymutem SOURCED dla wlotów). Serwer `storage7.openstreetcam.org` zwraca **HTTP 502** (test 2026-11-13 14:45 UTC, dwukrotnie) — obrazy niepobrane; dokumentacja: outage.

## Zadanie 2 — żywopłoty (≥ 20 odcinków)

**Definicja odcinka:** front jednej posesji (lub jedna strona kadru) widoczny w konkretnym zdjęciu; **odczyt wizualny** (analiza obrazu: Vibe `analyze_image`, 24 kadry przeanalizowane 2026-11-13), wysokość **ESTIMATED ±0,3–0,5 m** — odniesienie do ogrodzenia/furtki (płot drewniany/metalowy 1,2–1,5 m; siatka 1,5 m; porównanie w kolumnie `metoda`).

Wynik — **18 letnich odcinków** (M51-201…218):

| ulica | odcinki | gatunki | wysokości |
|---|---|---|---|
| Skidelska (wlot) | 10 | liściaste ×9, tuja/żywotnik ×1 | 0,5–2,0 m (mediany ~1,2–1,5 m) |
| Wileńska | 4 | żywotnik ×3 (1,5–2 m), liściasty 2–2,5 m ×1 | 1,5–2,5 m |
| Łańcucka/aleja | 4 | liściaste ×3 (1,2–2,2 m), żywotnik ×1 (1,2–1,5 m) | 1,2–2,2 m |

Razem z **G7-P01…P12** (wiosna 2024, te same ulice: Wołkowyska, Kowieńska, Grodzieńska, Wileńska, Lidzka, Racławicka, Łańcucka — 12 odcinków, ESTIMATED wg tej samej metody) daje **30 odcinków przy ulicach zadania**. Nowe odcinki M51 nie dublują G7 (inne daty, pory roku i pozycje).

**Braki i droga do progu ≥ 20:** analizę obrazu ogranicza limit 20 wywołań na odpowiedź (wyczerpany: 24 kadrów odczytane). Do dokończenia pozostały 2+ odcinki z przygotowanych kadrów: `files/c_20240626_103406/7/14.jpg`, `files/c_20230729_105303.jpg` (Łańcucka, lato) oraz 12 letnich kadrów KartaView przy alei (heading SOURCED) — `files/kv_*_summer_*.jpg`.

## Zadanie 3 — odtwarzalna detekcja koron (cały kafel)

- **Dane:** ortofotomapa GUGiK 2024-05-27, GSD 0,25 m, RGB, WMS `StandardResolution` (CC BY 4.0); kafel zadania [776971, 595199, 779019, 597247] (EPSG:2180) = 2048×2048 m; pobrano 4 kafle 1024×1024 m (4096×4096 px każdy), z 8-metrowym marginesem między kaflami.
- **Skrypt:** `tools/detect_crowns.py` (odtwarzalny: pobiera kafle → maska → korony → GeoJSON). Transformacja EPSG:2180↔WGS84: `tools/tm2180.py` (walidacja roundtrip < 1e-8°).
- **Metoda (krok po kroku):** (1) GetMap WMS 1.3.0, CRS=EPSG:2180; (2) maska roślinności ExG = 2g−r−b > 0,12 AND G > 60 (usuwa cienie); (3) opening 3×3, closing 5×5; (4) `scipy.ndimage.label`; (5) filtr r = sqrt(A·GSD²/π) ∈ [0,7, 6,5] m; (6) klasyfikacja iglaste/liściaste: V=(R+G+B)/3 < 85 (ciemna zieleń) LUB std(V) < 4 (gładka faktura) → iglaste, inaczej liściaste (**ESTIMATED** — jasne odmiany tuji mogą wypaść jako liściaste); (7) centroid → WGS84 (6 miejsc).
- **Wynik:** `crowns.geojson` — **5259 koron** (2520 iglaste, 2739 liściaste), r 0,71–6,49 m (mediana 1,15 m), 738 KB (< 5 MB, bez ZIP-a). Agregacja per ulica (bufor 8 m od osi): `street_agg.json`.
- **Porównanie z P10-201…237 (n=37, `comparison_p10.json`):** okna zgodne (|Δ pokrycia| ≤ 15 p.p.): **9/37**; mediana Δ = **−47 p.p.**; spadki > 30 p.p.: 22/37; suma koron P10=445 vs M51=94. Przyczyny różnic: (a) M51 wymaga jasnej, zwartej zieleni — młode korony < 0,7 m i częściowo przycięte krzewy wypadają; (b) pokrycie P10-2 liczone szerzej (trawniki/krzewy w buforze 8 m); (c) okna P10 nakładają się na siebie (podwójne liczenie koron), M51 liczy centroidy jednorazowo.
- **Porównanie z P10-301…313 (n=13, aleja/Andersa, młode drzewa r 0,7–2,0 w buforze 20 m):** okna bez młodych w P10 (305, 312) mają też 0 w M51 (spójność); największe różnice: P10-301 (0→6), P10-309 (18→2), P10-312 (6→0) — młode nasadzenia 2021/22 częściowo poniżej progu detekcji albo w oknach, gdzie P10-2 liczył również krzewy (109 krzewów nie odróżnia się od drzew w ortofoto — jak odnotowano w P10-2).

## Zadanie 4 — projekt zieleni Al. Tysiąclecia (Strabag 2021/22)

**SOURCED (karta postępowania BIP UM Białystok, 2026-11-13):**
- Postępowanie **ZDM-X.271.16.2018.JZ**, „Rozbudowa Alei Tysiąclecia Państwa Polskiego w Białymstoku od ul. Wileńskiej do terenu kolejowego przy ul. Poleskiej wraz z infrastrukturą techniczną" (formuła „zaprojektuj i buduj"), oferty 28.08.2020, wykonawca **STRABAG Sp. z o.o.**, cena brutto **32 883 642,97 zł**.
- Komunikat UM 31.01.2022 (oddanie): **posadzono 74 drzewa oraz 109 krzewów**, ponad 20 600 m² trawników i skarp, ~385 mb ekranów akustycznych; projekt „Poprawa dostępności centrum Białegostoku dla komunikacji miejskiej" (UE POPW 2014–2020, ~84,5 mln zł).

**UNVERIFIED — gatunki, obwody, rozstaw:** SIWZ.pdf (8,79 MB) to **20 stron skanów bez warstwy tekstowej**; załączniki (umowa, kosztorys ofertowy) również skany; **postanowienie RDOŚ** (17 s., CCITT G4) zdekodowano do PNG (niezależny dekoder G4 — `research/mistral/p10-greenery-3/tools/` … w ZIP `files/bip/rdos_pages/p01…17.png`); OCR skanów wymaga analizy obrazu (limit 20/odpowiedź — wyczerpany; do dokończenia). Dokumentacja projektowa zieleni (wykonana przez projektanta Strabag w formule D&B) **nie została opublikowana na BIP** — gatunki/obwody/rozstaw pozostają UNVERIFIED; na kadrze M51-101 (25.07.2022) młode przyuliczne drzewka palikowane są liściaste.

## Pliki

- `README.md`, `manifest.csv` (41 wierszy M51; kolumny jak P10-2), `crowns.geojson`, `comparison_p10.json`, `street_agg.json`, `audit_20_percent.json`, `sources.md`, `tools/` (detect_crowns.py, compare_with_p10.py, tm2180.py).
- **Zdjęcia nie idą do gita** (`files/` w `.gitignore` katalogu). Pakiet: **`mistral-p10-greenery-3-files.zip`** — karta do pobrania w wątku Vibe (PR zawiera informację). Zawartość: 105 kadrów JPG ≤ 1600 px (54 Commons: series 2020-07-11 CC BY 3.0, 2021-06-08 CC0, 2022-07-25 CC0, 2023-07-29 CC0, 2024-06-26 CC0 — autor Rakoon; 51 KartaView lth 1280 px, licencja KartaView/CC BY 4.0 wg zasad serwisu), metadane pobrania `dl_manifest.json`, `seq_*.json` (metadane sekwencji KartaView), skany BIP (SIWZ 20 s. JPG, RDOŚ 17 s. PNG, postanowienia), `kv_wloty_test.json` (142 kadry wlotów z azymutami SOURCED), `obs.json` (surowe odczyty wizualne), skrypty pomocnicze (w tym dekoder CCITT G4).

## Samokontrola (20%, jawny seed)

`audit_20_percent.json`: `random.Random(20261113).sample(ids, ceil(0.2*41))` = **9 próbek** (M51-001, -002, -102, -106, -109, -203, -209, -212, -218); automatyczne kontrole: istnienie pliku kadru w `files/`, zgodność daty z metadanymi Commons, bbox pozycji, zakres azymutu, sezon+pora_dnia, licencja z białej listy (CC BY-SA → „referencja, nie tekstura"), status SOURCED/ESTIMATED/UNVERIFIED. **Wynik: 9/9 PASS** (skrypt `audit.py` — w ZIP).

## Luki i dalsza praca

1. **6 ulic bez letnich kadrów street-level** (Kowieńska, Lidzka, Wołkowyska, Świsłocka, Grodzieńska, Racławicka) — potwierdzone braki w Panoramax/KartaView/Commons/Openverse; jedyne kadry wlotowe (KartaView 1155711, 23.03.2018) niedostępne przez outage `storage7` (HTTP 502, 2026-11-13). Świsłocka: 0 zdjęć w ogóle (luka trwa).
2. **18/20 odcinków żywopłotów** — 2+ czekają na kadry wymienione wyżej (limit analizy obrazu).
3. **OCR SIWZ/RDOŚ** (gatunki/obwody/rozstaw zadania 4) — strony gotowe w ZIP.
4. Azymuty Commons ESTIMATED (brak GPSImgDirection w metadanych Wikimedia).
