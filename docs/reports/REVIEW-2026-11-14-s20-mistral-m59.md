# Przegląd M59 (P16 lampy ciągnika i naczepy: fotometria R148/R150, budowa, lampka tablicy) — s20, 2026-11-14

**Werdykt: FIX.** Część przepisowa jest dobra: **71 z 78 cytatów wierszy `przepis` znalazłem dosłownie** w tekście Dz.U. L 347 z 30.9.2021 (PL, Cellar XHTML pobrany dziś; skrypt z normalizacją soft-hyphen/NBSP/spacji). Pozostałe 7: P16-001/002 (GSR2 zał. II — konsolidatu nie pobierałem, teza „pierwotna wersja wiąże w UE” niezweryfikowana), P16-074 (luka, pusty cytat — słusznie), P16-122/123/124/127 (cytaty EN, E9). Liczby tabel zgadzają się; są drobne errata (§3). Seed audytu da się odtworzyć, licencje 23 kadrów zgadzają się z Commons, Google nie użyto. Część zdjęciowa nie przechodzi:
- **Obejrzałem wszystkie 23 kadry; opis Mistrala zgadza się z obrazem w 2** (P16-218, P16-219), częściowo w 2 (206 — liczba komór, 212 — brud).
- W 8 kadrach **tył pojazdu w ogóle nie jest widoczny**: przód, bok lub pojazd z daleka (P16-207, 213, 214, 215, 220, 222, 223, a na P16-211 lampy to kilka pikseli). Mimo to każdy z nich ma opis „zespoły 3-komorowe z gładkim kloszem” albo „lampka nad tablicą”.
- P16-203 to ramię kamery bocznej, nie lampa.
- P16-208/209/212 to amerykańskie okrągłe lampy FMVSS, nie lampy zespolone ECE.
- W żadnym kadrze nie widać lampki tablicy ciężarówki ani naczepy.
- Kryterium 4 jest niespełnione: wymagano ≥ 15 zbliżeń lamp zespolonych, włączonych i wyłączonych, w dzień i o zmierzchu, z kolejnością funkcji. Takich zbliżeń są realnie 3 (P16-204/205 — ta sama lampa, 206), żadne nie jest włączone ani o zmierzchu, i żaden opis nie podaje kolejności funkcji.
- Tezy README §5.1, §5.2 i §6 („potwierdzone kadrami”, „13 kadrów z lampką nad tablicą”) nie mają pokrycia w obrazach.

Blok poprawek: `docs/owner/MISTRAL-FIXES-12.md` § M59-FIX. Nic nie scalono, nic nie scommitowano, PR #55 bez komentarza.

## 1. Zakres i metoda

- PR #55, gałąź `origin/research/mistral-p16-truck-lamps`. `git diff --stat main...` pokazuje 5 plików wyłącznie w `research/mistral/p16-truck-lamps/`: README, manifest (106 wierszy, separator `;`), sources, audit, `.gitignore`. Pliki czytane przez `git show`.
- **ZIP `mistral-p16-truck-lamps-files.zip` (68 125 864 B, sha256 `901edd3d…` z opisu PR) nie ma w `C:\Users\matma\Downloads`.** Katalogu `research/_incoming/…` nie utworzyłem. Sha256 i zawartość ZIP-a (43 kadry, `photo_meta.json`, PDF-y) są **niezweryfikowane**.
- Kadry pobrałem sam przez Commons API `imageinfo`: miniatury 1280 px pomniejszone do ≤ 960 px, licencja z `extmetadata`. **Obejrzanych: 23 z 23** (P16-201…223). Wycinki 3× zrobiłem dla 204 (lampy), 206 (lampy z miniatury 3840 px i tablica) i 221 (belka z tablicą). EXIF 204/205 (Commons `iiprop=metadata`): `Flash = 9` — lampa błyskowa wyzwolona.
- Przepisy: Cellar `publications.europa.eu/resource/celex/{42021X1719, 42021X1721, 42021X1718}` (XHTML PL), przekonwertowane do tekstu. Tekst EN UNECE `R148e.docx` z Wayback nie pobrał się (620 B HTML). **Tez README o serii 01 UNECE nie weryfikowałem.**
- Gra: ADR 0175/0178/0181, `game/Assets/_Project/Vehicle/Runtime/TruckLights.cs`, `TruckExterior.shader` (`_PlateIllum`), `tools/blender/truck/trailer/trailer_build.py` (lampa zespolona naczepy), `trailer_export.py` / `a6_export.py` (`light_group`).

