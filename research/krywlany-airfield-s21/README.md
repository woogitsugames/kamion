# M64 / K64 — lotnisko Krywlany widziane z drogi: nawierzchnie, obiekty, geometria widoku, kamery kontrolne

Zadanie: `docs/owner/MISTRAL-TASKS-10.md` § M64 (wykonane w sesji chmurowej s21; id wierszy `K64-NNN`, katalog `research/krywlany-airfield-s21/`). Data: 2026-11-15.
**Uzupełnienie M58**: oznakowania pasa, werdyktu „z drogi NIE”, ogrodzenia, słupków i szlabanów nie powtarzam. Odsyłacze: `research/cloud/p15-dojlidy-details/README.md` (dalej „M58”) i `docs/reports/REVIEW-2026-11-14-s20-cloud-m58.md` (dalej „recenzja M58”).

Pliki: `manifest.csv` (92 wiersze), `sources.md`, `audit_20_percent.json`, `STATUS.md`, `files/` (18 kadrów lotniska ≤1600 px + 13 wycinków ortofoto, razem ok. 6 MB), `tools/` (skrypty obliczeń).

## 0. Najważniejsze wnioski dla gry

1. **Nawierzchnia pasa 09R/27L** (AIP: CONC/ASPH, odsyłacz C58-029): na ortofoto 2025 jest **jasnoszara, jednolita i czysta**. Ma słabe podłużne pasma odcieni (ślady rozkładania warstwy), a w GSD 0,05 m nie widać łat ani spękań. W grze **bez łat `asphalt_worn`**. Pas ma **koronę 1,2–1,6 %** na obie strony i **spadek podłużny 0,34 %**: podnosi się ku E o ok. 4 m na 1200 m.
2. **Pas startowy (strip) z AIP: 1470 × 150 m** dla 09R/27L i **900 × 225 m** dla pasa trawiastego 840 × 160 m. M58 tych liczb nie podaje. W terenie strip to skoszona trawa bez widocznej granicy.
3. **Drogi kołowania:** wg AIP są oznaczone A, B i C. Pas z płytą łączy główna droga W (way 958211699, ok. 191 m): **ok. 15,4 m szerokości**, ten sam jasnoszary asfalt, żółta oś, bez linii krawędziowych. W trawie po obu stronach stoją okrągłe żółte elementy co ok. 15,6 m (ich typ jest UNVERIFIED).
4. **Płyty:**
   - betonowa (way 616186583): płyty ok. 5 × 5 m, żółte łuki stanowisk, plamy oleju;
   - trawiasta aeroklubu (way 234838629): wydeptana, z płatami gołej ziemi.

   Obie leżą na zachodnim krańcu lotniska, a z dróg publicznych ich nie widać.
5. **Z dróg widać tylko jeden obiekt lotniska: stary hangar** (way 304300294). Ma ok. 21,6 × 40,6 m, okap ok. 4 m i kalenicę ok. 8,5 m (NMPT), dach dwuspadowy z ciemnoszarej papy, szary drewniany szczyt i przed sobą szopę z czerwonobrązową ścianą. Widać go z ul. Dywizjonu 303 i z ronda kpt. Wünschego (P11-076, P11-080, kadr ronda 2020).
   - Oprócz hangaru widać: zielony płot, skoszoną trawę, małe samoloty i pomarańczowy rękaw wiatrowskazu przy hangarze.
   - Hangar aeroklubu (różowofioletowy tynk, 2012) i budynek LPR stoją 450 m dalej. W żadnym kadrze z drogi ich nie ma (UNVERIFIED).
6. **Wiatrowskazy:**
   - OSM ma 3, karta AIP 2 (N i S od pasa);
   - wokół każdego leży biały pierścień o średnicy **ok. 17,4 m** (pas ok. 1,3 m);
   - maszt do rękawa ma ok. **3,8–4,5 m** (z cienia).
