# P17 — Zmierzch w Białymstoku: niebo, oświetlenie ulic trasy, zapalone okna (M60, poprawka s21)

Gałąź: `research/mistral-p17-dusk-lighting-fix-s21` (od `research/mistral-p17-dusk-lighting` @ `46a0fdd13`). Poprawka wg
`docs/owner/MISTRAL-FIXES-12.md` § M60-FIX i przeglądu `docs/reports/REVIEW-2026-11-14-s20-mistral-m60.md`. Data dostępu w s21: **2026-11-15**.
Pełne dane: `manifest.csv` (109 rekordów), `sources.md`, `audit_20_percent.json`, `STATUS.md`.
**Zdjęcia są w gałęzi**: `files/P17-073.jpg` … `files/P17-109.jpg` — 37 kadrów Commons, ≤ 1600 px (miniatury 1280 px; pionowe przeskalowane do 1600 px), razem ≈ 8,2 MB, sha256 każdego pliku w kolumnie `uwagi`. ZIP z M60 nie jest już potrzebny.

## Co zmieniono w s21 (skrót)

1. **Seria „wieś” (Spitschan 2016) wycofana** z tabeli 1 razem z CCT 11 100 / 15 100 / 20 200 K (P17-008…012, 018…020 → UNVERIFIED, nie do gry). Seria miejska → ESTIMATED (to całkowanie suplementu, nie liczba z tekstu).
2. **Horyzont**: brak liczb z literatury OA (luka, niżej); dodane obserwacje kadrów (jakościowe).
3. **Wszystkie 37 kadrów obejrzane osobno** i opisane od nowa (bez szablonu). Poprawione m.in.: 076/099 (białe = girlandy), 077/105 (0 okien), 079/100 (brak latarni), 103 (oprawy drogowe nie świecą), 106 (mgła), 109 (dzień).
4. **EXIF**: 083 h0 −5,66°, 084 −6,45°, 087 ≈ −4,31° (policzone NOAA); `kierunek_deg` = UNVERIFIED we wszystkich kadrach (EXIF bez GPSImgDirection).
5. **Okna — odsetek** zapalonych / widocznych dla 19 kadrów (tabela 3).
6. **Trasa**: „trasa generalska = Andersa + Maczka” → ESTIMATED (definicja z Wikipedii); montaż LED na trasie UNVERIFIED; rozstawy OSM przeliczone (Tysiąclecia ≈ 39 m, Wysockiego ≈ 48 m); Lipnik usunięty z wierszy ulic trasy.

## Tabela 1. Niebo o zmierzchu (bezchmurnie)

| h0 (Słońce) | Ev poziome [lx] — miasto (Filadelfia, Spitschan 2016, ESTIMATED z suplementu) | AMS / Koomen | Luminancja zenitu [cd/m²] |
|---|---|---|---|
| 0° (zachód) | — | 585–410 lx (AMS) | ≈113 (EST) |
| −4° | 36,1 | — | ≈2,1 (EST, log-interp) |
| −5° | 11,3 | — | ≈0,79 (EST) |
| −6° (koniec zmierzchu cywilnego) | 3,5 | **3,5–2 lx** (AMS) | **0,29** (przeliczenie ze Schmude 13,94 mag/arcsec², EST) |
| −7° | 1,1 | — | — |
| −8° | 0,49 | ≈10× na 2° (Koomen) | ≈0,036 (EST, ekstrapolacja) |

**Kolumna „wieś” i CCT zenitu usunięte (s21).** Wartości z M60 (np. 60 lx przy −6°) są ~17× wyższe od AMS i serii miejskiej z tej samej pracy,
a praca pisze, że obie lokalizacje „largely agree … up to nautical twilight”. Przyczyna najpewniej w czasie/h0 przy przeliczaniu suplementu — w s21
nie powtórzono przeliczenia, więc kolumnę usunięto. **Nie przenosić do gry.**