## 2. Kryteria akceptacji M59

| Kryterium | Wynik |
|---|---|
| Fotometria R148/R150: seria, data, punkt; tabela min/max, kąty, stop/pozycyjne, jednorodność, barwa; lampka tablicy (B, gradient, kąt, położenie) | **TAK, z erratą (§3).** 71/78 cytatów dosłownie w Dz.U.; liczby tabel zgodne (lista niżej). |
| Budowa lamp: typy optyki, podział komór, wymiary 7-komorowej, wygląd wyłączonej, znak homologacji | **CZĘŚCIOWO.** Wymiary pochodzą z 4 kart sklepowych: tylko liczby, bez obrazów, akceptowalne. Znak homologacji zgadza się z pkt 3.3.2 i zał. 7. Typy optyki, kolejność komór i „wygląd wyłączonej” są opisane jako „potwierdzone kadrami”, ale żaden kadr tego nie pokazuje (§4). |
| Lampka tablicy na ciągniku i naczepie — z kadrów | **NIE.** 13 „potwierdzeń” w §6 README opiera się na kadrach, na których tablicy albo lampki nie widać (§4). |
| ≥ 15 kadrów lamp zespolonych z bliska (wł./wył., dzień/zmierzch) + ≥ 5 lampek tablicy, każdy OBEJRZANY | **NIE.** Zbliżenia lamp ECE to tylko 204/205 (ta sama lampa) i 206. Wszystkie 17 wierszy „lampa zespolona” mają szablon „dzień, wyłączone, 3-komorowe, gładki klosz”. Lampka tablicy jest rozpoznawalna w 218 i 219 (przyczepa kempingowa, SUV — nie ciężarówki). |
| Licencje CC0/BY/BY-SA, zakaz Google, sklepy tylko liczby | **CZĘŚCIOWO.** Licencje kadrów 23/23 zgodne z `extmetadata` Commons, brak Google. Według opisu PR ZIP ma w `docs/` „karty katalogowe” — dokumenty producentów z rysunkami i logo, bez licencji. Zadanie dopuszczało tylko liczby z URL, więc trzeba je usunąć z ZIP-a (M59-FIX pkt 5). ZIP-a nie widziałem. |
| Każda liczba: punkt + cytat ≤ 25 słów + wersja | **TAK** dla przepisów. Wyjątki są w erratach E4/E5/E9. |
| Samokontrola ≥ 20 %, jawny seed, kadry ponownie obejrzane | **CZĘŚCIOWO.** `Random(20261113).sample(range(106),22)` odtwarza te same 22 id ✓. Kadry nie zostały obejrzane ponownie: P16-204 ma status „PREV-VIEW”, a 217 i 223 „obejrzane przy tworzeniu wiersza”. Wszystkie trzy mają PASS, a **opisy 204, 217 i 223 są fałszywe**. P16-303 ma status „PREV”. |
| Zmiany tylko w katalogu paczki, ZIP + sha w PR | **TAK** (ZIP nie dotarł do lidera). |

## 3. Przepisy — weryfikacja z Dz.U. L 347 (PL)

