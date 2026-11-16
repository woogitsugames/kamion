# G3 — cztery punkty problemowe trasy C z bramki 3 (sesja s21, 2026-11-15)

Zadanie: `docs/owner/GPT-CHROME-RESEARCH-S20.md` p. 1 (G3), wykonane od zera w sesji chmurowej.
Problemy z gry: `docs/reports/REVIEW-2026-11-14-s20-gate3-phone.md` (P1-1, P1-2, P2-7, P2-10, P2-12).

**Liczby:** 38 wierszy manifestu (30 kadrów, 4 ortofoto, 4 OSM), **30 obejrzanych kadrów przypisanych**:
a = 6, b = 9, c = 9, d = 6 (+ 10 wycinków szczegółów). Łącznie obejrzano w pełnym kadrze 43 zdjęcia (13 odrzuconych jako
niepokazujące celu albo za daleko), a ok. 50 kolejnych tylko w arkuszach selekcyjnych (nie liczone). Daty kadrów: 2016–2022.
Samokontrola 8/38 (21 %, seed 20261115): **6 PASS, 2 FIX** (G3-012, G3-029 — poprawione), 0 FAIL.

## Metoda

1. Położenie punktów: kamery z `Data/Regions/bialystok-industrial-c/gate3_cameras.json` (lokalne E,N względem
   origin EPSG:2180 777995 / 596223 z `region.yaml`) → WGS84 przez pyproj; azymut kamery = atan2(ΔE, ΔN) pos → look_at.

   | punkt | kamera gry | WGS84 kamery | azymut | uwaga |
   |---|---|---|---|---|
   | a | g3b_rondo_putry_approach | 53.158525, 23.153206 | 308,5° | na łącznicy 173956083 (NW-bound, na poziomie terenu), 4 m od kadru CC0 7204 |
   | b | g3b_ext34_s1482 (szew) / g3b_eye_s1482 | 53.157895, 23.153876 / 53.157856, 23.154116 | 107,9° / 313,8° | ciężarówka na łącznicy przy rampie NW (1101181473) |
   | c | g3a_eye_s0412 | 53.152260, 23.166929 | 298,5° | NA pomoście NE estakady nad rondem Bieżeństwa (way 177895177), ok. 41 m przed jego końcem NW |
   | d | wyspa ronda Putry | 53.159177, 23.151580 | — | środek części N wyspy z ortofoto (okrąg OSM: 53.159032, 23.151625) |

2. Kadry: Wikimedia Commons (geosearch 400 m), Panoramax (bbox), KartaView (api.kartaview.org — działa; sekwencje
   z przejazdami po estakadach i rondzie). Każdy kadr obejrzany w 960 px, detale w wycinkach 2–3×. Opis = tylko to, co widać.
3. Kierunek: KartaView — kurs geograficzny z GPS sąsiednich klatek (ESTIMATED; pole `heading` API bywa błędne — np. 357°
   przy jeździe na 131° w sekw. 14055); Commons — ESTIMATED z geometrii OSM, gdy kamera patrzy wzdłuż drogi, inaczej
   UNVERIFIED; Panoramax — `view:azimuth` zapisany w uwagach, ale w tej kolekcji niezweryfikowany (R2 wykazał rozbieżności) → UNVERIFIED.
4. Wymiary z ortofoto GUGiK (WMS HighResolution; data nalotu UNVERIFIED) i z geometrii OSM (API 0.6, 2026-11-15).

## (a) Dojazd do ronda Putry — krawędź/chodnik przy estakadzie (P1-1 „chodnik na wiszącej płycie”)

**Stan faktyczny (pewność: wysoka — G3-001 z 4 m, G3-002/003/006 z 2019, ortofoto G3-007):**
- Łącznica do ronda biegnie **na poziomie terenu** obok estakady; po jej prawej stronie: krawężnik → pas trawy
  ok. **3,5 m** → ekran akustyczny → chodnik z szarej kostki → drugi ekran (ekrany są **przesunięte względem siebie**,
  chodnik ok. **2,5 m** przechodzi między nimi; OSM 319142221/222 równoległe + footway 319142233). Przy samej kamerze
  peron przystankowy z wiatą ok. **4,6 m** od krawężnika do ekranu (ESTIMATED, ortofoto ±0,5 m).
- **Chodnik leży na gruncie** — nie ma pod nim płyty, skarpy ani muru; brak balustrady przy chodniku.
- Ekran przy łącznicy: **biały betonowy cokół na ziemi**, nad nim ciemne pełne panele z pionowym żebrowaniem, wyżej
  panele przezroczyste, słupy stalowe zielone; koniec przy rondzie = pełne przęsło do ziemi (G3-003).
- Na estakadzie (G3-004/005) **nie ma chodnika**: za barierą stalową pas czerwonej nawierzchni (kapa) i ekran; ekran
  przechodzi z rampy na pomost bez przerwy (dylatacja modułowa w jezdni).
