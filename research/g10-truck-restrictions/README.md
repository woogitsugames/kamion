# G10 — ograniczenia dla ciężarówek w Białymstoku vs OSM

Data wykonania: 2026-11-13. Wykonawca: agent researcher (Claude), zlecenie G10 z `docs/owner/GPT-PRO-RESEARCH-01.md` przejęte po ChatGPT Pro. Nic nie commitowano, OSM nie edytowano, Google nie używano.

## Cel i metoda

Ustalić ograniczenia ruchu ciężarówek w Białymstoku i na dojazdach (S8, DK8, DK19, DK65, obwodnice) i porównać je z tagami OSM. Wynik ma odpowiedzieć: (1) czy "0 krawędzi z limitami" w KRTG v2 to rzeczywistość, czy luka w danych; (2) co nadaje się na `authored_overrides`.

Metoda:
- **OSM**: odczyt lokalnego `Data/raw/osm/podlaskie-261108.osm.pbf` (Geofabrik, stan 2026-11-08), pas 22,95–23,35 E / 53,03–53,25 N. Zero zapytań do serwerów OSM. Wyciąg wszystkich dróg z tagami masy, wysokości, długości, szerokości, nacisku, hgv, goods, access, conditional: `files/osm_truck_tags_bialystok.csv` (6277 way, ODbL, (c) OpenStreetMap contributors).
- **Źródła urzędowe**: komunikaty UM Białystok (bialystok.pl), Radio JARD za UM, załącznik do uchwały Rady Miasta LI/794/18 (plan ograniczeń ruchu ciężarowego, s. 23, pobrany PDF), PZDW, ELI/Sejm (Prawo o ruchu drogowym).
- **Nie udało się**: Mapillary (brak tokenu API, a wpisywanie kluczy jest poza moim zakresem; lokalne 400 zdjęć kafla leży na trasach głównych i nie obejmuje ulic z tagami hgv=no — sprawdzone zdjęcie pod wiaduktem Putry jest kontrasłoneczne, bez znaków), BIP z zarządzeniami o stałej organizacji ruchu (wyszukiwarka nie zwróciła dokumentów), Dziennik Urzędowy Woj. Podlaskiego (brak trafień dla ruchu ciężkiego), strony Poranny/ddb24/TVP (HTTP 403 — używam tylko streszczeń wyszukiwarki i oznaczam UNVERIFIED), ISAP (CAPTCHA, nie omijałem — użyłem API ELI).

Pliki: `manifest.csv` (29 pozycji), `sources.md`, `files/` (uchwała LI/794/18 PDF + render s. 23 z planem ograniczeń, ekstrakt OSM), `tools/` (skrypty odtwarzające ekstrakt i manifest; `python -I tools/build_g10.py tools/osm_all.json tools/named.json .`).

## Odpowiedź na pytanie (1): brak limitów w regionie — rzeczywistość czy luka?

**W głównej mierze rzeczywistość, ale jest jedna realna luka potoku i dwie ciche pułapki.**

- W kaflu `bialystok-industrial-c` nie znaleziono żadnego **potwierdzonego** ograniczenia ciężarówek (tonaż, wysokość, długość). Plan UM (2018) klasyfikuje Andersa, Maczka, Al. Tysiąclecia, Wasilkowską i Ciołkowskiego jako "40 t dla wszystkich" (brak limitu), a OSM tam nie ma `maxweight`/`maxheight` liczbowego. Zgodne.
- **Luka potoku (do naprawy po stronie worldgen)**: `tools/worldgen/roadgraph.py` (whitelist atrybutów, linie 34 i 110) nie przenosi do `roads.graph.json` tagów `maxaxleload`, `maxlength`, `maxweight:hgv`, `hgv:conditional`, `maxgvweightrating:hgv`. W kaflu OSM ma `maxaxleload=11.5` na 83 way (Andersa, Maczka, Tysiąclecia, rondo Putry, łącznice). Wpływ na grę dziś zerowy (limit równy parametrowi ciężarówki 11,5 t = dozwolone), ale po rozszerzeniu regionu zadziała w drugą stronę: 27 way `maxaxleload=10` (Szosa Knyszyńska, Szosa Ełcka) da "brak trasy" dla 11,5 t.
- **Pułapka 1**: `maxheight=default` (rondo Putry, wiadukty Andersa, ronda Wolnej Ukrainy i Żołnierzy Wyklętych, Al. Niepodległości) jest poprawnie parsowane jako brak limitu. Rzeczywista skrajnia pod wiaduktem Putry pozostaje UNVERIFIED (nie ma znaku B-16 ani pomiaru).
- **Pułapka 2**: w kaflu 6 krawędzi `no-truck` pochodzi z `hgv=no` na **Bitwy Białostockiej** (way 178208423, z `goods=delivery` — tagi sprzeczne) i **Sokólskiej** (188396757). To jedyne tagi tego typu w kaflu i nie mają żadnego źródła urzędowego ani zdjęcia znaku (UNVERIFIED). Jeśli to błąd mapowania, odcinają ulice, którymi ciężarówka mogłaby dojechać do celów w kaflu.
- Poza kaflem OSM jest gęsty w limity (176 way `maxweight`, 120 `hgv=no`, 847 `maxaxleload`). Czyli brak limitów w regionie wynika z położenia kafla na trasie krajowej, nie z ogólnej luki OSM.