7. **Nowy obiekt bez OSM:** biała hala namiotowa ok. 30 × 20,5 m, okap ok. 5,4 m, z 4 kratowymi masztami w narożnikach. Stoi ok. 150 m od Dywizjonu 303. Jest na ortofoto 2025-04-18, ale nie ma jej ani w NMPT 2023, ani w NMPT z WCS. **Nie stawiać bez nowego dowodu** (prawdopodobnie obiekt tymczasowy).
8. **Geometria widoku (8 punktów, §3):**
   - Z dróg pas jest **zasłonięty**:
     - ul. Mickiewicza i ul. Kuronia: zasłaniają drzewa i zabudowa, 1,4–9,6 m nad okiem;
     - Dywizjonu 303 przy rondzie: zasłania grzbiet terenu;
   - albo jest **na granicy**: Dywizjonu 303 naprzeciw pasa. Pas ma tam 0,01–0,03° wysokości kątowej, czyli < 1 px przy 1080 px i 40° w pionie. Dalsza połowa chowa się za koroną pasa, a trawa ≥ 0,1 m zasłania całość.
   - Pas widać naprawdę tylko od płotu przy narożniku NE, czyli z kamery `krywlany_runway` z ADR 0196: przekrój 31/31, ok. 16 px przy obiektywie 14°.
9. **Kamery kontrolne (§4):** `krywlany_runway` **potwierdzona** bez zmian. Proponuję też: `krywlany_runway_alt` (45 m na NNW, najlepszy punkt skanu płotu), `krywlany_road_p11_080` (1:1 z kadrem P11-080, heading 210°) oraz `krywlany_road_truck` (oko 2,5 m na Dywizjonu 303 naprzeciw progu 09R).
10. **Teren gry:** NMT 2018 ma przy pasie nasypy ok. 2 m, których w NMPT 2023 nie ma. To potwierdza M58 C58-056 drugim źródłem. Bez spłaszczenia terenu kamera pasa dostanie fałszywą przesłonę.

## 1. Nawierzchnie

| element | parametr | wartość | metoda / źródło | status | wiersz |
|---|---|---|---|---|---|
| pas 09R/27L | wymiary, nawierzchnia | 1350 × 30 m, CONC/ASPH | AIP (odsyłacz M58 C58-029; kartę ponownie obejrzałem) | SOURCED | K64-001 |
| pas 09R/27L | strip | 1470 × 150 m | AIP VFR AD 4 EPBK 2-1, 11 JUN 2026 | SOURCED | K64-017 |
| pas 09R/27L | wygląd | jasnoszary, jednolity, podłużne pasma odcieni, bez widocznych łat i spękań | ortofoto N-34-107-C-b-3-4, 2025-04-18, 0,05 m | SOURCED | K64-002…004 |
| pas 09R/27L | korona | 1,2–1,6 % | NMPT 2023, 7 przekrojów co 200 m | ESTIMATED | K64-005 |
| pas 09R/27L | spadek podłużny | 0,34 % (W→E w górę) | NMPT 2023; kontrola NMT 0,333 % | ESTIMATED | K64-006 |
| otoczenie pasa | wały | w NMT 2018 są, w NMPT 2023 ich nie ma | profile E 778900/779250/779600 | SOURCED | K64-007 |
| pas 09L/27R | wymiary | AIP 840 × 160 GRASS, strip 900 × 225; OSM width=245 (sprzeczne) | AIP, OSM | SOURCED | K64-008, -018 |
| TWY W (A wg AIP) | szerokość | 15,4 m; żółta oś; bez linii krawędziowych | ortofoto 0,05 m | ESTIMATED | K64-009 |
| TWY | liczba | 12 obiektów OSM; AIP: A, B, C | OSM, AIP | SOURCED | K64-010, -019 |
| TWY | elementy przy krawędziach | żółte, co ok. 15,6 m, ok. 2,5 m od krawędzi (typ UNVERIFIED) | ortofoto | ESTIMATED | K64-011 |
| płyta betonowa | wymiary, wygląd | boki 174/160 × 49/70 m; płyty ok. 5 × 5 m; żółte łuki; plamy oleju | OSM + ortofoto | SOURCED / ESTIMATED | K64-012, -013 |
| płyta trawiasta | wygląd | wydeptana, płaty gołej ziemi; samoloty i szybowce | ortofoto | SOURCED | K64-014 |
| trawa | sezonowo | sierpień: zielona, skoszona za płotem; po stronie drogi wyższa, z kwiatami; marzec/kwiecień: płowa / brązowozielona | kadry + ortofoto | SOURCED | K64-015 |
| stara płyta z płyt betonowych | stan 2012 | popękane płyty, trawa i mech w spoinach | kadry 2012 (CC BY-SA) | SOURCED (stan dziś UNVERIFIED) | K64-016 |