- Wysokości cokołu, paneli i ekranu: **UNVERIFIED** (nie zmierzono).

**Co zmienić w grze:** usunąć „wiszącą” płytę chodnika — chodnik jako nawierzchnia na terenie (teren dociągnięty do
krawężnika, krawędzi chodnika i stopy ekranu, bez widocznego spodu); między krawężnikiem a pierwszym ekranem trawnik
~3,5 m; ekran z białym cokołem stojącym na ziemi; odwzorować przesunięcie dwóch linii ekranu ze szczeliną dla chodnika.

## (b) Koniec muru oporowego z czerwonym pasem i ekranów przy Andersa (P1-2 „szew”, P2-10)

**Stan faktyczny (pewność: średnio-wysoka — 8 kadrów KartaView 2019/2021, G3-017 CC0, ortofoto G3-018):**
- **Mur rampy NW nie kończy się nad terenem**: jego wysokość maleje do zera razem z niweletą rampy, a czerwony pas
  (czerwona nawierzchnia korony/kapa) opada do poziomu terenu przy nosie klina (to samo na bliźniaczej rampie SE — G3-017:
  mur z jasnoszarych bloczków z ukośną fakturą, czerwony pas schodzący po skosie do ziemi). Koniec kapy rampy NW
  z ortofoto: ok. **53.157731, 23.154175** (±1,5 m); OSM: rampa 284022563 → 1101181473 od 53.157393, 23.154675.
- Na nosie klina rampa/łącznica: bariera W zawinięta zaokrąglonym łukiem na podwyższonym klinie (G3-012).
- Ekran na rampie zaczyna się od niskiej betonowej ściany przy początku rampy i rośnie z nią (G3-012/015).
- Z rampy czerwona kapa wygląda jak szeroki pas (G3-013/014/016), ale z poziomu łącznicy widać ją jako wąski
  czerwony pas na koronie muru — w grze zachować to rozróżnienie (P2-10).
- **Ekran NE przy łącznicy (OSM 319142225, 142,7 m) to osobny ekran na gruncie**, ciągnie się dalej na SE niż mur i
  **kończy pionowo pełnym przęsłem na ostatnim zielonym słupie**, z białym cokołem na trawie; za nim chodnik z żółtą
  barierką (G3-009 2019, G3-010 2021 — bez zmian). Koniec SE: ok. 53.157352, 23.154984 (OSM). Nie ma pojedynczego panelu w powietrzu.
- Pas trawy między rampą a łącznicą: ok. 25 okrągłych ciemnych plam Ø ~1 m (ortofoto) — prawdopodobnie misy
  nasadzeń (zgodne z „rzędem młodych drzew” z recenzji P2-10), interpretacja **UNVERIFIED**.

**Co zmienić w grze:** mur zakończyć klinem do zera z niweletą (bez „czapy” ponad terenem), czerwoną kapę sprowadzić
do terenu; ekran rampy kończyć razem z murem; ekran NE kończyć pełnym przęsłem na słupie z cokołem na gruncie;
na nosie klina bariera W z łukowym zawinięciem. Luka: brak kadru z otwartą licencją z samej łącznicy w pozycji kamery
gry (Mapillary 810525 tylko referencja) — lico muru rampy NW widziane z łącznicy: UNVERIFIED (przyjmujemy jak G3-017).

## (c) Wiadukt przy s0412 — czy jest tablica kierunkowa E- (P2-12)

**Stan faktyczny (pewność: wysoka dla „brak E”, średnia dla F-10):**
- Kamera s0412 stoi **na pomoście NE** estakady nad rondem Bieżeństwa. W 6 kadrach z tego samego pasa i kierunku
  (KartaView 2019: G3-020/021/022; 2021: G3-023/024/025; 10–50 m od kamery) **nie ma tablic kierunkowych E-** ani
  nad jezdnią, ani na barierach; przy końcu estakady tylko żółte trójkątne znaki ostrzegawcze (jeden z symbolem
  włączania się pasa z prawej).
- Pod estakadą od strony ronda (G3-027, G3-028; 2020): znaki B-2, A-7, D-6, zielone tablice z nazwą ulicy — **brak tablicy E**.
- „Niebieska tablica” z recenzji to wg ADR 0144 pkt 10 **F-10 „prosto | w prawo”** (Mapillary richlv 2020, tylko
  referencja). Tu potwierdzone niezależnie: (1) OSM — łącznica naziemna **177861600** (oneway, lanes=2,
  `turn:lanes=through|right`, `destination=Warszawa;Ełk`) przebiega 5,7 m od tego miejsca; (2) ortofoto G3-029 — mały
  jasny obiekt z cieniem w pasie trawy między barierą łącznicy a krawędzią pomostu NE, **53.152180, 23.166981**
  (= pozycja z ADR 0144). W moich kadrach otwartych tablicy nie widać (z pomostu zasłania ją bariera) — **treść,
  wymiar i stan 2026: UNVERIFIED** z otwartych źródeł.

