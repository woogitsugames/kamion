# M54 — Ograniczenia dla ciężarówek w Białymstoku i okolicach, część 3 (mistral)

**Repo:** woogitsugames/kamion · **Gałąź:** `research/mistral-p8-restrictions-3` (z najnowszego `origin/main`)
**Zadanie:** M54 (docs/owner/RESEARCH-PACK-03-MISTRAL.md) · **Data badania:** 2026-11-13 · **Autor:** agent mistral
**Kontynuacja:** `research/g10-truck-restrictions/` (G10) i `research/gptpro/p8-truck-restrictions-2/` (P8-2, identyfikatory P8-001…P8-041) — **bez dublowania**; odczyty sekcji e-TOLL i rejestr ZDM cytowane za P8-2 (P8-040).

## Cel i zakres

Cztery pytania badawcze dla symulatora Kamion (Białystok 1:1 z OSM):

1. **Rzeczywista skrajnia / znak B-16 pod wiaduktami:** rondo Putry (Maczka, Andersa), al. Tysiąclecia nad linią kolejową nr 6, ronda Wolnej Ukrainy i Żołnierzy Wyklętych, S8 nad al. Niepodległości (Choroszcz).
2. **Podstawa prawna** zakazów/ograniczeń: Bitwy Białostockiej (`hgv=no`+`goods=delivery`), Sokólska (`hgv=no`), Branickiego i Zwierzyniecka (`maxweight=8`), Warszawska (`maxweight=12 t` przy `hgv=no`).
3. **Nowa S19 Krynice–Dobrzyniewo–Białystok Zachód** (otwarta 20.10.2026): naciski osi, wiadukty, znaki, obecność i tagi w OSM.
4. **Zmiany w e-TOLL po 1.02.2026** w promieniu 40 km od Białegostoku (DK8, DK19, DK65, S8, S19).

Ustalone wcześniej (nie badam ponownie): skrajnia ustawowa 5,00 m (klasy A/S) i 4,50 m (pozostałe) wg § 80 Dz.U. 2022 poz. 1518; e-TOLL od 1.02.2026 (Dz.U. 2026 poz. 33, lista od 10.02.2026).

## Metoda

- **Źródła dozwolone:** OSM (API 0.6, ODbL), Dz.U./ELI, MF e-TOLL, GDDKiA, MI, BIP Białystok/ZDM (urzędowe), Panoramax, KartaView, Wikimedia Commons. **Zakaz Google Maps/Street View/Earth — przestrzegany.**
- **Mapillary:** brak tokenu w sesji → pozycje oznaczone UNVERIFIED; nie zgadywano kluczy, nie używano cudzych tokenów.
- Geometrię przecięć (wiadukty nad rondami/linią kolejową) zweryfikowano **własnym testem segmentowym** na pełnych geometriach z OSM API 0.6 (punkt przecięcia odcinków, nie bbox).
- Historię tagów OSM pobrano z API 0.6 (`/way/{id}/history.json`) — wersja, changeset, użytkownik, source.
- Każda wartość: **źródło + data dostępu + cytat ≤ 25 słów** (sources.md) albo **UNVERIFIED/ESTIMATED**.
- **Kadry fotosferyczne:** wszystkie 40 pobranych kadrów Panoramax opisano w `photos.csv` (id, plik, odległość od punktu manifestu danego obiektu, azymut kamery `view:azimuth` z API Panoramax — w pierwszej turze metadanych azymut był `null`, pobrano go ponownie; 1-zdaniowy opis treści; obecność obiektu badanego w kadrze).
- **Samokontrola 20% z jawnym seedem** `20261113`: `audit_20_percent.json` — 6 z 28 pozycji (21,4%), każda z realnymi kontrolami wykonanymi ponownie (HTTP, OSM API, bbox, pliki, treść). **Samokontrola kadrów:** seed `20261113-m54fix`, 8 z 40 kadrów (20%) — niezależne ponowne wywołanie narzędzia wizji porównane z opisem w `photos.csv` (`audit_frames_20_percent.json`).

