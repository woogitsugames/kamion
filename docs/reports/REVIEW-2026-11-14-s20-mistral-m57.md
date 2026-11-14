# Przegląd M57 (P14 wieżowiec „Biazet”, Andersa 38, Kwadrat Park): elewacje NE/NW, parter, dach — s20, 2026-11-14

**Werdykt: FIX.** Część formalna jest dobra: OSM, BDOT10k i LoD się zgadzają, ZIP ma poprawne sha256, licencje są czyste, Google nie użyto, ściana NE jest uczciwie UNVERIFIED. Ale kluczowe ustalenia zdjęciowe są błędne albo zmyślone:
- **Kadr 073045 pokazuje szczyt SW i ścianę NW, nie SE.** Kamera stoi na SW–WSW od wieży, a nie na S. Szczyt jest po prawej, długa ściana po lewej. Wiersz P14-007 („fragment SE po prawej”) jest fałszywy.
- **Ściana NW nie ma siatki osobnych okien.** Ma poziome pasma, po 6 grup okien na kondygnację na ochrowym tynku (073045, 105711, 115626). Teza „ortofoto ujawnia siatkę na NW” nie wynika z kafelka WMS w ZIP-ie (P14-015): na nim widać tylko ściany SE i NE, a NW zasłania dach. Kafelek repo 2024-05-27 (ADR 0180/0190) pokazuje NW, ale jako rzędy krótkich kresek, które nie rozstrzygają między siatką a pasmami ze słupkami.
- **Kadry KartaView P14-017 i P14-018 pokazują wieżę wyraźnie.** Przy prawej krawędzi widać szczyt SW z napisem i ścianę SE. Manifest i audyt piszą „wieży brak”. Opisy audytowe kadrów KV (P14-004, 005, 017) opisują treść, której w obrazach nie ma.
- **P14-012 (parter NW: „witryny + wejście”, SOURCED)** to witryny hali giełdy. Parteru wieży w 105711 nie widać.
- Ortofoto ma cienie skierowane na **NW**, nie na NE. Nadbudówki maszynowni o wysokości ok. 1 kondygnacji nie widać na żadnym kadrze. Kierunki KV 14055 (357°) są sprzeczne z obrazem: kamera jedzie na SE estakadą.

Blok poprawek: `docs/owner/MISTRAL-FIXES-12.md` § M57-FIX. Nic nie scalono, nic nie scommitowano, PR #56 bez komentarza. **Dla gry przegląd daje konkretne poprawki** (§6): NW = pasma w 6 grupach (nie siatka), środkowy maszt kratowy, maszty przy końcu NE, parterowy przybudówek SE. Kolor SE (biała czy piaskowa) to otwarty konflikt źródeł.

## 1. Zakres i metoda

- PR #56, gałąź `origin/research/mistral-p14-office-tower` @ `502d574e9` (6 commitów od `54a50ad3f`). Zmiany są tylko w `research/mistral/p14-office-tower/` (README, manifest 18 wierszy, sources, audit, `.gitignore`). Pliki obejrzane przez `git archive` w scratchu.
- ZIP `~/Downloads/mistral-p14-office-tower-files.zip`: **8 341 903 B, sha256 `a4e05d20…eaddd4e` = README ✓**. 29 pozycji = 26 plików + 3 katalogi. Rozpakowany w `research/_incoming/mistral-p14-office-tower-files/`. md5 nie ma duplikatów (26 unikalnych).
- **Obejrzałem wszystkie 26 plików** (pomniejszone do ≤ 960 px) i wycinki 3–6×: 073045 (góra i dół), 105711, 115626 (całość, pasma, dach), KV 1326673613 i 993062122 (wieża), ortofoto 80 m (dach, ściana SE). Do koloru wziąłem medianę sRGB pól; ramki próbek narysowałem na wycinkach i obejrzałem (`b19.png`, `b21.png`, `bo.png`).
- OSM: `Data/raw/osm/podlaskie-261108.osm.pbf`, pyosmium (`uv run` w tools/worldgen, `python -I`). Lokalny ENU od środka wieży.
- Commons API (imageinfo/extmetadata) dla 073045, 105711 i 115626: licencja, autor, data, rozmiar oryginału (4608 × 2592).
- Gra: ADR 0180, 0190, `Data/Regions/bialystok-industrial-c/overrides.yaml` (`g3a-office-tower-colour`, `roof_masts`), rendery `artifacts/tower2-0190/r2/` (`photo-vs-r2-s150.jpg`, `z/High-nw60.jpg`, `z/ph177.jpg`), ortofoto repo `artifacts/tower2-0190/ortho-roof.jpg` (2024-05-27, 0,25 m).