**Co zmienić w grze:** **nie dodawać** tablicy E pod ani na wiadukcie. P2-12 dotyczy tablicy F-10 (niebieskiej, pasy
ruchu) dla łącznicy naziemnej — ADR 0144 już ją dodał; sprawdzić tylko, czy w buildzie telefonu stoi przy łącznicy
177861600 licem na SE (do ruchu ok. 299°) i czy jest widoczna z kamery s0412 nad barierą (na 482392 jest przy prawej krawędzi).

## (d) Rondo Putry — wyspa środkowa (P2-7 „kopce z cegły”)

**Stan faktyczny (pewność: wysoka — 6 kadrów 2016–2022 + ortofoto G3-037):**
- Część wyspy poza estakadą (N): **obwódka z luźnego szaro-beżowego żwiru 2,5–3,5 m** wzdłuż krawężnika, **środek
  trawa** (niejednolita, zielono-brązowa, z suchymi placami); w żwirze słupy sygnalizatorów i zielona tablica na słupku.
  Kształt: łuk/owal wydłużony na SE, szerokość W–E ok. **30 m** (ESTIMATED ±1 m); oś jezdni ronda wg OSM ~66 m (rondo
  nieokrągłe, odchyłki do 15 m).
- Część pod pomostami: **żwir/tłuczeń**, wzdłuż krawędzi krawężnik + pas płyt + **bariera W na słupkach**, ochrowe podpory (G3-031/033/036).
- **Brak** rzeźby, bruku, kostki, rabat, kopców.

**Co zmienić w grze:** wyspa Putry = trawa w środku z żwirową obwódką przy krawężniku; pod estakadą żwir z barierą W;
usunąć wszelkie „kopce”.

**Uwaga — „kopce z cegły” są w recenzji przy rondzie Bieżeństwa** (P2-7: `g3a_rondo_bie_approach`, s0312, s0362), nie
przy Putry. Dla Bieżeństwa (G3-028, CC0, 2020-11): na wyspie **niskie, strzyżone rabaty krzewów** (jesienią
czerwonobrązowe liście) w pasach z trawą, pod estakadą żwir (G3-027). W grze zastąpić kopce niskimi rabatami krzewów z
listowiem i ziarnem żwiru — pewność średnia (2 kadry, bez wymiarów; osobne zadanie, jeśli potrzebne).

## UNVERIFIED / luki

1. Wysokości i wymiary: cokół, panele i ekrany (a, b), kapa czerwona (b), tablica F-10 (c) — nie zmierzono.
2. Data nalotu ortofoto HighResolution — nieznana (serwis skorowidzów niedostępny).
3. Kierunek kadrów Panoramax (4) i 3 kadrów Commons — UNVERIFIED.
4. Brak kadrów z otwartą licencją z lat 2023–2026 dla a–d → stan bieżący UNVERIFIED (najnowsze: 2022-12-03).
5. (b) brak kadru z samej łącznicy w pozycji kamery gry; KartaView sekw. 14055 (2016, zjazd rampą SE) — pliki niedostępne.
6. (c) F-10 niewidoczna w żadnym obejrzanym kadrze otwartym.
7. (b) okrągłe plamy w pasie trawy — interpretacja jako nasadzenia niepotwierdzona.

## Samokontrola

`audit_20_percent.json`: seed 20261115, 8 z 38 wierszy. Ponownie obejrzane pliki z `files/` (ortofoto: wycinek 3×
wokół mierzonego obiektu) + ponowne sprawdzenie URL (wszystkie 200). **6 PASS, 2 FIX**: G3-012 (była „podwójna
bariera”, jest bariera zawinięta łukiem; dopisany znak pasów z zakazem dla ciężarówek na lewym pasie), G3-029
(doprecyzowane położenie obiektu: w pasie trawy między łącznicą a pomostem).

## Pliki

`manifest.csv` (38 wierszy, kolumny w nagłówku; `plik_lokalny`, `sha256`, `url_pliku`, `punkt`), `sources.md`,
`audit_20_percent.json`, `STATUS.md`, `files/` (30 kadrów ≤ 1600 px + 4 ortofoto + 10 wycinków; ~7,5 MB),
`osm/` (data pobrania, wyciąg way), `meta_*.json` (metadane pobrań), `tools/` (skrypty: pobieranie, wycinki,
`build_manifest.py` + `rows.py` z opisami). Odtworzenie manifestu: `python3 -I tools/build_manifest.py <katalog_pobrań>`.

CC BY-SA / CC BY = referencja, nie tekstura; napisy firmowe na billboardach i zbiorniku — nie odtwarzamy.
