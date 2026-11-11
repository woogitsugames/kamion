# Recenzja wizualna s10 — GPT J (ADR 0103 side-by-side) i K (ADR 0104 kabina/lusterka)

Data: 2026-11-11. Recenzent: visual-critic (niezależny, nie autor). Bez edycji kodu, bez commitów.
Źródła: `.claude/worktrees/gpt-sbs-gate3` (gałąź `gpt-sbs-gate3`, HEAD `7be94d1b`), `.claude/worktrees/gpt-cab-r1`
(gałąź `gpt-cab-r1`, HEAD `4f0a2f33`), kopie dowodów w `artifacts/sbs-gate3/`, `artifacts/cab-r1/`.
Obie gałęzie mają bazę `9e6e9fde`, czyli są **sprzed** scaleń 0101 r2, 0102, 0105 i 0085 r2. Rendery J pokazują więc
wiadukt bez konstrukcji pod pomostem z 0105 i słupy bez fundamentów z 0102. Po scaleniu trzeba wyrenderować je ponownie.

---

## J — ADR 0103: zestaw side-by-side do bramki 3

### Werdykt scalenia: **PASS warunkowy** (narzędzie i dane kamer; bez zmian świata/runtime)
Scalenie jest bezpieczne: gałąź dodaje tylko narzędzia, JSON-y `sbs_*` i dokumentację, a świata/runtime nie rusza.
Jako **dowód bramki 3 zestaw jest jednak FAIL**, dopóki nie zostaną wycięte pary z rozjechaną pozą (niżej J1).
Sam autor (VISUAL-REVIEW.md) też nie zgłasza PASS bramki, co jest uczciwe.

### Co obejrzano
Przeglądy wszystkich 160 par (`review/{Low,High}-{clear,overcast}/G3-{A,B}.jpg`) oraz 28 pełnych arkuszy 960 px
w różnych stanach. G3-A: 2818555625124739, 177786140912399, 178689077481862, 3970163613102941, 320326319617139,
751431972202262, 1259231227807789, 500263111404933, 454716650857984, 2948595898752384, 303305168125936,
1406533339711789. G3-B: 3281350541967811, 297817221966185, 810525063224609, 209622370971977, 494288258686575,
339463879238809, 150280503737744, 962702164479831, 810896133189484, 1528935774382039, 182011943700132,
468026894483428, 4312632558767412, 2279538078845158, 326454015490067, 1801374876712141.

### Jakość narzędzia — oceny
| Kategoria | Ocena | Uzasadnienie |
|---|---|---|
| Pozy kamer (horyzont/FOV/punkty charakterystyczne) | 5/10 | Ok. 25 z 40 par trzyma kadr naprawdę dobrze: pomost wiaduktu w 2818/3970/5002 pokrywa się z dokładnością do kilku px, a FOV po rektyfikacji fisheye się zgadza. Około 9 par ma przesunięcie boczne 3–8 m (kamera stoi na trawie, a zdjęcie robiono z pobocza przy barierze). 5–6 par nie nadaje się do niczego (J1). |
| Rektyfikacja obiektywu | 8/10 | Wyprostowane 27 zdjęć fisheye ma proste krawędzie pomostu i słupów. Roll nie jest korygowany; w 326454 i 2948 widać błąd pochylenia (pitch). |
| Metryki | 5/10 | Histogram 32-bin jest użyteczny: pokazuje, że render ma szczyt w półtonach, a zdjęcie ciemniejszy asfalt i jaśniejsze niebo. Maski są heurystyczne i autor to uczciwie zaznacza. Kamery z maską samochodu na zdjęciu i zdjęcia o zachodzie słońca psują statystykę całego zbioru. |
| Licencje | 9/10 | 40/40 to Mapillary CC BY-SA 4.0. W `docs/refs/sbs-gate3-attribution.md` jest autor, data, URL i SHA256 każdego zdjęcia. Zdjęcia są poza gitem i buildem. Brak Google. |
| Pokrycie | 4/10 | Pierwsze ~300 m G3-A jest bez pokrycia. 22/40 zdjęć to jeden autor z jednego dnia (richlv 2020-08-15, z pobocza). 8/40 to zachód słońca/pod słońce. 13/40 zdjęć jest sprzed 2020 r. i mogą pokazywać stan sprzed przebudów. |
| Odtwarzalność | 8/10 | Jedna komenda `sbs_gate3.py prepare` + `scripts/sbs-gate3.ps1`, `authored_overrides` w JSON i testy SBS 10/10. |