## 2. Kryteria akceptacji M57

| Kryterium | Wynik |
|---|---|
| Pozycja i way_id obiektu, środek | **TAK.** way/219260018 „Biazet”, środek 53.153231, 23.168022 = PBF (≤ 1 m). Normalne krawędzi w OSM: 212 / 122 / 301 / 31°. README podaje 208 / 118 / 298 / 28° (BDOT, ADR 0180), różnica 3–4°. Giełda way/219260052 leży na az 322°, 281 m ✓ (NW). Circle K way/236606116 na az 189°, 72 m ✓ |
| Zdjęcia każdej ściany NE/NW/SE/SW i parteru, każdy kadr OBEJRZANY z poprawnym opisem | **NIE.** SW ✓ (073045). NW jest, ale z błędnym układem okien (§3). SE: jedyne dwa kadry, które ją pokazują (P14-017/018), opisano jako „wieży brak”. Fragment SE z 073045 (P14-007) nie istnieje. NE: UNVERIFIED, uczciwie. Parter: P14-012 przypisany do złego budynku |
| Dach: liczba, wysokości metodą 3,7 m, położenie, kolor | **CZĘŚCIOWO.** Liczba 4–5 i metoda są jawne. Rozmieszczenie z ortofoto jest opisane niedokładnie (§4). „Nadbudówka ~1/4 dachu, ~1 kondygnacja” (SOURCED) nie ma potwierdzenia w kadrach. Cienie są na NW, nie na NE |
| UKE / BIP | Dwie decyzje (Play BIA1035, T-Mobile 24026) z URL. **Nie sprawdzałem ponownie strony BIP UKE.** Przyjęte warunkowo |
| Pozycja kamery WGS84, kierunek z API/EXIF albo UNVERIFIED | **CZĘŚCIOWO.** Commons: pozycje UNVERIFIED, ale 073045 umieszczona po złej stronie (S zamiast SW–WSW). KV 14055: heading API 357° wpisany jako SOURCED, choć obraz i tor (bearing 7119872→7119876 = 123°) pokazują jazdę na SE |
| Samokontrola ≥ 20 %, jawny seed, kadry ponownie OBEJRZANE | **NIE (merytorycznie).** Seed 14 daje `[4, 17, 8, 5]` = ta sama próba ✓. Ale opisy „zaobserwowano” dla P14-004 (błoto/trawa, dom z dwuspadowym dachem), P14-005 (stacja paliw z literami, blok 4–5 kond.) i P14-017 (hale, ogrodzenie z blachy) **nie odpowiadają obrazom**: estakada, akumulator ciepła EC i w 017 sama wieża. Audyt P14-008 potwierdził „witryny” hali, które potem przypisano wieży. W audycie P14-005 i P14-017 mają etykietę „dach”, a w manifeście „ściana_SW” i „ściana_SE” |
| JPG ≤ 1600 px | **Prawie.** 20210328_110412 ma 1280 × 2276. README podaje „KV lth 1280×960”, ale 2 z 7 to 1280 × 720 |
| Licencje, zakaz Google | **TAK.** Commons API: 073045 CC BY 3.0, 105711 i 115626 CC0 (Rakoon, daty EXIF zgodne). KV CC BY-SA jako referencja, GUGiK, ODbL. Mapillary uczciwie pominięty |
| Dedup względem REFERENCES/INDEX | TAK (deklaracja). 110808 i 131224 są w ZIP-ie, ale nie ma ich w sources.md (kadry bez wieży) |

## 3. Oględziny kadrów — opis Mistrala a obraz

Strony ściany z geometrii. Kamera na azymucie φ od wieży widzi ścianę o normalnej n, gdy cos(φ − n) > 0. Szczyt SW jest po prawej, a długa ściana po lewej tylko wtedy, gdy φ ∈ (212°, 301°). Wtedy długa ściana to **NW**.

