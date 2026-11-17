# Knyszyn — podobieństwo zabudowy i punktów orientacyjnych (knyszyn-look-s23)

Zakres: kafel `knyszyn` poza parkiem Rynku, targowicą i rondem (te należą do PR #169) oraz poza chodnikami i
skrzyżowaniem Południowa × Szkolna (PR #165). Kryterium: D51 — rozpoznawalność układu, zabudowy i punktów
orientacyjnych z wysokości oczu; bez polerki nieba i trawy.

Źródła: OSM (Geofabrik `podlaskie-261108`, ODbL), BDOT10k 2008 / LoD1 2024 / LoD2 2017 (GUGiK), ortofoto GUGiK 2025
0,1 m (tylko referencja), Mapillary 2020 (CC BY-SA 4.0, tylko referencja, pliki poza gitem w `Data/raw/mapillary/knyszyn`,
400 klatek: Tykocka, Rynek, Grodzieńska, DK65; **brak pokrycia ul. Szkolnej**), fakty od właściciela
(`docs/owner/KNYSZYN-OWNER-FEEDBACK-S21.md`). Google: nieużyte.

Pliki: `inventory_knyszyn.json`, `inventory_knyszyn-w.json`, `inventory_knyszyn-s.json` (obiekty OSM ze znacznikiem
funkcji → obrys w grze; bez nazw sklepów, marek, telefonów i adresów e-mail), `before_after_knyszyn.json`
(klasa, podtyp, ściany i dach przed / po).

## 1. Inwentarz

| Obiekt | Dane | W grze przed | Ocena | Po zmianie |
|---|---|---|---|---|
| Kościół św. Jana (OSM way/294345650, BDOT `…8DAE…`) | własny generator ADR 0227 | bryła z wieżą, czerwony dach | jest; detale w ADR 0227 | bez zmian (nie ruszane) |
| Urząd Miejski / dom kultury (`…4817…`, `…46DC…`) | własny generator ADR 0227 | L, czerwony dach, lukarny | jest | bez zmian |
| Poczta (way/300660473, `…AB81…`), wsch. róg Rynku | 2 kond., LoD2 kalenica 10,19 / okap 7,65 m, typ 1130 | „biurowiec” beżowy z **płaskim** dachem | źle: dach i kolor | ściany pomarańczowo-ceglaste (`plaster_peach`, ESTIMATED z Mapillary), dach czterospadowy grafit (ortofoto) |
| Dom narożny Grodzieńska / Rynek (`…2E17…`) | 2 kond., dom | szary tynk, dach grafit | źle: kolor ścian i dachu | biały tynk (Mapillary), dach czerwony (ortofoto) |
| Biblioteka (way/300660485; BDOT podaje „policja”, `…46DA…`) | 3 kond., LoD2 1040 | biurowiec z dachem czterospadowym, kolor dachu losowy | kolor dachu losowy | dach czerwony z ortofoto |
| Dom Klattów (way/294345657, `material=wood`, `…2F22…`) | zabytek drewniany, 171 m² | **tynkowany** beżowy dom | źle: materiał | dom drewniany (deskowanie), dach czerwony (ortofoto) |
| Dom pogrzebowy (way/300664551, `…465F…`), **Rynek płn.** (760926, 612483) | 1 kond., LoD2 1130, wznios 1,8 m | ceglany „biurowiec” z płaskim dachem | źle: dach | dach dwuspadowy (wznios zmierzony w LoD2), kolor z ortofoto; elewacja nieznana |
| Dyskont, ul. Szkolna (node/1849116070, `…468D…`) | 1 kond., 5,9 m, 1033 m² | biały pawilon z płaskim dachem i regułową witryną, **trawnik zamiast parkingu** | brak parkingu | parking: kostka szara + pasy czerwonej kostki z ortofoto (ESTIMATED ±1 m); bryła bez zmian |
| Budynek usługowy 2 kond. przy Szkolnej (way/1040185031, `…f5dd66ff45a7` + `…a90aa8b9c759`) | tylko OSM/BDOT nowe, 7,0 m z liczby kondygnacji | jasny biurowiec, płaski dach | nie do oceny bez zdjęcia | bez zmian |
| Blok 3 kond. przy Szkolnej (`…46DE…`, 11,7 m) | BDOT wielorodzinny, LoD2 1030, wznios 0,6 m | blok 3 kond. z balkonami, kremowy | zgodny z danymi; kolor losowy | bez zmian |
| Blok 3 kond. za Szkolną (`…2F9A…`, 10,21 m, 442 m²) | BDOT wielorodzinny, dach płaski | blok 3 kond. z balkonami, biały | zgodny z danymi | bez zmian |
| „Wielorodzinny” 104 m² przy Rynku (`…182081cd6d92`, OSM `building=hut` 68 m²) | 3 kond. / 10 m z BDOT, bez LoD | blok 3 kond. | podejrzany błąd danych | bez zmian — do sprawdzenia (lista dla właściciela) |
| Szkoła (way/300653941…45; `…4818…` 3 kond., `…4819…` sala) | LoD2: okap 4,06 m przy kalenicy 16,81 m (niespójne) | beżowe biurowce z płaskim dachem | nie do oceny bez zdjęcia | bez zmian |
| Stacja paliw | w OSM tylko punkt LPG: way/300665704 (kafel `knyszyn-w`, 760524, 611959) i zbiornik way/300665706 | budynek handlowo-usługowy bez dystrybutorów | **brak stacji w danych** | bez zmian — pytanie do właściciela |
| Bank (`…46D9…`), remiza OSP (way/300653253), apteki | BDOT + LoD | biurowce; dachy z reguły | kolory dachów losowe | kolory dachów z ortofoto |
| Maszt telekomunikacyjny (node/3048977067, 45 m) | OSM | — | nie sprawdzano | poza zakresem |

### Zabudowa ogółem (największa różnica w kadrach z ulicy)

| Zjawisko | Liczba | Przed | Po |
|---|---|---|---|
| Obrysy tylko z OSM (`function: yes`, wysokość domyślna 6,0 m) | 149 (mediana 48 m²) | **płaskie „biurowce” 6 m** w ogrodach | 99 < 60 m² → budynek gospodarczy 3,0 m (WORKING_VALUE); 49 po 60–250 m² → dom; 1 większy bez zmian |
| Budynki usługowe z LoD2 1130 / 1010 i zmierzonym wzniosem ≥ 1,5 m | 20 | płaski dach | dach dwuspadowy / jednospadowy |
| Kolor dachu domów | 717 domów | losowany: czerwony 244, brązowy 246, grafit 227 | z ortofoto 2025: grafit 263, czerwony 172, jasnoszary 163, brązowy 119 (reszta: reguła) |
| Dachy odczytane z ortofoto łącznie | 1577 z 1903 budynków | — | plik `overrides.ortho_roofs.json`; zgodność z 4 dachami odczytanymi ręcznie w ADR 0227: 4/4 |

## 2. Zdjęcia Wikimedia Commons (tylko linki; nic nie pobrano)

| Plik | Licencja | Autor | Co pokazuje |
|---|---|---|---|
| https://commons.wikimedia.org/wiki/File:Podlaskie_-_Knyszyn_-_Knyszyn_-_kosciol_pw._sw_Jana_Apostola_i_Ewangelisty_-_front.JPG | do sprawdzenia na stronie pliku (wskazany w OSM) | — | front kościoła |
| https://commons.wikimedia.org/wiki/File:Podlaskie_-_Knyszyn_-_Knyszyn_-_rynek.JPG | CC BY-SA 4.0 | Athantor (2009) | Rynek |
| https://commons.wikimedia.org/wiki/File:Knyszyn_Rynek_1.jpg | CC BY-SA 3.0 | Henryk Borawski (2012) | pierzeja Rynku |
| https://commons.wikimedia.org/wiki/File:Knyszyn_Rynek_4.jpg | CC BY-SA 3.0 | Henryk Borawski (2012) | pierzeja Rynku |
| https://commons.wikimedia.org/wiki/File:Grodzieńska_and_Rynek_(Knyszyn).jpg | CC BY-SA 3.0 | Henryk Borawski (2012) | narożnik Grodzieńska / Rynek |
| https://commons.wikimedia.org/wiki/File:Dom_pogrzebowy_w_Knyszynie.jpg | CC BY-SA 3.0 | Henryk Borawski (2012) | dom pogrzebowy (kategoria „Rynek in Knyszyn”) |
| https://commons.wikimedia.org/wiki/File:Knyszyn_sklep_mięsny_Podlasie_2.JPG | CC BY-SA 3.0 | Henryk Borawski (2012) | sklep przy Rynku (szyldu nie odtwarzać) |
| https://commons.wikimedia.org/wiki/File:Zabytkowy_dom_z_XVIII_w._w_Knyszynie,_zdj._18_lipca_2019_r.jpg | CC BY-SA 4.0 | Jwdys (2019) | zabytkowy dom drewniany |
| https://commons.wikimedia.org/wiki/File:Podlaskie_-_Knyszyn_-_Knyszy_-_krzyz_PT.JPG | CC BY-SA 4.0 | Athantor (2009) | krzyż przy rondzie (kafel `knyszyn-w`) |

Kategorie do przejrzenia w następnej iteracji: `Category:Knyszyn town hall`, `Category:6 Kościelna Street in Knyszyn`,
`Category:Shops and shopping malls in Knyszyn`, `Category:Roman Catholic churches in Knyszyn`. Licencja i autor
z API Commons (`extmetadata`), sprawdzić na stronie pliku przed użyciem jako referencji.

## 3. Czego nie da się ustalić bez nowych zdjęć (lista dla właściciela)

1. **Zakład pogrzebowy „przy Szkolnej”.** W OSM, BDOT i Commons jest tylko dom pogrzebowy przy północnej pierzei
   Rynku (760926, 612483). Przy Szkolnej dane pokazują nowy budynek usługowy z grafitowym dachem i fotowoltaiką obok
   dyskontu (761067, 612140). Który z nich to ten z opisu? Potrzebne zdjęcie frontu.
2. **Dyskont:** kolor elewacji, położenie wejścia i przeszklenia, wiata na wózki, układ miejsc na czerwonej kostce.
3. **Blok trzykondygnacyjny:** który z dwóch (przy samej Szkolnej, 761113, 612125, czy dłuższy w głębi, 761110, 612263),
   kolor elewacji, balkony / loggie, wejścia. Muralu nie odtwarzamy.
4. **Stacja paliw:** w danych jest tylko punkt LPG przy rondzie. Czy w Knyszynie jest stacja z wiatą i dystrybutorami,
   i gdzie?
5. **Szkoła:** widok od Białostockiej (liczba kondygnacji, dach, kolor), sala gimnastyczna.
6. **Poczta:** potwierdzenie cegły licowej (klatka Mapillary z 2020 r.) i wejścia.
7. **Pierzeje Rynku i Tykockiej:** po jednym zdjęciu każdej pierzei z chodnika naprzeciwko — kolory ścian i domy
   drewniane (dachy już są z ortofoto).
8. **Budynek 104 m² „wielorodzinny, 3 kondygnacje” przy wschodnim placu** (761065, 612437): w OSM to „hut” 68 m².
   Co tam stoi?
9. Żółte barierki i przejścia przy Południowa × Szkolna — nadal UNVERIFIED (PR #165).

## 4. Jak odtworzyć

```
uv run --project tools/worldgen python tools/worldgen/qa/landmark_inventory.py --region knyszyn --out docs/reports/knyszyn-look/inventory_knyszyn.json
uv run --project tools/worldgen python tools/worldgen/qa/class_fixes_data.py --region knyszyn
uv run --project tools/worldgen python tools/worldgen/qa/roof_tones_ortho.py --region knyszyn [--check]
uv run --project tools/worldgen python tools/worldgen/qa/landmark_before_after.py --region knyszyn --out docs/reports/knyszyn-look/before_after_knyszyn.json
```

Kolejność źródeł dla budynku: `overrides.yaml` (ręczne) > `overrides.ortho_roofs.json` > `overrides.class_fixes.json` >
reguły generatora. Regiony bez tych plików nie zmieniają się.
