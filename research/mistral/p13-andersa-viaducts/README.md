# P13 — Estakady ul. gen. Andersa w Białymstoku: badanie dokumentacyjno-wizualne

Gałąź: `research/mistral-p13-andersa-viaducts` (katalog wyników: `research/mistral/p13-andersa-viaducts/`).
Data badania: 13.11.2026. Autor: subagent badawczy (Vibe/Mistral), zlecenie: M56/P13.

## 1. Cel

Dwie estakady Trasy Generalskiej w Białymstoku są landmarkami trasy w grze Kamion:
- **Obiekt A** — estakada **E4** nad Al. Tysiąclecia Państwa Polskiego (rondo Putry, DK8/DK19/DK65; OSM target: 1101181473, 173956078, 284022563, 606396460),
- **Obiekt B** — estakada nad rondem **Pamięci Bieżeństwa 1915 r.** nad ul. I Armii Wojska Polskiej (OSM target: 175157461, 177895177).

Do tej pory wymiary konstrukcji szacowano „na oko" z kilku zdjęć. Celem badania: zebranie twardych danych
z dokumentów urzędowych i legalnych źródeł otwartych (osobno A i B, osobno każda jezdnia), z oznaczeniem
statusu każdej liczby: SOURCED / ESTIMATED / UNVERIFIED.

## 2. Metoda

**Źródła (zgodnie z zasadami zadania):** Białystok.pl/BIP (dokumenty urzędowe, art. 4 pr. aut.), GUGiK/Geoportal
(ortofoto WMS — dane otwarte), OpenStreetMap (ODbL), Wikimedia Commons (CC0/CC BY/CC BY-SA), Panoramax
(CC BY-SA 4.0), portale branżowe i materiały wykonawców (tylko fakty — referencja, nie materiał graficzny).
**NIE użyto** żadnych treści Google (Maps/Street View/Earth/3D Tiles). Mapillary: dostęp wymaga tokenu
(którego nie wolno pozyskiwać z cudzych stron) → kadry z ADR-ów repo traktowane wyłącznie jako **referencja
niezweryfikowana** (wartości zapisano jako UNVERIFIED z atrybucją ADR).

**Geometria:** długości jezdni i rozstawy osi liczone z węzłów OSM (api.openstreetmap.org, haversine; przypisanie
kadru: odległość punkt→odcinek equirect, próg ≤ 60 m). **Ortofoto:** pomiar szerokości pomostu profilem jasności
na ortofotomozaice HR (0,25 m/px) prostopadle do osi — wynik ESTIMATED z metodą. **Zdjęcia:** każdy kadr
pozycjonowany WGS84 (6 miejsc), kierunek z EXIF/API (inaczej UNVERIFIED); kadr liczy się jako dowód tylko z
zdaniem „co widać" zapisanym po OBEJRZENIU obrazu.

**Ograniczenia uczciwe:**
1. Narzędzie analizy obrazu (vision) ma **limit wywołań na sesję** — wyczerpał się po obejrzeniu części kadrów.
   Kadry obejrzane wcześniej mają status SOURCED i zdanie „co widać"; kadry nieobejrzane są konsekwentnie
   **UNVERIFIED** (nawet jeśli pozycja/licencja są potwierdzone) — bez obserwacji kadr nie jest dowodem.
2. Środowisko wykonawcze było dwukrotnie resetowane; wszystkie strony źródłowe pobrano ponownie 13.11.2026
   i wtedy też powtórzono weryfikację cytatów (audyt).
3. Dokumentacja projektowa/ZRID/decyzje dla obu estakad **nie są publicznie dostępne** (brak w BIP;
   ewidencja obiektów mostowych ZDM niepublikowana). Wymiarów konstrukcyjnych nie da się potwierdzić
   dokumentami — luki oznaczone UNVERIFIED zamiast zgadywania.

## 3. Ustalenia — obiekt A (estakada E4, rondo Putry)