| Kadr | Opis / status M57 | Co widać (recenzent) | Ocena |
|---|---|---|---|
| P14-001 (073045, CC BY) | szczyt SW frontalnie, kamera S (53.151600, 23.168000) | Szczyt z napisem i jedną kolumną okien **po prawej**, długa ściana **po lewej**. Stosunek szerokości rzutów (≈ 1:2) daje φ ≈ 220–250°, czyli kamera SW–WSW od wieży, ok. 150–200 m, na/przy Andersie (ESTIMATED; nie S). Kolumna: 10 okien + pas szklenia parteru w prawej połowie podstawy. Ramy białe w ciemnoszarym obramieniu. Klimatyzatory pod **4. i 5. oknem kolumny od góry** (nie „przy prawym narożniku”). Tak samo jest na szczycie SW w Mapillary (`ph177.jpg`, ADR 0190), co niezależnie potwierdza, że to szczyt SW, a nie NE. Drabiny brak. Rur brak. Na szczycie możliwe pionowe żebrowanie okładziny (moiré w 1280 px, UNVERIFIED) | ✓ SW / ✗ pozycja kamery, szczegóły |
| P14-007 (073045) | „fragment ściany SE skośnie po prawej” | **Po prawej od szczytu jest niebo.** Lewa ściana = **NW**: poziome pasma okien w białych ramach na ochrowym tynku, klimatyzatory | **fałszywy** (to NW) |
| P14-008 (105711, CC0) | NW, „regularna siatka, ~6 kolumn”, witryny + wejście, 2 maszty, nadbudówka | Wieża w środku kadru, w tle. Długa ściana prawie frontalnie, wąski pasek szczytu po prawej. **Pasma okien w grupach** (biało obramowane), tynk ochrowy. Parter zasłonięty namiotami i ludźmi. Ponad dachem ok. 8 konstrukcji, w tym **2 wysokie maszty**: w środku długości i przy końcu SW. Nadbudówki brak | ✓ NW / ✗ układ, parter, nadbudówka |
| P14-009 / P14-014 (115626, CC0) | „4 maszty po prawej”, układ nierozstrzygnięty | NW frontalnie. **Każda kondygnacja ma 6 grup po ok. 5 okien**, rozdzielonych wąskimi filarami. Ułamki długości od lewej (koniec NE), ESTIMATED ±0,02: [0,01–0,14], [0,17–0,30], [0,33–0,47], [0,51–0,64], [0,67–0,81], [0,84–0,99]. Widać 9–10 rzędów (dół za namiotami). Dach: **wysoki maszt kratowy w ok. 0,48 długości** (ok. 2,8 podziałki kondygnacji ponad attyką), **maszt z odciągami w ok. 0,89 (przy SW)** podobnej wysokości, 3–4 krótsze maszty z panelami przy końcu NE, anteny na narożniku W. Ciemny pionowy pas spod środkowego masztu (feeder?) przez ok. 1–2 kondygnacje | ✗ rozkład masztów, ✓ 11 kond. |
| P14-002–006 (KV 14055, 2016) | „wieży brak — zasłona drzew/słupów, zbiornik stacji paliw”, heading 357° | Wszystkie 5 klatek: **jazda estakadą Andersa na SE** (tor pozycji = 123°). Na wprost/po prawej biało-niebieski zbiornik z logo — najpewniej akumulator ciepła EC Białystok (nie sprawdzałem w PBF), na pewno nie zbiornik stacji paliw. Wieża za kamerą. Pięć identycznych zdań szablonowych | negatyw ✓, uzasadnienie i kierunek ✗ |
| P14-017 (KV 993062122, 2019) | „wieży brak, hale giełdowe, ogrodzenie z blachy” | **Wieża przy prawej krawędzi** (za latarnią): szczyt SW z napisem i kolumną po lewej, **ściana SE z grupami okien na żółtym tynku** po prawej, maszty | **fałszywy negatyw** |
| P14-018 (KV 1326673613, 2021) | „wieży brak” | **Wieża wyraźna, w słońcu**, przy prawej krawędzi. Szczyt SW (napis, kolumna białych okien) i **ściana SE: krótka grupa okien przy narożniku S, przerwa, dłuższe pasmo** (zgodne z ADR 0180). **Tynk SE jasnożółty jak szczyt.** Dach: 2 wysokie maszty kratowe (przy W i dalej wzdłuż osi, ok. 2,3–2,7 podziałki ponad attyką), białe anteny panelowe wzdłuż krawędzi SE, 2 maszty z talerzami | **fałszywy negatyw, najlepszy kadr SE** |
| P14-015 (orto 80 m) | maszty 2 + 2, nadbudówka jaśniejsza centralna, cienie na NE, „przechył ujawnia NW = siatka, SE = ciemne pasy” | Dach ciemnoszary. **4 podstawy kratowe (X):** narożnik N, narożnik E, środek krawędzi SE, narożnik W (największa, z długimi odciągami). Przy końcu SW kraty i platformy z antenami. Kilkanaście niebieskich wentylatorów dachowych. Długi prostokąt korytek kablowych wzdłuż osi (nie jasna nadbudówka). **Cień budynku i masztów pada na NW.** W tym kafelku dach jest przesunięty względem podstawy na W, więc widać **ścianę SE** i **wąski pas szczytu NE**. Ściana SE jest w słońcu prawie biała, mediana (228, 229, 220); pasm w rzucie nie da się rozdzielić. Szczyt NE jest w cieniu, szary khaki, z ciemniejszą plamką w środku — zgodną z kolumną okien, ale to tylko poszlaka. **Ściany NW w tym kafelku nie widać.** (Inny kafelek, repo 2024-05-27, pokazuje NW: jasnokremowa, rzędy krótkich kresek.) Przy środku ściany SE niski przybudówek (ok. 1 kondygnacja, krótki cień) | ✗ NW, ✗ cienie, ✗ nadbudówka |
| orto 160 / 320 m | kontekst | Andersa na S/SW, cień wieży na NW. Duża hala na N w kafelku 320 m to nie giełda (giełda leży 281 m na NW, poza kafelkiem) | — |
| 065632, 072453, 073116, 152417, 152422, 105802, 105959, 110412, 110541, 110808, 131224, 20191211 ×2 | kontekst / „wieży brak” | Wieży brak ✓ (estakada B, budynek 38A, wnętrza hali, stragany) | ✓ |

