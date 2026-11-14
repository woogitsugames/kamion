# P17 — Zmierzch w Białymstoku: niebo, oświetlenie ulic trasy, zapalone okna (M60)

Gałąź: `research/mistral-p17-dusk-lighting` (od `main` @ 913c8e2). Data dostępu źródeł: **2026-11-13**.
Pełne dane: `manifest.csv` (109 rekordów, id `P17-001`…`P17-109`), `sources.md`, `audit_20_percent.json`.
Zdjęcia **nie są w gicie** (`files/` w `.gitignore`); paczka: `mistral-p17-dusk-lighting-files.zip` (23 719 011 B, sha256 `93cddd14fcfeb0c162b3f39e2f5f49d4a251146c7523e931d36844a4575f4914`), 37 kadrów Commons ≤1600 px.

## Cel i metoda

Recenzja obrazu (`docs/reports/REVIEW-2026-11-13-s19-0182.md` P1-4, P1-5, P2-6/7/8) wykazała: brak plam światła pod latarniami, zero zapalonych okien, zbyt różowy horyzont. Pakiet dostarcza liczby i obserwacje do korekty:

1. **Niebo o zmierzchu** — literatura OA (AMS Glossary, Koomen 1952, Spitschan 2016, Schmude 2024, Faid 2024, Krieg 2026, Jechow 2019, Lee 1994) + własne przeliczenia (ESTIMATED z metodą).
2. **Oświetlenie ulic trasy gry** — PN-EN 13201-2:2015 (klasy M/P wg otwartej tabeli POLAB), przykład urzędowy starej normy (gmina Lipnik), wytyczne ZDM Kraków (Ra, fotokomórka + zegar astronomiczny), modernizacja Białegostoku 2023–2026 (bialystok.pl, TED, Yunex), rozstaw latarni z OSM (`highway=street_lamp`).
3. **Zapalone okna** — Team Nachtlichter/Kyba, Nature Cities 2025 (największe liczenie świateł: 234 044) + **15 kadrów CC** liczonych wizyjnie.
4. **Kadry ulic nocą** — **22 kadry CC** ulic Białegostoku (2020–2023, gł. autor Rakoon, CC0/CC BY; 1× CC BY-SA „tylko referencja”) — opis plam, barwy, halo.

Każdy kadr OBEJRZANY przez model wizyjny (zdanie „co widać”); wysokości Słońca z algorytmu NOAA z daty/godziny EXIF + GPS (strefa CET/CEST, w tym poprawka DST 2023-10-27). Ulice z GPS — reverse geocoding Nominatim. **RGB z pikseli nie było używane jako luminancja** — obserwacje kadrów są jakościowe/liczbowe wizyjne (ESTIMATED).

## Tabela 1. Niebo o zmierzchu (bezchmurnie, wieś vs miasto)

| h0 (Słońce) | Ev poziome [lx] — wieś | Ev [lx] — miasto (Filadelfia) | CCT zenit/otoczenia — wieś | Luminancja zenitu [cd/m²] |
|---|---|---|---|---|
| 0° (zachód) | 585–410 | — | — | ≈113 (EST) |
| −4° | **312** (mediana, n=25) | 36,1 | ≈11 100 K (EST) | ≈2,1 (EST, log-interp) |
| −5° | **146** (n=27) | 11,3 | — | ≈0,79 (EST) |
| −6° (koniec zmierzchu cywilnego) | **60** (n=24) | 3,5 | ≈15 100 K (EST) | **0,29** (przeliczenie ze Schmude 13,94 mag/arcsec²) |
| −7° | **21** (n=27) | 1,1 | — | — |
| −8° | **6,0** (n=27) | 0,49 | ≈20 200 K (EST) | ≈0,036 (EST, ekstrapolacja) |

