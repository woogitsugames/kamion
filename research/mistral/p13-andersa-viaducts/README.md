# P13 — Estakady ul. gen. Andersa w Białymstoku: badanie dokumentacyjno-wizualne

Gałąź: `research/mistral-p13-andersa-viaducts` (katalog wyników: `research/mistral/p13-andersa-viaducts/`).
Data badania: 13.11.2026 (Vibe/Mistral, zlecenie M56/P13); poprawki **M56-FIX: 14.11.2026** (Claude Code, wg
`docs/owner/MISTRAL-FIXES-12.md` § M56-FIX i przeglądu `docs/reports/REVIEW-2026-11-14-s20-mistral-m56.md`).

## 1. Cel

Dwie estakady Trasy Generalskiej w Białymstoku są landmarkami trasy w grze Kamion:
- **Obiekt A** — estakada **E4** nad Al. Tysiąclecia Państwa Polskiego; pod nią leży **„Rondo Krzysztofa Jakuba Putry
  Wicemarszałka Sejmu RP”** (OSM ways 257367424 / 257367425 / 257367428, DK8/DK19),
- **Obiekt B** — estakada nad rondem **Pamięci Bieżeństwa 1915 r.** nad ul. I Armii Wojska Polskiego.

**OSM — way z zadania to rampy, nie mosty** (sprawdzone 14.11.2026 w OSM API 0.6, `ways.json` / `way/<id>/full.json`;
Overpass API był z tego środowiska nieosiągalny — reset połączenia / 504 na 4 instancjach):
- 1101181473, 173956078, 284022563, 606396460 (A) oraz 175157461 (B) mają `layer=1` **bez `bridge=*`** — to rampy/dojazdy.
- Mosty (`bridge=viaduct`, `layer=1`): **A** — 173985172 + 23844386 (pomost NE, ruch na NW) oraz 25447143 + 173985170
  (pomost SW, ruch na SE); **B** — 177876107 (pomost SW, ruch na SE) i 177895177 (pomost NE, ruch na NW).
- Wszystkie długości i rozstawy w tym raporcie liczono na way mostowych (nie na rampach z listy zadania).

**Etykiety jezdni (kolumna `jezdnia`, A i B jednolicie):** strona pomostu (NE/SW) + kierunek ruchu w nawiasie,
np. „NE (ruch na NW; ways 173985172+23844386)”. Kierunki z kolejności węzłów OSM (oneway=yes): A 173985172/23844386
≈ 304–313°, A 25447143/173985170 ≈ 109–132°, B 177876107 = 122°, B 177895177 = 302°.

## 2. Metoda

**Źródła:** Białystok.pl/BIP (dokumenty urzędowe, art. 4 pr. aut.), GUGiK/Geoportal (ortofoto WMS — dane otwarte),
OpenStreetMap (ODbL), Wikimedia Commons (CC0/CC BY/CC BY-SA), Panoramax (CC BY-SA 4.0), materiały wykonawców (tylko
fakty). **NIE użyto** treści Google. Mapillary — bez tokenu, wartości z ADR-ów repo = referencja UNVERIFIED.

**Geometria:** długości i rozstawy osi z węzłów OSM (haversine). Strona kamery i pikietaż `s` względem osi pomostu
liczone w lokalnym układzie ENU (odległość punkt→odcinek). **Ortofoto:** profil jasności (A, ESTIMATED).

**Zdjęcia (M56-FIX):** wszystkie **23 kadry** z manifestu (12 Commons + 11 Panoramax) pobrano 14.11.2026 i **obejrzano
osobno — jeden plik na jedno wywołanie modelu wizyjnego**; zdania „co widać” napisano z obrazu. Commons: miniatury
3840 px z serwera miniatur (pobranie oryginałów 4000–5520 px zwracało HTTP 429), Panoramax: `assets.hd` (2560 px)
z API itemu. Do kształtu słupów i liczenia rzędów robiono wycinki z plików 2560–3840 px (Python + PIL) i oglądano je
osobno (11 wycinków, ZIP §9). Kierunek Panoramax = `properties.view:azimuth` z API; Commons nie podaje kierunku →
UNVERIFIED. Pozycje GPS z EXIF Commons są zaokrąglone do 1″ (~±15 m) — przy kadrach podano to w uwagach.

**Ograniczenia:**
1. Dokumentacja projektowa/ZRID/ewidencja mostowa obu estakad nie jest publicznie dostępna — przęsła, wymiary słupów,
   wysokości ekranów/barier i skrajnia pozostają UNVERIFIED.