**Kolor SE — otwarty konflikt** (mediana sRGB, ramki obejrzane):
- Za „żółta jak szczyt”: KV 2019 SE (206, 190, 138) przy szczycie (169, 159, 130); KV 2021 SE (137, 138, 106) i (157, 153, 119) przy szczycie w słońcu (204, 203, 170). W obu kadrach SE ma ten sam odcień co szczyt.
- Za „biała”: Mapillary 2020-08-15 (ADR 0180: ok. (249, 248, 246); szczyt tam khaki) i kafelek WMS w ZIP-ie (SE w słońcu (228, 229, 220)).
- Kamery KV mają silną kompresję i inny balans bieli. Mapillary i ortofoto mogą przepalać jasne ściany. Nie rozstrzygam: **WORKING_VALUE**, decyzja po sesji zdjęciowej właściciela (pkt 6).

## 4. Dach — zestawienie źródeł

| Element | Ortofoto 80 m | 105711 / 115626 (z NW) | 073045 (z SW–WSW) | KV 2021 (z SSE) | Gra (`roof_masts`, ADR 0190) |
|---|---|---|---|---|---|
| Wysoki maszt kratowy przy końcu SW / narożniku W, z odciągami | X z odciągami przy W | maszt z odciągami w 0,89 długości | maszt z odciągami tuż za lewą częścią szczytu | lewy wysoki maszt | lattice SW u 0,30, 9,5 m ✓ |
| **Wysoki maszt kratowy w środku długości (przy krawędzi SE)** | X w środku krawędzi SE | maszt w 0,48 długości, ≈ tej samej wysokości | prawdopodobnie zasłonięty przez pierwszy (oś widoku ≈ oś budynku) | prawy wysoki maszt | **brak**. Uwaga: w Mapillary 2020-08 z S (`ph177.jpg`), w miejscu gdzie powinien stać (ok. x 400), widać tylko krótki maszt. Niezgodność do wyjaśnienia: inny czas? inna pozycja? |
| Narożnik S | kraty, małe anteny, bez X | — | anteny panelowe na ścianie, sięgają ok. linii attyki | panele wzdłuż SE | lattice SW u 0,90, **6,5 m**. Mapillary `ph177`: konstrukcja ok. 1,5 kondygnacji przy S — **konflikt z 073045 i ortofoto** |
| Koniec NE (narożniki N i E) | X przy N i przy E | 3–4 krótsze maszty z panelami | panele na dalekim końcu | — | tylko pole SE u 0,97, 2,6 m |
| Nadbudówka ≥ 1 kondygnacja | brak (korytka) | brak | brak | brak | brak ✓ |
| Wentylatory | kilkanaście, niebieskie | — | — | — | brak (drobne, pominąć) |

