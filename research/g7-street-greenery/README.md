# G7 — zieleń przy ulicach: gatunki, układ, żywopłoty (tile `bialystok-industrial-c`)

Data: 2026-11-13. Wykonawca: researcher (Claude), zlecenie G7 z `docs/owner/GPT-PRO-RESEARCH-01.md` przejęte po ChatGPT Pro. Nie commitowano.
Cel: liczby z metodą dla generatora roślinności (ADR 0154 — korony jak pinie zamiast lip/klonów; D51 zieleń ulic domów PARTIAL).

## Najważniejsze ustalenia (po polsku, wprost)

1. **Na ulicach domów tile nie ma drzew przyulicznych.** Kowieńska, Lidzka, Skidelska, Wołkowyska, Świsłocka, Wileńska, Grodzieńska (a także Racławicka, Łańcucka) mają jezdnię z kostki/asfaltu, chodnik z kostki po jednej stronie, słupy z napowietrznymi liniami i **zero nasadzeń w pasie drogowym** (12 zdjęć Commons z 2022-2024 + 27 kadrów analogicznych ulic Białegostoku; OSM: 0, BDOT10k: 0 punktów w 12 m od osi). Cała „zieleń ulicy” to **zieleń posesji widoczna zza płotu**: iglaki (świerki, żywotniki), żywopłoty, niskie krzewy, drzewa ogrodowe nad dachami. To tłumaczy, czemu „szpalery lip/klonów” generatora nie pasują do rzeczywistości — nie trzeba ich dodawać na ulicach domów.
2. **OSM w tile jest praktycznie pusty:** 0 `barrier=hedge`, 0 `natural=tree_row`, 2 węzły `natural=tree` (oba pomniki przyrody: wiśnia ptasia 24 m, dąb szypułkowy 20 m, na skrajach tile). Brak żywopłotów w OSM nie oznacza ich braku w terenie — na zdjęciach są wszędzie. Generator nie może opierać się na OSM; źródłem pozycji koron zostaje ortofoto (`plot_canopy.json`).
3. **Gęstość koron w pasie frontowym ulic domów (≤ 8 m od osi, obie strony łącznie):** 9,9 drzew/100 m osi + 3,5 krzewu/100 m (n = 131 drzew na 1329 m ulic; ortofoto 2024-05-27). Mediana promienia korony 1,95 m (kwartyle 1,5–2,55; p90 3,05) → średnica mediana 3,9 m. Korony ≥ 4 m promienia to ok. 2 % drzew (3 szt. na 1,3 km). Czyli typowe „drzewo przy ulicy domów” to **małe drzewo ogrodowe (owocowe, brzoza, iglak) 5–8 m**, a nie duża lipa; duże korony (10–20 m) to wyjątki w narożnikach.
4. **Gatunki:** brak w Białymstoku udokumentowanego rejestru gatunków drzew przyulicznych w otwartych źródłach (UNVERIFIED). Wiemy: (a) pomiary 4 drzew miejskich (dąb 18 m, klon pospolity 20 m/korona 18×22 m, topola 22 m/25×22 m, młoda lipa 7 m/4,6×5,4 m — SGGW 2022); (b) zdjęcia pokazują iglaki dominujące w ogrodach: świerk srebrzysty/pospolity i żywotnik zachodni (kolumnowy i na żywopłot), forsycja, niskie krzewy; drzewa liściaste bezlistne w kwietniu 2024 — brzoza, modrzew, klon/jesion/lipa przy większych koronach (identyfikacja po pokroju, ESTIMATED). Proporcje w tabeli poniżej to WORKING_VALUE.
5. **Żywopłoty:** na 11 zdjęciach frontów ulic tile (Commons, kwiecień 2024): wysoki żywopłot/szpaler iglasty w 6 (55 %), niskie krzewy w 5 (45 %), sam płot w 0 — ale zdjęcia wybierano ręcznie (zakręty, skrzyżowania), więc zawyżają. Na 27 kadrach Mapillary analogicznych ulic domów w Białymstoku (poza tile): żywopłot ≥ 1,2 m w 26 %, niskie krzewy/bluszcz 22 %, sam płot 52 %. Rekomendacja robocza: 40 % posesji z żywopłotem, 25 % z pasem niskich krzewów, 35 % bez zieleni od ulicy (ESTIMATED, niepewność ±15 pp). Żywopłoty strzyżone z żywotnika (Smaragd/Brabant): 2,0–2,5 m (do 3 m na narożnikach), szerokość 0,8–1,2 m, za płotem 1,2–1,6 m; liściaste/niskie: 0,8–1,5 m.
6. **Andersa / Aleja Tysiąclecia (ulica główna):** brak dojrzałych drzew przyulicznych; pas środkowy i pobocza to trawnik (w sierpniu wypalony, żółty), **młode drzewka na 3 palikach** (kilka kadrów 2024 i zdjęcie G7-P10), ekrany akustyczne zamiast żywopłotów; po zachodniej stronie dzikie zadrzewienie 8–15 m i ogrody domów; wyspy ronda Bieżeństwa: sucha trawa, bez krzewów (n ≈ 3 kadry). Gęstość młodych drzewek/100 m: UNVERIFIED (nie zliczono).
7. **Korony „jak pinia” — przyczyna i lekarstwo z danych:** w pomiarach białostockich korona zaczyna się nisko: baza korony (CBH) 3 m przy drzewie 18–20 m (dąb, klon), 1,3 m przy młodej lipie 7 m; szerokość korony ≈ 0,6–1,1 × wysokość (dąb 10×13/18 m, klon 18×22/20 m). Katalog Ebben: lipa, klon, kasztanowiec, grab mają koronę **jajowatą/kulistą, zwartą**; brzoza i jesion **otwartą/półotwartą**; parasol na gołym pniu nie występuje u żadnego z nich. Parametry w tabeli: baza korony 0,15 H, szerokość/wysokość 0,55–0,75, sufity wysokości wg gatunku (brzoza 20 m, nie 23 m jak w ADR 0154).