### Problemy J (narzędzie)
| ID | Prio | Lokalizacja | Problem | Poprawka |
|---|---|---|---|---|
| J1 | **P0** (dla dowodu bramki, nie dla scalenia) | `sbs-g3-b-810896133189484` (kamera przy/wewnątrz ekranu akustycznego; cały kadr to panel i słup), `sbs-g3-b-339463879238809` (render: chodnik obok ekranu, ~8–10 m w bok od pasa ze strzałkami na zdjęciu), `sbs-g3-b-962702164479831` (kurs ~35–40° w bok: render patrzy w poprzek jezdni), `sbs-g3-b-182011943700132` (kurs ~30–40° w prawo: wyspa zamiast jezdni z sygnalizacją), `sbs-g3-b-326454015490067` (zdjęcie zadarte o ~15–20°; czerwony horyzont ~80 px nad punktem zbiegu drogi), `sbs-g3-a-1406533339711789` (kurs dalej rozjechany, pod słońce) | Te pary porównują inne miejsca albo inne kierunki. Dowodzą błędów pozy, a nie świata. | W `sbs_cameras.json` dodać pole `pose_confidence` (A dobra / B przybliżona / C odrzucona), a do arkusza bramki brać tylko A+B. Dla C poprawić kurs/pozycję w `authored_overrides` (dopasowanie 2–3 punktów charakterystycznych: słup wiaduktu, latarnia, krawędź jezdni) albo wymienić zdjęcie. |
| J2 | P1 | Seria richlv: 1259231227807789, 751431972202262, 500263111404933, 209622370971977, 810525063224609, 468026894483428, 4312632558767412; też strudel 1528935774382039 | Systematyczne przesunięcie boczne: na zdjęciu kamera stoi na krawędzi jezdni przy barierze, w renderze 3–8 m dalej na trawie, przez co ściany i skarpy wypełniają kadr. Kierunek się powtarza (w stronę skarpy), więc to raczej błąd GPS sekwencji albo odsunięta oś drogi w modelu niż przypadek. | Dopasowanie boczne do krawędzi jezdni widocznej na zdjęciu jako `authored_override`, z adnotacją, czy różnica wynika z pozy, czy z geometrii drogi (to drugie trafia do ADR 0100). |
| J3 | P1 | `sbs-g3-a-2948595898752384` | Autorski horyzont ~30 px (~7 % wysokości) poniżej punktu zbiegu jezdni na zdjęciu, przez co render jest pochylony względem zdjęcia. | Wyznaczać horyzont z punktu zbiegu krawędzi jezdni (2 linie), a nie ręcznie. |
| J4 | P1 | cały zestaw | Rendery z bazy `9e6e9fde`, sprzed 0102/0105/0101 r2/0085 r2. | Po scaleniu `pwsh scripts/sbs-gate3.ps1 -EditMode` na aktualnym main i podmiana arkuszy przed jakimkolwiek wnioskiem o wiadukcie i słupach. |
| J5 | P2 | 8 par zachodu (1406533339711789, 223210302566110, 309664504075286, 381800493259507, 2279538078845158, 837235577143499, 275528677534382, 3678296072299092) i ~12 z maską auta | Bezużyteczne do fotometrii; histogram całej klatki jest zdominowany przez maskę i słońce. | Flaga `photometric_use: false` i maskowanie maski auta stałym poligonem per sekwencja. |
| J6 | P2 | metadane | Brak flagi wieku zdjęcia względem danych (2017 vs nowsze ortofoto/BDOT). | Pole `photo_vs_data_age` i ostrzeżenie na arkuszu dla zdjęć < 2020. |
| J7 | P2 | arkusz | Brak punktów charakterystycznych na obu panelach (tylko horyzont i siatka). | Nakładka 2–3 klikniętych punktów (JSON) na obu panelach, z błędem w px jako miarą jakości pozy. |