2. Liczba rzędów podpór jest szacowana z perspektywicznych kadrów (pary słupów i rzędy obu pomostów się nakładają) —
   status ESTIMATED z opisem, które słupy się zasłaniają.
3. Kadry z samochodu (Panoramax, P13-018) są lekko nieostre i przez szybę.

## 3. Ustalenia — obiekt A (estakada E4, rondo Putry)

**Dokumenty (SOURCED):** estakada E4 powstała w ramach przebudowy ul. Gen. S. Maczka (kontrakt PEUiM + PRM „Mosty
Łódź”, >159 mln zł, 22 miesiące). Odbiór końcowy: **30 września 2011**. UM Białystok: „Dla każdej jezdni ul. Gen. St.
Maczka ... estakadę nad Al. Tysiąclecia Państwa Polskiego o długości blisko 220 m” — **dwie równoległe estakady, po
jednej na jezdnię**. W zakresie projektu: „ekrany akustyczne, oświetlenie oraz sygnalizację świetlną”. Obiekt
figuruje w dokumentach ZDM jako **E4**; w 2024 r. remont dylatacji modułowych (B2 Sp. z o.o., 244 278 zł).

**PFU BIP 61046 nie dotyczy obiektu A (poprawka M56-FIX).** PDF dotyczy ekranów „na ul. Gen. N. Sulika i ul. Gen. St.
Sosabowskiego”, lokalizacja „Przedłużenie ulicy Wł. Andersa”. „E1 … E19” to numery **proponowanych ekranów** z „Tabeli
11.1” analizy porealizacyjnej, **nie numery estakad** — ekran „E4” z PFU to nie estakada E4 z BIP 2024. Wiersz P13-009
przeniesiono do „inny odcinek Trasy Generalskiej” (SOURCED tylko dla faktu istnienia PFU).

**Geometria (OSM, ESTIMATED):** pomost NE (ruch na NW, ways 173985172+23844386) — **219,0 m**; pomost SW (ruch na SE,
25447143+173985170) — **212,9 m**; rozstaw osi **14,2 m**; szerokość pomostu ~11 m (ortofoto HR).

**Obserwacje z kadrów (obejrzane 14.11.2026):**
- **Słupy: prostokątne z fazowanymi narożami, z poszerzoną głowicą (oczepem)**, w parach pod każdym pomostem,
  kolor ochra/musztarda. Najlepiej widać na wycinku 7204 (P13-015, CC0) i z bliska na Panoramax 6fc62548 (P13-026):
  szeroka ściana czołowa z jaśniejszym prostokątnym panelem, skośna faza, ściana boczna, oczep z łożyskiem.
  Poprzedni wpis „owalne” był błędny.
- **Gzyms zielony** (lekko spatynowany) z rurą odwodnienia pod wspornikiem.
- **Ekrany przezroczyste na zewnętrznych krawędziach obu pomostów:** NE — 7204 (P13-015/039, CC0); SW — 20221203_111814
  (P13-018/040, CC0, kamera 9 m na SW od osi 173985170). **Od strony pasa dzielącego** — stalowa balustrada
  z poziomymi pochwytami, bez ekranu (Panoramax 6fc62548, P13-079, referencja BY-SA).
- **Rampy:** mur oporowy z bloczków o fakturze kamiennej z czerwonym pasem na koronie, ekran ciągnie się po rampie
  (P13-016, 021, 029 — wszystkie BY-SA, referencja; P13-083).
- **Rzędy podpór (ESTIMATED, niska pewność):** pomost SW ok. **7–9** (P13-022: 4 rzędy między kamerą w s≈92 m
  a przyczółkiem SE; P13-027 ≥5–6 do autobusu; P13-019 ok. 8–9 sylwetek od końca NW; P13-018 5–6 do aut); pomost NE
  ok. **7–9, ≥6 widocznych** (P13-015 ok. 8 sylwetek od końca SE; P13-023 ≥6 w widoku z boku). Rytm słupów pod pomostem
  SW jest regularny — w kadrach nie widać przęsła ~95 m bez podpór.

## 4. Ustalenia — obiekt B (estakada nad rondem Pamięci Bieżeństwa 1915 r.)

