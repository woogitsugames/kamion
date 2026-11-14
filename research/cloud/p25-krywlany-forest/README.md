# M68 — ściana lasu przy Krywlanach: sylwetka, krawędź, podszyt, gatunki (cloud p25)

Gałąź `research/cloud-p25-krywlany-forest`, wiersze `C68-NNN`, data dostępu wszystkich źródeł: **2026-11-14**. Autor: subagent badawczy (Claude). Tylko źródła otwarte (D43); bez Google/Bing/Apple/Yandex, bez Mapillary.

**Liczby:** manifest 277 wierszy (obszar 30, gatunek 41, wysokość 41, krawędź 112, horyzont 11, kadr 42); **42 kadry obejrzane** (29 z okolicy Krywlan — Commons; 13 z DK19 w Puszczy Knyszyńskiej — Panoramax) + 13 obejrzanych i odrzuconych (`data/rejected_frames.json`) + 8 wycinków z pełnej rozdzielczości lub 3×; 715 profili NMPT−NMT; 316 opisów taksacyjnych BDL (141 LP + 175 poza LP).

## 0. Najważniejsze ustalenia (wprost)

1. **Czyj las:** Las Solnicki (K1) to **Lasy Państwowe — RDLP Białystok, Nadleśnictwo Dojlidy, obręb 1, leśnictwo 09 „Solnicki Las”, oddz. 144–167** (PUL 2017–2026; BDL stan 2026). Las Zwierzyniecki z Lasem Komunalnym (K2) oraz zadrzewienia przy lotnisku (K3, K5, część K4) to **lasy gminne (m. Białystok)** — w BDL warstwa „poza PGL LP”, stan 2023; skrawek 143 (8,5 ha) w K2 jest LP. Na miejscu potwierdzają to tablice nadleśnictwa widoczne w kadrach C68-234/235/236.
2. **To nie jest bór sosnowy „z kulami”:** przy ul. Mickiewicza 76 % powierzchni drzewostanów przydrożnych ma sosnę jako gatunek panujący, ale siedlisko to **las mieszany świeży / las świeży** z dębem, brzozą, świerkiem, grabem i — co kluczowe dla wyglądu — **podszytem o pokryciu 0,6–1,0 (mediana 0,8): leszczyna, kruszyna, podrost brzozy, świerka, dębu, grabu, klonu**. W kadrach skraj jest **zamknięty liśćmi od ziemi**; pnie widać tylko miejscami.
3. **Wysokości:** BDL — sosna 57–99 lat, **24–29 m**; średnia ważona całego kompleksu 26,3 m. NMPT−NMT (lot ulistniony 2023-09-15), pas 0–30 m od ściany: **mediana 19–20 m, p90 25–26 m, max 31–33 m** (Mickiewicza i Ciołkowskiego). Zadrzewienia przy lotnisku są niższe: olsza szara/osika 12–15 lat, **9–13 m** wg BDL; CHM p50 12–14 m, p90 15–21 m.
4. **Krawędź nie jest pionowa:** wysokość okapu narasta od ~9 m na samej krawędzi do ~18 m po 5 m i ~20 m po 8 m (mediana 383 profili); do 0,8·p90 dochodzi po **4 m (mediana), 10,5 m (p90)**.
5. **Osobny płaszcz krzewów przed lasem jest rzadki przy samych drogach** (koszone pobocza): profil z płaszczem ≥2 m ma 9 % stacji przy Mickiewicza, 26 % przy Ciołkowskiego, 34 % przy granicy lotniska, 50 % przy Dywizjonu 303. Tam, gdzie jest, ma 2–10 m szerokości i 3–8 m wysokości. Zamiast płaszcza przed lasem występuje **podszyt w linii pni**.
6. **Dywizjonu 303 i Kuronia biegną w otwartym terenie:** las w zasięgu ≤30 m ma tylko 11 % długości Dywizjonu 303 i 0 % Kuronia (mediana odległości do lasu 344 m i 257 m). Tam potrzebna jest **sylwetka na horyzoncie**, nie ściana.