Uzupełnienia: tempo zaniku ≈10× na każde 2° dla h0 = −3…−11° (Koomen 1952); zmierzch nawigacyjny 3,5 → 0,008 lx, astronomiczny 0,008 → 0,0006 lx (AMS, cytat sprawdzony 2026-11-15).
Chmury nocą: nad wsią przyciemniają niebo (Jechow 2019), nad miastem rozjaśniają (Krieg 2026; liczby tabeli niepotwierdzone w s21 — P17-032).

## Horyzont — od strony Słońca i przeciwnie (zad. 1)

**Liczb (cd/m², CCT/xy) z literatury OA nie znaleziono → UNVERIFIED.** Sprawdzono (2026-11-15): Nawar i in., „Discontinuity in the Brightness of the
Twilight Sky at Different Wavelengths” (arXiv 1011.3024) — pomiary w pionie słonecznym i antysłonecznym na wys. 0/5/10/30/50/70° przy różnych
depresjach, ale w jednostkach S10 (gwiazdy 10 mag/deg²), z danych Abu-Simbel/Daraw (Nawar 1981/1983), tabele nieprzetworzone — do przeliczenia
na cd/m² potrzebny oryginał tabel (UNVERIFIED). Lee 1994 („Horizon brightness revisited”, Appl. Opt.) — tylko abstrakt/DTIC, bez tabel w dostępnej formie.

Obserwacje kadrów (jakościowe, nie pomiar):

| h0 | Kadr | Od strony Słońca | Przeciwnie / zenit |
|---|---|---|---|
| −3,3° | P17-103 | ciepły brzoskwiniowo-pomarańczowy pas tuż nad horyzontem, pod chmurami | wyżej bladoszare z lawendowym odcieniem |
| −3,7° | P17-073 | — (kierunek nieznany) | niebieskie, bez różu |
| −4,3° | P17-087 | — | niebieskie z chmurami, bez różu przy horyzoncie |
| −5,7° | P17-083 | — | granatowe, przy horyzoncie szaroniebieskie, bez różu |
| −6,5° | P17-084 | — | nasycone niebieskie (długi czas), przy horyzoncie jaśniejszy niebieskawy pas, bez różu |
| −8,1° | P17-101 | — | granatowe, ku horyzontowi jaśniejsze niebieskie |

Kierunki kadrów względem Słońca są nieznane (EXIF bez kierunku), więc strona „od Słońca / przeciwnie” rozstrzygnięta tylko dla 103 (ciepły pas = najpewniej strona zachodnia, UNVERIFIED).

## Tabela 2. Ulice trasy gry

| Ulica | Klasa (PN-EN 13201) | Lm / Uo | Wysokość [m] | Rozstaw [m] (OSM, ESTIMATED) | Źródło światła | Status |
|---|---|---|---|---|---|---|
| normy (kontekst) | M1: 2,0/0,40/0,70; M2: 1,5/0,40/0,70; M3: 1,0/0,40/0,60; M4: 0,75/0,40/0,60; M5: 0,50/0,35/0,40; M6: 0,30/0,35/0,40 | wg klasy | — | — | — | SOURCED (POLAB) |
| gen. Wł. Andersa | BRAK DANYCH | BRAK | UNVERIFIED | **≈31,5** (1 para; node 12625592983/984) | przetarg 2023 „trasa generalska” (obejmuje Andersa wg Wikipedii — ESTIMATED); montaż UNVERIFIED | ESTIMATED/UNVERIFIED |
| Al. Tysiąclecia PP | BRAK DANYCH | BRAK | UNVERIFIED | **≈38,7–39,0** (3 lampy; node 9845363979/81/85) | przetarg 2023; montaż UNVERIFIED | ESTIMATED/UNVERIFIED |
| gen. S. Maczka | BRAK DANYCH | BRAK | UNVERIFIED | 0 latarni w OSM | j.w. Andersa | UNVERIFIED |
| rondo Putry / Sokólska | BRAK DANYCH | BRAK | UNVERIFIED | 0 / 0–1 w OSM | — | UNVERIFIED |
| Wł. Wysockiego | BRAK DANYCH | BRAK | UNVERIFIED | **≈48,0** (2 lampy; node 12300169918/923) | przetarg 2023; montaż UNVERIFIED | ESTIMATED/UNVERIFIED |
| Kombatantów | BRAK DANYCH | BRAK | UNVERIFIED | **31,3–32,6** (+ para naprzeciw 12,3) | — | ESTIMATED |