**Zgodne z tekstem** (liczby odczytane z tabel Dz.U.; dla tab. A2-2/A2-3 i pkt 3.3.2/3.3.3 tylko dosłowny cytat z manifestu, bez osobnego odczytu tabeli):
- **Tab. 4:** R1/RM1 4 / 17 / 8,5; R2/RM2 4 / 42 / 21.
- **Tab. 7:** S1 60 / 260 / 130; S2 60 / 730 / 365.
- **Tab. 8:** 2a 50 / 500 / 250; 2b 50 / 1000 / 500; kat. 5 0,6 / 280 / 140.
- **Tab. 9:** SM1 4,0 / 0,6 / 25,0, ±45°/±10°; czerwone 0,25 cd w zakresie 60–90° w przód.
- **Tab. 10:** 80 / 300 / 600 / 8000. **Pkt 5.8.2:** 25 cd przy 30° do wewnątrz.
- **Tab. 11:** F1 150 / 300; F2 150 / 840. **Pkt 5.9.4:** 140 cm².
- **Pkt 4.8.11 (stosunek stop/pozycyjne):** „co najmniej 5: 1 w granicach pola wyznaczonego przez proste poziome przechodzące przez ± 5 V” i pionowe ±10 H. Cytat dosłowny ✓.
- **Pkt 5.2.3:** 60 cd poniżej 5°D. **Pkt 5.2.4 i 5.5.3:** minima 0,05 i 0,3 cd.
- **Tab. A2-1:** wiersze R, RM, S, 2a zgodne. **Brak wiersza AR i F1/F2 jest prawdziwy** (L1 słusznie UNVERIFIED).
- **Pkt 5.11.3:** 2,5 / 2,0 cd/m², gradient 2 × B₀/cm. **Pkt 5.11.5:** 82°, zakaz emisji do tyłu. **Zał. 3 pkt 3.1–3.5:** wymiary kategorii tablic.
- **R150 tab. 3:** IA/IB 300 / 200 / 100 i 5 / 2,8 / 2,5. **Tab. 5:** IIIA 450 / 200 / 150 i 12 / 8 / 8. Mnożniki 2,5 i 4 (PL l. 1185, 1189). **Zał. 5 pkt 2.3/2.5/2.6:** 15 mm, ≥ 4 zestawy, 150–200 mm, 20 %.
- **R48 §2.11.1.1/.3/.4 i §2.11.2:** granice i narożniki barw biała / żółta samochodowa / czerwona, emitowane i nocne odbite. Zgodne.

**Errata (do poprawy w M59-FIX):**
- **E1.** README §2: RM1 „maks D = nd.” jest błędne. Tab. 4 daje dla „R1 lub RM1” 4 / 17 / **8,5**, a „nd.” dotyczy wiersza **MR**. Ten sam błąd jest w uwagach P16-020.
- **E2.** P16-302 i README §5.3: „żarówkowa 7-funkcyjna, 12 V”, a cytat z karty mówi „24 V 4xASS2”. URL wskazuje lampę LED 24 V.
- **E3.** P16-304: pole `punkt` mówi „mediana trzech kart”, a metoda czterech. Mediana głębokości 70 / 72,3 / 88 / 90 wynosi **80,15 mm**, nie 81.
- **E4.** P16-082: 75 cd to wymaganie **warunkowe**. Stosuje się tylko, „jeżeli oględziny światła wskazują na istnienie znaczącej miejscowej zmienności” (zał. 3 pkt 2.6). Cytat w wierszu nie zawiera liczby 75.
- **E5.** P16-095: ±85° / ±60° to odczyt z rys. A2-IV. Status powinien być ESTIMATED (odczyt rysunku), nie SOURCED.
- **E6.** README §1: „R150 zastępuje R3 i część R104 — pkt 1.1 R148” jest błędne. Uwagi wstępne R150 łączą regulaminy **3, 27, 69, 70 i 104** (Dz.U. s. 297, wstęp), a R148 pkt 1.1 R3 ani R104 nie wymienia.
- **E7.** README §4: „Gradient luminancji (max/min między punktami)” jest błędne. To gradient **na centymetr** między dwoma punktami pomiarowymi, ≤ 2 × B₀/cm, a nie stosunek max/min.
- **E8.** README §1: tezy o serii 01 UNECE (kat. 1 i 11 maks. 1200/600, „kat. 2a/2b, 5, 6, 12 bez zmian”) nie mają wiersza w manifeście ani cytatu. Trzeba dodać wiersz z cytatem z R148r1am2E albo oznaczyć UNVERIFIED.
- **E9.** P16-122/123/124/127 cytują wersję EN, choć PL istnieje (Dz.U. R150 l. 1185, 1189, 1193). Zgodnie z deklaracją README podstawą ma być tekst PL — podmienić cytaty.

## 4. Oględziny kadrów — opis Mistrala a obraz

