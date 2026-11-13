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
- **Samokontrola 20% z jawnym seedem** `20261113`: `audit_20_percent.json` — 6 z 28 pozycji (21,4%), każda z realnymi kontrolami wykonanymi ponownie (HTTP, OSM API, bbox, pliki, treść).

## Ustalenia

### Zad. 1 — Skrajnia / B-16 pod wiaduktami

**Wynik główny: dla żadnego z badanych wiaduktów nie znaleziono potwierdzonej wartości skrajni** (ani znaku B-16 na zdjęciach, ani dokumentu projektowego/inwentaryzacji). Wszystkie pozycje = UNVERIFIED + skrajnia ustawowa 4,50 m (A/S: 5,00 m).

| Obiekt | Weryfikacja lokalizacji | Materiał foto | Wynik wizji |
|---|---|---|---|
| Rondo Putry: Maczka (23844386, 173985170), Andersa (25447143, 173985172) | bbox nad rondem 180144451 | 10× Panoramax (15–97 m, 2019-08-15/09-01) + 4× Commons (2013–2021) | **17 analiz: brak B-16 w kadrze**; brak B-5/B-18; na kadrze 6ded8ec0 widoczne B-19 i E-67 (M54-007) |
| Al. Tysiąclecia nad linią kolejową nr 6 (197904073/74) | **potwierdzona testem segmentowym** — przecięcie way 34171047 (rail ref=6, PKP PLK) w pkt 53.16450/23.15006 i 53.16467/23.15010 | 4 najbliższe kadry (14–73 m) | **wiadukt nad jezdnią, brak znaków w kadrze** (M54-008) |
| Rondo Wolnej Ukrainy: al. JP2 (615609894, 615614873) | potwierdzona testem segmentowym (bbox wiaduktów pokrywa rondo 615607647) | 10× Panoramax, **wszystkie ≥576 m** — brak obserwacji | brak |
| Rondo Żołnierzy Wyklętych: Sulika (262041391, 175054484), Sosabowskiego (175054483, 262041392) | za P8-2 | **0 zdjęć** | brak |
| S8 nad al. Niepodległości, Choroszcz (183639791/92) | **potwierdzona**: mosty przecinają way 297345998 (ciąg al. Niepodległości **z brakującym tagiem `name`**; łączy się node 1908957194 z nazwanym segmentem 180455821) | 10× Panoramax (165–190 m) | **analiza niedostępna w cyklu (limit 20 wywołań narzędzia wizji)** — zdjęcia w ZIP do ręcznej kontroli (M54-006) |

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
- **W promieniu 40 km płatne pozostają tylko odcinki S8**: Rzędziany–Tykocin (5470 m), Tykocin–Choroszcz (3490 m), węzeł Choroszcz (960 m); **DK8/DK19/DK65: zero** odcinków płatnych; odcinki S19 występujące na liście = południowe (poza regionem). Odczyt sekcji z PDF za dekodowaniem **P8-2** (fonty CID w ObjStm — tekst nieekstraktowalny standardowo) (M54-025).
- **Lista nowych odcinków** (MF, od 10.02.2026): żaden nowy odcinek w promieniu 40 km — wnioskowanie pośrednie z pełnej listy; do potwierdzenia dekodowaniem (M54-026).
- **Lista artykułów MF** (82–84 pozycje z datami, dostęp 13.11.2026): ostatni artykuł o zmianach sieci = „Zmiany w systemie e-TOLL od 1 lutego 2026 r." (**19.01.2026**); 16 artykułów nowszych dotyczy IKK/MOK/EETS/zwrotów — **0 dot. sieci** (zweryfikowane programowo w audycie, M54-027).
- **S19 Krynice poza e-TOLL** na 13.11.2026 (M54-028) — spójne z P8-2.

## Ograniczenia badania

1. **Mapillary** — brak tokenu (UNVERIFIED; nie używano cudzych kluczy).
2. **KartaView** — istnieją metadane serii przy badanych obiektach, ale storage/CDN niedostępny w sesji (NXDOMAIN/502) → zdjęcia niepobrane; udokumentowane jako ograniczenie.
3. **Analiza wizyjna** — limit 20 wywołań na cykl odpowiedzi: 21 analiz wykonanych (Putry 17, Tysiąclecia 4); kadrów S8/Choroszcz **nie przeanalizowano** — pliki w ZIP do ręcznej kontroli (M54-006).
4. **PDF-y MF/BIP** — fonty CID w ObjStm: pełny tekst nieekstraktowalny standardowo; sekcje e-TOLL cytowane za P8-2; tematy zarządzeń BIP identyfikowane wizyjnie w sesji (skany).
5. **GDDKiA/inwentaryzacje obiektów** — publicznie dostępne komunikaty nie podają skrajni wiaduktów; projekty budowlane S19/rond niedostępne online w sesji.

## Samokontrola

`audit_20_percent.json`: seed **20261113**, populacja 28 pozycji, próba **6 (21,4%)** — wylosowane deterministycznie `random.Random(20261113).sample(...)`: M54-001, M54-005, M54-006, M54-012, M54-021, M54-027. Kontrole: HTTP źródeł, ponowne pobranie ways z OSM API 0.6 + porównanie tagów, współrzędne vs bbox geometrii, obecność plików foto + zgodność metadanych Panoramax, treść listy artykułów MF. **Wynik: 6/6 PASS.**

## Struktura

```
research/mistral/p8-restrictions-3/
├── README.md            # ten plik
├── manifest.csv         # 28 pozycji M54-001..M54-028 (sep ';', UTF-8 BOM, kolumny jak P8-2)
├── sources.md           # wszystkie źródła: URL + data dostępu + licencja + cytat/strona + SHA256 PDF
├── audit_20_percent.json
└── files/
    ├── rozp_2026_33.pdf.b64           # Dz.U. 2026 poz. 33 (MF, q05hn11w) — base64
    ├── full_list_2026-02-01.pdf.b64   # pełna lista odcinków płatnych od 10.02.2026 (MF, pmlhwkrm) — base64
    └── new_sections_2026-02-01.pdf.b64# lista nowych odcinków od 10.02.2026 (MF, skpplztd) — base64
```

**PDF-y w gicie jako `.b64`** (base64 = ASCII, kopiowanie bajt-dokładne przez `base64 -d plik.b64 > plik.pdf`; SHA256 oryginałów w sources.md — push binariów przez używany kanał API był uszkodzony, patrz komunikat PR). Oryginały PDF, zdjęcia (Panoramax 40×, Commons 4×), metadane Panoramax i kopie stron źródłowych (HTML) — w **`mistral-p8-restrictions-3-files.zip`** (Artifact do pobrania w PR; zdjęcia NIE trafiły do gita zgodnie z zasadami — `files/photos/` w `.gitignore`).

## ID powiązań

- Kontynuacja: P8-001–P8-041 (`research/gptpro/p8-truck-restrictions-2/manifest.csv`), G10 (`research/g10-truck-restrictions/README.md`).
- Cytowania międzymanifestowe: **P8-040** (rejestr ZDM), odczyt sekcji e-TOLL z pełnej listy (dekodowanie P8-2), lokalizacja mostów nad rondem Żołnierzy Wyklętych (P8-2).