## Najważniejsze ustalenia

1. **Dojlidy (DK19 stary przebieg)**: zakaz > 3,5 t na ul. Dojlidy Fabryczne i ks. Suchowolca; tranzyt przeniesiony na Kuronia – Dywizjonu 303 – Ciołkowskiego (komunikaty UM 2025-11-19, 2025-12-01). OSM ma `maxweight=3.5` + `hgv=no` na 10 + 5 way, kończąc dokładnie na węźle Plażowa/Kuronia. **Zgodne**. Zastrzeżenia: zakres słowny w źródłach się rozjeżdża (Meyera–Plażowa vs Plażowa–Ciołkowskiego), wyjątki dostaw nieznane, `hgv=no` blokuje dostawy.
2. **Mickiewicza (Kuronia–Ciołkowskiego) > 8 t**: nowość listopada 2025 (Radio JARD). OSM `maxweight=8` na 14 way od węzła Kuronia do węzła Ciołkowskiego, 2 krótkie way bez tagu. **Zgodne**.
3. **Plan 2018 UM (s. 23 uchwały LI/794/18)**: miasto ma zhierarchizowane klasy tonażowe: 3,5 t (żółte, śródmieście), 12 t (zielone, większość ulic osiedlowych i miejskich), 40 t dla wszystkich (czerwone: Andersa, Maczka, Ciołkowskiego, Wasilkowska, Suchowolca/Dojlidy Fabryczne wtedy), 40 t z zaopatrzeniem (czerwone przerywane). W OSM praktycznie **brakuje** klas 12 t i strefy 3,5 t w centrum (**BRAK**). Plan jest z 2018 i część ulic zaostrzono po nim (Dojlidy, Mickiewicza), więc nie traktować go jako stanu aktualnego.
4. **Rozbieżności wartości**: Branickiego i Zwierzyniecka — OSM 8 t, plan 2018 12 t (**NIE**, aktualność UNVERIFIED). Warszawska way 842154286: `maxweight=12 t` razem z `hgv=no` (sprzeczne).
5. **OSM-only, bez potwierdzenia**: Czesława Miłosza/Branickiego północ (8 t + `hgv=no`, wyjątek dostaw), Niewodnicka (15 t, `hgv=designated`), osiedle Dojlidy Górne (43 way 3,5 t + `hgv=no`), obrzeża 10/15/24 t, Plażowa. Nie używać jako override bez zdjęcia znaku.
6. **Klucz `maxgvweightrating:hgv`** (używany w Białymstoku na Miłosza, Nowowarszawskiej, Niskiej) nie jest czytany przez `build_route_graph.py`, a towarzyszący `hgv=no` blokuje całkowicie; wyjątek `none @ delivery` jest ignorowany.
7. **S8**: w OSM 24 way z `toll:hgv=yes`, `maxspeed:hgv=80`. Oficjalnej listy odcinków e-TOLL nie pobrano (UNVERIFIED dla DK8/19/65).
8. **Prawo ogólne**: wysokość pojazdu z ładunkiem ≤ 4,0 m (PoRD art. 61 ust. 10, t.j. Dz.U. 2024 poz. 1251, ELI). Masy 40 t i długości zestawu w tej sesji NIE zweryfikowano. Wyrok WSA Białystok II SA/Bk 438/13 (2013): tonażowe B-18 bez zbadania nośności bywają unieważniane — tagi 8 t bez źródła warto traktować ostrożnie.
9. **Drogi wojewódzkie** w Białymstoku: tabela PZDW nie wymienia ograniczeń. **Parkowanie ciężarówek**: nie znaleziono zakazów postoju ani miejskich parkingów TIR (SPP w śródmieściu; abonament tylko ≤ 3,5 t).

## Top 10 dla trasy gry