Metoda rozstawu (s21): Overpass (maps.mail.ru, 2026-11-15) — `way[highway][name=…]` w granicach Białegostoku + `node[highway=street_lamp]`; lampy ≤ 25 m od osi;
odległość do najbliższego sąsiada. Wynik zgodny z przeglądem s20 (PBF 2026-11-08). Pokrycie OSM bardzo słabe (n ≤ 6 na ulicę).
Przykład z gminy Lipnik (droga wiejska, stara norma ME4b/ME5, h 9 m) **usunięty z wierszy ulic trasy** — nie dotyczy arterii.

## Timeline modernizacji Białystok (HPS → LED)

- **2023:** 8 mln zł; 4 650 opraw; przetargi m.in. „Alei 1000-lecia PP, Produkcyjnej, gen. Kleeberga, W. Wysockiego, tzw. „trasie generalskiej”” (UM 28.07.2023 — Andersa i Maczka w tekście **nie** padają).
  „Trasa Generalska biegnie ulicami generałów Franciszka Kleeberga, Stanisława Maczka, Władysława Andersa, Nikodema Sulika, Stanisława Sosabowskiego” (pl.wikipedia, CC BY-SA) → objęcie Andersa/Maczka przetargiem: ESTIMATED.
  **Przetarg ≠ montaż**: komunikatu o odbiorze ani kadru CC z LED na trasie nie znaleziono (s21). Kandydat TED 697205-2023 — treści nie zweryfikowano.
- **2024–2025:** ponad 6 900 opraw (UM 18.08.2026).
- **Próg włączania:** UNVERIFIED dla Białegostoku. Kadry: P17-089 (−3,6°, pochmurno) i P17-073 (−3,7°) — latarnie świecą; **P17-103 (−3,3°) — wysokie oprawy drogowe jeszcze NIE świecą** (świecą 2 niskie lampy). Sygnał: włączenie ok. −3…−3,5° (n = 3, ESTIMATED).

## Tabela 3. Zapalone okna — odsetek (zad. 3)

Literatura (Nachtlichter/Kyba 2025, OA): prywatne okna najczęstszym typem światła; okna gasną w ciągu nocy. Kadry (s21, ESTIMATED; liczone zapalone / widoczne,
bez witryn, lampek świątecznych i odbić; wycinki z miniatur 1280 px tam, gdzie zaznaczono):

