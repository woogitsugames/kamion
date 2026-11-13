# mistral-p6-dojlidy-gates — bramy Dojlidy/Krywlany: szerokości, promienie łuków, RS16, PZZ, organizacja ruchu

**Projekt:** Kamion — realistyczny mobilny symulator ciężarówki z naczepą; świat Białegostoku 1:1 (OSM + GUGiK); gra komercyjna, budżet 0 zł.
**Zadanie M49:** uzupełnienie luk po paczce research/gptpro/p6-next-regions-2 (dalej: P6) — szerokości bram wjazdowych (12 bram bez szerokości), promienie łuków wjazdu (14 bram bez promieni), dokładna pozycja RS16 (WIM Zabłudowska), adres/brama PZZ (Elewatorska vs Zbożowa), organizacja ruchu na końcówkach dojazdów (Myśliwska, Karpińskiego, Dojlidy Fabryczne, rondo Meyera, Adama Mickiewicza) z numerami dokumentów BIP/ZDM.
**Gałąź:** research/mistral/p6-dojlidy-gates (od origin/main). **Data:** 2026-11-13. **Język:** polski.
**Status: W TOKU** — pomiary bram UKOŃCZONE (sekcje 4–5); RS16/PZZ-adres/BIP w trakcie (sekcje 6–8).

## 1. Cel
(por. zadanie — 4 bloki: A. pomiary 14 bram P6-G01..G14; B. RS16 WIM; C. adres PZZ; D. zarządzenia organizacji ruchu)

## 2. Metoda
- Ortofotomapa: GUGiK WCS `Orthoimagery_High_Resolution` (PZGIK, otwarte dane), wycinki 160×160 m = 1600×1600 px (10 cm/px) — identyczne bboxy jak P6 (files/M49-GXX.jpg), dodatkowo warianty PNG do analizy programowej.
- Skorowidz ortofotomapy WFS: https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WFS/Skorowidze — uwaga: usługa oczekuje bbox w kolejności (N,E) dla EPSG:2180 (weryfikacja empiryczna w tej sesji). Dla Białegostoku metadane podają wyłącznie rok aktualności (akt_rok), bez dokładnej daty zobrazowania.
- OSM: API 0.6 (api.openstreetmap.org), wycinki map?bbox= ±200 m wokół każdej bramy, transformacja EPSG:2180 własnym modułem TM/GRS80 (zwalidowany na parach z manifestu P6: Δ < 0,5 m).
- Pomiar szerokości przejazdu (metoda programowa): profil prostopadły ±2,5 m wzdłuż linii ogrodzenia (way OSM z barrier=fence przechodzący przez node bramy) — stacje co 0,5 m; brama = ciąg „nie-trawy" (asfalt/struktura); szerokość = rozpiętość ciągu przez node. Metoda druga: szerokość asfaltowego podjazdu w profilach prostopadłych do drogi serwisowej (way zawierający node bramy) w odległości 3–15 m od bramy. Metoda trzecia (tam, gdzie geometria OSM ma przerwę w ogrodzeniu): cięciwa między końcami ways barrier=fence (jak w P6). Analiza obrazu (vision) — tylko jakościowo (typ bramy, strona ulicy, sezon, pojazdy); próby ilościowe wykazały brak powtarzalności modelu (wartości-kotwice), więc NIE są źródłem liczb.
- Wynik = mediana dostępnych pomiarów (≥ 2 tam, gdzie to możliwe); niepewność ±1–3 m jawnie.
- Promień łuku wjazdu (krawędź jezdni): wycinek WCS 40×40 m @ 0,1 m/px w narożniku „ulica × podjazd" (J = punkt styku osi podjazdu z osią ulicy wg OSM; kierunki z geometrii ways). Maska asfaltu (klasyfikator: max−min<16, 45<avg<235, g−r<10), erozja nie-asfaltu 0,3 m, krawędzie asfaltu w ćwiartce narożnika 14×14 m; okrąg dopasowany RANSAC (4000 iter., tol 0,3 m, r∈[1,5; 25] m) + dopasowanie algebraiczne (LSQ) na inlierach; seed jawny, deterministyczny (seed_for(name, side)). Każdy narożnik zwizualizowany mapą ASCII (piksele krawędzi vs przebieg dopasowanego okręgu) — wizualna walidacja przed akceptacją. Raportujemy mniejszy z dwóch narożników (wiążący dla pojazdu), z jawną niepewnością.

## 3. Struktura (plan)
README.md, manifest.csv, sources.md, audit_20_percent.json, files/ (orto, poza git), files/docs/ (PDF urzędowe ≤ 5 MB, w gicie).