Uzupełnienia: tempo zaniku **≈10× na każde 2°** dla h0 = −3…−11° (Koomen 1952); zmierzch nawigacyjny 3,5→0,008 lx, astronomiczny 0,008→0,0006 lx (AMS). Chmury: **nocą** nad wsią przyciemniają niebo (tłumik do 5,2×, naturalne Ev ≤0,34 mlx — Jechow 2019), nad miastem rozjaśniają 3,7–9× (8–37 → 38–230 mlx — Krieg 2026; Ettlingen 1,67→2,33 mlx). Barwa zmierzchu bardzo zmienna (Lee 1994); łuk przy horyzoncie po stronie Słońca ciepły żółtopomarańczowy, zenit chłodnieje z depresją (CCT 11k→20k K).

**Luka (UNVERIFIED):** brak w literaturze OA pomiarów lx przy **pochmurnym zmierzchu** −4…−8°.

## Tabela 2. Ulice trasy gry: klasa / luminancja / Uo / wysokość / rozstaw / źródło światła

| Ulica | Klasa (PN-EN 13201) | Lm [cd/m²] / Uo / Ul | Wysokość [m] | Rozstaw [m] | Źródło światła | Status |
|---|---|---|---|---|---|---|
| normy (kontekst) | M1: 2,0/0,40/0,70; M2: 1,5/0,40/0,70; M3: 1,0/0,40/0,60; M4: 0,75/0,40/0,60; M5: 0,50/0,35/0,40; M6: 0,30/0,35/0,40 | wg klasy | — | moduł 46–48 m przy h=9 m (przykład urzędowy ME4b/ME5) | — | SOURCED (POLAB, Lipnik BIP) |
| gen. Wł. Andersa | BRAK DANYCH | BRAK | UNVERIFIED (przykład urzędowy: 9) | **≈31,7** (OSM, 1 para, EST) | HPS→LED (przetarg 2023 „trasa generalska”) | ESTIMATED/UNVERIFIED |
| Al. Tysiąclecia PP | BRAK DANYCH | BRAK | UNVERIFIED | ≈11,3 (mediana; dwujezdnia — po stronie ≈2×; EST) | HPS→LED (przetarg 2023) | ESTIMATED/UNVERIFIED |
| gen. S. Maczka | BRAK DANYCH | BRAK | UNVERIFIED | 0 latarni w OSM (luka pokrycia) | HPS→LED (przetarg 2023) | UNVERIFIED |
| rondo Putry | BRAK DANYCH | BRAK | UNVERIFIED | 0 latarni w OSM | HPS→LED (przetarg 2023) | UNVERIFIED |
| Sokólska | BRAK DANYCH | BRAK | UNVERIFIED | 1 latarnia w OSM | — | UNVERIFIED |
| Wł. Wysockiego | BRAK DANYCH | BRAK | UNVERIFIED | ≈16,1 (2 latarnie; możliwe naprzemienne strony → ~32 m po stronie) | HPS→LED (przetarg 2023) | ESTIMATED/UNVERIFIED |
| Kombatantów | BRAK DANYCH | BRAK | UNVERIFIED | **31,2–33,4** (4 odstępy, OSM; light:lit=dusk-dawn) | — | ESTIMATED/UNVERIFIED |

**Klasa/luminancja/Uo/wysokość dla konkretnej ulicy trasy = UNVERIFIED** — dokumentacja projektowa przetargów nie jest dostępna anonimowo (Marketplanet: endpoint ZIP zwraca błąd; BIP: skany bez warstwy tekstowej). Rozstawy z OSM mają małą n — pokrycie OSM słabe (np. Andersa: 4 latarnie w bazie). Ortofoto GUGiK **odrzucone** jako metoda detekcji słupów (test kalibracyjny na znanych latarniach Andersa: model wizyjny zbeletryzował równomierne pozycje).

## Timeline modernizacji Białystok (HPS → LED)