| Kadr | Opis M59 (skrót) | Co widać (recenzent) | Ocena |
|---|---|---|---|
| P16-201 (CC0) | 2 pionowe zespoły 7-komorowe, gładki klosz, lampka tablicy centralnie | Naczepa koncepcyjna na targach. **Lampy w kształcie L** (bursztynowy pasek + czerwona komora) wtopione w zderzak. Nad bramą wąski pas czerwono-bursztynowy. W miejscu tablicy napis ostrzegawczy z trójkątami. Lampki tablicy nie widać | ✗ |
| P16-202 (CC0) | lewy zespół 7-komorowy + pojedynczy klosz, pryzmaty, lampka pod zderzakiem | Ten sam pojazd z drugiej strony. Te same lampy L, gładkie, bez pryzmatów. Brak tablicy | ✗ |
| P16-203 (CC0) | 3 komory w pionie: pomarańczowa, czerwona, biała | **Ramię kamery bocznej (lusterko-kamera)** z małym czerwono-pomarańczowym obrysem. To nie lampa tylna | ✗ |
| P16-204 (CC0) | 2 zespoły 3-komorowe, pryzmatyczny klosz, wyłączone; lampka na belce | Lekka ciężarówka, zdjęcie z **lampą błyskową** (EXIF Flash 9). Poziome prostokątne lampy: czerwone pole środkowe błyszczy plamkami (prawdopodobnie odblask oświetlony fleszem; czy lampa świeci — nierozstrzygalne), wokół bezbarwna obwódka z kubkami (wycinek 3×). Trzech komór ani pryzmatów nie widać. W miejscu tablicy tabliczka z marką, lampki nie widać | ✗ (budowa, lampka) |
| P16-205 (CC0) | 2 zespoły 3-komorowe, gładki klosz; lampka nad tablicą | Ta sama lampa z innej strony (flesz): czerwone pole + bezbarwna obwódka. Tabliczka z marką, **lampki nie widać** | ✗ (lampka) |
| P16-206 (CC0) | 4-komorowe, gładki klosz, 4. komora = obrysowe; lampka nad tablicą centralnie | Poziome lampy z **4 sekcjami** (wycinek z 3840 px): bezbarwna, czerwona z **rozetą punktów/pryzmatów**, 2 bezbarwne z żebrowaniem i kubkami; biała obudowa z 4 wkrętami. Liczba komór ✓, klosz NIE jest gładki, funkcji „obrysowe” nie da się przypisać. Tablica wysoko na ramie, lampki nad nią nie widać. Przy naczepie kontenerowej to najlepszy kadr paczki | ✗ (opis), kadr wartościowy |
| P16-207 (CC0) | po jednym zespole na stronę, gładki klosz | Podwozie kontenerowe **z boku**, lamp tylnych nie widać | ✗ |
| P16-208 (BY-SA) | 2 zespoły 3-komorowe, gładki klosz, lampka między zespołami | Podwozie kontenerowe z USA. **Okrągłe czerwone lampy FMVSS, po 2 na stronę**, odblaski, taśma. Nie ECE | ✗ |
| P16-209 (BY-SA) | jw. | Chłodnia z USA, **okrągłe lampy po 2 na stronę**. Nie ECE | ✗ |
| P16-210 (BY 4.0) | 2 zespoły 3-komorowe, gładki klosz | Naczepa-transporter z otwartą rampą, widok ¾ z tyłu. Lamp prawie nie widać | ✗ (nieweryfikowalne) |
| P16-211 (BY-SA 2.0) | zespoły 3-komorowe, gładkie, wyraźnie zabrudzone | Naczepa z boku, z odległości około 30 m. Lampy tylne to kilka pikseli. Brudu ani komór nie da się ocenić | ✗ (zmyślony detal) |
| P16-212 (BY-SA) | zespoły 3-komorowe, gładki klosz, zabrudzone | Naczepa z USA: **okrągłe lampy po 2 na stronę** na zardzewiałej belce. Brud ✓, typ ✗ | ✗ (typ), ✓ (brud) |
| P16-213 (BY-SA) | zespoły 3-komorowe, lampka poniżej lamp nad tablicą | Firanka z ciągnikiem terminalowym **z boku**, na nabrzeżu, z daleka. **Tyłu nie widać** | ✗ |
| P16-214 (CC0) | zespoły 3-komorowe, lampka nad tablicą | Ciągnik 8×4 **z przodu** na wystawie. **Tyłu nie widać** | ✗ |
| P16-215 (CC0) | zespoły 3-komorowe | Ciągnik **z przodu i boku** w hali. **Tyłu nie widać** | ✗ |
| P16-216 (BY-SA) | zespoły 3-komorowe, gładki klosz, lampka nad tablicą | Pojazd szynowo-drogowy od tyłu: **pojedyncze okrągłe lampy** (czerwone, bursztynowe, białe), uchwyt tablicy pusty | ✗ |
| P16-217 (CC0) | zespoły 3-komorowe, gładki klosz, punkty LED, lampka nad tablicą | **Pickup** z pionowymi lampami w stylu osobowym (czerwony klosz z żebrowaniem i białe cofanie). Zamiast tablicy napis | ✗ |
| P16-218 (BY-SA) | lampka tablicy: mały bezbarwny prostokąt nad tablicą; lampy 2-komorowe | Przyczepa kempingowa. Nad tablicą widać biały daszek z lampką ✓. Lampy są **pojedyncze okrągłe** | ✓ (lampka), ✗ (lampy) |
| P16-219 (BY-SA 3.0 pl) | nocą lampka nad tablicą świeci bezbarwnie | SUV nocą: biała poświata nad tablicą ✓ (to samochód osobowy) | ✓ |
| P16-220 (BY-SA 3.0) | nocą lampka tablicy nad tablicą, wyłączona | Ciężarówka z iluminacją **z przodu i boku**. Widać tylko **przednią** tablicę. Lampki tablicy nie ma | ✗ |
| P16-221 (BY 4.0) | lampka nad tablicą, bezbarwna, wyłączona; lampy 2-komorowe | Cysterna nocą od tyłu. Tablica na belce z lewej. **Lampki nie widać** (wycinek 3×). Lampy poziome: czerwony pas + biały pas odblaskowy | ✗ (lampka), ~ (lampy) |
| P16-222 (BY-SA) | lampka nad tablicą świeci; lampy 2-komorowe po bokach | Ciężarówka serwisowa **z boku**, nocą. **Tyłu nie widać** | ✗ |
| P16-223 (BY-SA) | **dzień**, lampka nad tablicą, 2-komorowe | Pickup-skrzyniowy **z przodu i boku**, **nocą** (nazwa pliku „at_night”). Tyłu nie widać | ✗ |