---

## Priorytety bramki 3 z porównań side-by-side

Liczba par = pary (z 40 unikalnych kadrów), w których problem jest wyraźnie widoczny na arkuszu albo w przeglądzie.
Pary z J1 (pozy odrzucone) nie są liczone do problemów świata. Kolejność według liczby par. Liczby są szacunkiem
recenzenta (28 pełnych arkuszy + przeglądy 160), nie automatyczną klasyfikacją.

| # | Problem świata | Liczba par | Przykładowe arkusze | Charakter / kierunek poprawki |
|---|---|---|---|---|
| 1 | **Niebo i ekspozycja dnia**: niebo clear to płaski, szaroniebieski gradient bez chmur, z wypaloną białą połacią po lewej. Na zdjęciach jest nasycony błękit z cumulusami albo zróżnicowane, jasne overcast. Grunt w renderze jest ciemniejszy, a histogram render ma jeden szczyt w półtonach, gdzie zdjęcie ma dwa garby (ciemny grunt, jasne niebo). | ~32 (wszystkie dzienne) | 3281350541967811, 297817221966185, 2948595898752384, 454716650857984, 2818555625124739 | ADR 0098 (światło/post): skybox z chmurami (HDRI CC0 dla clear), kalibracja ekspozycji niebo vs grunt. To element zawsze w kadrze, więc daje największy zysk. |
| 2 | **Trawa i pobocza „trawnik golfowy”**: ciemna, jednolita, przycięta zieleń. Na zdjęciach jest żółtozielona, nierówna, z kępami, chwastami, przesuszonymi plamami, wysoką trawą przy barierach i piachem przy krawędzi. | ~24 | 1528935774382039, 500263111404933, 320326319617139, 209622370971977, 468026894483428 | ADR 0088: albedo trawy jaśniejsze i cieplejsze, wariacja makro (pas koszony przy krawędzi vs wysoka trawa dalej), kępy/chwasty jako instancje. |
| 3 | **Asfalt za jasny i za jednolity**: średnio jasnoszary, bez ciemniejszych śladów kół, łat, spękań i przebarwień; linie zbyt czyste i kontrastowe. Na zdjęciach asfalt jest ciemniejszy, z wyraźnymi koleinami i łatami. | ~21 | 454716650857984, 2948595898752384, 303305168125936, 2279538078845158, 1801374876712141, 150280503737744 | ADR 0099 + 0101: niższe albedo asfaltu (zmierzyć na zdjęciach właściciela z kartką A4; dziś UNVERIFIED), maski kolein i łat. |
| 4 | **Bariery i balustrady**: (a) na pomoście zdjęcia pokazują stalowe bariery energochłonne (taśma W na słupkach) wzdłuż jezdni, a render pokazuje szeroki biały gzyms/chodnik z balustradą pieszą i bez bariery. (b) Przy łącznicach pod wiaduktem zdjęcia mają barierę W w pierwszym planie, w renderze jej brak. | 14 (7 pomost + 7 parter) | pomost: 454716650857984, 2948595898752384, 303305168125936, 1406533339711789; parter: 500263111404933, 1259231227807789, 751431972202262, 177786140912399 | ADR 0100 (Claude, bariery na wiadukcie): bariera W na pomoście, węższy i szary (nie biały) gzyms; bariery przy łącznicach DK8. Śnieżnobiałe kapy gzymsu to czerwona flaga „sterylna czystość”. |
| 5 | **Przestrzeń pod wiaduktem**: zdjęcia pokazują jasne łoże z kruszywa/otoczaków, jasny spód pomostu (odbite światło) i okrągłe słupy z czerwonym pasem. Render ma ciemną trawę pod pomostem, ciemny spód i prostokątne/skośne tarcze słupów o innym rozstawie. W G3-B (468026894483428, 4312632558767412) pod przęsłem jest **zamknięta ciemna ściana** zamiast prześwitu na zabudowę. | 13 (11 G3-A + 2 G3-B) | 2818555625124739, 3970163613102941, 178689077481862, 500263111404933, 468026894483428, 4312632558767412 | 0105 (scalone po bazie J) mogło część naprawić, więc najpierw ponowny render (J4). Dalej: materiał kruszywa pod pomostem, kształt słupów wg zdjęć/ortofoto, otwarcie przęseł G3-B, odbicie światła od jasnego gruntu. |
| 6 | **Drzewa i krzewy**: zdjęcia mają dojrzałe, gęste korony przy drogach, młode nasadzenia w szeregu wzdłuż skarp i ekranów oraz zarośla. Render ma rzadkie, małe sylwetki albo nic, a na Low bryłowate korony. | ~14 | 3281350541967811, 297817221966185, 1528935774382039, 810525063224609, 209622370971977, 468026894483428 | ADR 0088: szeregi młodych drzew wzdłuż skarp DK8/ekranów (BDOT10k/ortofoto), krzewy przy łącznicach, większe korony dojrzałych drzew. |
| 7 | **Rodziny latarni**: na pomoście i przy głównych jezdniach zdjęcia pokazują latarnie dwuramienne/łukowe w pasie dzielącym. Render ma jednoramienne latarnie po bokach. | ~7 | 1406533339711789, 2948595898752384, 454716650857984, 303305168125936, 150280503737744, 1801374876712141 | ADR 0102 r2: rodzina dwuramienna na pas dzielący wg Mapillary; pozycje z OSM/ortofoto. |
| 8 | **Brak obiektów infrastruktury**: bramownice drogowskazowe (3281, 3394), sygnalizacja świetlna (1820), znaki D-6 i inne na słupkach (3203, 5002), tablica z nazwą ulicy (2818, 3970), linie napowietrzne (8105). W 1777/1786 render ma za to znak nakazu tuż przed kamerą, którego zdjęcie tam nie ma. | ~8 | 3281350541967811, 320326319617139, 182011943700132, 177786140912399, 810525063224609 | Znaki i wyposażenie z OSM + detekcji Mapillary (ADR 0069/0102); weryfikacja położenia znaku przy rondzie. |
| 9 | **Okładziny ścian oporowych i przyczółków**: zdjęcia pokazują ściany z płyt/bloków z nieregularnymi fugami, kamień i czerwony gzyms. Render ma płaską szarą/ciemną płaszczyznę bez fug, a w G3-B zielony zamiast czerwonego pasa. | 5 | 751431972202262, 810525063224609, 209622370971977, 468026894483428, 4312632558767412 | Materiał „panel oporowy” z fugami, kolor gzymsu wg zdjęć; ADR 0105/0101. |
| 10 | **Budynki generyczne**: białe/szare pudełka zamiast kolorowych obiektów handlowych i ciemnoszklanych hal. W 1801 render ma podmiejskie domy ze spadzistym dachem tam, gdzie zdjęcie (2019) pokazuje teren handlowy i pola. | ~5 | 150280503737744, 326454015490067, 1801374876712141, 2279538078845158 | ADR 0097 (fasady): kolory i materiały z Mapillary. W 1801 sprawdzić klasyfikację BDOT vs stan ze zdjęcia. |
| 11 | **Ekrany akustyczne — słupy i panele**: na zdjęciach słupy są ciemniejsze, masywniejsze i gęstsze, a panele bardziej przezroczyste (zielonkawe odbicia). Render ma jasnoszare, cienkie słupy i mleczne panele. | 4 | 494288258686575, 339463879238809, 326454015490067, 810525063224609 | ADR 0101: kolor słupa, przezroczystość/odbicie paneli. |