## Ustalenia

### Zad. 1 — Skrajnia / B-16 pod wiaduktami

**Wynik główny: dla żadnego z badanych wiaduktów nie znaleziono potwierdzonej wartości skrajni** (ani znaku B-16 na zdjęciach, ani dokumentu projektowego/inwentaryzacji). Wszystkie pozycje = UNVERIFIED + skrajnia ustawowa 4,50 m (A/S: 5,00 m).

| Obiekt | Weryfikacja lokalizacji | Materiał foto | Wynik wizji |
|---|---|---|---|
| Rondo Putry: Maczka (23844386, 173985170), Andersa (25447143, 173985172) | bbox nad rondem 180144451 | 10× Panoramax (16–90 m, 2019-08-15/09-01) + 4× Commons (2013–2021) | **brak B-16 w kadrze (10/10 Panoramax + 4 Commons)**; brak B-5/B-18; na 6ded8ec0 znaki **B-26** (zakaz wyprzedzania przez samochody ciężarowe) **i B-33 „70”** oraz tablice DK19/E67 — **nie B-19** (M54-007) |
| Al. Tysiąclecia nad linią kolejową nr 6 (197904073/74) | **potwierdzona testem segmentowym** — przecięcie way 34171047 (rail ref=6, PKP PLK) w pkt 53.16450/23.15006 i 53.16467/23.15010 | 10 kadrów (24–154 m; 7 z nich — jazda po jezdni wiaduktu; 3 bez mostu w kadrze, w tym 128187d5 skorygowany w audycie) | **kamera jedzie PO jezdni wiaduktu (droga na obiekcie, bridge=yes layer=1) — nad jezdnią nic nie wisi, brak B-16** (M54-008). **Al. Tysiąclecia nad linią 6: brak ograniczenia skrajni (droga na obiekcie)** |
| Rondo Wolnej Ukrainy: al. JP2 (615609894, 615614873) | potwierdzona testem segmentowym (bbox wiaduktów pokrywa rondo 615607647) | 10× Panoramax, **wszystkie 593–608 m od ronda** (photos.csv) | **wszystkie 10 kadrów: droga wielkomiejska (593–608 m od ronda) — rondo/wiadukty poza kadrem**; brak B-16 (M54-004; photos.csv) |
| Rondo Żołnierzy Wyklętych: Sulika (262041391, 175054484), Sosabowskiego (175054483, 262041392) | za P8-2 | **0 zdjęć** | brak |
| S8 nad al. Niepodległości, Choroszcz (183639791/92) | **potwierdzona**: mosty przecinają way 297345998 (ciąg al. Niepodległości **z brakującym tagiem `name`**; łączy się node 1908957194 z nazwanym segmentem 180455821) | 10× Panoramax (6–343 m od pkt manifestu 53.159539/22.996835; photos.csv) | **kadr 671cb8f5: kamera NA wschodnim moście S8** (pozycja = punkt przecięcia z al. Niepodległości); w żadnym kadrze most nie jest widoczny od strony jezdni (brak kadrów z al. Niepodległości pod mostami); brak B-16; na 6ac337cc w głębi widoczny inny wiadukt (ul. Podleśna nad S8, way 183641838) (M54-006) |

**Korekta względem G10:** w Starosielcach nad al. Niepodległości (318134435/626485641) **nie przebiega S8** — obiektem nad trasą jest **rondo Kmicica** (318134414/661035215, bridge=yes, layer=1); S8 przebiega ~4 km na zachód (węzeł Choroszcz). Założenie G10 o „wiadukcie S8 nad al. Niepodległości w Starosielcach" — **odrzucone** (M54-009).

Uwaga metodologiczna: kadr bez znaku ≠ brak znaku w terenie (obserwacje negatywne M54-007/M54-008 opisują tylko widoczne kadry). OSM na żadnym z wiaduktów nie ma `maxheight` (wszystkie mają `maxaxleload=11.5`, source: Dz.U. 2011 nr 222 poz. 1321).

### Zad. 2 — Podstawa prawna zakazów HGV