**Wynik:** z 23 kadrów 2 mają opis zgodny z obrazem, 2 częściowo (206, 212), 8 nie pokazuje tyłu, 5 to inne typy lamp (FMVSS ×3, okrągłe pojedyncze, osobowe pickupa), 1 to nie lampa; w żadnym nie widać lampki tablicy ciężarówki. Szablon zdania jest powtarzany bez oglądania. To ten sam wzorzec, co w M56, M57 i M62.

Wartościowe referencje do zachowania: **206** (lampa zespolona naczepy z bliska, 4 sekcje, rozeta i żebrowanie), **204/205** (lampa z bezbarwną obwódką, z bliska, flesz), 218 i 219 (lampka tablicy — pojazdy inne niż ciężarówka).

## 5. Gra a normy — konkretne liczby i poprawki

**G1. Stop i pozycyjne nie różnią się o zmierzchu (ADR 0181 r2 P2-5).**
- **Norma:** pkt 4.8.11 wymaga dla świateł wzajemnie sprzężonych stosunku (stop + pozycyjne) : pozycyjne **≥ 5:1** w polu ±5° V / ±10° H. Dla świateł oddzielnych z tab. 4 i 7 wynika minimum 60 cd (S1) przy maksimum 17 cd (R1), czyli **≥ 3,5:1** w osi.
- **Gra przed limiterem:** `TruckLights.cs` ma `TailNits = 1,3e3`, `BrakeNits = 2,0e4`, czyli **15,4:1** (spełnia).
- **Gra po limiterze 0178** (`knee 0,4`, `ceiling 0,8`): o zmierzchu oba trafiają w sufit. Pomiar after6 daje High 201 vs 202, Low 193 vs 194, czyli **≈ 1,0:1**.
- **Druga przyczyna:** naczepa ma **oddzielne** sekcje `rear_lens_tail_*` i `rear_lens_stop_*` (`trailer_build.py`, sekcje 17 % + 17 %), ale `trailer_export.light_group` przypisuje obie do `TAIL_BRAKE`. Przy pozycyjnych świecą więc obie sekcje (sekcja stop też), a przy hamowaniu obie skaczą do stopu. W rzeczywistej lampie zespolonej z oddzielnymi komorami przy pozycyjnych świeci tylko komora pozycyjna.
- **Poprawka (a):** rozdzielić grupy na naczepie. Sekcja `tail` dostaje grupę TAIL (wartość tail), sekcja `stop` nową grupę BRAKE (0 albo `BrakeNits`). Wtedy hamowanie zapala drugą komorę, co da się odróżnić nawet przy limiterze.
- **Poprawka (b):** dla komór wspólnych (ciągnik, lampa `lens_red` = TAIL_BRAKE) przenieść stosunek do domeny po limiterze. Limiter ma liczyć sufit dla poziomu stopu, a stan pozycyjny skalować liniowo: `wyj = lim(BrakeNits·k) · (stan / BrakeNits)`. Przy obecnych nitach daje to pozycyjne ≈ 0,8 / 15,4 = **0,052** liniowo (15:1). **Cel:** pozycyjne w przedziale 0,052–0,16 liniowo o zmierzchu (0,16 = 0,8 / 5 to górna granica z pkt 4.8.11; sRGB ≈ 0,44, czyli ~112/255 wobec ~231/255 dla stopu). Jeśli 0,052 będzie wizualnie za ciemne, podnieść pozycyjne do co najwyżej 0,16. WORKING_VALUE.
- **Test:** EditMode readback stosunku stop/pozycyjne ≥ 5 przy ekspozycji zmierzchu i dnia oraz pomiar ROI z P2-5 po zmianie.