**Dokumenty (SOURCED):** UM Białystok: projekt obejmował „budowę estakady na skrzyżowaniu ul. Gen. Wł. Andersa z ulica
I Armii Wojska Polskiego” [sic]; wykonawca **STRABAG Sp. z o. o.**, koszt **50 211 296,17 PLN** (UE 39 960 025,15 PLN,
85%), realizacja **III.2012–X.2013** (STRABAG: 02/2012–10/2013). STRABAG: „Skrzyżowanie nad ul. I Armii Wojska
Polskiego przecięto estakadą o konstrukcji **dwudźwigarowej sprężonej posadowionej bezpośrednio**”; nasypy dojazdowe
„w murach oporowych z gruntu zbrojonego”; kładka łukowa stalowa z windą. Droga klasy **GP**, dwie jezdnie po dwa pasy.

**Geometria (OSM, ESTIMATED):** pomost SW (ruch na SE, way 177876107) — **195,8 m**; pomost NE (ruch na NW, way
177895177) — **195,5 m**; rozstaw osi **12,1 m**.

**Obserwacje z kadrów (obejrzane 14.11.2026):**
- **Ekrany: NA ESTAKADZIE B NIE MA EKRANÓW** (SOURCED). Pomost NE: 20201102_152339 (P13-059/073, CC0) — czerwony gzyms
  i stalowa balustrada z poziomymi prętami (to ją pomylono z ekranem). Pomost SW, połowa SE: 20210320_092717 / 092737
  (P13-061/062/080, CC0) — czerwony gzyms, balustrada, brak ekranu. Potwierdzają P13-060 i P13-065. Wątek „obserwacji
  z sesji” usunięty.
- **Połowa SE (P13-061/062, CC0):** słupy szare o przekroju zaokrąglonym z **czerwonym pasem** na czole, czerwony gzyms,
  balustrada stalowa, przyczółek, mur rampy z **dużych gładkich paneli**. P13-065 (CC BY, z poziomu ronda) pokazuje
  słupy z bliska: szeroka jasnoszara ściana + węższa ściana pomalowana na czerwono, narożniki zaokrąglone.
- **Rzędy podpór w połowie SE (ESTIMATED):** pomost SW ok. **4–5** między przyczółkiem a prawą krawędzią kadru
  (P13-061, wycinek 3840 px; 1200/1270 to prawdopodobnie para jednego rzędu; kadr kończy się przed wyspą ronda);
  P13-065 ok. **6 grup słupów** od wyspy do przyczółka (przypisanie do pomostu/par niepewne). Połowa NW nieobjęta.
  Wartość 4 rzędy/połowę z ADR 0144 (Mapillary) pozostaje referencją; nasze liczenie zgadza się z nią tylko na dolnej
  granicy.
- **Przekrój (pkt 9): UNVERIFIED.** Na kadrach spodu pomostu (P13-061/062/059 w cieniu, P13-065 z bliska — płaska
  podsufitka) nie da się rozróżnić dwóch żeber ani skrzynki. „Dwudźwigarowa” może znaczyć dwa żebra w przekroju albo
  dwa ustroje (po jednym na jezdnię) — nierozstrzygnięte.
- P13-060: kamera stoi przy końcu NW i patrzy na SE; **Elektrociepłownia jest W TLE** (poprzednio „widziana od strony
  Elektrociepłowni” — błąd).

## 5. Kadry — co pokazują (23/23 obejrzane)

| Kadr | Licencja | Obiekt w kadrze | Wykorzystanie |
|---|---|---|---|
| P13-015 7204 | CC0 | A, pomost NE z zewnątrz | ekran NE, kolor, kształt słupów, rzędy NE |
| P13-016 / 017 Andersa_Maczka | BY-SA | A, pomost SW / bok | referencja: ekran, rampa, balustrada |
| P13-018 20221203_111814 | CC0 | A, pomost SW z zewnątrz | ekran SW (P13-040), rzędy SW |
| P13-019 / 022 / 027 Panoramax | BY-SA | A, pomost SW | referencja: słupy fazowane, rzędy SW |
| P13-021 / 029 Panoramax | BY-SA | A, tylko rampa/koniec | referencja: mur z bloczków, czerwony pas |
| P13-023 Panoramax | BY-SA | A, pomost NE z boku | referencja: balustrada + ekran NE, rzędy NE |
| P13-026 Panoramax | BY-SA | A, spod pomostu SW | referencja: słup z bliska, krawędź od pasa dzielącego |
| P13-020 / 024 / 025 / 028 Panoramax | BY-SA | **brak obiektu w kadrze** | nie kandydaci |
| P13-059 20201102_152339 | CC0 | B, pomost NE z boku | brak ekranu NE, gzyms, słupy |
| P13-060 20200711_072453 | CC BY | B od końca NW, EC w tle | brak ekranu, mur rampy |
| P13-061 / 062 20210320_092717/737 | CC0 | B, połowa SE od SW | brak ekranu SW, słupy z czerwonym pasem, rzędy |
| P13-065 20200711_073116 | CC BY | B z jezdni ronda przy pomoście | słupy z bliska, rzędy połowy SE |
| P13-063 / 064 / 066 | CC BY / CC BY / CC0 | **brak obiektu w kadrze** | nie kandydaci |