## Metoda i dane (krótko)

| Co | Jak | Wynik/plik |
|---|---|---|
| OSM w tile | pyosmium na lokalnym PBF (bez odpytywania serwerów) | `tools/osm_tile_greenery.py` → 0 hedge, 0 tree_row, 2 tree |
| BDOT10k | wycinek tile z repo | 71 punktów drzew/grup, 0 w ≤ 12 m od osi ulic domów |
| Korony z ortofoto | `plot_canopy.json` (detektor G/luma na ortofoto 0,25 m, 2024-05-27) × osie ulic z grafu | `tools/house_streets_agg.py` → `tools/house_streets_agg.json` |
| Zdjęcia ulic tile | Wikimedia Commons geosearch r = 1,2 km; 12 z 300 plików (CC0, Rakoon) | `files/g7-photo-01..12.jpg` (1600×900) |
| Kadry Mapillary | już w repo (API bez tokenu niedostępne) — klasyfikacja wzrokowa, bez kopiowania | `mapillary_sample.csv` |
| Wymiary drzew | pomiary SGGW dla UM Białystok (2022) + katalog Ebben | `manifest.csv` G7-T*, G7-S* |

Współrzędne tile: 53,1499–53,1672 N, 23,1437–23,1761 E; ulice domów leżą w jego zachodniej części (ok. 53,152–53,156 N, 23,149–23,154 E) przy Andersa (w OSM: Aleja Tysiąclecia Państwa Polskiego / Gen. Andersa). Wartość 23,168 E z zadania to wschodnia część tile (przemysł), nie ulice domów.

Zdjęcia (`files/`): G7-P01 Wołkowyska · P02 Kowieńska · P03 Grodzieńska · P04–P06, P08 Wileńska · P07 Lidzka · P09 Racławicka · P10 Aleja Tysiąclecia/Andersa (młode drzewo na palikach) · P11–P12 Łańcucka (żywopłoty z żywotnika). Wszystkie CC0, autor Rakoon, pozycja = geotag Commons (azymut UNVERIFIED), szczegóły i opisy w `manifest.csv`.

## Braki i niepewności

- Brak rejestru drzew przyulicznych Białegostoku (UNVERIFIED): proporcje gatunków to WORKING_VALUE z ok. 40 zdjęć i katalogów. Zalecenie: wniosek o informację publiczną do ZDM/Wydziału Ochrony Środowiska o inwentaryzację drzew w pasach drogowych (Andersa, Sokólska, Wileńska).
- Mapillary API bez tokenu niedostępne; Panoramax: kadry tylko przy północnym końcu Andersa, brak ulic domów. Pokrycie ulic Kowieńska/Lidzka/Skidelska/Wołkowyska/Świsłocka: wyłącznie Commons (12 zdjęć, jeden fotograf, kwiecień 2024 — drzewa bez liści, więc gatunki liściaste UNVERIFIED).
- Detektor koron: nie rozróżnia gatunków; udział iglastych 11 % jest prawdopodobnie zaniżony (na zdjęciach iglaki są w większości ogrodów) — w tabeli przyjęto 25 % (WORKING_VALUE, zakres 15–40 %). Korony > 6,5 m promienia są obcinane przez detektor, sąsiednie mogą się zlewać.
- Wysokości z oszacowania wzrokowego mają ±0,5 m (żywopłoty) do ±2 m (drzewa). Tab. 2 raportu SGGW wyciągnięta z PDF ma przemieszane kolumny; przypisanie odtworzono z DBH/obwodów (jawna uwaga w manifeście).
- Wymiary gatunków z Ebben to szkółka holenderska (cieplejszy klimat; sufit, nie średnia).
- Nie sprawdzano trawników poza opisem (koszenie/chwasty): ESTIMATED z kadrów.