**G2. Czerwień `(1, 0, 0)` (ADR 0178 pkt 2).**
- R48 §2.11.1.4 według Dz.U. ma granicę purpury `y = 0,980 − x` (obszar: x + y ≥ 0,980). Czerwień sRGB (0,640; 0,330) ma x + y = **0,970**, czyli leży **poza** obszarem o 0,010.
- Cały obszar czerwieni ECE leży poza gamutem sRGB: maksimum x + y w trójkącie sRGB to 0,970, w samym prymarnym czerwonym. `(1, 0, 0)` jest więc najlepszym osiągalnym punktem — kodu nie zmieniać.
- **Poprawka tekstu ADR 0178:** zamiast „w obszarach ECE” napisać „najbliższy osiągalny punkt; obszar R48 czerwony poza sRGB”. Cytat R48 jest teraz SOURCED (Dz.U. L 347 s. 1, §2.11.1.4) — wcześniej był „pośredni, GRE 2006/25”.

**G3. Bursztyn `(1, 0.28, 0)` — POZA R48.**
- R48 §2.11.1.3 (Dz.U.) ma granicę zieleni `y ≤ x − 0,120`. Bursztyn gry to x 0,524, y 0,422, a granica w tym punkcie wynosi 0,404, więc **przekroczenie o 0,018 w stronę żółto-zielonej**.
- Pasmo 0,398 ≤ y ≤ 0,429 z ADR 49/00, użyte w ADR 0178, nie jest pasmem R48.
- Także r1 `(1, 0.25, 0)` (y 0,415 przy granicy 0,413) był tuż poza obszarem.
- W gamucie sRGB czworokąt A1–A4 R48 zawiera `(1, g, 0)` dla **g ≈ 0,16–0,245** (x 0,535–0,562, y 0,392–0,413; policzone macierzą sRGB→XYZ D65).
- **Poprawka:** `TruckLights.Amber = (1, 0.22, 0)` (x 0,542, y 0,408 — najmniej pomarańczowy punkt ze środka zakresu, zgodnie z życzeniem recenzji s18). Do tego test `TruckLampEncodingTests` sprawdzający czworokąt A1–A4 z R48 zamiast pasma ADR 49/00.
- To samo dotyczy `a6_export.py:90` (`IND_*` preview `(1.0, 0.42, 0.02)`, tylko podgląd).