Uwaga: przegląd s20 oznaczył jako „bez obiektu” 024, 063, 066; obejrzenie wszystkich 23 kadrów dodało **020, 025, 028
i 064** (estakady nie widać albo nie widać jej jednoznacznie).

## 6. Tabele parametrów (parametr → wartość → źródło → status)

### A — dokumenty
| Parametr | Wartość | Źródło (id) | Status |
|---|---|---|---|
| konstrukcja / liczba estakad nad Al. Tysiąclecia PP | 2 (po jednej na jezdnię) szt | dokument [P13-001] | SOURCED |
| konstrukcja / długość (wg zamawiającego) | blisko 220 m | dokument [P13-002] | SOURCED |
| konstrukcja / odbiór końcowy | 30 września 2011  | dokument [P13-003] | SOURCED |
| konstrukcja / wykonawca | PEUiM (lider konsorcjum) + PRM „Mosty Łódź”  | dokument [P13-004] | SOURCED |
| konstrukcja / koszt kontraktu | ponad 159 mln PLN | dokument [P13-005] | SOURCED |
| wyposażenie / ekrany akustyczne w zakresie projektu | występują  | dokument [P13-006] | SOURCED |
| ewidencja / oznaczenie obiektu w dokumentach ZDM | E4  | dokument [P13-007] | SOURCED |
| utrzymanie / remont dylatacji modułowych (2024) | wykonawca B2 Sp. z o.o.; cena 244 278,00 zł  | dokument [P13-008] | SOURCED |

### Inny odcinek Trasy Generalskiej (nie A)
| Parametr | Wartość | Źródło (id) | Status |
|---|---|---|---|
| ekrany akustyczne / PFU ul. Sulika i ul. Sosabowskiego | PFU istnieje; E1–E19 = numery proponowanych ekranów (Tabela 11.1), nie estakad | dokument [P13-009] | SOURCED (tylko istnienie PFU) |

### A — geometria / pomost
| Parametr | Wartość | Źródło (id) | Status |
|---|---|---|---|
| geometria / długość osi — pomost NE (ruch na NW) | 219,0 m | OSM [P13-010] | ESTIMATED |
| geometria / długość osi — pomost SW (ruch na SE) | 212,9 m | OSM [P13-011] | ESTIMATED |
| geometria / rozstaw osi jezdni | 14,2 m | OSM [P13-012] | ESTIMATED |
| pomost / szerokość jezdni (pomostu) | ok. 11 m | ortofoto [P13-013] | ESTIMATED |

### A — elementy konstrukcyjne (pola z overrides.yaml)
| Parametr | Wartość | Źródło (id) | Status |
|---|---|---|---|
| podpory / liczba rzędów — pomost NE | ok. 7–9 (≥6 widocznych) | zdjęcia [P13-030] | ESTIMATED |
| podpory / liczba rzędów — pomost SW | ok. 7–9 | zdjęcia [P13-031] | ESTIMATED |
| podpory / rozpiętości przęseł — NE / SW | — (brak danych) m | dokument [P13-032/033] | UNVERIFIED |
| podpory / kształt słupa | prostokątny z fazowanymi narożami, z głowicą (oczepem) | zdjęcie [P13-034] | SOURCED |
| podpory / wymiary słupa | — (brak danych) m | dokument [P13-035] | UNVERIFIED |
| ekrany akustyczne / wysokość ekranu — NE / SW | — (brak danych) m | dokument [P13-036/037] | UNVERIFIED |
| ekrany akustyczne / rozstaw słupków ekranu | — (brak danych) m | dokument [P13-038] | UNVERIFIED |
| ekrany akustyczne / strona — pomost NE | zewnętrzna krawędź NE (prawa przy jeździe na NW) | zdjęcie CC0 [P13-039] | SOURCED |
| ekrany akustyczne / strona — pomost SW | zewnętrzna krawędź SW (prawa przy jeździe na SE) | zdjęcie CC0 [P13-040] | SOURCED |
| ekrany akustyczne / krawędź od pasa dzielącego | balustrada stalowa, bez ekranu | zdjęcie BY-SA (ref.) [P13-079] | SOURCED |
| ekrany akustyczne / obecność | przezroczyste, na zewnętrznych krawędziach obu pomostów | zdjęcia [P13-041] | SOURCED |
| bariery / wysokość bariery | — (brak danych) m | dokument [P13-042] | UNVERIFIED |
| gzyms / kolor | zielony | zdjęcie [P13-043] | SOURCED |
| podpory / kolor słupów | ochra/musztarda | zdjęcie [P13-044] | SOURCED |
| dojazdy / lico muru rampy | bloczki o fakturze kamiennej, czerwony pas, ekran | zdjęcia BY-SA (ref.) [P13-083] | SOURCED |
| skrajnia / skrajnia pod obiektem | — (brak danych) m | dokument [P13-045] | UNVERIFIED |