## 2. Obiekty lotniska

| obiekt | pozycja WGS84 | id | wymiary / wysokość | wygląd | widoczny z drogi? |
|---|---|---|---|---|---|
| stary hangar | 53.104607, 23.164571 | way 304300294 | 21,6 × 40,6 m; okap ~4, kalenica 8,5 m (NMPT 2023) | dach dwuspadowy z ciemnoszarej papy; szczyt z szarych desek z pasem okien; wrota i drzwi z desek, niebieskie (2012) | **TAK**: P11-076, P11-080, rondo 2020 |
| hangar aeroklubu | 53.103819, 23.162504 | way 229040230 | 25,6 × 37,7 m; p95 8,8 m, max 10,6 | płaski dach; piętrowe skrzydła z różowofioletowym tynkiem; wrota z niebieskich paneli; pas przeszklenia; wiatrowskaz na dachu (2012) | brak kadru (UNVERIFIED) |
| budynek LPR | 53.103142, 23.160890 | way 1234358789 | p95 9,7 m, max 12,6 (maszt) | biało-jasnoszary; część hangarowa z dachem łukowym; brama w kolorze morskim (2012) | ok. 450 m od drogi, brak kadru |
| biała hala namiotowa | 53.104250, 23.168936 | brak w OSM | ok. 30 × 20,5 m; okap ~5,4 m | biały dach dwuspadowy, 4 maszty kratowe | ortofoto 2025 TAK, NMPT NIE → UNVERIFIED |
| wiatrowskazy | N 53.104039, 23.171309; S 53.099476, 23.172763; W 53.103058, 23.161619 | node 5920347042, 7437888765, 11436697402 | pierścień Ø 17,4 m; maszt 3,8–4,5 m | rękaw biało-czerwony (2012) / pomarańczowy (2023) | rękaw przy starym hangarze widać na P11-080 |
| oświetlenie krawędzi | — | brak w OSM | — | pojedyncze żółte elementy przy krawędzi N | UNVERIFIED → w grze nie stawiać |
| brama części aeroklubu | 53.105040, 23.164720 | node 4759528833 | rama ok. 5,5 m w rzucie | stalowa, ramowa; wjazd z płyt betonowych | brak kadru |
| brama E | odsyłacz M58 C58-069 | — | ok. 9,9 m | — | P11-022 (przez bramę widać tylko łąkę) |
| parking aeroklubu | ul. Krywlany | 19 × amenity=parking | 2091 m² | kostka, miejsca prostopadłe | — |
| inne budynki aeroklubu | — | way 304300297, 1232848101, 304300295, 304300296 | 3,6–6,1 m | — | szopa przed hangarem widoczna (przypisanie UNVERIFIED) |
| płot, tabliczki, banery | — | — | — | odsyłacz M58 §3 | — |

## 3. Geometria widoku

**Dane:** NMPT 2023-09-15 (ulistniony, 0,5 m, arkusze N-34-107-C-b-3-2, -3-4, -4-3, sha256 zgodne z M68) jako powierzchnia przeszkód i celu, NMT 1 m (WCS) tylko do porównań. Oś pasa to OSM way 958211700, krawędzie ±15 m, nawierzchnia s ∈ [−11,4; 1342,4] m (M58). Pozycje obserwatorów leżą na osi jezdni OSM (way w tabeli) albo 1 m na zewnątrz płotu.