| # | Pozycja | Wniosek |
|---|---|---|
| 1 | G10-001/002 Dojlidy Fabryczne i Suchowolca > 3,5 t | zgodne z OSM; wzorcowy override: wyjątek dostaw UNVERIFIED |
| 2 | G10-005 Mickiewicza 8 t (Kuronia–Ciołkowskiego) | zgodne z OSM |
| 3 | G10-004 trasa Kuronia–Dywizjonu 303–Ciołkowskiego | w OSM bez wskazania; dodać preferencję routingu (authored) |
| 4 | G10-013 Rondo Putry i wiadukty Andersa `maxheight=default` | brak znaku; skrajnia UNVERIFIED, ustawowo 4,0 m |
| 5 | G10-012 `maxaxleload=11.5` na 83 way kafla | luka potoku (roadgraph whitelist); dziś bez skutku |
| 6 | G10-014 Bitwy Białostockiej `hgv=no` | OSM-only, w kaflu, ryzyko fałszywej blokady |
| 7 | G10-015 Sokólska `hgv=no` | OSM-only, w kaflu |
| 8 | G10-011 Andersa/Maczka/Tysiąclecia bez limitów | zgodne z planem UM |
| 9 | G10-006/007/009 Miłosza, Branickiego, Warszawska | niespójne tagi (8 t vs 12 t, `hgv=no` + 12 t) |
| 10 | G10-021 S8 e-TOLL i 80 km/h dla HGV | informacja ekonomiczna, lista odcinków UNVERIFIED |

## Rekomendacje (bez zmian w repo)

- Rozszerzyć whitelist w `roadgraph.py` o `maxaxleload`, `maxlength`, `maxweight:hgv`, `maxgvweightrating:hgv`(+`:conditional`), `hgv:conditional`, `goods`, `toll:hgv` i dodać test z way 249640399 (Andersa, `maxaxleload=11.5`, kafel) jako przypadkiem. Nie zmieniałem kodu (poza moją własnością).
- `authored_overrides` (kolejność wiarygodności): G10-005, G10-001/002 (z wyjątkiem dostaw UNVERIFIED); G10-014/015 tylko po zdjęciu znaku. Nie zaszywać G10-007/008 (12 vs 8 t) bez dowodu.
- Zdjęcia znaków (Mapillary, CC BY-SA) dla Bitwy Białostockiej, Sokólskiej, Dojlid, Miłosza, Branickiego i wiaduktu Putry to jedyny sposób zamknięcia UNVERIFIED — wymaga tokenu API właściciela.

## Samokontrola (20 % = 6 z 29 pozycji, losowanie `random.seed(13)`: wiersze 6, 9, 10, 21, 22, 27)

- **6 (Miłosza i inne)**: ponownie odczytano 7 way z PBF — wszystkie tagi zgodne z manifestem.
- **9 (Warszawska)**: way 842154286 i 2 pozostałe — tagi zgodne.
- **10 (śródmieście, plan 2018)**: obejrzano render s. 23 (300 dpi) — żółte ulice w centrum potwierdzone; nazwy ulic częściowo nieczytelne, więc zostawiono UNVERIFIED.
- **21 (S8 e-TOLL)**: liczba 24 way z `toll:hgv` zgodna z ekstraktem; źródła odcinków nie pobrano — status UNVERIFIED utrzymany.
- **22 (zakaz weekendowy > 12 t)**: strona GITD tylko z wyników wyszukiwania — UNVERIFIED utrzymany.
- **27 (Poleska/Towarowa)**: ponowny odczyt Porannego — 403; UNVERIFIED utrzymany.
- Dodatkowo ponownie odczytano komunikat UM z 2025-12-01 (wiersz 2): potwierdza 3,5 t i sformułowanie "od Plażowej do Konstantego Ciołkowskiego" (źródło słowne różni się od prasy).
- Wynik: 0 pozycji z błędnym linkiem/tagiem; brak dowodu dla pozycji oznaczonych UNVERIFIED jest wprost opisany.

## Braki i niepewności

- Brak numerów zarządzeń/projektów stałej organizacji ruchu (BIP nie zwrócił wyników), brak typów znaków (B-5 vs B-18) i godzin wyjątków.
- Brak oficjalnych skrajni pionowych wiaduktów (S8, DK8/19/65, Putry, Towarowa–Poleska) i żadnych zdjęć B-16.
- Plan 2018 jest jedynym urzędowym dokumentem ze strefami 12 t i 3,5 t; jest nieaktualny w części i ma niską rozdzielczość mapy w PDF.
- Artykuły prasowe (Poranny, ddb24, TVP) nie zostały pobrane — nie opieram na nich żadnej liczby poza zaznaczoną jako UNVERIFIED datą 1 I 2026.