## 4. Wyniki pomiarów — tabela zbiorcza (STAN: 2026-11-13)

Ortofotomapa: usługa WCS podaje warstwę najnowszą; wg skorowidza WFS jest to dla wszystkich bram nalot **2025** (akt_rok=2025), GSD **0,05 m** (G09: 0,10 m); dokładna data zobrazowania nie jest publikowana w metadanych (tylko rok). Bboxy pomiarowe = bboxy P6 (files/M49-GXX.jpg) + wycinki narożników R-* (files/).

| Brama | Obiekt (P6) | Node OSM (P6) | Szerokość [m] ± | Status szer. | Promień [m] ± | Status prom. | Uwagi |
|---|---|---|---|---|---|---|---|
| G01 | BIAZET (Andersa 44) | 12126375017 | 12,1 ±2 | ESTIMATED | 10,4 ±2,5 | ESTIMATED | brama 378 m w głąb od Andersa; szer. z jedynego profilu z **ograniczeniem** (bounded) przy bramie; promień = narożnik zjazdu z Andersa w drogę wewnętrzną (service 177719991, node 1881569071) |
| G02 | Kwadrat (Andersa 38) | 10024132807 | — | UNVERIFIED | 4,3 ±1,5 | ESTIMATED | brak bariery/ogrodzenia w geometrii OSM w przejeździe (fence 1094472354 przechodzi ciągłościem, całość asfalt); wizja (jakościowo): przejazd 2-pasowy bez szlabanu; promień = krawężnik zjazdu z drogi wewnętrznej 537184112 (node 10024132807 leży 4,3 m od niej) |
| G03 | Rosti (Dojlidy Fabryczne 8) | 6596800253 | 8,0 ±1 | ESTIMATED | 7,3 ±2 | ESTIMATED | skan płotu i profil podjazdu zbieżne (7,5–8,0); narożnik z ul. F. Karpińskiego (way 275237230) |
| G04 | KAN (Karpińskiego 7) | 4656499172 | 7,7 ±1 | ESTIMATED | 8,1 ±2 | ESTIMATED | skan 7,5 / podjazd 7,9; ul. F. Karpińskiego |
| G05 | BIAFORM (Dojlidy Fabryczne 12) | 2814000970 | 7,0 ±2 | ESTIMATED | 6,2 ±2 | ESTIMATED | node bramy ~4 m N od krawędzi asfaltu (profil bounded d=3 przy bramie); po stronie podwórka plac 15,7–18,9 m; ulica przy bramie = Rondo Artura Hasbacha (way 221209012) |
| G06 | Browar Dojlidy (Dojlidy Fabryczne 4) | 6085185775 | 9,0 ±2 | ESTIMATED | 21,5 ±3 | ESTIMATED | skan ~0,9 asfaltu przy bramie; podjazd 9,8; oba narożniki 21,5–21,7 (łagodny łuk) |
| G07 | WER (Welurowa 1) | 9306871344 | 15,4 ±1 | SOURCED | 11,8 ±2 | ESTIMATED | szer. = cięciwa końców fence ways (nodes 9289975821/9289975834 = 15,5 m; asfalt wzdłuż 0,96) — potwierdza P6 (15,5); promień z narożnika Welurowa × WER |
| G08 | DPD (Welurowa 16) | 6448194342 | 12,6 ±1 | SOURCED | 6,4 ±2 | ESTIMATED | szer. = cięciwa (nodes 9289965580/9289975827 = 12,6 m; asfalt 0,96) = P6; promień z narożnika zjazdu |
| G09 | Raben Żółtki (brak w OSM) | — (P6 bez node) | ~26 ±7 | ESTIMATED | 7,3 ±2 | ESTIMATED | brak bramy w OSM; wjazd = service 550896624 z ul. Warszawskiej (node 5320426952); korytarz utwardzony na granicy terminala (profile co 5 m: 17–33 m, mediana ~25–28) — szerokość wjazdu na teren, nie pojedynczego szlabanu (szlaban: UNVERIFIED); promień = narożnik Warszawska × podjazd |
| G10 | Podlaskie Zakłady Zbożowe (G2 w P6) | 3465808562 | ~11 ±3 | ESTIMATED | 8,3 ±2 | ESTIMATED | **BŁĄD P6:** node 3465808562 = brama na zlikwidowanym torze (way 339393639 railway=disused), nie brama drogowa. Wjazd drogowy: service 248109974 z ul. Elewatorskiej (node 5161111758); profile korytarza d=12/16/20/40/60: 10,3/7,3/14,3/11,6/13,7 → mediana ~11–12; promień = narożnik Elewatorska × service |
| G11 | Masterpress (Kuronia 5) | 2999986083 | 7,8 ±1 | ESTIMATED | 11,7 ±2 | ESTIMATED | profile street-side d=6: 7,8; d=9: 7,7 (zbieżne); ulica bez nazwy (way 236885861) przy Kuronia 258564448 |
| G12 | Elektrociepłownia Białystok (Andersa 15) | — (brak w OSM) | 5,8 ±1 (prześwit bramy); podjazd 13,9 ±2 | ESTIMATED | 6,0 ±1,5 | ESTIMATED | **brama dla ciężarówek** (szukana w zad. 1): node 3954799626 (EPSG:2180 778613, 595397) na service 177903959, wjazd od ul. Andersa przez trunk_link 182399965 (zjazd z ronda Pamięci Bieżeństwa 1915 r.) i ul. Bitwy Białostockiej (service 392226325); prześwit w płocie (fence 392226284): asfalt ≥0,6 w przedziale s∈[−3,5; +1,0] → ~5,5–6 m; profile podjazdu d=20: 13,9, d=25: 14,0; promień = narożnik Bitwy Białostockiej × podjazd bramy. Inne bramy EC w OSM: 3954799591 (od Bitwy — otwarcie niemierzalne, asfalt ulicy), 3954799571 (w 5,5-metrowej przerwie trawiastej — raczej nie-drogowa), gate 13528916930 access=destination (778574, 595438) |
| G13 | Bieldruk (Św. Proroka Eliasza 8A) | 10875232003 | 16,5 ±3 | ESTIMATED | 10,4 ±2,5 | ESTIMATED | asfalt na linii płotu s∈[−6,5; +10] (przedłużenie segmentu + forward); jasna nawierzchnia (bright 185–197) sugeruje nowy overlay; alternatywa: wąskie gardło ~12 m — nie rozstrzygnięte (wizja niedostępna); promień = narożnik Św. Proroka Eliasza (275244664) × Bieldruk |
| G14 | Bravilor Saby (Św. Proroka Eliasza 6) | 6539179208 | 7,0 ±1 | ESTIMATED | 4,5 ±1,5 | ESTIMATED | czysty skan płotu (asph 1,0, s∈[−2,5; +4,0]; trawa ±11–13); profile 15–17 odrzucone (szeroki plac) |