Wniosek dla bramki 3: geometria (przebieg dróg, wiadukt, bryły hal) jest w większości kadrów rozpoznawalna.
Świat przegrywa na **niebie, gruncie (trawa/asfalt) i wyposażeniu drogi (bariery, latarnie, znaki)**. Dziś to wygląda jak
czysty render gry mobilnej z ok. 2018 r.: schludnie, jednolicie, za jasno w półtonach. Zdjęcia są brudniejsze, bardziej
kontrastowe i bardziej zarośnięte.

---

## K — ADR 0104: kabina r1 — wnętrze i lusterka

### Werdykt scalenia: **PASS** (z P1 do rundy r2, przed bramką 3)
Główna poprawka jest prawdziwa i widoczna. Przed nią naczepa w obu lusterkach głównych była na **zewnętrznej**
krawędzi. Po niej jest na wewnętrznej: w lewym lusterku przy prawej krawędzi, w prawym przy lewej
(`review/after/High-clear/cab-mirrors-{left,right}-pair.jpg`, natywne RT). Test `MirrorPresentationTests` pilnuje
tej zależności. Wpięcie obudowy LOD0 odsłania szkło szerokokątne. Delta draws/tris = 0 we wszystkich 36 wierszach,
a tabele RT i kadencji są identyczne z ADR 0068. Zmiana jest mała i addytywna (flaga `flipHorizontally`,
`MirrorHousingRecess` tylko na LOD0).