**G4. Lampka tablicy (ADR 0181 pkt 3).**
- „R4: ≥ 2,5 cd/m² — z pamięci, UNVERIFIED” jest teraz **SOURCED**: R148 pkt 5.11.3 lit. a, 2,5 cd/m² dla kat. 1b (520 × 120; tablica PL 520 × 114) **w każdym punkcie pomiarowym**.
- **Metoda normy (pkt 5.11.2):** luminancję mierzy się na rozpraszającej powierzchni i koryguje do współczynnika odbicia **1,0**, w punktach z zał. 3 (rys. A3-X; okręgi 25 mm). Albedo tablicy nie wchodzi do porównania.
- **Gra:** `MarkerNits 2000 × _PlateIllum 0,005 × plate` przy ρ = 1 daje 10 cd/m² × `plate`. `plate = 1/(1 + (x² + y²)/100²)` (`KamionLampLens.hlsl`, x poza listwą 0,22·W, y od listwy 15 mm nad krawędzią). Wychodzi: góra-środek ≈ **9,8 cd/m²**; skrajny dolny róg ≈ **2,1 cd/m²**; punkt ~20 mm od dołu i ~40 mm od boku (położenie punktów z rys. A3-X **niesprawdzone** — ESTIMATED) ≈ **3,0 cd/m²**.
- **Ocena:** punkty pomiarowe prawdopodobnie spełniają minimum 2,5, ale z zapasem ~20 %; róg poza punktami jest poniżej. Gradient przy B₀ ≈ 3 dopuszcza 6 cd/m²/cm, a w grze jest ~0,6–0,8 cd/m²/cm — OK.
- **Rekomendacja:** odczytać punkty z rys. A3-X i dodać test EditMode „min luminancja w punktach A3-X przy ρ = 1 ≥ 2,5 cd/m²”. Jeżeli test nie przejdzie, podnieść `_PlateIllum` do ≥ 0,0065 albo spłaszczyć zanik. ADR 0181: „R4 z pamięci, UNVERIFIED” zmienić na R148 5.11.3 lit. a (SOURCED).
- **Do sprawdzenia:** pkt 5.11.5 zakazuje emisji bezpośrednio do tyłu, a `PLATE` ustawia też lico listwy lampki na `MarkerNits` (2000 cd/m², biel). Jeżeli lico listwy patrzy do tyłu, lampka świeci kierowcy z tyłu jak biała kropka. Klosz powinien patrzeć w dół, na tablicę, a z tyłu być ciemny. Kamera `plate-trailer` z ADR 0181: obejrzeć.

**G5. Wymiary lampy zespolonej naczepy.**
- **Gra** (`trailer_build.py` `rear_lamp_body`): **520 × 170 × 75 mm** (x 0,66–1,18; z ± 0,085; y −0,045…0,03).
- **Karty P16-301…305:** 390–450 × 138–153 × 70–90 mm (mediana 425 × 142 × 80).
- Lampa gry jest o **~22 % dłuższa i ~20 % wyższa** od mediany. To WORKING_VALUE z ADR 0175, które mieści 5 sekcji: ind / tail / stop / rev / fog.
- **Rekomendacja:** przy najbliższej zmianie geometrii zmniejszyć do ~450 × 145 mm (górna granica kart) albo zapisać w ADR, dlaczego 520 × 170. Nie jest to warunek scalenia.

**G6. Soczewki (ADR 0181) a kadry.**
- M59 nie dostarcza materiału do oceny struktury LED: jedyne zbliżenia to 204/205 i 206, wszystkie zgaszone (204/205 z fleszem).
- **P16-206** pokazuje dla naczepy **bezbarwne sekcje z żebrowaniem i kubkami** obok czerwonej z rozetą punktów. Zgaszona lampa jest głównie jasna i bezbarwna, nie „ciemne szyby”. To argument za obecnym otwartym punktem ADR 0181: „niezapalona cofania / przeciwmgłowa = ciemna szyba” nie odpowiada lampie z jasnym wkładem.
- **P16-204/205** pokazuje czerwone pole z plamkami (odblask w świetle flesza) w bezbarwnej obwódce z kubkami. Jak wygląda zapalona komora, z tych kadrów nie wynika.
- Do decyzji artystycznej potrzebne są lepsze kadry (M59-FIX pkt 3).

## 6. Co przyjąć bez zmian

Przyjmuje się wiersze P16-003…144 (fotometria R148/R150/R48, znaki homologacji) z erratą E1–E9; P16-001/002 (GSR2) nie sprawdzono, wiersze P16-301/303/305 (wymiary, tylko liczby) oraz licencje i seed audytu. Wiersze P16-201…223, README §5.1, §5.2 i §6 oraz audyt części zdjęciowej są do przerobienia.

## 7. Dla lidera

- Poprawki G1 (rozdzielenie TAIL/BRAKE na naczepie + stosunek ≥ 5:1 po limiterze) i G3 (bursztyn w czworokącie R48) można zlecić od razu jako follow-up ADR 0178/0181 — nie zależą od M59-FIX. G4 to test plus ewentualne podbicie `_PlateIllum`.
- 71/78 cytatów przepisów potwierdzonych dosłownie w Dz.U.; GSR2 (P16-001/002) i seria 01 UNECE niesprawdzone.