### B — dokumenty
| Parametr | Wartość | Źródło (id) | Status |
|---|---|---|---|
| konstrukcja / schemat statyczny | estakada o konstrukcji dwudźwigarowej sprężonej posadowionej bezpośrednio | dokument [P13-046] | SOURCED |
| konstrukcja / okres realizacji | 02/2012 – 10/2013  | dokument [P13-047] | SOURCED |
| konstrukcja / wykonawca | STRABAG Sp. z o.o.  | dokument [P13-048] | SOURCED |
| konstrukcja / koszt projektu | 50 211 296,17 PLN | dokument [P13-049] | SOURCED |
| finansowanie / dofinansowanie UE | 39 960 025,15 PLN (85%) | dokument [P13-050] | SOURCED |
| droga / klasa drogi i układ jezdni | GP; dwie jezdnie po dwa pasy ruchu; trasa 1,5 km  | dokument [P13-051] | SOURCED |
| dojazdy / konstrukcja nasypów dojazdowych | mury oporowe z gruntu zbrojonego  | dokument [P13-052] | SOURCED |
| infrastruktura piesza / kładka | kładka łukowa o konstrukcji stalowej z windą  | dokument [P13-053] | SOURCED |
| konstrukcja / roboty mostowe w kontrakcie | 17 785 TPLN netto (kontrakt 40 160 TPLN netto) | dokument [P13-054] | SOURCED |
| konstrukcja / estakada na skrzyżowaniu z ul. I Armii WP | „budowę estakady na skrzyżowaniu ul. Gen. Wł. Andersa z ulica I Armii Wojska Polskiego” | dokument UM [P13-055] | SOURCED |

### B — geometria / pomost
| Parametr | Wartość | Źródło (id) | Status |
|---|---|---|---|
| pomost / szerokość jezdni (pomostu) | — (brak danych) m | ortofoto [P13-014] | UNVERIFIED |
| geometria / długość osi — pomost SW (ruch na SE) | 195,8 m | OSM [P13-056] | ESTIMATED |
| geometria / długość osi — pomost NE (ruch na NW) | 195,5 m | OSM [P13-057] | ESTIMATED |
| geometria / rozstaw osi jezdni | 12,1 m | OSM [P13-058] | ESTIMATED |

### B — elementy konstrukcyjne (pola z overrides.yaml)
| Parametr | Wartość | Źródło (id) | Status |
|---|---|---|---|
| podpory / liczba rzędów — pomost SW | połowa SE: ok. 4–5 do krawędzi kadru | zdjęcia CC0 [P13-067] | ESTIMATED |
| podpory / liczba rzędów — pomost NE | połowa SE: ok. 6 grup słupów (przypisanie niepewne) | zdjęcie CC BY [P13-068] | ESTIMATED |
| podpory / rozpiętości przęseł — SW / NE | — (brak danych) m | dokument [P13-069/070] | UNVERIFIED |
| podpory / wymiary słupa | ok. 0,70 x 1,40 m (ADR 0144, Mapillary) | referencja [P13-071] | UNVERIFIED |
| podpory / rozstaw słupów w rzędzie | ok. 3,5 m (ADR 0144, Mapillary) | referencja [P13-072] | UNVERIFIED |
| ekrany akustyczne / pomost NE | brak ekranów; balustrada stalowa z poziomymi prętami | zdjęcie CC0 [P13-073] | SOURCED |
| ekrany akustyczne / pomost SW | brak ekranów; balustrada stalowa z poziomymi prętami | zdjęcia CC0 [P13-080] | SOURCED |
| bariery / wysokość balustrady | — (brak danych) m | dokument [P13-074] | UNVERIFIED |
| gzyms / kolor | czerwony | zdjęcia [P13-075] | SOURCED |
| podpory / kolor i wygląd słupów | szare, zaokrąglone, czerwony pas na jednej ścianie | zdjęcia [P13-076] | SOURCED |
| konstrukcja / przekrój (dwa żebra vs skrzynka) | nierozstrzygnięte | zdjęcia [P13-081] | UNVERIFIED |
| dojazdy / lico muru rampy | duże gładkie jasnoszare panele, spoiny częściowo ukośne | zdjęcia [P13-082] | SOURCED |
| skrajnia / skrajnia pod obiektem | — (brak danych) m | dokument [P13-077] | UNVERIFIED |
| oświetlenie / lampy między jezdniami | co ~32 m (ADR 0123) | ortofoto [P13-078] | UNVERIFIED |