### Oceny (stan po K, High; Low w nawiasie)
| Kategoria | Ocena | Uzasadnienie |
|---|---|---|
| Lusterka główne — poprawność | 8/10 | Kierunek odbicia jest poprawny. Naczepa zajmuje ~15–25 % szerokości, widać pas i krawędź, więc lusterko jest użyteczne do cofania. |
| Lusterka główne — jakość obrazu | 5/10 (3/10) | RT 171×384 (Low 100×224) daje miękki obraz, na Low szkło jest rozmyte. Odświeżanie na telefonie: UNVERIFIED. |
| Lusterka klasy V/VI (krawężnikowe, przednie) | **2/10** | K1: widać w nich wnętrze kabiny z góry. |
| Materiały deski | 4/10 | Plastik czyta się jako gładka, matowa guma. Ziarno jest widoczne dopiero w kamerze inspekcyjnej `cab-grain`, z odległości kierowcy znika. |
| Szwy, zużycie | 4/10 | Przeszycie kierownicy jest czytelne. Zużycie fotela, podłokietnika i kierownicy z punktu oka jest niewidoczne, więc kabina jest sterylna (czerwona flaga §2). |
| Czytelność zegarów | 6/10 | „0” i bieg są czytelne. Małe cyfry pomocnicze na Low są nieczytelne, telefon nie był testowany. |
| Skala i układ | 7/10 | Pozycja oka, kierownica i ekran nawigacji są wiarygodne. |
| Ogólnie widok kierowcy | 5/10 | „Porządna gra mobilna ok. 2019”, a nie zdjęcie z kabiny: brak odbić deski w szybie, brak kurzu i śladów palców, jednolite światło wnętrza. |