## 1. Obszar — kompleksy leśne (kryterium: lista z id i powierzchnią)

OSM: Overpass (mirror), stan bazy 2026-11-14T16:46:28Z, zapytanie `tools/osm_query.overpassql`. BDOT10k: paczka powiatu 2061 (m. Białystok), obiekty `OT_PTLZ_A`, wersje 2024-09-23. Powierzchnie liczone w EPSG:2180.

| id | kompleks | OSM | pow. OSM [ha] | PTLZ w obrysie [ha] | BDL: zarządca | krawędź widoczna z drogi (strona; długość) |
|---|---|---|---|---|---|---|
| K1 | Las Solnicki | relation 11022876 (`landuse=forest`, `leaf_type=mixed`) | 723,02 | 721,54 (86 obiektów; największy `1261081e-…` las/mieszany 225,56 ha) | PGL LP 607,85 ha, oddz. 144–167 | Mickiewicza NE 1720 m, SW 1260 m; Ciołkowskiego SE 980 m; lotnisko NE 140 m |
| K2 | Las Zwierzyniecki + Las Komunalny | way 59421874, 59421872, 59421873 | 111,71 | 108,09 (`2BE4B432-6B82-…` las/liściasty 62,70 ha) | gminne 81,80 ha (oddz. B610110010-0415…0417); LP 8,51 ha (oddz. 143) | Ciołkowskiego NW 700 m; Dyw. 303 W 20 m |
| K3 | zadrzewienie olszowo-osikowe N/NW od lotniska | way 234039558, 1329697013 (`natural=scrub`) | 21,81 | 19,97 (`2BE4B432-6C19-…` las/liściasty 18,16 ha) | gminne 11,46 ha (B610110022-0424), Skarb Państwa 0,36 ha | Ciołkowskiego SE 200 m; **Dyw. 303 SW 110 m**; lotnisko NW/SW 70 m |
| K4 | lasek przy S/SE krawędzi lotniska | way 797866399 | 13,22 | 10,71 (`146db268-…` las/mieszany 5,99 ha) | gminne 1,46 ha; reszta bez opisu w BDL | lotnisko S ~450 m (odcinki wg PTLZ w `data/chm_edges.csv`, 32–77 m od granicy) |
| K5 | pas brzozowy Mickiewicza ↔ E krawędź lotniska | way 797866400 | 1,89 | 1,88 | gminne 1,87 ha (B610110022-0424 r) | lotnisko S/SE 260 m (1,5–2,5 m od granicy); Mickiewicza SW 20 m |

Uwagi: (a) OSM oznacza K3 jako `scrub`, BDOT10k jako „las liściasty”, BDL jako 12–15-letni drzewostan olszy szarej z osiką 9–13 m — w grze to **młodnik-zagajnik, nie krzaki i nie stary las**. (b) Ul. Kuronia nie ma lasu ≤80 m (najbliżej 201 m, p10). (c) Długości krawędzi = liczba stacji co 10 m, na których profil NMPT−NMT znajduje ścianę lasu ≤80 m od osi; kierunki i pełna lista 55 odcinków: `data/chm_edges.csv`, wiersze manifestu `obszar` i `krawędź`.

## 2. Gatunki i wiek (BDL)

