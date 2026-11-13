# Przegląd PR #49 (Mistral M51 / P10 — zieleń ulic osiedla) — s17, 2026-11-13

## NASTĘPNY KROK (dla sesji przejmującej)
Przegląd ZAKOŃCZONY. Lider: wkleić blok **M51-FIX** (koniec `docs/owner/MISTRAL-FIXES-8.md`) do sesji Mistrala; PR #49 NIE scalać. Agent 0170: **nie używać `crowns.geojson` z tego PR** (lustrzane N–S, patrz §3.3); fakty w §5.

## 1. Werdykt
**NADAL DO POPRAWY (M51-FIX).** Dwa błędy krytyczne:
1. **Detekcja koron (zad. 3) jest odbita lustrzanie N–S w każdym kaflu 1024 m** — przy pozycjach z GeoJSON tylko 11 % środków koron trafia na zieleń ortofoto (losowo: 13,6 %); po odbiciu `N' = n0 + 1024 − (N − n0)` w obrębie kafla — **100 %** (68/68 w oknie 300×300 m). Porównanie z P10 (`comparison_p10.json`, „mediana −47 p.p.”) jest przez to bezwartościowe. Dodatkowo filtr `r ≤ 6,5 m` wycina każdy zwarty drzewostan (las, zadrzewiona skarpa, rzędy drzew) — detektor widzi tylko pojedyncze kępy.
2. **Zdjęcia (zad. 1) i żywopłoty (zad. 2): ten sam wzorzec co P1B/P11** — 17/18 kadrów to spacer Rakoona **wzdłuż Al. Tysiąclecia / Motoszko / Sokólskiej**, przypisany do Skidelskiej/Wileńskiej/Łańcuckiej po „najbliższej ulicy osiedla” (odległości do przypisanej osi 30–170 m, w uwagach manifestu jawnie „dist do osi: 160 m”). Azymut „ESTIMATED = kierunek od geotagu do osi ulicy” jest **wnioskowaniem w kółko** (zakłada tezę). Opisy żywopłotów w dużej części nie odpowiadają obrazom.

Część BIP (zad. 4) — rzetelna; wynik negatywny dla gatunków/obwodów uczciwy.

## 2. Metoda
- `git fetch`; `gh pr diff 49 --name-only` → 11 plików, tylko `research/mistral/p10-greenery-3/` ✓; `git diff --stat origin/main...` = 1514 linii. Brak komentarzy w PR. ZIP `mistral-p10-greenery-3-files*.zip` **nie ma** w `Downloads` → próba pobrana z Commons API do scratchpada (10 plików, miniatury 900 px; potem HTTP 429).
- Geometria: lokalny `Data/raw/osm/podlaskie-261108.osm.pbf` (pyosmium, ways drogowe bez footway/path/service), odległość geotagu do osi każdej nazwanej ulicy.
- Korony: GUGiK ORTO WMS `StandardResolution` (to samo źródło co skrypt), okno 300×300 m wokół 53,1555 N 23,1525 E (EPSG:2180 przez pyproj), nałożenie `crowns.geojson`, maska ExG > 0,06, test przesunięć ±20 m oraz hipotez odbicia/transpozycji w kaflach skryptu.
- BIP: komunikat UM 31.01.2022 pobrany i przeszukany.
- **Próba:** 10 kadrów obejrzanych (M51-101, 104, 106, 107, 109, 111, 112, 113, 117, 118) — 55 % zdjęć; 18/18 wierszy zdjęć przeliczonych geometrycznie.

## 3. Wyniki
### 3.1 Przypisanie kadrów do ulic (18/18 przeliczone, 10 obejrzane)
| Kadry | Manifest | OSM: najbliższa oś / odległość do przypisanej | Obraz |
|---|---|---|---|
| 101 | Skidelska | Al. Tysiąclecia 5 m / Skidelska 8 m | arteria Al. Tysiąclecia z chodnika, TIR, pomarańczowe słupki; żywopłotów brak |
| 102, 103, 106, 107 | Skidelska | Al. Tysiąclecia 2–6 m / Skidelska 64–159 m | 107: aleja, Shell, Bocaro, żywopłot tylko po prawej (nie „po obu stronach”); 106: drewniany płot i brama, domek |
| 104, 108 | Skidelska | **Motoszko** 0–28 m / Skidelska 75–103 m | 104: czarny płot, szafka, dwa słupki, żywopłot po prawej ✓ |
| 105 | Skidelska | Al. Tysiąclecia 39 m / Skidelska 110 m | — |
| 109, 110 | Wileńska | Al. Tysiąclecia 10–21 m / Wileńska 30–53 m | 109: krzyż przydrożny, świerk ~8 m, płot drewniany — **żywotnika 1,5–2 m brak** |
| 111, 112 | Wileńska | living_street 5 m / Wileńska 47 m | 111: aleja z busem, żółte barierki; **„wysoki żywopłot liściasty 2–2,5 m (P)” — brak**. 112: ścieżka rowerowa, bloki, trawnik z autami — **żywopłotu brak** |
| 113, 114, 116, 118 | Łańcucka | **Sokólska** 1–8 m / Łańcucka 69–91 m | 118: wiata z napisem **„353 Sokólska / Al. Tysiąclecia Państwa Polskiego”**, ekran, drzewa za ekranem — „wysoki gęsty żywopłot ~2 m” — brak |
| 115 | Łańcucka | Kombatantów 22 m / Łańcucka 170 m | — |
| 117 | Łańcucka | Al. Tysiąclecia 2 m / **Łańcucka > 400 m** | ten sam krzyż co 109 (rejon Wileńskiej); w manifeście ten sam plik jako M51-216 „Wileńska” — sprzeczność |
**Wynik:** 0/18 kadrów z wnętrza Skidelskiej/Wileńskiej/Łańcuckiej; „luka Skidelska zamknięta” — **fałsz**. Metadane Commons (geotag, data, autor Rakoon, licencja) wierne 10/10.