| Kadr | Miejsce / typ | h0 [°] | Zapalone / widoczne | Odsetek | Uwagi |
|---|---|---|---|---|---|
| P17-073 | Białystok, blok/biurowiec + budynek z balkonami | −3,7 | ≈10 / ≈68 | ≈15 % | wycinki 3× i 2,2×; L 8/28, P 2/40 |
| P17-089 | Lipowa, kamienice | −3,6 | 1–2 / ≈40 | 3–5 % | pochmurno |
| P17-087 | Warszawa, bloki | −4,3 | ≈7–8 / ≈75 | ≈10 % | wycinki |
| P17-074 | Lipowa, kamienica | −4,5 | 1–2 / ≈25 | 4–8 % | |
| P17-075 | blok z bankiem w parterze | −5,0 | 1–2 / ≈6 | — | za mała próba |
| P17-083 | Warszawa, blok wielkopłytowy | −5,7 | ≈32 / ≈250 | **≈13 %** (±3) | klatki (4 pionowe przeszklenia) prawie całe zapalone; wycinek 1,6× |
| P17-090 | Rynek/Lipowa, kamienice | −6,0 | 1–2 / ≈30 | 3–7 % | |
| P17-084 | Warszawa, bloki | −6,5 | ≈50–65 / ≈240 | 20–27 % | długi czas naświetlania zawyża |
| P17-104 | Lipowa | −6,9 | 1–3 / ≈20 | 5–15 % | |
| P17-078 | willa/budynek instytucji | −7,0 | 3 / 9 | — | piętro 3/5, parter 0/4 (odbicia) |
| P17-105 | Lipowa | −7,1 | 0–1 / ≈30 | 0–3 % | |
| P17-077 | Lipowa, kamienice | −7,3 | 0 / ≈20 | 0 % | |
| P17-076 | Rynek, kamienice | −8,4 | ≈5–8 / ≈35 | 15–23 % | z miniatury 800 px |
| P17-088 | Lipowa/Rynek | −8,8 | 0–1 / ≈35 | 0–3 % | |
| P17-079 | blok | −12,1 | 4–5 / ≈25 | 16–20 % | wycinek |
| P17-080 | zespół bloków | −14,3 | ≈16 / ≈108 | ≈15 % | **klatki 8/10**, mieszkania ≈8/≈98 (≈8 %) |
| P17-081 | blok | −18,8 | ≈10–11 / ≈60 | ≈17 % | ±2 |
| P17-085 | biurowiec, Warszawa | b.d. | ≈1/3 kondygnacji | — | HDR; EXIF bez daty |
| P17-086 | szczyt bloku | b.d. | 1–3 / 12 | — | EXIF bez daty |
| P17-082 | Rynek | −17,9 | nierozstrzygalne | — | iluminacja fasad |

**Wnioski (ESTIMATED):** bloki mieszkalne przy h0 −4…−6° — ≈10–15 % okien (083, 087, 073), przy −12…−19° — ≈15–20 % (079, 080, 081); 084 (20–27 %) zawyżony długim czasem.
Kamienice deptaka Lipowa/Rynek o zmierzchu — 0–8 % (powód UNVERIFIED), wyjątek Rynek 076 (15–23 %).
Klatki schodowe w blokach są zapalone prawie w całości (080: 8/10; 083: 4 pionowe przeszklenia). **Żaden kadr bloku nie daje ≥ 30 %.**
Przegląd s20 (7 kadrów, 14–24 %) — potwierdzone co do rzędu, moje liczby dla 083/087 niższe (13 % / 10 % wobec 18 % / 14 %).

## Kadry ulic Białegostoku nocą (zad. 4) — wnioski z poprawionych opisów

22 kadry `kadr` to **deptak Lipowa i Rynek Kościuszki** (2020–2023), w większości grudniowe: ozdobne latarnie i iluminacja świąteczna (girlandy, lampki na drzewach, łuki).
**Nie są to arterie trasy C** — nie służą jako dowód stanu oświetlenia trasy. Wyjątki: 094 (przystanek), 101/103 (okolice kościoła), 106 (ul. Wyszyńskiego, mgła), 109 (dzień).