**Dokumenty (SOURCED):** estakada E4 powstała w ramach przebudowy ul. Gen. S. Maczka (kontrakt PEUiM +
PRM „Mosty Łódź", >159 mln zł, 22 miesiące). Odbiór końcowy: **30 września 2011**. UM Białystok: „Dla każdej
jezdni ul. Gen. St. Maczka ... estakadę nad Al. Tysiąclecia Państwa Polskiego o długości blisko 220 m" —
czyli **dwie równoległe estakady, po jednej na jezdnię**. W zakresie projektu: „ekrany akustyczne, oświetlenie
oraz sygnalizację świetlną". Obiekt figuruje w ewidencji ZDM jako **E4**; w 2024 r. przetoczono remont dylatacji
modułowych (B2 Sp. z o.o., 244 278 zł). PFU (zał. SIWZ, BIP) potwierdza segmenty ekranów akustycznych na
Trasie Generalskiej „ok. 2200 m (E1...E19), w tym E4".

**Geometria (OSM, ESTIMATED):** jezdnia NW (ways 173985172+23844386) — **219,0 m**; jezdnia SE
(25447143+173985170) — **212,9 m**; rozstaw osi jezdni **14,2 m**. Szerokość pomostu jezdni ~11 m
(ortofoto HR, profil jasności: pas płyty krawędziowej ±5,4–5,7 m od osi, szczelina ~3 m między jezdniami).

**Obserwacje z kadrów (SOURCED, obejrzane):** słupy **żółte**, przekrój **owalny**; płyta krawędziowa (gzyms)
**zielona**; ekrany akustyczne **przezroczyste**, obecne na **obu jezdniach** (kadr CC0 z 2021-05-03; CC BY-SA
2013 jako referencja). Precyzyjne strony ekranów (lewa/prawa krawędź jezdni): wg ADR 0125 (Mapillary —
referencja) ekran po prawej stronie jazdy; **niezweryfikowane** w tym badaniu.

**Jezdnia NW vs SE:** dokumenty nie rozróżniają jezdni („dla każdej jezdni"); geometria OSM pokazuje
symetrię (219,0 vs 212,9 m — różnica w granicach dokładności osadzenia osi). Kadry dowodowe nie
obejmują jednoznacznie obu stron każdej jezdni — patrz luki.

## 4. Ustalenia — obiekt B (estakada nad rondem Pamięci Bieżeństwa 1915 r.)

**Dokumenty (SOURCED):** estakada powstała w ramach przebudowy ul. Gen. W. Andersa (Trasa Generalska):
wykonawca **STRABAG Sp. z o. o.**, koszt projektu **50 211 296,17 PLN** (dofinansowanie UE 39 960 025,15 PLN,
85%), realizacja **III.2012–X.2013** (STRABAG: 02/2012–10/2013). Konstrukcja: „estakada o konstrukcji
**dwudźwigarowej sprężonej**"; nasypy dojazdowe „w murach oporowych z gruntu zbrojonego"; w sąsiedztwie
kładka łukowa stalowa z windą. Droga klasy **GP**, „dwie jezdnie po dwa pasy ruchu", trasa 1,5 km.

**Geometria (OSM, ESTIMATED):** jezdnia SW (way 177876107) — **195,8 m**; jezdnia NE (way 177895177) —
**195,5 m**; rozstaw osi **12,1 m**.

**Obserwacje z kadrów:** kadr CC0 z 2020-11-02 (rondo Pamięci Bieżeństwa) był podstawą ADR 0117 („brak
ekranów"); obserwacja z tej sesji brzmi sprzecznie („ekrany przezroczyste po obu stronach") — **konflikt
nierozstrzygnięty** (ponowne oględnięcie zablokowane limitem narzędzia): wiersz UNVERIFIED z adnotacją.
Kadr CC BY z 2020-07-11 (obejrzany): estakada widziana od strony Elektrociepłowni — potwierdza lokalizację
i generalny wygląd obiektu. Kandydatury na brakujący kadr połowy SE (20210320_092717, CC0) — UNVERIFIED
(nie obejrzano).

## 5. Tabele parametrów (parametr → wartość → źródło → status)

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

### A — geometria / pomost
| Parametr | Wartość | Źródło (id) | Status |
|---|---|---|---|
| geometria / długość osi jezdni | 219,0 m | OSM [P13-010] | ESTIMATED |
| geometria / długość osi jezdni | 212,9 m | OSM [P13-011] | ESTIMATED |
| geometria / rozstaw osi jezdni | 14,2 m | OSM [P13-012] | ESTIMATED |
| pomost / szerokość jezdni (pomostu) | ok. 11 m | ortofoto [P13-013] | ESTIMATED |

### A — elementy konstrukcyjne (pola z overrides.yaml)
| Parametr | Wartość | Źródło (id) | Status |
|---|---|---|---|
| ekrany akustyczne / zakres trasowy segmentów ekranów (Trasa Generalska) | ok. 2200 m, segmenty E1–E19, w tym E4 m | dokument [P13-009] | SOURCED |
| podpory / liczba rzędów podpór | — (brak danych)  | dokument | UNVERIFIED |
| podpory / liczba rzędów podpór | — (brak danych)  | dokument | UNVERIFIED |
| podpory / rozpiętości przęseł | — (brak danych) m | dokument | UNVERIFIED |
| podpory / rozpiętości przęseł | — (brak danych) m | dokument | UNVERIFIED |
| podpory / kształt słupa | owalny  | zdjęcie [P13-034] | SOURCED |
| podpory / wymiary słupa (średnica/rozstaw w rzędzie) | — (brak danych) m | dokument | UNVERIFIED |
| ekrany akustyczne / wysokość ekranu | — (brak danych) m | dokument | UNVERIFIED |
| ekrany akustyczne / wysokość ekranu | — (brak danych) m | dokument | UNVERIFIED |
| ekrany akustyczne / rozstaw słupków ekranu | — (brak danych) m | dokument | UNVERIFIED |
| ekrany akustyczne / strona jezdni z ekranem | prawej stronie jazdy (zewnętrzna krawędź)  | zdjęcie [P13-039] | UNVERIFIED |
| ekrany akustyczne / strona jezdni z ekranem | — (brak danych)  | zdjęcie | UNVERIFIED |
| ekrany akustyczne / obecność na jezdniach | ekrany przezroczyste na obu jezdniach  | zdjęcie [P13-041] | SOURCED |
| bariery / wysokość bariery | — (brak danych) m | dokument | UNVERIFIED |
| gzyms / kolor płyty krawędziowej (gzymsu) | zielony  | zdjęcie [P13-043] | SOURCED |
| podpory / kolor słupów | żółty  | zdjęcie [P13-044] | SOURCED |
| skrajnia / skrajnia pod obiektem | — (brak danych) m | dokument | UNVERIFIED |

### B — dokumenty
| Parametr | Wartość | Źródło (id) | Status |
|---|---|---|---|
| konstrukcja / schemat statyczny | estakada o konstrukcji dwudźwigarowej sprężonej  | dokument [P13-046] | SOURCED |
| konstrukcja / okres realizacji | 02/2012 – 10/2013  | dokument [P13-047] | SOURCED |
| konstrukcja / wykonawca | STRABAG Sp. z o.o.  | dokument [P13-048] | SOURCED |
| konstrukcja / koszt projektu | 50 211 296,17 PLN | dokument [P13-049] | SOURCED |
| finansowanie / dofinansowanie UE | 39 960 025,15 PLN (85%) PLN | dokument [P13-050] | SOURCED |
| droga / klasa drogi i układ jezdni | GP; dwie jezdnie po dwa pasy ruchu; trasa 1,5 km  | dokument [P13-051] | SOURCED |
| dojazdy / konstrukcja nasypów dojazdowych | mury oporowe z gruntu zbrojonego  | dokument [P13-052] | SOURCED |
| infrastruktura piesza / kładka | kładka łukowa o konstrukcji stalowej z windą dla niepełnosprawnych  | dokument [P13-053] | SOURCED |
| konstrukcja / roboty mostowe w kontrakcie | 17 785 TPLN netto (kontrakt 40 160 TPLN netto) PLN | dokument [P13-054] | SOURCED |
| konstrukcja / kontekst: estakada w ciągu Trasy Generalskiej | estakada nad ul. I Armii Wojska Polskiego (Trasa Generalska)  | dokument [P13-055] | SOURCED |

### B — geometria / pomost
| Parametr | Wartość | Źródło (id) | Status |
|---|---|---|---|
| pomost / szerokość jezdni (pomostu) | — (brak danych) m | ortofoto [P13-014] | UNVERIFIED |
| geometria / długość osi jezdni | 195,8 m | OSM [P13-056] | ESTIMATED |
| geometria / długość osi jezdni | 195,5 m | OSM [P13-057] | ESTIMATED |
| geometria / rozstaw osi jezdni | 12,1 m | OSM [P13-058] | ESTIMATED |

### B — elementy konstrukcyjne (pola z overrides.yaml)
| Parametr | Wartość | Źródło (id) | Status |
|---|---|---|---|
| podpory / liczba rzędów podpór | — (brak danych)  | dokument | UNVERIFIED |
| podpory / liczba rzędów podpór | — (brak danych)  | dokument | UNVERIFIED |
| podpory / rozpiętości przęseł | — (brak danych) m | dokument | UNVERIFIED |
| podpory / rozpiętości przęseł | — (brak danych) m | dokument | UNVERIFIED |
| podpory / wymiary słupa | ok. 0,70 x 1,40 m (kształt owalny/stadium) m | zdjęcie [P13-071] | UNVERIFIED |
| podpory / rozstaw słupów w rzędzie | ok. 3,5 m (para słupów pod każdej jezdnią) m | zdjęcie [P13-072] | UNVERIFIED |
| ekrany akustyczne / obecność ekranów | SPRZECZNOŚĆ: brak ekranów (repo) vs przezroczyste ekrany (obserwacja sesji)  | zdjęcie [P13-073] | UNVERIFIED |
| bariery / wysokość balustrady | — (brak danych) m | dokument | UNVERIFIED |
| gzyms / kolor płyty krawędziowej (gzymsu) | — (brak danych)  | zdjęcie | UNVERIFIED |
| podpory / kolor słupów | — (brak danych)  | zdjęcie | UNVERIFIED |
| skrajnia / skrajnia pod obiektem | — (brak danych) m | dokument | UNVERIFIED |
| oświetlenie / lampy między jezdniami | co ~32 m, dwustronne wysięgniki m | ortofoto [P13-078] | UNVERIFIED |

Pełny wykaz (także kadry z pozycjami, licencjami i przypisaniem do way_id) — `manifest.csv` (78 wierszy:
27 SOURCED, 7 ESTIMATED, 44 UNVERIFIED).

## 6. Luki (uczciwie) i rekomendacje

1. **Rozpiętości przęseł i liczba rzędów podpór (A i B):** brak dokumentacji projektowej/ZRID; ortofoto nie
   pozwala policzyć podpór (pomost zasłania filary). Repo zakłada 8 rzędów i przęsła ~21,3+26,4 m dla B
   (ADR 0144, Mapillary — **referencja niezweryfikowana**). → Rekomendacja: sesja zdjęciowa z drogi publicznej
   (rondo Putry / rondo Bieżeństwa) — zliczenie rzędów podpór z jednego kadru ustali geometrię.
2. **Wysokość ekranów, rozstaw słupków, wysokość bariery, skrajnia (A i B):** zero danych w otwartych
   źródłach. Wartości robocze w repo (screen_h 3,0 m; rail_h 1,10 m) pozostają **UNVERIFIED**.
3. **Kadr połowy SE estakady B:** kandydaci oznaczeni, ale nieobejrzani (limit vision) — do oględzin.
4. **Konflikt ekranów B (ADR 0117 vs obserwacja sesji):** wymaga decyzji lidera; sugerowane: zachowanie
   obecnego stanu „brak ekranów" w grze + adnotacja w overrides.yaml, że obserwacja badania była niepewna.
5. **Ewidencja obiektów mostowych (SIMB/ZDM):** niepubliczna; jedyny ślad ewidencji to oznaczenie „E4"
   w postępowaniu BIP z 2024 r.
6. **Mapillary:** potencjalnie najlepsze źródło wymiarów podpór, ale niedostępne legalnie bez tokenu —
   wszystkie wartości z Mapillary (przez ADR-y repo) pozostają referencją UNVERIFIED.

## 7. Samokontrola (audyt ≥20%)

Seed: **20261113**; metoda: `random.Random(seed).sample(ids, max(10, round(78*0.2)))` = **16 wierszy**.
Dla dokumentów: ponowne pobranie strony + sprawdzenie cytatu (normalizacja HTML); dla PDF: md5 +
zdekompresowany tekst; dla zdjęć: ponowne pobranie URL/metadanych — **ponowna analiza obrazu niemożliwa**
(limit narzędzia, odnotowane w JSON); dla wierszy bez źródła: potwierdzenie, że dokumentują brak.
Wynik: wszystkie cytaty potwierdzone (BIP zwrócił przy audycie 503 — weryfikacja przeciw snapshotowi
z 13.11.2026, odnotowane). Szczegóły: `audit_20_percent.json`.

## 8. Pliki

- `README.md` — ten raport; `manifest.csv` — 78 pozycji; `sources.md` — źródła z licencjami i cytatami;
  `audit_20_percent.json` — samokontrola.
- `files/.gitignore` ignoruje katalog `files/` (binaria poza gitem); `files/README.md` opisuje archiwum.
- **ZIP (poza gitem, przekazywany liderowi):** `mistral-p13-andersa-viaducts-files.zip` — 12 kadrów
  Commons (≤1600 px), 11 kadrów Panoramax (≤1600 px, przekodowane z sd 2048 px), 4 klatki ortofoto GUGiK,
  PDF PFU (md5 e34b42bcb705066affa2ebbe32a30bb2), snapshoty HTML stron źródłowych, metadane JSON.
  Nazwa, rozmiar i sha256 — w `files/README.md` i opisie PR.

*Zgodnie z zasadami: CC BY-SA (Commons 2013, Panoramax) = „referencja, nie tekstura"; materiały prasowe/
firmowe = tylko fakty (referencja); żadne treści Google nie zostały użyte.*