Pełny wykaz (kadry z pozycjami, azymutami, licencjami i przypisaniem do way_id) — `manifest.csv` (**83 wiersze:
48 SOURCED, 11 ESTIMATED, 24 UNVERIFIED**).

## 7. Luki i rekomendacje

1. **Rozpiętości przęseł (A i B), wymiary słupów, wysokości ekranów/barier, skrajnia:** brak publicznych dokumentów —
   UNVERIFIED. Liczby rzędów podpór są tylko ESTIMATED z kadrów perspektywicznych.
2. **B — połowa NW** nie ma kadru do liczenia rzędów; przekrój pomostu (dwa żebra?) nierozstrzygnięty.
3. **Gra (do decyzji lidera, poza zakresem tej gałęzi):** opis słupów A „round” → „chamfered rectangular”; ekran A na
   zewnętrznej krawędzi obu pomostów potwierdzony kadrem CC0 20221203_111814; pomost SW A ma w kadrach regularny rytm
   słupów (sprawdzić przęsło ~95 m bez podpór w modelu); B bez ekranów potwierdzone.
4. **Mapillary:** dalej wyłącznie referencja przez ADR-y repo (UNVERIFIED).

## 8. Samokontrola (audyt ≥ 20 %)

M56-FIX: nowy seed **20261114**, `random.Random(20261114).sample(ids, 17)` z 83 id (20,5 %), plus dobór, aby było
≥ 5 wierszy z kadrów (warunek spełniony przez losowanie — patrz JSON). Dla każdego kadru **ponowne wywołanie modelu
wizyjnego** na pliku obrazu i porównanie z zapisanym opisem; dla dokumentów — sprawdzenie cytatu **i kontekstu**
(czego dotyczy dokument). Wynik i szczegóły: `audit_20_percent.json` (sekcja `m56_fix`; audyt z 13.11.2026 zachowany
w sekcji `original`).

**Wynik M56-FIX: 17 wierszy (20,5 %), w tym 5 wierszy kadrów (P13-017, 020, 062, 064, 065) i 4 kolejne oparte na obrazie
(P13-031, 075, 076, 082) — wszystkie ponownie obejrzane. 15 zgodnych, 2 niezgodne (drobne, poprawione): P13-065
(kamera stoi przy krawędzi pomostu, nie pod nim) i P13-082 (spoiny paneli rampy B częściowo ukośne, nie „prostokątny
podział”).** Dokumenty (P13-004, 009, 049, 051, 054) zgodne z cytatem i kontekstem; OSM (P13-056/057) odtworzone.

## 9. Pliki

- `README.md` — ten raport; `manifest.csv` — 83 pozycje; `sources.md` — źródła z licencjami i cytatami;
  `audit_20_percent.json` — samokontrola.
- `files/.gitignore` + `files/README.md` — binaria poza gitem.
- ZIP Mistrala (13.11.2026): `mistral-p13-andersa-viaducts-files.zip` (nie dotarł do lidera).
- **ZIP M56-FIX (14.11.2026, poza gitem):** `m56fix-p13-crops.zip` — 2 686 939 B, sha256
  `c3fdca5fd73914e3ede6d591ee515a6e9812ca747e74a654240187bcd7c9829a`; 11 wycinków użytych do liczenia rzędów i oceny
  kształtu słupów + `README.txt` (źródło i współrzędne każdego wycinka) + robocze notatki z oględzin 23 kadrów.
  Przekazanie liderowi: przez właściciela (jak ZIP Mistrala).

*CC BY-SA (Commons 2013, Panoramax) = „referencja, nie tekstura”; materiały prasowe/firmowe = tylko fakty; Google nie użyto.*