- **2023:** budżet 8 mln zł; 4 650 opraw w tym roku; przetargi m.in. **Al. 1000-lecia PP, W. Wysockiego, „trasa generalska”** (Andersa+Maczka przez rondo Putry), gen. Kleeberga, Wasilkowska (bialystok.pl 28.07.2023); plan 19,62 mln zł do 2025.
- **2024–2025:** wymieniono **ponad 6 900 opraw** (bialystok.pl 18.08.2026).
- **2026:** kolejne etapy poza trasą: Ciołkowskiego/Zaułek Podlaski 382 latarnie LED (400 tys. zł); TED 193118/396132: listy ulic bez trasy. Sieć: do 25 000 punktów świetlnych, 325 szaf sterowniczych, 1 100 km tras (Yunex Traffic 2026; ~25% infrastruktury PGE Dystrybucja).
- **Próg włączania:** UNVERIFIED dla Białegostoku (brak publikacji progu lx). Praktyka ogólnopolska: **fotokomórka + zegar astronomiczny**, „załączenie opraw na 100% o zmierzchu”, redukcja 60% o 2:00 (ZDM Kraków, zał. 6 do zarz. 162/2025); OSM na Kombatantów: `light:lit=dusk-dawn`.

## Tabela 3. Zapalone okna (literatura + kadry CC liczone wizyjnie)

Literatura (Nachtlichter/Kyba 2025, Nature Cities, OA): **prywatne okna = najczęstszy typ świecącego światła w mieście** (przed latarniami); 39% prywatnych okien „pomarańczowych”; latarnie 46% pomarańczowe, 48% w pełni ekranowane; okna **wygasają** z porą nocy (krzywa logistyczna, 8 327 okien/386 sondaży).

Kadry (liczenie wizyjne, ESTIMATED ±2–3 okna; pełne wiersze w manifest.csv):

| Kadr (Commons) | Miejsce | h0 [°] | Zapalone okna |
|---|---|---|---|
| 20211209_153430 | pl. Niepodległości, Białystok | −3,7 | 20–30 |
| 20211209_154125 | Lipowa, Białystok | −4,5 | 5–7 |
| 20211209_154516 | Grochowa, Białystok (biurowiec) | −5,0 | 2 |
| 20221205_160356 | Lipowa, Białystok (kamienice) | −7,3 | 20–30 |
| 20221215_160004 | Lipowa, Białystok (budynek publiczny) | −7,0 | 6–8 |
| 20221215_160115* | Lipowa, Białystok | −7,1 | 20–30 |
| 20211211_161103 | Rynek Kościuszki, Białystok | −8,4 | 20–30 |
| 20221215_163819 | Zachodnia, Białystok (blok, LED) | −12,1 | 4–5 |
| 20221215_165405 | Zachodnia, Białystok (blok, LED) | −14,3 | ≈10 |
| 20221215_172504 | Kręta, Białystok (blok, LED) | −18,8 | 6–8 |
| 20231202_172101 | Rynek Kościuszki, Białystok (kamienice) | −17,9 | ≈30 |
| Mokotów nocą (panoramio) | Warszawa (bloki+biurowce) | b.d. | 50–100 |
| Skorosze (panoramio) | Warszawa | b.d. | 50–100 |
| Biurowiec „newcity” (panoramio) | Warszawa | b.d. | 50–60 |
| Osiedle (panoramio) | b.d. (blok) | b.d. | 1 |
| Biała, Warsaw | Warszawa | b.d. | 10–15 |

\* kadr wykorzystany też w kategorii „kadr”.

**Wniosek dla gry:** o zmierzchu (−3…−8°) pali się wyraźna mniejszość okien kamienic/bloków (pojedyncze do ~30 w kadrze ulicy), późnym wieczorem (−12…−19°) na blokach tylko pojedyncze okna (4–10), biurowce o zmierzchu mają dziesiątki zapalonych okien (50–60), w nocy gasną (krzywa logistyczna wg literatury). Zero zapalonych okien (obecny stan gry) jest nierealistyczne.

## Kadry ulic Białegostoku nocą (zad. 4) — wnioski dla grafiki

22 kadry (manifest: kategoria `kadr`). Wnioski:

