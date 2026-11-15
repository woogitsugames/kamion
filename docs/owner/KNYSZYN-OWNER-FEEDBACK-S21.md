# Knyszyn — opinia właściciela (15.11 ~19:0x, s21)

Właściciel pochodzi z Knyszyna. Po obejrzeniu renderów High za dnia (stan po 0216: rynek-above, rynek-fountain, tykocka-rynek-junction, dk65-inlet-south):

- **Z poziomu ulicy w ogóle nie poznaje miasta.**
- Rynek rozpoznaje WYŁĄCZNIE z lotu ptaka i tylko po trójkątnym kształcie.

Wnioski dla szlifu (knyszyn-rynek-0227, Codex):
1. Kryterium sukcesu = właściciel rozpoznaje miejsce z kabiny / kamery na wysokości oczu, nie z góry. Każda kamera kontrolna Rynku na wysokości 1,7–2,5 m, w miarę ten sam kadr co zdjęcia właściciela (`research/_incoming/owner-knyszyn-photos-2026-11-14/`).
2. Na kadrze „rynek-fountain” jest pusty plac z kostki z dwiema wiatami i budką — brak fontanny (stoi ~93 m dalej w zachodnim parku wg ortofoto), brak charakteru rynku małego miasta. Plac wschodni wygląda jak parking, nie jak rynek.
3. Kolejność: (a) poprawne położenie i bryła tego, co widać na zdjęciach właściciela z każdego kadru (fontanna, park, pierzeje, kościół, jeśli w kadrze); (b) wysokości, dachy, kolory i parterowe witryny pierzei wg zdjęć; (c) nawierzchnie, zieleń, mała architektura.
## Zdjęcie Rynku od właściciela (15.11 ~19:1x, z lotu ptaka, zachód słońca; tylko opis — plik w czacie, źródło i prawa nieznane, NIE do gita ani tekstur)
Co widać (obejrzane przez lidera), patrząc mniej więcej wzdłuż osi trójkąta w stronę kościoła:
- Rynek to **trójkątny skwer trawiasty**, nie plac z kostki: dwa duże trawniki rozdzielone ukośną alejką z szarej kostki, alejki obwodowe szare, ławki. Drzewa **liściaste, rzadko** (kilka dużych lip/klonów, **wierzba płacząca** przy środku, świerk/sosna pojedynczo na prawym rogu), NIE gęsty las sosnowy.
- Wzdłuż prawego boku trójkąta **pas parkingowy z czerwonej/bordowej kostki** (skośne miejsca), chodniki wokół też w dużej części czerwona kostka.
- Dwie jezdnie asfaltowe obiegają trójkąt (lewa z linią krawędziową i przejściem dla pieszych w zebrę u wierzchołka, prawa łączy się u wierzchołka); przejścia zebry u ostrego końca trójkąta.
- Na końcu osi: **kościół z czerwonym dachem i białą wieżą zakończoną czerwonym, ostrym hełmem** — główny punkt orientacyjny, widoczny ponad drzewami.
- Po prawej: **duży biały budynek, 2 kondygnacje + mansarda, czerwony dach z lukarnami** (urząd/budynek publiczny), drugi podobny dalej.
- Po lewej pierzeja: niskie domy 1–2 kondygnacje, dachy czerwone/brązowe/blacha, elewacje jasne/beżowe/żółte, parterowe wejścia od chodnika.
- Teren płaski, na horyzoncie pola i lasy.
Porównanie z grą (render rynek-above po 0216): trójkąt w grze jest **wypełniony gęstym lasem sosnowym** — to największy błąd (najpewniej generator roślinności / landuse=forest|wood albo park→las). Kadr „rynek-fountain” pokazuje inny plac (wschodni, z kostki), który nie jest Rynkiem z tego zdjęcia.
Priorytet poprawek: (1) trójkąt = trawniki + alejki + rzadkie drzewa liściaste + wierzba; (2) kościół z białą wieżą i czerwonym hełmem w osi; (3) biały budynek z czerwonym dachem i lukarnami po prawej; (4) czerwona kostka parkingu i chodników; (5) pierzeja lewa.

## Targowica — 2 zdjęcia od właściciela (15.11 ~19:2x, z drona: pionowe i ukośne; tylko opis, nie do gita)
To jest plac, który w grze pokazuje kamera „rynek-fountain” (plac wschodni z kostki) — to NIE Rynek, tylko targowica. Co widać:
- Prostokątny plac z **jasnego betonu / jasnoszarych płyt**, podzielony **pasami z terakotowej/czerwonej kostki** (poprzeczne pasy co jedno zadaszenie i przy wjazdach).
- **4 długie, otwarte zadaszenia targowe w jednym rzędzie** (osobne, z przerwami): dachy czterospadowe, ciemnoszare/grafitowe (blacha na rąbek), na słupach, pod spodem rzędy stołów/lad; na pierwszym od wjazdu **panele fotowoltaiczne** na połaci. Wymiary oszacuj z ortofoto GUGiK.
- Wokół zadaszeń owalne/zaokrąglone obwódki z kostki; **wyspy z ziemią/nasadzeniami o zaokrąglonych (łukowych) krawędziach** przy wjazdach i w narożach, z młodymi drzewkami/podporami; latarnie parkowe.
- Wzdłuż ulicy **ogrodzenie panelowe** z wjazdami; po drugiej stronie ulicy pas zieleni z łukowymi zatokami/parkingami.
- W narożu przy wjeździe **mały żółty pawilon z ciemnym czterospadowym dachem** (szalet/kasa) z osobnym parkingiem z płyt.
- Z tyłu wzdłuż placu **długi parterowy budynek** (część elewacji pomarańczowa/łososiowa, część czerwona/bordo przy sklepie z szyldem — szyld generyczny, bez marki), ciemny płaski/dwuspadowy dach z papy; przed nim **świerk**.
- Za nim biała hala magazynowa, skład złomu/maszyn rolniczych, hałdy piasku i żwiru, dalej pola — skraj miasta.
Porównanie z grą: w grze jest szary plac z kostki z dwiema czerwonymi wiatami przystankowymi i ceglaną budką — brak 4 zadaszeń targowych, brak pasów terakoty, brak łukowych wysp i ogrodzenia, brak żółtego pawilonu. Do poprawy jako generator/authored_override „market_hall_canopy” z danymi z OSM (amenity=marketplace) + ortofoto.

4. Raportuj zestawienia „zdjęcie właściciela | render” dla każdego kadru (zdjęcia tylko lokalnie w artifacts, nie w gicie). Lider pokaże je właścicielowi do oceny rozpoznawalności.