Szerokości G07/G08 są przeliczeniem deterministycznym z geometrii OSM (STAN: SOURCED, ODbL); wszystkie pozostające pomiary z ortofotomapy mają status ESTIMATED z metodą; brak wartości = UNVERIFIED z uzasadnieniem. Niepewność ± obejmuje GSD (0,05–0,10 m), klasyfikację „asfalt/trawa" (skrajne stacje ±0,5 m) i wybór stacji pomiarowych; dla G09/G10/G13 dodatkowo rozrzut profili (±3–7 m).

## 5. Samokontrola pomiarów (wstępna, przed audit_20_percent.json)
- Każdy promień: wizualna walidacja ASCII (nakładanie dopasowanego okręgu na piksele krawędzi asfaltu) — wszystkie 14 narożników zaakceptowane; fits o niskiej frakcji inlierów (G01: 0,16; G02: 0,20) oznaczone większą niepewnością.
- Transformacja EPSG:2180↔WGS84: walidacja na parach z manifestu P6 (Δ<0,5 m); odwrotna z liczbą iteracji Newtona (tol 1e-4 m).
- Źródła liczb: ortofoto GUGiK WCS (URL w sources.md), geometria OSM (API 0.6), skorowidz WFS (akt_rok/GSD). Google Maps/Street View/Earth — NIEUŻYTE. Mapillary — brak tokenu, nieużyte.

## 6. RS16 WIM ul. Zabłudowska — W TOKU
(P6: 53.088753, 23.246754 = EPSG:2180 (784259, 588808), ESTIMATED ±150 m; PFU BIP id.77056: „1295 m od stałego punktu kontroli". Do doprecyzowania z dokumentów GDDKiA/ITD/BIP/ortofoto.)

## 7. Adres PZZ (Elewatorska 14 vs ul. Zbożowa) — W TOKU

## 8. Organizacja ruchu (Myśliwska, Karpińskiego, Dojlidy Fabryczne, rondo Meyera, Adama Mickiewicza) — W TOKU
(P8 znalazło komunikaty ZDM z 19.11/1.12.2025; brak numerów zarządzeń — do uzupełnienia z BIP Białystok.)