**Wzory** (`tools/viewgeo.py`):
- z_oka = z_teren(obserwator) + h, gdzie h = 2,5 m (kierowca ciężarówki) albo 1,7 m (pieszy); z_teren to minimum NMPT w oknie 1,5 m (usuwa auta i słupy);
- linia wzroku do punktu P krawędzi pasa w odległości D: wysokość linii w odległości s to z_L(s) = z_oka + (z_P − z_oka)·s/D;
- **prześwit** = min_s [z_L(s) − z_NMPT(s)] dla 3 m ≤ s ≤ D − 5 m. Wartość ujemna oznacza, że coś zasłania;
- kąt depresji α = atan((z_P − z_oka)/D); **rozpiętość pionowa pasa** = |α(bliższa krawędź) − α(dalsza krawędź)|; w pikselach ≈ 27 px/° przy 1080 px i 40° w pionie;
- przekrój: 31 punktów co 1 m w poprzek pasa. Punkt liczę jako „widoczny”, gdy prześwit > −0,10 m (błąd średni NMPT to 0,10 m);
- werdykt: **ZASŁONIĘTY**, gdy prześwit do bliższej krawędzi < −0,10 m; **NA GRANICY**, gdy |prześwit| ≈ 0,10 m albo dalsza krawędź jest zasłonięta; **WIDOCZNY**, gdy widać cały przekrój;
- krzywizna Ziemi pominięta (0,01–0,02 m przy 500 m).

| punkt | położenie | D [m] | α_bliż. (2,5 / 1,7 m) | rozpiętość pasa | przeszkoda | prześwit bliż./dalsza (1,7 m) | przekrój (1,7 m) | werdykt |
|---|---|---|---|---|---|---|---|---|
| R1 | Dywizjonu 303 przy wjeździe do aeroklubu (way 443103344) | 466 | −0,28° / −0,19° | 0,015–0,020° | grzbiet terenu 152,4 m w 240 m | −0,59 / −0,52 | 0/31 | ZASŁONIĘTY |
| R2 | Dywizjonu 303 naprzeciw progu 09R (P11-099) | 371 | −0,38° / −0,26° | 0,02–0,03° (< 1 px) | trawa przy krawędzi | +0,11 / −0,16 | 26/31 | NA GRANICY |
| R3 | Dywizjonu 303 przy P11-056 | 371 | −0,16° / −0,03° | 0,004–0,014° | jw. | +0,10 / −0,23 | 22/31 | NA GRANICY |
| R4 | Mickiewicza przy bramie E (way 206333509) | 342 | −0,85° / −0,71° | 0,007° | drzewa +1,4…+2,2 m nad okiem w 48 m | −2,83 / −5,76 | 0/31 | ZASŁONIĘTY |
| R5 | Kuronia, 40 m na E od Mickiewicza (way 1540798842) | 559 | −0,65° / −0,57° | 0,03° | zabudowa/drzewa +8,8…+9,6 m w 130 m | −12,2 / −10,4 | 0/31 | ZASŁONIĘTY |
| F1 | płot NE, kamera `krywlany_runway` (ADR 0196) | 138 | −1,36° / −1,02° | 0,12–0,15° | brak | +0,05 / +0,06 | 31/31 | WIDOCZNY (mały zapas) |
| F2 | płot N naprzeciw środka pasa | 355 | −0,21° / −0,08° | 0,01–0,02° | trawa przy krawędzi | +0,12 / −0,19 | 23/31 | NA GRANICY |
| F3 | brama E w osi pasa | 316 | −0,97° / −0,83° | 0,007° | drzewa +3,1…+3,9 m w 12 m | −4,07 / −5,14 | 0/31 | ZASŁONIĘTY |