Źródło: Bank Danych o Lasach — geometria wydzieleń z `ogcapi.bdl.lasy.gov.pl` (LP) i z usługi `WMS_BDL_kat_wlasnosci` (poza LP), opis taksacyjny z punktu `StandDescriptionData` portalu (ten sam, którego używa mapa BDL). Warunki: Regulamin BDL cz. III i V — dostęp „powszechny i nieodpłatny”; przy ponownym wykorzystaniu obowiązek „poinformować o źródle, czasie wytworzenia i pozyskania informacji publicznej” (https://www.bdl.lasy.gov.pl/portal/regulamin, dostęp 2026-11-14). Pełne tabele: `data/bdl_wydzielenia.csv` (141), `data/bdl_poza_lp.csv` (175).

**K1 jako całość (132 drzewostany LP w oknie, 602,11 ha):** gatunek panujący wg powierzchni — sosna 72,9 %, brzoza 10,1 %, olsza 6,4 %, dąb 5,3 %, świerk 4,6 %, jesion 0,4 %; wiek średni ważony 79 lat (6–162); wysokość gat. panującego średnio ważona 26,3 m (3–31 m).

| pas przy drodze (wydzielenia ≤80 m) | n / ha | gat. panujący (% pow.) | wiek [lata] min–med–max | H [m] min–med–max | podszyt: pokrycie (med; zakres) i gatunki (liczba wydzieleń) |
|---|---|---|---|---|---|
| ul. Mickiewicza (oddz. 149, 151, 152, 161–163) | 23 / 102,0 | SO 76, BRZ 11, ŚW 6, DB 4, OL 2 | 10–76–99 | 3–26–29 | 0,8; 0,3–1,0 — leszczyna 21, kruszyna 14, brzoza 13, świerk 11, dąb 9, grab 9, klon 3, jarząb 3 |
| ul. Ciołkowskiego SE (oddz. 143–146) | 7 / 52,0 | SO 93, ŚW 7 | 57–77–162 | 24–28–29 | 0,6; 0,3–0,8 — leszczyna 6, czeremcha 6, jarząb 4, suchodrzew 4, grab 3, kruszyna 3, świerk 3 |

Przykłady (pełny skład w manifeście, kategoria `gatunek`): 162-a: `9SO(76 l., H 28, D 36) 1DB(101 l., H 27, D 43)`, podszyt 0,9; 151-b: `10BRZ(85 l., H 27)`, podszyt 0,9; 152-g (ols): `6OL(87 l., H 26) 3BRZ(H 29)`; 163-k (uprawa/młodnik): `3ŚW(14 l., H 4) 1SO 2DB(21 l., H 6)…` — **młodnik 4–11 m przy samej ulicy (47 m od osi)**.

**Poza LP (gminne):** K3 — oddz. B610110022-0424 a/b/k/l: `7–8 OL.S (olsza szara) 2–3 OS (osika)`, 15 lat, **H 10–13 m**, zwarcie pełne/umiarkowane, podszyt leszczynowy 0,6–1,0; -c/-d: osika, brzoza, czeremcha, iwa, klon 13–15 lat, H 7–10 m. K5 — 0424-r: `5BRZ(80 l., H 26) 2OS(35 l., H 18) 1GB…`, zwarcie luźne. 0424-s (7,86 ha przy S granicy lotniska): bez warstwy drzew, „podszyt” 0,3: jabłoń dzika, wierzba biała, śliwa, iwa — sukcesja na gruncie porolnym. Skarb Państwa 0324-k: topola 50 lat H 25 m.

Zwarcie w danych LP (stan 2026) ma kody liczbowe 0.4/0.6/0.9 — podaję je surowo; ich przełożenie na „luźne/przerywane/umiarkowane” jest **UNVERIFIED**.

## 3. Wysokość drzew z NMPT − NMT

**Metoda** (`tools/chm_lib.py`, `chm_edges.py`, `chm_agg.py`):
- NMPT (lot **ulistniony 2023-09-15**, siatka 0,5 m, błąd śr. wysokości 0,10 m): arkusze ASC z `opendata.geoportal.gov.pl/NumDaneWys/NMPT/78825/` — N-34-107-C-b-3-2, -3-3, -3-4, -4-3 (sha256 w `sources.md`).
- NMT: WCS GUGiK `…/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF`, pokrycie `DTM_PL-KRON86-NH_TIFF`, 92 kafle 250 m, 1 m.
- Dodatkowo NMPT z WCS (`…/NMPT/GRID1/WCS/DigitalSurfaceModel`, `DSM_PL-KRON86-NH`, przeskalowany do 1 m). **Sprawdziłem, co ta usługa podaje:** wiersz arkusza z lotu 2025-04-18 zgadza się z WCS co do 4·10⁻⁶ m, a z lotu 2023-09-15 różni się medianą o 0,92 m (`tools/which_dsm.py`) — czyli **WCS = lot bezlistny (18 kwietnia 2025)**. Dlatego podstawą jest arkusz 2023; WCS służy tylko do porównania „lato/bez liści”.
- Arkusze 2023 mają układ wysokości EVRF2007, NMT z WCS — KRON86; różnica układów (rząd 0,1–0,2 m) nie jest korygowana i mieści się w błędzie metody. **Dokładność CHM przyjmuję ±0,5 m.**
- Profil: co 10 m wzdłuż osi drogi (OSM) / granicy lotniska, prostopadle, 0–100 m, próbka co 0,5 m. „Ściana lasu” = pierwszy punkt z CHM ≥5 m, za którym mediana CHM na 15 m ≥10 m i który leży w PTLZ. To **okap koron**, nie linia pni. Statystyki z pasa 0–30 m i 0–5 m za ścianą. 715 stacji: Mickiewicza 355, Ciołkowskiego 238, lotnisko 108, Dywizjonu 303 14, Kuronia 0.

| obiekt | stacji | CHM 0–30 m: p10 / p50 / p90 / max [m] | CHM 0–5 m: p50 / p90 | oś → ściana: p10 / p50 / p90 [m] | bez liści ÷ lato (mediana p50) |
|---|---|---|---|---|---|
| ul. Mickiewicza | 355 | 8,1 / 20,2 / 25,9 / 33,3 | 14,4 / 22,5 | 4,0 / 7,0 / 13,3 | 0,72 |
| ul. Ciołkowskiego | 238 | 7,7 / 20,4 / 25,3 / 30,8 | 14,6 / 22,9 | 10,0 / 18,2 / 28,7 | 0,75 |
| ul. Dywizjonu 303 (K3) | 14 | 5,2 / 12,3 / 21,4 / 25,0 | 9,6 / 13,6 | 9,2 / 15,2 / 34,5 | 0,68 |
| granica lotniska | 108 | 6,2 / 13,8 / 23,4 / 31,0 | 11,4 / 23,4 | 1,4 / 33,8 / 61,1 | 0,54 |
| razem | 715 | 7,6 / 19,2 / 25,5 / 33,3 | 13,7 / 22,7 | 4,5 / 11,0 / 39,0 | 0,71 |

Per kompleks/wydzielenie — 41 wierszy `wysokość` (każdy odcinek ≥50 m). Przykłady zgodności z BDL: Ciołkowskiego SE, 145-a: CHM p90 26,4 m, max 30,8 m ↔ BDL sosna 28 m, dąb 27–30 m; Mickiewicza NE, 162-a: p90 26,6 ↔ 28 m; lotnisko NW, K3: p90 20,6 m (starsze drzewa na skraju) przy BDL 10–13 m dla młodnika → **K3 jest dwupiętrowy: młodnik 10–13 m z pojedynczymi starszymi drzewami do 26 m**.

Udział próbek <5 m w pasie 0–30 m: 5,1 % (luki, drogi leśne) — ściana jest **ciągła**.

**Podszyt (pas 0–5 m):** NMPT to powierzchnia pierwszego odbicia — pod zwartym okapem podszytu nie widzi. Jedyny ślad: lot bezlistny daje medianę 0,71 wysokości letniej (lotnisko 0,54), czyli duża część górnej powierzchni koron to liściaste. Wysokość i pokrycie podszytu biorę z BDL (pokrycie 0,6–1,0) i z kadrów (2–5 m; §4).

## 4. Profil krawędzi lasu (kryterium: liczby z ≥8 kadrów)

Z NMPT−NMT (383 profile z pełnym przedpolem, `data/chm_profile_mean.json`), odległość liczona od okapu (− = przed lasem):

| d [m] | −10 | −5 | −2 | −1 | 0 | +1 | +2 | +3 | +5 | +8 | +12 | +20 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CHM mediana [m] | 0,3 | 0,3 | 0,3 | 0,5 | 8,8 | 10,5 | 13,1 | 15,1 | 18,1 | 20,2 | 19,6 | 19,3 |
| p25–p75 | 0,2–0,4 | 0,2–0,5 | 0,2–1,9 | 0,2–4,0 | 6,2–14,8 | 7,2–17,9 | 8,1–19,8 | 8,8–20,7 | 11,3–22,3 | 13,9–23,1 | 13,2–23,3 | 12,4–23,7 |

Z kadrów — **30 kadrów typu „krawędź”**, w tym 19 z okolicy; każdy ma w manifeście wiersz „wysokość ściany lasu z kadru” (ESTIMATED, metoda w uwagach) i, gdzie widać, „szerokość płaszcza”:

| cecha | Mickiewicza (K1, lato 2024; C68-207…237) | Ciołkowskiego (K1/K2/K3; C68-240…266) | DK19 Puszcza Knyszyńska (C68-170…204) |
|---|---|---|---|
| wysokość ściany [m] (ESTIMATED) | 20–26 (latarnia 9±1 m jako miara) | sosny 22–28; liściaste K2 18–24; wierzby 6–9 | 15–28 |
| płaszcz krzewów przed lasem | zwykle brak (0–2 m); wyjątki: pas brzozowy przy bramie lotniska 3–5 m, młodnik 8–15 m po stronie NE | 2–6 m pod sosnami i przed Lasem Solnickim (wys. 2,5–4 m); przy chodniku pas ziół ~5 m | 0 przy drągowinach sosnowych; 4–10 m krzewów przy starszych borach |
| pnie widoczne przy krawędzi | tylko miejscami (brzozy, pojedyncze sosny, na skarpie); częściej ściana liści od ziemi | sosny: tak — goły pień do 60–70 % wysokości, korona w górnej 1/3 | sosna: tak („kolumny”); świerk: korona do ziemi |
| odstęp od jezdni | trawa 2–4 m, po stronie NE rów z płyt ażurowych + chodnik z kostki + asfaltowa droga rowerowa | trawa 2–3 m przy ciągu; 15–20 m łąki po stronie SE na zachodnim odcinku | pobocze-skarpa 5–15 m |
| rów / nasyp / ściółka | rów umocniony płytami po stronie NE; po stronie SW miejscami skarpa 1–2 m ze ściółką liściastą | brak rowu w kadrach | trawiaste skarpy, miejscami wykop |

Ogrodzenie lotniska: odstęp granicy lotniska (OSM) od ściany lasu wg NMPT — K5 1,5–2,5 m (las dochodzi do granicy), oddz. 149 ok. 32 m, K4 32–77 m, K3 37–59 m. **Samego płotu w żadnym kadrze nie widać z bliska (luka)**; brama od ul. Mickiewicza — C68-207.

**Sezony (opis):** lato (VI–VIII) — liściaste nasycona średnia zieleń, młodnik i krzewy wyraźnie jaśniejsze i bardziej żółtawe niż stare drzewa; korony sosen ciemna, przygaszona zieleń z sinym odcieniem, pnie w górnej części rudopomarańczowe, niżej szarobrązowe; świerk najciemniejszy. Przedwiośnie/kwiecień (C68-261, 263, 266) — liściaste to szarobrązowa, **prześwitująca** masa gałęzi, przez którą widać budynki i pnie; sosny zostają jedyną zielenią; pod drzewami brązowa ściółka. Późna wiosna (C68-237, maj 2010) — świeża jasna zieleń, mocny kontrast ze świerkami. **Jesień i zima ze śniegiem — brak kadrów (luka).**

## 5. Sylwetka lasu na horyzoncie

- **P11-056** (C68-269; pobrany i obejrzany, plus dwa wycinki 3×): kadr patrzy w poprzek ul. Dywizjonu 303 na północ (ESTIMATED z położenia słońca, ±30°). Lewa część horyzontu to **ciągły, ciemny pas o gładkiej, łagodnie falistej linii — bez ząbków**, z jaśniejszym pasem zaokrąglonych zarośli u podstawy (dwie warstwy tonalne). Prawa część — luźny rząd pojedynczych zaokrąglonych koron nad łanem żółtozielonych ziół. Pas lasu zajmuje w kadrze ok. 3–4 % wysokości obrazu. Nad linię drzew wystaje tylko jedna cienka wieża; dachy leżą poniżej linii koron.
- Rondo na Dywizjonu 303 (C68-271): za płytą lotniska **równa, cienka, ciemna kreska lasu** na całej szerokości (ok. 2 % wysokości kadru).
- Puszcza Knyszyńska (C68-194, C68-205): z 200–500 m las iglasty to zwarte ciemne bryły; **drobne ząbki (wierzchołki świerków/sosen) widać dopiero z bliska**; między płatami przerwy z niskimi krzewami i łąką.
- **Stosunek wysokości lasu do budynków: UNVERIFIED** (C68-277) — w kadrach horyzontu nie ma budynku na tle lasu. Pośrednio z danych: las 20–26 m ≈ 6–8 kondygnacji; zabudowa przy Dywizjonu 303/Ciołkowskiego w kadrach ma 2–4 kondygnacje, a świerki przy 3-kondygnacyjnym budynku (C68-246) sięgają ok. 1,7 jego wysokości.
- Otwarte pola w przerwach: Dywizjonu 303 — mediana odległości do lasu 344 m (p90 602 m), najbliższy las najczęściej na W/NW/N; Kuronia — 257 m (201–344), najczęściej na S.

## 6. Przepis dla artysty (każdy punkt ze źródłem)

1. **Wysokość ściany lasu starego (K1, K2): korony 20–26 m, pojedyncze do 31–33 m; nie niżej niż 18 m.** Źródło: NMPT−NMT p50 20 m / p90 25–26 m / max 33 m (wiersze `wysokość`); BDL sosna 24–29 m (C68-033…062).
2. **Krawędź ma skos, nie pion:** na samym okapie 8–10 m (opadające gałęzie drzew skrajnych), +2 m → 13 m, +5 m → 18 m, +8 m → pełna wysokość. Źródło: profil średni, wiersze `krawędź` „CHM w odległości …” (n = 383).
3. **Zamknij ścianę od ziemi podszytem, nie płaszczem przed lasem:** w linii pni krzewy i podrost 2–5 m (leszczyna, kruszyna, młode klony, graby, świerki) o pokryciu ok. 0,8; pnie widoczne najwyżej na 1/4–1/3 długości krawędzi. Źródło: BDL podszyt 0,6–1,0 (C68-033…062); kadry C68-213, 216, 217, 220.
4. **Osobny płaszcz krzewów dawaj tylko wybiórczo:** 2–6 m szerokości, 3–5 m wysokości, jaśniejszy od lasu — przy Ciołkowskiego (ok. 1/4 długości) i przy granicy lotniska (ok. 1/3); przy Mickiewicza prawie wcale (9 %). Źródło: `plaszcz_udzial_ge2m` w `data/chm_edges.csv`; kadry C68-207, 255, 249.
5. **Sosna = „kolumna”: goły pień na 60–70 % wysokości, korona tylko w górnej 1/3, pień u góry rudopomarańczowy; zawsze w grupie i zawsze z niższym piętrem liściastym u podstawy** (poza prześwietlonymi rzędami przy targowisku). Świerk — korona do ziemi, najciemniejszy. Brzoza — białe cienkie pnie na skraju. Źródło: kadry C68-249, 258, 261, 263, 185, 188; BDL skład.
6. **K3 przy Dywizjonu 303 i Ciołkowskiego to młodnik olszowo-osikowy 10–13 m o równej górnej linii, ulistniony do ziemi, z pojedynczymi starszymi drzewami do ~25 m; miejscami zarośla wierzbowe 6–9 m.** Źródło: BDL B610110022-0424 (C68-064…069); NMPT p50 12–16 m, p90 17–22 m (C68-110, C68-102); kadr C68-240.
7. **Odstęp od jezdni:** okap koron 4–13 m od osi ul. Mickiewicza (mediana 7 m — gałęzie nad poboczem) i 10–29 m od osi ul. Ciołkowskiego (mediana 18 m); między jezdnią a lasem koszona trawa 2–4 m, po stronie NE Mickiewicza rów z płyt ażurowych, chodnik z kostki i asfaltowa droga rowerowa. Źródło: wiersze `krawędź` „odległość osi…”; kadry C68-213, 217, 220; OSM way 237088754.
8. **Horyzont z Dywizjonu 303/Kuronia:** ciągły ciemny pas o gładkiej, lekko falistej linii, ok. 2–4 % wysokości kadru, z jaśniejszą „listwą” zarośli u dołu; żadnych pojedynczych sadzonek ani prostopadłościanów; ząbki dopiero <300 m. Las zawsze wyższy niż dachy niskiej zabudowy. Źródło: C68-269/270, 271/272, 194/195, 205/206; `data/horizon_dist.json` (C68-166…169).

## 7. Kadry

42 wiersze `kadr` (C68-170…275, przeplatane z wierszami pochodnymi): pozycja WGS84, kierunek, data, sezon, pora dnia, „co widać”, gatunek, wysokość ESTIMATED z metodą, płaszcz/podszyt, najbliższy PTLZ z odległością.
- **Okolica Krywlan — 29 kadrów** (Wikimedia Commons; 28 × CC0, autor Rakoon; 1 × CC BY-SA 3.0): ul. Mickiewicza w Lesie Solnickim 14 (2024-06-23) + 1 (2010-05-22), ul. Ciołkowskiego/Wiosenna 10, ul. Dywizjonu 303 i horyzont 4 (w tym P11-056). 28 z 29 leży ≤80 m od PTLZ; P11-056 (561 m) jest kadrem horyzontu, celowo dalej.
- **Podlasie, siedliska podobne — 13 kadrów** (Panoramax, CC BY-SA 4.0 — referencja, nie tekstura): DK19 Wasilków–Czarna Białostocka, 2019-08-15 i 2019-09-01, 12 z 13 ≤80 m od PTLZ.
- **Kierunek:** Panoramax — azymut geometryczny z kolejnych pozycji sekwencji (dla sekwencji z 2019-08-15 pole `view:azimuth` powtarza magnetyczny EXIF i różni się o 30–50° — nie użyto). Commons nie ma azymutu: 15 kadrów ma kierunek ESTIMATED z osi ulicy (OSM) i wskazówki z obrazu (strona drogi rowerowej wg OSM, lico znaku, położenie słońca wyliczone w `tools/sun.py`), 14 — UNVERIFIED.
- Wymiar: Panoramax 2560×1920 (po pobraniu pomniejszyć do ≤1600 px); miniatury Commons 1280 px.

## 8. Pliki — odstępstwo od briefu (ważne)

`fetch.py` (stdlib) pobiera 42 pliki z `manifest.csv` do `files/` i sprawdza sumy. **Oryginały z Commons były dla mnie niedostępne**: `upload.wikimedia.org` odpowiadał HTTP 429 z `retry-after: 600` na wspólnym adresie wyjściowym przez całą sesję (próby co ~10 min, 17:27–17:48 UTC i dalej). Kadry Commons obejrzałem więc na **standardowych miniaturach 1280 px** (to rozmiar zalecany w komunikacie błędu Wikimedia). W manifeście: `url_pliku` = URL oryginału, `sha256` puste dla 29 plików Commons; w `uwagi` i w `files_index.csv` jest **sha1 oryginału z API Commons** oraz URL i sha256 obejrzanej miniatury. `fetch.py` weryfikuje oryginał przez sha256, a gdy go brak — przez sha1 z API; jeśli oryginał dalej zwraca 429, pobiera miniaturę i sprawdza jej sha256 (niezgodność miniatury = ostrzeżenie). Kody wyjścia: 1 niezgodna suma, 2 błąd pobierania, 3 (`--strict`) są pliki tylko jako miniatury.
Test na czystym katalogu (2026-11-14): `RAZEM: 42 plików; oryginały ok=13; tylko miniatura=29; niezgodne=0; błędy=0`, exit 0. Łączny rozmiar oryginałów wg źródeł: **135 209 722 B** (13 Panoramax 17 132 877 B pobrane i zweryfikowane sha256; 29 Commons 118 076 845 B wg API).

## 9. Samokontrola (≥20 %)

Seed `random.Random(20261114).sample(range(277), 56)` → 56 wierszy (20,2 %); odtworzenie: `python3 tools/audit_sample.py`; zapis: `audit_20_percent.json`.
- **19 kadrów obejrzanych ponownie** (6 na wycinkach z pełnej rozdzielczości/3×, 13 na arkuszach kontrolnych) → **5 poprawek opisu**: PX30 (znak A-18b), PX35 (dopisany świerk), C151034287 (dąb zamiast klonu), C151034278 (gatunek → UNVERIFIED), C149115308 (liczba aut).
- **7 opisów BDL pobranych ponownie** — skład identyczny; 2 wiersze zbiorcze przeliczone.
- **4 ponowne odczyty NMPT/NMT z WCS** w punkcie 10 m za ścianą — zgodne z kaflami użytymi w obliczeniach; pozostałe wiersze CHM porównane z `data/chm_edges.csv`.
- **Linki:** audyt wykrył, że `url_źródła` wierszy CHM wskazywał katalog (HTTP 404) → poprawiono w 109 wierszach na URL arkusza; po poprawce 56/56 odpowiada 200/206.

## 10. Luki i zastrzeżenia

- Oryginały Commons niepobrane (§8); detale oglądane w 1280 px.
- Panoramax: 0 kadrów w oknie Krywlan; KartaView: 0 w promieniu 500 m od 6 punktów; Mapillary nie użyto. Wszystkie kadry lokalne pochodzą od jednego autora i z chodnika (wysokość oczu pieszego, nie kierowcy).
- **Brak kadrów ul. Kuronia**, brak zbliżenia ogrodzenia lotniska z lasem, brak jesieni i zimy ze śniegiem.
- Wysokości z kadrów są zgrubne (±30–40 %): wysokość latarni to WORKING_VALUE 9±1 m. Do modelowania używać NMPT i BDL, kadrów — do pokroju.
- Gatunki z kadrów do rodzaju; dąb/grab/klon w ścianie liściastej często UNVERIFIED.
- NMPT nie mierzy podszytu pod okapem; wysokość podszytu 2–5 m pochodzi z kadrów (ESTIMATED), pokrycie z BDL.
- K4: BDL opisuje tylko 1,46 ha (gminne); skład reszty UNVERIFIED (PTLZ: las mieszany), wysokość z NMPT p50 12–13 m, p90 15–18 m.
- Planu urządzenia lasu ani BIP nie cytuję osobno — opis taksacyjny BDL jest wyciągiem z PUL (LP 2017–2026; lasy gminne: stan 2023).

## Pliki

`manifest.csv` · `files_index.csv` · `fetch.py` · `sources.md` · `audit_20_percent.json` · `data/` (BDL, CHM, kompleksy, horyzont, skorowidze, odrzucone kadry) · `tools/` (skrypty; NMPT/NMT/BDOT pobierane do katalogu roboczego, nie do gita).

## Errata lidera (s20, 2026-11-14)
Patrz `docs/reports/REVIEW-2026-11-14-s20-cloud-m68.md` §5 (errata 1–9, m.in. C68-213 pnie widoczne; K2/K3; udziały wg gatunku panującego). Atrybucja BDL do docs/LICENSES.md.