Wysokość środkowego masztu: w 115626 widać ok. 2,8 podziałki kondygnacji (3,8 m) ponad attyką, a dolne ok. 1,5–2 m zasłania attyka. Daje to **ok. 10–12 m nad dachem (ESTIMATED)**. KV 2021 daje podobny wynik (ok. 2,7 podziałki).

## 5. Uczciwość statusów

Do pochwały: NE zostało UNVERIFIED („nie dopisywać »jak SW«”), wysokości mają przedziały ESTIMATED z metodą, negatywy Panoramax i NMPT są udokumentowane, a rozbieżność „ciemne vs białe ramy” zapisano zamiast ją ujednolicać. W tej rozbieżności obie strony mają częściowo rację: białe skrzydła w ciemnoszarym obramieniu.

Błędy: SOURCED dla NW-siatki (przesłanka z ortofoto zmyślona), P14-007, P14-012 i nadbudówki. „Zaobserwowano” w audycie nie pochodzi z obrazów. Wniosek „przypisanie NW z 3 przesłanek” jest trafny tylko co do strony ściany, a „oświetlenie szczytu” to argument słaby przy zachmurzeniu.

## 6. Porównanie z grą i konkretne poprawki

| Element | Gra dziś | Przegląd M57 | Działanie |
|---|---|---|---|
| **NW — układ okien** | bez reguły: haszowana siatka okien punktowych `office_d` (antracytowe ramy), `plaster_beige` (render `z/High-nw60.jpg`: ok. 10 kolumn ciemnych okien) | **6 grup pasmowych na kondygnację**, ok. 5 świateł w grupie, białe ramy, jasne szkło/żaluzje, tynk jak szczyt (073045, 105711, 115626) | **P1:** reguła `facades` `{facing: NW, min_len_m: 30, windows: ribbon, glazing: light, sill_m: 1.0, head_m: 2.3, spans: [[0.01,0.14],[0.17,0.30],[0.33,0.47],[0.51,0.64],[0.67,0.81],[0.84,0.99]]}` (ułamki od końca NE; sprawdzić konwencję `spans` i to, czy po `footprint_open_m` NW jest jedną krawędzią — w OSM to 4 współliniowe odcinki 9,6+6,1+11,5+9,6 m). Ściana bez `plaster_white`. Kamera kontrolna: z pozycji 115626 (giełda, ok. 145 m na NW) |
| SE — kolor | `wall_material: plaster_white` | konflikt: KV 2019/2021 — odcień jak szczyt; Mapillary 2020 i ortofoto WMS — prawie biała (§3) | **P2, na razie bez zmiany:** test A/B `plaster_beige` vs `plaster_white` na kamerze KV 1326673613; decyzja po sesji zdjęciowej (pkt 6) |
| SE — pasma | krótki odcinek 0,03–0,20 + długie od 0,30 | KV 2021 potwierdza krótką grupę przy S, przerwę i dłuższe pasmo. Dłuższe pasmo może być dzielone filarami jak na NW (rozdzielczość nie rozstrzyga) | bez zmian. Ewentualnie podział jak NW, gdy kadr 4608 px pokaże filary |
| **Maszt środkowy** | brak | kratowy, ok. 10–12 m (ESTIMATED), ok. 0,5 długości, przy krawędzi SE (ortofoto X, 105711, 115626, KV 2021; brak w Mapillary 2020 — §4) | **P1:** dodać `{kind: lattice, facing: SE, u: 0.5, inset_m: ~2, height_m: 11, sectors: 3}` |
| Maszt narożnika S 6,5 m | lattice SW u 0,90, 6,5 m | Mapillary 2020 (z S): konstrukcja ok. 1,5 kondygnacji przy S. 073045 (z SW–WSW): tylko panele na ścianie do linii attyki. Ortofoto WMS: bez X przy S | **zostawić z adnotacją konfliktu** (wysokość UNVERIFIED). Rozstrzygnie sesja zdjęciowa albo oryginał 073045 w 4608 px |
| Koniec NE | pole SE u 0,97, 2,6 m | ortofoto: kratowe przy N i przy E. 115626: 3–4 maszty ok. 4–6 m z panelami | **P2:** maszt ok. 5 m z panelami przy N (`facing: NE` / `NW` u ≈ 0,95) i podnieść maszt E do ok. 5 m (ESTIMATED) |
| Odciągi masztu W | brak (ADR 0190 Otwarte) | widoczne w 073045, 115626, ortofoto | P3 (sylwetka z 150 m) |
| 4 maszty z bębnami wzdłuż SE | 4 pole | KV 2021: 2 maszty z talerzami w prawej części, panele wzdłuż krawędzi | bez zmian (pozycje UNVERIFIED) |
| Nadbudówka maszynowni | brak | brak na wszystkich kadrach | ✓ — **nie przyjmować** tezy M57 |
| Parter SE | `footprint_open_m: 3.3` usuwa występ BDOT 6,3 × 1,8 m (ADR 0180: „czym jest przy gruncie — nieznane”) | ortofoto: niski (ok. 1 kond.) przybudówek przy środku SE, w miejscu występu BDOT | **P2:** występ BDOT to najpewniej parterowy wiatrołap/przybudówek. Dodać bryłę 1-kondygnacyjną, wieżę zostawić prostą (ESTIMATED, wymiar z BDOT) |
| Parter SW | wiata Circle K. W LOD1 szczyt SW ma 10 okien | 073045: pas ciemnego szklenia w prawej (S) połowie podstawy szczytu | P3: okno/pas parteru przy S zamiast pustego pola |
| Ramy kolumny szczytu | `variants: [2]` biała rama | białe skrzydła w ciemnoszarym obramieniu | P3 (opcjonalnie ciemna opaska) |
| NE | kopia reguły SW (WORKING_VALUE) | brak zdjęcia. Ortofoto: wąski ochrowy pas z ciemniejszą plamką w osi (poszlaka kolumny) | bez zmian, confidence low |
| Rury spustowe | `downpipes: false` | 073045 / 115626: brak rur zewnętrznych na SW i NW | ✓ potwierdzone dla NW |
| Bramka 3 / referencje | Mapillary 177786… / 178689… | nowe: 115626 (CC0, NW frontalnie), 073045 (CC BY 3.0, SW + NW), KV 1326673613 (BY-SA, tylko ref.) | dodać do `gate3_reference_map.json` jako kadry porównawcze |