- **Plamy:** wyraźnych plam pod latarniami w kadrach deptaka zwykle **nie widać** — bruk i śnieg są oświetlone dość równo (088, 092, 093, 095), a na mokrej nawierzchni plam nie da się odróżnić od odbić (089, 104). Plamy pod latarniami widać na arterii w Warszawie (083, z wysoka). Teza M60 „pod KAŻDĄ latarnią jasna plama” — **wycofana** (106 to mgła, 092 śnieg oświetlony równo).
- **Barwa:** ozdobne latarnie deptaka — ciepłe pomarańczowe (074, 088, 090, 105) albo ciepłobiałe (092, 095, 102); maszty przy pl. Niepodległości — białawe, przepalone (073). Białe punkty w 076/097/099 to **iluminacja świąteczna**, nie oprawy LED.
- **Halo:** silne halo tylko we mgle (106 — rozpraszanie, nie cecha oprawy). Bez mgły halo słabe.
- **Łuna przy zachmurzeniu:** niebo i śnieg pomarańczowo-brązowe (079, 080, 081, 2022); 107 (2023) — niebo bardzo ciemne szarobrązowe.
- **Włączanie latarni:** patrz Timeline (103: −3,3° jeszcze nie; 089/073: −3,6…−3,7° już tak).
- **P17-109** to kadr dzienny/poranny (EXIF 07:28, h0 ≈ +13°) — poza kategorią „noc”.

## Luki

1. lx przy pochmurnym zmierzchu −4…−8° — brak danych OA (UNVERIFIED).
2. **Luminancja i barwa horyzontu (od Słońca / przeciwnie) dla h0 −2…−8°** — brak liczb OA (UNVERIFIED; kandydat: tabele Nawar 1981/1983 w S10, nieprzeliczone).
3. Seria „wieś” Spitschan 2016 — wycofana, przeliczenie suplementu do powtórzenia (plik, kolumna czasu, strefa, wzór h0).
4. Klasa M / Lm / Uo / wysokość montażu per ulica trasy — dokumentacja projektowa niedostępna (UNVERIFIED).
5. Montaż LED na trasie generalskiej / Tysiąclecia / Wysockiego — brak dowodu odbioru (UNVERIFIED); stan sód/LED na DK8 nieznany.
6. Próg włączania latarni w Białymstoku — nieopublikowany; sygnał z 3 kadrów (ESTIMATED).
7. Kadry nocne samej trasy gry — brak w otwartych licencjach.
8. Odsetek okien: n kadrów bloków przy h0 −4…−8° = 4 (073, 083, 084, 087), w tym 2 z Warszawy 2008; nowych kadrów (Commons „Blocks of flats at night in Poland”, Openverse, Panoramax) w s21 **nie szukano** (brak czasu).
9. P17-032 (Krieg 2026, tabela) i TED 193118/396132 (P17-058/059) — cytatów nie potwierdzono w s21.
10. Kierunki kadrów — UNVERIFIED (EXIF bez kierunku).

## Samokontrola s21

`audit_20_percent.json`: seed **20261115**; 8 kadrów + 14 innych = 22/109 (20,2 %). Kadry obejrzane ponownie osobnymi wywołaniami w dniu audytu:
**5 zgodnych, 3 niezgodne → poprawione** (084 kondygnacje i horyzont, 095 lampki, 107 niebo). Pozostałe 14: URL i cytaty sprawdzone ponownie — 1 niepotwierdzony
cytat (P17-032), 2 strony TED niesprawdzalne (HTTP 202), 2 wiersze wycofane zgodnie z FIX. Poprzedni audyt (seed 20261113) zachowany tylko jako historia.

## Licencje

- Kadry: Commons CC0 (Rakoon), CC BY 3.0 (Rakoon), CC BY 4.0 (Raf24), CC BY-SA 3.0 — **„tylko referencja, nie tekstura”** (Borawski, panoramio Klisowski/gustawkaz/Bromaski). Pliki w `files/` z atrybucją w manifeście.
- OSM: ODbL (© OpenStreetMap contributors). Wikipedia: CC BY-SA (tylko definicja nazwy, cytat).
- Teksty prasowe (bialystok.pl, Yunex): © — tylko fakty z krótkimi cytatami.
- Naukowe: CC BY 4.0 (OA) — Spitschan 2016, Faid 2024, Krieg 2026, Jechow 2019, Nature Cities 2025; arXiv 1011.3024 (licencja arXiv, tylko referencja).
- Google Maps/Street View/Earth — nie użyto. Mapillary — nie pobierano.