### Problemy K
| ID | Prio | Lokalizacja | Problem | Poprawka |
|---|---|---|---|---|
| K1 | **P1** (przed bramką 3; nie blokuje scalenia, bo istniało przed K) | `after/*/native-mirrors/MIRROR_Front_Camera.png`, `MIRROR_Kerb_Camera.png` (wszystkie 4 stany Low/High × clear/overcast); widoczne też na szkle w `phone-lead-cab-mirror-front_overcast.jpg` (pomarańczowa plama w lusterku przednim) | Lusterko przednie i krawężnikowe pokazują **wnętrze kabiny z góry, z fotelami koniak, bez dachu**. Kamera lustrzana nie widzi dachu: albo wycina go maska warstw, albo przycina near clip ≈1,9 m. ADR 0104 twierdzi, że „front/kerb showed the road”, a to nieprawda: pokazują drogę **i** wnętrze. | Dach i zewnętrzną skorupę kabiny dodać do culling mask kamer V/VI, a wnętrze wyłączyć (spójne z 0068: wnętrze kosztuje 81 k tris na widok). Albo poprawić near clip względem płaszczyzny lustra. Dodać test: piksele materiału fotela w RT V/VI = FAIL. Sprostować ADR 0104. |
| K2 | P1 | `cab-mirrors-left` (High i Low), dolne szkło szerokokątne | Czarny cylindryczny wspornik przechodzi **przed** szkłem szerokokątnym (z punktu oka) i zasłania ~25–30 % jego dolnej połowy. W prawdziwym zestawie ramię jest za obudową albo nad nią. | Przesunąć ramię za płaszczyznę szkła lub zmienić punkt mocowania; dodać okluzję przez ramię do `mirror_sightlines.py` (97,5 % WideL to promienie źródłowe, a ramię w kadrze widać wyraźnie). |
| K3 | P2 | `cab-mirrors-right` / `-left`, zewnętrzna krawędź szkła głównego | Szkło wystaje poza obudowę (górny łuk kończy się przed krawędzią szkła): ostry prostokątny róg bez ramki, wygląda jak naklejka. Było przed K, wpięcie tego nie naprawiło. | Ramka (bezel) wokół całego obwodu, szkło lekko cofnięte w obudowie. |
| K4 | P2 | `cab-grain-High-clear.jpg`, góra deski między kratkami nawiewu | Rozmazana/rozciągnięta smuga tekstury (ok. 1/6 szerokości kadru), wygląda na szew UV albo rozciągniętą normal mapę. | Sprawdzić UV i texel density panelu, przepiec. |
| K5 | P2 | `cab-seat-entry-*` | Podłokietnik i kierownica przenikają przez boczek fotela (autor też to wskazuje). | Korekta geometrii podłokietnika (WORKING_VALUE +15–25 mm na zewnątrz). |
| K6 | P2 | `cab-dash`, `cab-driver` | Ziarno plastiku i zużycie niewidoczne z punktu oka, wnętrze sterylne. | Makro-wariacja roughness (wytarcia przy uchwytach, kurz w zagłębieniach, połysk krawędzi przełączników) w skali widocznej z 0,6–0,9 m, bez globalnego szumu. |
| K7 | P2 | proces | Brak zrzutu z telefonu po zmianie (są tylko pomocnicze „dirty” klatki A16 lidera). | Lider: APK + kamery `cab-*` na A16 (i S24+, gdy bateria ≥ 40 %). |

---

## Podsumowanie

- **J: PASS warunkowy** jako narzędzie (scalenie bezpieczne). **FAIL** jako dowód bramki 3, dopóki 6 par z błędną pozą
  (J1) nie zostanie odrzuconych lub poprawionych, a całość nie zostanie wyrenderowana na aktualnym main (J4).
  Jakość narzędzia: ~6/10.
- **K: PASS**. Odbicie w lusterkach głównych naprawione, budżet bez zmian. Przed bramką 3 trzeba naprawić lusterka V/VI
  pokazujące wnętrze kabiny (K1) i ramię zasłaniające lusterko szerokokątne (K2).
- **Top 5 priorytetów bramki 3 (z par)**: (1) niebo/ekspozycja, ~32 pary; (2) trawa/pobocza, ~24; (3) asfalt za jasny
  i jednolity, ~21; (4) bariery na pomoście i przy łącznicach, 14; (5) przestrzeń pod wiaduktem (kruszywo, jasny spód,
  kształt słupów, zamknięte przęsło G3-B), 13, po ponownym renderze z 0105.