Pełne liczby dla obu wysokości oka: wiersze K64-043…K64-058; kamery K64-059…K64-062; kadry K64-063…K64-092. Wnioski:
- Wynik zgadza się z werdyktem M58 („z drogi oznakowania NIE widać”) i z odrzuceniem wariantu r2 kamery w ADR 0196 („las między płotem E a pętlą zasłania pas”).
- Przy R2/R3/F2 linia wzroku idzie 0,1 m nad trawą przy krawędzi. Latem trawa ma ≥ 0,1 m (kadry), więc **w praktyce pas jest niewidoczny**. Przy oku 2,5 m też: 0,38° depresji to tylko 0,03 m spadku linii na każde 5 m.
- Skan płotu N i NE co 50 m (63 punkty, `tools/fence_scan.py`): cały przekrój pasa widać tylko przy narożniku NE (punkty S51–S57, D 139–278 m). Największa rozpiętość jest w punkcie S55: 0,39°.

## 4. Kamery kontrolne (współrzędne gotowe do wpisania)

| id | WGS84 | EPSG:2180 (E, N) | lokalnie Dojlidy (E, N; origin 780043, 590079) | heading | oko | uwagi |
|---|---|---|---|---|---|---|
| `krywlany_runway` (jest) | 53.101282, 23.185276 | 780064,1; 589958,0 | 21,1; −121,0 | 252,5° | 1,7 m | **potwierdzona**: 31/31, −1,02°, ~16 px przy fov 14° |
| `krywlany_runway_alt` (nowa) | 53.101691, 23.184993 | 780042,5; 590002,3 | −0,5; −76,7 | ok. 240° | 1,7 m | najlepszy punkt skanu (0,39°); położenie względem płotu ±1 m |
| `krywlany_road_p11_080` (nowa) | 53.105805, 23.166742 | 778795,2; 590388,2 (pozycja EXIF kadru; 7 m od way 671082746, ul. Krywlany) | −1247,8; 309,2 | 210° ±10 | 1,6 m | do porównania 1:1 z P11-080: płot, trawa, samoloty, stary hangar |
| `krywlany_road_truck` (nowa) | 53.104427, 23.170405 | 779049,1; 590249,4 | −993,9; 170,4 | 178,5° (wariant 85° jak P11-099) | 2,5 m | dowód „z kabiny pasa nie widać” |

Heading 210° i 85° są ESTIMATED: punkt znany z OSM, jego położenie w kadrze i HFOV ≈ 66° (WORKING_VALUE). Kąt widzenia telefonu nie jest znany, bo Commons nie ma EXIF ogniskowej w imageinfo.

## 5. Kadry (18 lotniska + 12 odrzuconych, wszystkie obejrzane)

- **Z dróg i od płotu (10):**
  - P11-080, P11-079, P11-099, P11-078, P11-076, rondo 2020 — **6 kadrów pokazuje, co jest za płotem**;
  - P11-022 (przez bramę E tylko łąka);
  - P11-023, P11-024 (Mickiewicza: sam las, lotniska nie widać);
  - P11-056 (skrzyżowanie, lotniska nie da się wskazać).
- **Z terenu lotniska (8, 2011–2012, CC BY-SA 3.0, „referencja, nie tekstura”):** hangar aeroklubu (2), stary hangar, LPR, pole przedwiośniem, flota, dwupłat z hangarem w tle, górnopłat na tle lasu.
- **Odrzucone po obejrzeniu (12):** kadry z Dywizjonu 303 w stronę N, ogródki działkowe, biurowce, pomnik. Lista w manifeście.
- **3 najlepsze dla artysty:**
  - P11-080: płot, trawa, samoloty, hangar, rękaw wiatrowskazu;
  - P11-076: hangar od drogi, słupki z łańcuchem na pierwszym planie;
  - P11-099: oś drogi i płot, dobry do kamery ciężarówki.

## 6. Luki i UNVERIFIED