**Wynik główny: dla żadnej z 5 ulic nie ustalono numeru zarządzenia ani projektu organizacji ruchu** — wszystkie pozycje UNVERIFIED. Ustalono natomiast **pochodzenie tagów w OSM** (historia changesetów):

| Ulica (way) | Tagi | Historia tagu w OSM |
|---|---|---|
| Bitwy Białostockiej (178208423) | hgv=no + goods=delivery | **od v1** (2012-08-27, cs 12883607, cyunczykg; way jako „I Armii Wojska Polskiego") |
| Sokólska (188396757) | hgv=no | dodane **v20, 2026-10-22, cs 190904727** (Michoo, JOSM, source „Geoportal 2: BDOT500…", comment „Białostoczek - parkingi…") |
| Warszawska (842154286) | maxweight=12 t + hgv=no; goods=delivery | maxweight+hgv: **v7, 2025-03-01, cs 163097076** (Marek-M, „Korekta geometrii skrzyżowań"); goods od v1 (2020-08-29) |
| Branickiego (572651591–94) | maxweight=8 | **od v1** (2018-03-24, cs 57486579) — bez source |
| Zwierzyniecka (261469444) | maxweight=8 | dodane **v4, 2014-08-05, cs 24555223** (cyunczykg, **source „Wizja lokalna"**, comment „znaczniki maxweigt turnlanes i destination") → **znak fizycznie stał w terenie w 2014 r.**, akt prawny nieznany |

Weryfikacja urzędowa (negatywna): BIP UM Białystok — zarządzenia 295/26, 462/26, 786/26 istnieją, ale dotyczą innych tematów (identyfikacja w sesji: szkoła/lodowisko/służebność; skany bez warstwy tekstowej → identyfikacja UNVERIFIED). Komunikaty bialystok.pl: 20.11.2025 (Bitwy Białostockiej) = droga dojazdowa, ruch **jednokierunkowy** (nie hgv); 05.10.2026 (Sokólska) = remont mostku nad Białą (nie hgv). Rejestr organizacji ruchu ZDM niepubliczny — cyt. **P8-040**. Zdjęć znaków B-5/B-18 dla tych ulic nie było w Panoramax (0 wyników przy każdej ulicy), KartaView niedostępna technicznie (poniżej).

### Zad. 3 — S19 Krynice–Dobrzyniewo–Białystok Zachód (otwarta 20.10.2026)

Źródła: komunikaty MI i GDDKiA z 20.10.2026 (cytaty w sources.md). OSM: **37 ways `ref=S19;65`** na odcinku (węzeł Białystok Zachód ~53.1595/23.026 → Krynice ~53.1997/23.034).

- **Naciski osi:** urzędowo **11,5 t/oś**; OSM: `maxaxleload=11.5` na wszystkich 37 ways → **ZGODNA** (M54-017).
- **Wiadukty:** urzędowo **8** (w tym nad DK65 i nad linią kolejową Białystok–Ełk–granica z Litwą = przyszła Rail Baltica); OSM: **10 ways `bridge=viaduct` = 5 obiektów** → **CZĘŚCIOWA**, 3 obiekty do naniesienia w OSM (M54-018).
- **Mosty/przejścia:** urzędowo **4 mosty** (Supraśl, Biała; z funkcją przejść dla zwierząt) i **12 przejść dla zwierząt** (M54-019).
- **Skrajnia (maxheight):** brak w OSM, brak danych urzędowych w komunikatach → UNVERIFIED; obowiązuje skrajnia ustawowa (M54-020).
- **Opłaty (toll:hgv):** brak w OSM; odcinka **nie ma** na liście dróg płatnych e-TOLL (stan 13.11.2026) → **odcinek bezpłatny**; spójność 3 źródeł (M54-021, M54-028).
- **Węzeł Białystok Zachód:** łączy S8+S19; przebudowa S8 na 1,9 km; parametry: 2×2 + pas awaryjny + pas rozdziału; PORR+Unibep, umowa 19.05.2021, design&build 405,6 mln zł (M54-022).
- **Sąsiednie odcinki:** Czarna Białostocka–Białystok Północ i Białystok Północ–Dobrzyniewo w budowie, oddanie **Q1 2029**; dalej Południowa Obwodnica Białegostoku (Białystok Zachód–Deniski) (M54-023).

### Zad. 4 — e-TOLL po 1.02.2026 (promień 40 km od Białegostoku)

**Wynik główny: brak zmian sieci płatnych po 1.02.2026** w badanym promieniu.

- Podstawa listy obowiązującej od **10.02.2026**: rozporządzenie RM z 8.01.2026, **Dz.U. 2026 poz. 33** (ELI zweryfikowany 13.11.2026) (M54-024).
- **W promieniu 40 km płatne pozostają tylko odcinki S8**: Rzędziany–Tykocin (5470 m), Tykocin–Choroszcz (3490 m), węzeł Choroszcz (960 m); **DK8/DK19/DK65: zero** odcinków płatnych; odcinki S19 występujące na liście = południowe (poza regionem). Odczyt **własny** z pełnej listy (tekst PDF ekstraktowalny; cytaty ze str. 31–32 w sources.md; zgodny z P8-2) (M54-025).
- **Lista nowych odcinków** (MF, od 10.02.2026): żaden nowy odcinek w promieniu 40 km — potwierdzone **własnym odczytem** listy (6 stron: S8 — 0 sekcji; DK8 wyłącznie Augustów–Augustów Borki–Janówka–Raczki, str. 1; cytaty w sources.md) (M54-026).
- **Lista artykułów MF** (82–84 pozycje z datami, dostęp 13.11.2026): ostatni artykuł o zmianach sieci = „Zmiany w systemie e-TOLL od 1 lutego 2026 r." (**19.01.2026**); 16 artykułów nowszych dotyczy IKK/MOK/EETS/zwrotów — **0 dot. sieci** (zweryfikowane programowo w audycie, M54-027).
- **S19 Krynice poza e-TOLL** na 13.11.2026 (M54-028) — spójne z P8-2.

## Ograniczenia badania

1. **Mapillary** — brak tokenu (UNVERIFIED; nie używano cudzych kluczy).
2. **KartaView** — kontrola ponowna (poprawka PR): API `api.kartaview.org` odpowiada, ale zapytania o zdjęcia zwracają HTTP 400 „Restricted access!”; stara domena `api.openstreetcam.org` — niedopasowany certyfikat TLS → zdjęcia niepobrane; udokumentowane jako ograniczenie (żadna pozycja manifestu nie cytuje KartaView).
3. **Analiza wizyjna** — limit 20 wywołań narzędzia wizji na cykl odpowiedzi; badanie prowadzono w dwóch cyklach (2026-11-13): **wszystkie 40 kadrów Panoramax opisano w `photos.csv`** (Putry 10, Tysiąclecia 10, S8/Choroszcz 10, Wolnej Ukrainy 10).
4. **PDF-y MF** — tekst list e-TOLL **jest ekstraktowalny** (`pdftotext -layout`, potwierdzone w recenzji; w sesji — własny ekstraktor strumieni PDF/ObjStm z mapowaniem ToUnicode): sekcje S8/DK8/DK19/DK65 odczytano własnoręcznie (M54-025/026, cytaty ze stron w sources.md). PDF-y BIP (skany zarządzeń) pozostają bez warstwy tekstowej; tematy identyfikowane wizyjnie w sesji.
5. **GDDKiA/inwentaryzacje obiektów** — publicznie dostępne komunikaty nie podają skrajni wiaduktów; projekty budowlane S19/rond niedostępne online w sesji.

## Samokontrola

`audit_20_percent.json`: seed **20261113**, populacja 28 pozycji, próba **6 (21,4%)** — wylosowane deterministycznie `random.Random(20261113).sample(...)`: M54-001, M54-005, M54-006, M54-012, M54-021, M54-027. Kontrole: HTTP źródeł, ponowne pobranie ways z OSM API 0.6 + porównanie tagów, współrzędne vs bbox geometrii, obecność plików foto + zgodność metadanych Panoramax, treść listy artykułów MF. **Wynik: 6/6 PASS.**

**Kontrola zgodności opisów kadrów z obrazem** (nowa, poprawka PR): `audit_frames_20_percent.json` — seed **`20261113-m54fix`**, populacja 40 kadrów (`photos.csv`), próba **8 (20%)** wylosowana deterministycznie `random.Random("20261113-m54fix").sample(...)`: putry_35224dcb, putry_3717771d, s8_25c37bd1, s8_3c44481e, s8_3e661f95, s8_671cb8f5, s8_94dd9f98, tysiac_128187d5. Dla każdego wylosowanego kadru wykonano **niezależne ponowne wywołanie narzędzia wizji** i porównano z opisem w photos.csv (co widać + obecność obiektu w kadrze). **Wynik: 7/8 PASS, 1 niezgodność wykryta i skorygowana** (tysiac_128187d5: pierwotny opis „jazda po wiadukcie” odrzucony — 2 z 3 niezależnych odczytów: zwykła jezdnia bez mostu w kadrze; photos.csv poprawione, licznik kadrów „na obiekcie” dla Al. Tysiąclecia 8→7; wniosek M54-008 bez zmian). Pole `obiekt_w_kadrze` dla s8_671cb8f5 jest ustaleniem geolokalizacyjnym (pozycja = punkt przecięcia), nie wizualnym — wyjaśnione w pliku audytu.

## Struktura

```
research/mistral/p8-restrictions-3/
├── README.md            # ten plik
├── manifest.csv         # 28 pozycji M54-001..M54-028 (sep ';', UTF-8 BOM, kolumny jak P8-2)
├── photos.csv           # 40 kadrów Panoramax: id, plik, odległość_m, azymut_kamery, co_widać, obiekt_w_kadrze (sep ';', UTF-8 BOM)
├── sources.md           # wszystkie źródła: URL + data dostępu + licencja + cytat/strona + SHA256 PDF
├── audit_20_percent.json
├── audit_frames_20_percent.json  # kontrola zgodności opisów kadrów z obrazem, seed 20261113-m54fix
└── files/
    ├── rozp_2026_33.pdf.b64           # Dz.U. 2026 poz. 33 (MF, q05hn11w) — base64
    ├── full_list_2026-02-01.pdf.b64   # pełna lista odcinków płatnych od 10.02.2026 (MF, pmlhwkrm) — base64
    └── new_sections_2026-02-01.pdf.b64# lista nowych odcinków od 10.02.2026 (MF, skpplztd) — base64
```

**PDF-y w gicie jako `.b64`** (base64 = ASCII, kopiowanie bajt-dokładne przez `base64 -d plik.b64 > plik.pdf`; SHA256 oryginałów w sources.md — push binariów przez używany kanał API był uszkodzony, patrz komunikat PR). Oryginały PDF, zdjęcia (Panoramax 40×, Commons 4×), metadane Panoramax i kopie stron źródłowych (HTML) — w **`mistral-p8-restrictions-3-files-v2.zip`** (Artifact do pobrania w PR; zdjęcia NIE trafiły do gita zgodnie z zasadami — `files/photos/` w `.gitignore`). **v2:** zdjęcia Panoramax pomniejszone z 2048×1536 do **1600×1200 px** (LANCZOS, JPEG q90) — wersja v1 ZIP zawierała pliki 2048 px; Commons pobrane jako miniatury i przeskalowane do ≤1600 px; dodano wyniki kontroli KartaView.

## ID powiązań

- Kontynuacja: P8-001–P8-041 (`research/gptpro/p8-truck-restrictions-2/manifest.csv`), G10 (`research/g10-truck-restrictions/README.md`).
- Cytowania międzymanifestowe: **P8-040** (rejestr ZDM), odczyt sekcji e-TOLL z pełnej listy (dekodowanie P8-2), lokalizacja mostów nad rondem Żołnierzy Wyklętych (P8-2).