- **Plamy światła:** pod KAŻDĄ latarnią HPS widać jasną plamę na jezdni/chodniku, rozdzieloną ciemniejszymi przerwami między słupami (np. 20231027_184842: 12 latarni = 12 plam; 20210114_163725: plamy na śniegu). Jezdnia NIE jest równomiernie jasna — potwierdza uwagę recenzji P1-4/P1-5.
- **Barwa:** dominują oprawy HPS — **żółtopomarańczowe** (2000 K klasy). Białe LED pojawiają się punktowo od 2021 (targ świąteczny 20211204 — oświetlenie tymczasowe; bloki Zachodnia 20221215; budynek handlowy 20211209_165940) — spójnie z timelinem modernizacji (masowa wymiana 2023–2025).
- **Halo:** przy HPS wyraźne halo/obłoczek wokół źródła (m.in. 20201206_161447, 20211202_183847); przy LED halo słabsze lub brak (20211204_183706 „słabe halo”, 20221215_163819 „brak halo”). Śnieg wzmacnia plamy i halo.
- **Zmierzch w kadrach potwierdza włączanie „o zmierzchu”:** przy h0 = −3,2° (20221209_153027) i −3,6° (20201218_153418) latarnie już świecą.

## Luki

1. lx przy pochmurnym zmierzchu −4…−8° — brak danych OA (UNVERIFIED).
2. Klasa M/luminancja/Uo/wysokość montażu per ulica trasy — dokumentacja projektowa niedostępna anonimowo (UNVERIFIED); przywołane wartości przykładowe z Lipnika (ME4b/ME5, h=9 m, moduł 46–48 m) i normy (POLAB).
3. Próg włączania latarni w Białymstoku (lx) — nieopublikowany (UNVERIFIED); pośrednio: dusk-dawn (OSM), fotokomórka+zegar astronomiczny (ZDM Kraków).
4. Kadry nocy ulic samej trasy gry (Andersa/Tysiąclecia/Maczka) — **brak w otwartych licencjach** (Commons: centrum Białegostoku; KartaView sekw. 2769366 z trasy = kadry dzienne 08.2019; Panoramax/Mapillary — poza zakresem). Kadry centrum (Lipowa/Rynek Kościuszki ~1,5 km od trasy) pokazują tę samą epokę HPS→LED.
5. Ortofoto GUGiK — zdjęcia pozyskane, ale detekcja słupów wizyjna odrzucona po teście kalibracyjnym (niewiarygodna).
6. Poważne wyliczenie odsetka zapalonych okien (%) wymaga liczby okien wszystkich — kadry dają liczbę zapalonych (przedziały); odsetek wyłącznie jakościowo.

## Samokontrola (audit)

`audit_20_percent.json`: seed **20261113**, `random.Random(seed).sample(ids, ceil(0.2·109))` = **22 rekordy**. Dla każdej pozycji ponownie sprawdzono: URL (HTTP), cytat/metodę w uwagach, status, datę dostępu, spójność GPS↔ulica i h0 (NOAA). Ograniczenie: analiza obrazów była jednorazowym przejściem wizyjnym (46 kadrów w 2 turach; limit 20 wywołań wizyjnych na turę odpowiedzi uniemożliwił niezależne drugie obejrzenie kadrów z próby — zamiast tego zweryfikowano metadane i pochodzenie plików).

## Licencje

- Kadry: Commons CC0 (Rakoon) i CC BY 3.0 (Rakoon), CC BY 4.0 (Raf24), CC BY-SA 3.0 — **„tylko referencja, nie tekstura”** (Borawski „Streetlamps in Białystok by night 1”, panoramio Klisowski/gustawkaz/Bromaski).
- OSM: ODbL (© OpenStreetMap contributors). GUGiK: dane otwarte.
- Teksty prasowe (bialystok.pl, Yunex): © — tylko fakty z krótkimi cytatami (referencja).
- Naukowe: CC BY 4.0 (OA) — Spitschan 2016, Faid 2024, Krieg 2026, Jechow 2019, Nature Cities 2025; abstrakty publiczne — Koomen 1952 (JOSA), Lee 1994 (Appl. Opt.); Schmude 2024 (Georgia J. Sci., OA).