1. **Kadry z dróg: 10 zamiast ≥ 12.**
   - Commons: wyczerpane wyszukiwanie po kategoriach (Białystok-Krywlany Airfield, LPR base, Aeroklub Białostocki), geosearch 5 × 1 km i prefiksy serii Rakoon;
   - Panoramax: 0 zdjęć (3 instancje);
   - KartaView: 0 (`api.kartaview.org`, 10 punktów po 500 m);
   - Openverse: tylko lustra Commons;
   - Mapillary: niedostępne (brak tokenu).

   Wymóg „≥ 12 kadrów lotniska” jest spełniony łącznie (18), ale z drogi mamy tylko 10.
2. **Ul. Kuronia:** brak kadru w stronę lotniska; wynik tylko z geometrii (R5).
3. **Kierunki kadrów:** Commons nie podaje azymutu. 6 kadrów ma kierunek ESTIMATED z geometrii, reszta UNVERIFIED. Kadr ronda z 2020 ma zaokrągloną pozycję EXIF (84 m od osi).
4. **Oświetlenie krawędzi i progu:** UNVERIFIED (żółte elementy przy TWY i pasie bez kadru z bliska).
5. **Biała hala namiotowa:** czy stoi dziś, UNVERIFIED. Jej brak w WCS DSM podważa wniosek M68, że WCS = lot 2025-04-18.
6. **Hangar aeroklubu i LPR:** wygląd tylko z 2012 r.; widoczność z dróg UNVERIFIED.
7. **Wysoki maszt** przy starym hangarze (P11-080): pozycja i wysokość UNVERIFIED.
8. **Trawa:** wysokość liczbowo UNVERIFIED (0,3–0,6 m poza płotem — zgrubnie).
9. **AIP** nie opisuje świateł (M58). Przypisanie liter TWY B i C do way OSM: UNVERIFIED.

## 7. Uzgodnienie z M58

| temat | M58 | M64 (ta paczka) |
|---|---|---|
| oznakowanie pasa | pełne (progi, strzałki, oznaczniki) | nie powtarzam; tylko nawierzchnia (kolor, stan, korona, spadek) |
| AIP | wymiary, LDA, TORA | odsyłacz + **nowe**: strip 1470 × 150 i 900 × 225, oznaczenia TWY A/B/C, 2 wiatrowskazy |
| widoczność | werdykt NIE dla 3 ulic (oko 2,5 m, NMT) | 8 punktów, oko 2,5 i 1,7 m, **NMPT 2023** (przeszkody: drzewa, budynki), przekrój 31 pkt; werdykt zgodny |
| ogrodzenie, brama E, tabliczki | pełne | odsyłacz |
| wały w NMT | ortofoto pokazuje, że ich nie ma | NMPT 2023 też pokazuje, że ich nie ma (drugie źródło) |
| wysokość Słońca, lot 2025-04-18 | 43,7° | 44,4° (z azymutu cieni, wzór NOAA); różnica bez znaczenia |

## 8. Samokontrola

`random.Random(20261115).sample(ids, ceil(92/5) = 19)`. Ponownie obejrzałem 12 obrazów (plansza kontrolna), przeliczyłem geometrię R2 i F3 z krokiem 1 m (zgodna), spadek podłużny sprawdziłem z NMT, a 2 obrysy pobrałem ponownie z API OSM. Kartę AIP pobrałem ponownie i obejrzałem (render 150/300 dpi). Zapytanie WCS dla hali namiotowej powtórzyłem. **17 PASS, 2 FIX:**
- K64-013: plama oleju 6 × 4 → 8 × 9 m;
- K64-039: rama bramy 6 → 5,5 m; opis nawierzchni drogi rowerowej poprawiony.

Szczegóły i statusy HTTP linków są w `audit_20_percent.json`.

## 9. Licencje

- Kadry Rakoon: CC0.
- Kadry 2011–2012: CC BY-SA 3.0, z atrybucją w manifeście. To „referencja, nie tekstura”.
- Ortofoto, NMPT i NMT: dane PZGiK (GUGiK), udostępniane bez opłat.
- AIP: dokument urzędowy PAŻP. Biorę z niego tylko fakty, karty nie kopiuję.
- OSM: ODbL.
- Google, Bing, Apple, Yandex i Mapillary nie były używane.