## Samokontrola (20 %)

Powtórnie sprawdzono 8 z 41 pozycji manifestu (20 %): 5 zdjęć Commons (P01, P02, P03, P06, P07 — losowo) — licencja CC0, autor Rakoon i współrzędne zgodne z zapisanymi (5/5); 3 karty Ebben (Smaragd 4–6/1–1,8 m; lipa 20–25/10–15 m; brzoza 15–20/6–12 m) pobrane ponownie — zgodne (3/3). Raport SGGW przeczytany bezpośrednio z PDF (tekst + tabela). Liczby z OSM/BDOT/ortofoto odtwarzalne skryptami w `tools/`. Wniosek: brak rozbieżności; największe ryzyko to trafność wzrokowej klasyfikacji (G7-M01, P-opisy), nie link/licencja.

## Parametry dla generatora

Konwencja: „/100 m osi” = na 100 m długości osi ulicy, obie strony łącznie, w pasie ≤ 8 m od osi (front posesji + pas drogowy). Status: S = SOURCED, E = ESTIMATED, W = WORKING_VALUE (decyzja z niepewnych dowodów), U = UNVERIFIED.

| # | Parametr | Wartość (zakres) | Status | Podstawa |
|---|---|---|---|---|
| 1 | Drzewa przyuliczne w pasie drogowym, ulice domów (Kowieńska, Lidzka, Skidelska, Wołkowyska, Świsłocka, Wileńska, Grodzieńska, Racławicka, Łańcucka) | **0 / 100 m** | E | OSM 0, BDOT 0, 12 zdjęć Commons, 27 kadrów analogów |
| 2 | Drzewa ogrodowe widoczne z ulicy (korony r ≥ 1,25 m, ≤ 8 m od osi) | **10 / 100 m osi** (9–12); ≤ 12 m: 12,7 | E | ortofoto 2024, n = 131/1329 m (G7-C01..C04) |
| 3 | Krzewy/małe korony r < 1,25 m w tym pasie | **3,5 / 100 m** (3,5–4,4) | E | jw. |
| 4 | Promień korony drzewa ogrodowego | mediana **1,95 m**; Q1 1,5; Q3 2,55; p90 3,05; max sensowny 6,5 | E | jw. (detektor ucina przy 6,5 m) |
| 5 | Udział koron r ≥ 4 m (drzewa duże, 10–20 m) | **2 %** drzew (≈ 0,2 / 100 m) | E | 3 z 131 |
| 6 | Wysokość z średnicy korony D | **H = D / 0,65** (D/0,75 … D/0,5); D 3,9 m → 6 m; D 6 → 9 m; D 8 → 12 m; D 10 → 15 m | W | Białystok: dąb 10–13/18, klon 18–22/20, lipa młoda 4,6–5,4/7; Ebben W/H 0,5–0,8 |
| 7 | Baza korony (CBH) | **0,15 H** (min 1,3 m dla młodych; 2,5 m dla ogrodowych; 4 m jeśli przycinana nad chodnikiem) | E | dąb 3/18, klon 3/20, lipa 1,3/7 (G7-T01,T03,T04) |
| 8 | Udział iglastych wśród drzew ogrodowych | **25 %** (15–40) — detektor 11 %, zdjęcia: iglaki w ≥ 9 z 12 kadrów | W | G7-C01, G7-P01..P12 |
| 9 | Iglaste: podział | świerk (pungens/abies) **50 %**, żywotnik kolumnowy **35 %**, inne **15 %** | W | zdjęcia |
| 10 | Iglaste: wymiary | świerk H 8–14 m, szer. 3–5 m (stożek); żywotnik kolumnowy H 4–6 m, szer. 1–1,8 m | E/S | zdjęcia, Ebben S08/S09 |
| 11 | Liściaste drzewa ogrodowe: podział (udział w liściastych) | klon (platanoides/pseudoplatanus) **25 %**, brzoza **20 %**, lipa **15 %**, jesion/robinia **15 %**, owocowe (jabłoń, wiśnia, śliwa) **20 %**, inne **5 %** | W | brak inwentaryzacji; zdjęcia (U dla proporcji) |
| 12 | Sufity wysokości (dojrzałe, miasto) | lipa 24; klon 22–25; jesion 25; kasztanowiec 22; **brzoza 20** (ADR 0154: 23 → obniżyć); grab 18; owocowe 5–8 | S/W | Ebben S01–S07, pomiar G7-T03 |
| 13 | Szerokość korony / wysokość | lipa 0,5–0,6; klon 0,65–0,75; kasztanowiec 0,6–0,8; jesion 0,7–0,8; brzoza 0,4–0,6; grab 0,7 | S | Ebben (szer./wys.) |
| 14 | Kształt i gęstość (zamiast parasola) | lipa: jajowata, **zwarta**; klon, kasztanowiec: kulista/owalna, **zwarta**; jesion: kulista, **półotwarta**; brzoza: wąskojajowata, **otwarta**; świerk: wąskostożkowa, zwarta | S | Ebben |
| 15 | Posesje z żywopłotem ≥ 1,2 m od strony ulicy | **40 %** (25–55) | E | Commons 6/11 (zawyżone), Mapillary analogi 7/27 |
| 16 | Posesje z pasem niskich krzewów 0,5–1,2 m (forsycja, berberys, kwiaty, bluszcz) | **25 %** (15–30) | E | Commons 5/11, Mapillary 6/27 |
| 17 | Posesje bez zieleni od ulicy (sam płot/mur) | **35 %** (20–50) | E | Mapillary 14/27 |
| 18 | Żywopłot: skład | żywotnik zachodni (Smaragd/Brabant) **70 %**, liściaste (ligustr/berberys/grab — gatunek U) **30 %** | W | G7-P01,P04,P09,P11,P12; Ebben S09–S11 |
| 19 | Żywopłot iglasty strzyżony | H **2,0–2,5 m** (do 3,0 na narożnikach, zaokrąglony); szer. **0,8–1,2 m**; odsunięcie 0,3–1,0 m za linią płotu; ponad płotem 1,2–1,6 m widoczne 0,6–1,2 m | E | G7-P11, P12 (±0,5 m) |
| 20 | Żywopłot liściasty/niski | H **0,8–1,5 m**, szer. 0,5–0,8 m | E | G7-P05..P09 |
| 21 | Długość żywopłotu wzdłuż frontu posesji | **80 %** szerokości frontu przy posesjach z żywopłotem (przerwy: brama, furtka, wjazd) | W | zdjęcia (do weryfikacji na ortofoto) |
| 22 | Ogrodzenie (kontekst) | płot drewniany sztachetowy 1,2–1,6 m, słupki ceglane, panele; żywopłot rośnie za płotem, nie zamiast niego | E | G7-P01..P12 |
| 23 | Ulica główna (Andersa/Al. Tysiąclecia, Sokólska): drzewa dojrzałe w pasie | **0 / 100 m** | E | ortofoto G7-C05, OSM 0, BDOT 1 punkt |
| 24 | Ulica główna: młode drzewka na paliku | H **3,5–5 m**, korona ⌀ 1,5–2,5 m, 3 paliki; gęstość **UNVERIFIED** (robocze 4–6 / 100 m na stronę tylko tam, gdzie jest trawnik ≥ 2 m) | U/W | G7-P10, Mapillary 2024 |
| 25 | Pasy zieleni: pas środkowy Andersa | trawnik niski, koszony, **wypalony latem** (VII–VIII żółto-brązowy); bez krzewów | E | G7-M02 |
| 26 | Wyspy i ronda | trawnik bez krzewów; maks. młode drzewka na palikach | E (n ≈ 3) | G7-M02 |
| 27 | Zadrzewienia dzikie (strona zachodnia Andersa, skarpy) | zwarta masa mieszana H 8–15 m, nie szpaler | E | G7-M02, ortofoto G7-C05 |
| 28 | Posesje zaniedbane / pustostany | wysokie chwasty 0,5–1,2 m, brak koszenia (VII) | U (n = 1) | jedno zdjęcie Commons 2022-07-25 (`20220725 132426`, ok. 53,155278 N 23,152222 E), nieprzypięte do `files/`; do potwierdzenia |
| 29 | Pomniki przyrody w tile (węzły OSM) | wiśnia ptasia H 24 m obw. 2,61 m (53,163997 N 23,148236 E); dąb szypułkowy H 20 m obw. 3,2 m (53,149787 N 23,148593 E) | S | OSM 6763732952 / 6763732994 |

Uwagi wdrożeniowe: (a) na ulicach domów nie sadzić szpalerów — dodać **zielonej masy do 2–3 m na wysokości wzroku** (żywopłoty, krzewy przy płotach) zgodnie z p. 15–21, także na Low; (b) korony: zwarte i nisko osadzone (p. 7, 13, 14), nie parasol; (c) iglaki są ważnym elementem sylwetki ulic domów — p. 8–10; (d) wszystkie wartości `W`/`U` oznaczyć w grafie jako `default` z niską pewnością.