### 3.2 Żywopłoty (odcinki powiązane z obejrzanymi kadrami)
Potwierdzone 3/9 (M51-205 przy 104, M51-208 przy 107 (prawa strona), M51-216 przy 117 — krzewy iglaste ~1,5 m, ale to rejon Wileńskiej/Al. Tysiąclecia); niepotwierdzone 6/9 (M51-201, 207 — lewa strona kadru to jezdnia, 211, 213, 214, 217 — żywopłotu na kadrze brak albo to ekran/barierka). Liczba „18 odcinków” jest zawyżona; próg ≥ 20 niespełniony.

### 3.3 Korony (zad. 3)
- Kafel i GSD zgodne z zadaniem (bbox WGS84 53,1489–53,1681 N, 23,1437–23,1756 E; 5259 punktów, r 0,7–6,5 m, mediana 1,15 m).
- **Błąd rejestracji:** pozycje odbite N–S w obrębie każdego z 4 kafli 1024 m (prawdopodobnie wiersz 0 obrazu przypisany do `n0` zamiast `n0 + 1024`). Dowód: trafienia w zieleń 11 % → 100 % po odbiciu; przesunięcia ±20 m nie dają > 27 %; transpozycja 9 %. Po odbiciu na ortofoto widać też fałszywe trafienia na zielonych obiektach (zielony autobus) i **brak detekcji zwartej zieleni** (zadrzewiona skarpa na N od bloków przy Al. Tysiąclecia — kilka kółek zamiast drzewostanu; drzewa w ogrodach domków w większości pominięte).
- Klasyfikacja iglaste/liściaste (jasność/tekstura) — ESTIMATED, niesprawdzalna przy tej rejestracji.

### 3.4 Inne
- Zad. 4: komunikat UM 31.01.2022 potwierdzony dosłownie: „posadzono 74 drzewa oraz 109 krzewów”, „Ponad 20 tys. 600 m2” trawników i skarp, „około 385 mb ekranów”, koszt 31,7 mln zł ✓. Karta BIP (ZDM-X.271.16.2018.JZ, STRABAG, 32 883 642,97 zł) — nie pobrałem (niezweryfikowane, wiarygodne). Gatunki/obwody/rozstaw UNVERIFIED — uczciwie.
- `audit_20_percent.json` 9/9 PASS — kontrole automatyczne (plik istnieje, data, bbox, format); nie sprawdzały przypisania ani treści obrazu.
- Licencje: CC0 i CC BY 3.0 (seria 2020-07-11) — poprawne; brak NC/ND. KartaView opisane jako „CC BY 4.0 wg zasad serwisu” — w repo przyjęto CC BY-SA 4.0 (P1B, M50); do ujednolicenia.
- Brak Google/Mapillary ✓.

## 4. Luki — stan faktyczny
| Ulica | Lato z poziomu ulicy |
|---|---|
| Skidelska, Wileńska, Łańcucka | **0** (kadry są z Al. Tysiąclecia/Motoszko/Sokólskiej przy wlotach) |
| Kowieńska, Lidzka, Wołkowyska, Grodzieńska, Racławicka, Świsłocka | 0 (negatyw Mistrala wiarygodny; G7 IV 2024 jedyne street-level) |

## 5. Fakty dla agenta 0170 (horyzont / las / korony) — obejrzane
- **Nie używać `crowns.geojson` z PR #49** bez odbicia N–S w kaflach 1024 m; nawet po korekcie brak drzewostanów zwartych (filtr r ≤ 6,5 m) → na las/skarpy potrzebna maska powierzchniowa (ExG/NDVI bez górnego limitu wielkości), nie punkty koron.
- Ortofoto GUGiK (WMS StandardResolution, okno 53,1555 N 23,1525 E): na N od bloków przy Al. Tysiąclecia — **zadrzewiona skarpa / zagajnik liściasty z pojedynczymi iglakami** (~1 ha, zwarta korona); osiedle domków na W od alei — ogrody z pojedynczymi drzewami i krzewami, zieleń nieciągła; strefa bloków na E — trawniki z nielicznymi młodymi drzewami. Pas zieleni alei — trawa, bez dużych koron (stan po przebudowie).
- Kadry lato 2022–2024 (Commons CC0, Rakoon): **linia horyzontu nad aleją = niski pas drzew (sosny + liściaste) i słupy kratowe WN**, nie zabudowa wysoka; ogrody: świerki ~8–15 m, brzozy, tuje/krzewy iglaste ~1,5 m przy płotach; wzdłuż alei 2024 — młode palikowane drzewka liściaste (nasadzenia 2021/22), ekrany akustyczne z drzewami za nimi (118).
- Ilości z inwestycji (SOURCED, UM 31.01.2022): 74 drzewa, 109 krzewów, > 20 600 m² trawników i skarp, ~385 mb ekranów — gatunki nieznane.