Korekta do ADR 0180 §2.5 i komentarza override: odczyt „NW long wall (orthophoto 2024-05-27, building lean): regular grid of punched windows” to interpretacja silnie skróconego rzutu. Widać w nim rzędy krótkich kresek (`ortho-roof.jpg`), które nie odróżniają siatki od pasm ze słupkami. Rozstrzygają trzy zdjęcia z boku (073045, 105711, 115626): **pasma w 6 grupach**. Kolor NW (jasny piaskowy) potwierdzają zgodnie ortofoto i zdjęcia. ADR 0190 §1 („NW ma ten sam plan okien na LOD0 i LOD1”) jest spójny wewnętrznie, ale sam plan nie zgadza się ze zdjęciami.

## 7. Dla lidera

- **Nie scalać** M57 w obecnej postaci (blok M57-FIX). Na wynik FIX nie trzeba czekać z poprawkami gry z §6. Przekazać do następnego zadania wieżowca (ADR 0190 r3 / nowy ADR), w kolejności: (1) reguła NW pasmowa, (2) dodać maszt środkowy ok. 11 m (maszt „S 6,5 m” zostaje z adnotacją konfliktu), (3) maszty końca NE, (4) parterowy przybudówek SE, (5) test A/B koloru SE (bez zmiany przed sesją zdjęciową).
- Pętla wizualna dla tych poprawek: kamery z pozycji 115626 (NW), 073045 (SW–WSW, ok. 150–200 m) i KV 1326673613 (53.151269, 23.169290, kierunek 302°).
- Wycinki recenzenta (tymczasowe): scratch sesji `…/scratchpad/m57/img/` (`c073045_top/bot.jpg`, `c105711.jpg`, `c115626*.jpg`, `c_kv3686.jpg`, `c_kv2769.jpg`, `o80_roof.jpg`, `o80_se.jpg`, `g_*.jpg`).
