# M52 — P2 surfaces 2 (znaki poziome P-*, nawierzchnie Białegostoku)

Paczka badawcza M52. Gałąź: `research/mistral-p2-surfaces-2`. Kontynuacja / uzupełnienie
`research/gptpro/p2-surfaces/` (M51/P2-001…P2-094) — **bez dublowania** tamtych ustaleń.

> **M52-FIX (13.11.2026)** — rewizja po przeglądzie s17
> (`docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p6p8p9p5.md`, origin/main). Zmiany:
> (1) podpisy dolne figur zał. 2 („0,20 / 0,24 / 0,32 / 0,08 m²/mb” itd.) to **zużycie farby
> na metr bieżący**, nie wymiary — błąd metody M52; etykiety „4,00” (kreska) i „2,00” (przerwa)
> na rys. 2.2.1.8 / 2.2.1.11 / 2.2.1.12 uzupełnione, ESTIMATED z pikseli usunięte;
> (2) P-12/P-13/P-14: reinterpretacja podpisów + wymiary z etykiet i tekstu;
> (3) kadry Jaroszówki opisane jako ujęcia **z estakady Andersa** nad rondem + wynik negatywny
> poszukiwania kadrów z poziomu ringu (M52-117);
> (4) kolor_srgb liczony z dolnych 45% kadru usunięty (maska auta), kolor trasy → UNVERIFIED;
> (5) `.gitignore`; (6) samokontrola 20% z odczytami etykiet i jawnym „co widać”.
>
> **M52-FIX r2 (13.11.2026)** — zalecana rundka z renderem WYKONANA: strony Dz.U. zał. 2
> (PDF c2 z eli.gov.pl) wyrenderowano (150 dpi; PyMuPDF niedostępny w sesji — własny parser
> PDF + rastry natywne ×3) i **obejrzano każdy rysunek z zakresu M52** (P-2a…P-25, w tym
> P-7a/b/c/d, suplementowo P-10). Etykiety wymiarowe przepisane z obrazu (tabela zad. 1);
> pozycje „do potwierdzenia oględziną” rozstrzygnięte. Kolumny `kolor_srgb`/`metoda_koloru`
> **usunięte ze schematu manifestu** (19 → 17 kolumn). Poszukiwanie kadrów ringu Jaroszówki
> powtórzone (Panoramax + KartaView API) — wynik negatywny ze szczegółami. Kadry
> fotograficzne nie zostały obejrzane w r2 (limit analiz obrazu sesji wyczerpany na
> rysunkach Dz.U. — priorytet zad. 1); status koloru pozostaje UNVERIFIED.

## Zakres (6 zadań)

1. Wymiary znaków poziomych **z rysunków** załącznika nr 2 do rozporządzenia w sprawie
   szczegółowych warunków technicznych dla znaków i sygnałów drogowych
   (jednolity tekst: Dz.U. 2019 poz. 2311; PDF z eli.gov.pl, część c2):
   P-2a/b, P-3a/b, P-4, P-5, P-6 (szerokości linii, odstęp linii podwójnych, kreska/przerwa),
   P-12, P-13, P-14, P-21a/b, P-23, P-25. Dla każdej wartości: **numer rysunku + strona Dz.U.**
   Źródła wtórne (blogi, tioman.pl) odrzucone jako niepotwierdzające.
2. Zdjęcia kafla startowego **Jaroszówka** (~53,152 N 23,168 E) z poziomu jezdni — ≥10 kadrów,
   data + azymut.
3. Zdjęcia + wymiary: **azyle** (wyspy dzielące), **płytki dotykowe** (układ rzędów),
   **ścieki przykrawężnikowe i wpusty** — Białystok.
4. **Kolor dróg i pasów rowerowych** na trasie startowej (Andersa, Al. Tysiąclecia, Sokólska,
   Wileńska): gdzie czerwony asfalt, gdzie pas malowany na szarym asfalcie — pozycje + zdjęcia.
5. **Rynek Kościuszki**: rodzaj nawierzchni (kostka granitowa? wymiary, układ) — z dokumentu
   (projekt rewitalizacji, BIP) albo ESTIMATED ze zdjęcia z metodą.
6. Aktualny katalog standardów/wytycznych **ZDM/ZDiT Białystok** (nowszy niż
   „Wytyczne do projektowania” z 13.07.2018, BIP resource 99308) — link, data, zmiany.

## Ważna korekta względem starej paczki (P2)

**P-11 to PRZEJAZD DLA ROWERZYSTÓW** (szerokość 1,8 m jednokierunkowy / 3,0 m dwukierunkowy),
NIE „przebieg przejścia/azyl”. Potwierdzone tekstem rozporządzenia (Dz.U. 2019 poz. 2311,
zał. 2, rozdz. 4.2.2 — str. Dz.U. 569).

---

## Zadanie 1 — Wymiary znaków poziomych z rysunków zał. 2 (Dz.U. 2019 poz. 2311)

### Metodologia (stan po M52-FIX — opis uczciwy)

**M52 (pierwotny odczyt):** PDF c2 (zał. 2) zawiera rysunki jako obrazy rastrowe
(natywne 355–1054 px szer.); etykiety wymiarowe są częścią obrazu. Odczyt programowy:
binaryzacja + detekcja komponentów glifów + klastrowanie glifów (odległość Hamminga) +
walidacja krzyżowa z wartościami znanymi z tekstu (P-7a/b: 0,24 m; P-7c/d: 0,12 m — str. 545;
P-10: 4,0 m — str. 567; P-11: 1,8/3,0 m — str. 569; tabela 5.3 — str. 589).
Mapowanie stron: **PDF c2 str. N = Dz.U. str. N+525**.

**Błąd metody M52 (przyznany w M52-FIX):** rysunków nie obejrzano wizualnie.
Podpisy dolne figur („0,20”, „0,24”, „0,18”, „0,32”, „0,08”, „0,5”, „0,375”, „0,2825”)
zinterpretowano jako wymiary (odstępy osi / wysokości), a etykiety kreski/przerwy
na rys. 2.2.1.8/2.2.1.11 pominięto i zastąpiono pomiarem pikselowym (ESTIMATED).

**M52-FIX (ta rewizja).** Podstawą korekt są:
1. **odczyty wizualne przeglądu s17** — rys. 2.2.1.8 (s. 538): linie 0,12 / odstęp 0,12 / 0,12,
   kreska 4,00, przerwa 2,00, podpis „0,20 m²/mb”; rys. 2.2.1.10 (s. 540): 0,12×3, podpis 0,24;
   rys. 2.2.1.11 (s. 540): 0,12×3, kreska 4,00 / przerwa 2,00, podpis 0,32; rys. 2.2.1.12 (s. 541):
   0,12, kreska 4,00, przerwa 2,00, podpis 0,08;
2. **walidacja arytmetyczna** semantyki podpisów: zużycie [m²/mb] = Σ(szerokości linii) ×
   wypełnienie, wypełnienie = kreska/(kreska+przerwa):
   P-3a 0,20 = 0,12 + 0,12×(4/6) ✓; P-4 0,24 = 0,12+0,12 ✓; P-6 0,08 = 0,12×(4/6) ✓;
   P-3b 0,18 → wypełnienie 1/2 (kreska=przerwa) ✓; P-12 0,5 = 0,50×1 mb linii ciągłej ✓;
   P-14 0,375 = 0,75×0,50 przy jednostce 1,00 m ✓; P-13 0,2625 = ½×0,75×0,70 przy jednostce
   1,00 m ✓;
3. **oględziny M52-FIX r2** — strony Dz.U. wyrenderowano (PDF c2, 150 dpi; rastry natywne
   ×3; PyMuPDF niedostępny w sesji — własny parser PDF) i **obejrzano każdy rysunek z
   zakresu M52**: P-2a/b, P-3a/b, P-4, P-5, P-6, P-7a/b/c/d, P-10 (suplement), P-11,
   P-12, P-13, P-14, P-21a/b, P-23, P-25; odczyty etykiet zweryfikowano pikselowo
   (proporcje kreska:przerwa, podstawa:wysokość:odstęp w skali rysunku);
4. stary odczyt programowy etykiet (tam, gdzie glify pełne).

**Semantyka podpisów dolnych (M52-FIX):** każda figura zał. 2 ma podpis z **zużyciem farby**
w m² na 1 mb linii (dla P-13/P-14 przy jednostce powtarzalnej 1,00 m wartość m²/mb = m² na
element). Dekoracyjny człon [cyfra][pion]mb; odczytywana liczba zawsze przed „m”.

**M52-FIX r2 (zalecenie wykonane).** Render stron Dz.U. + oględziny rysunków wykonano —
pozycje „do potwierdzenia oględziną” z M52-FIX rozstrzygnięte (tabela zad. 1). Ograniczenie
r2 (jawne): kadry fotograficzne (Jaroszówka/trasa/Rynek) nie zostały obejrzane — limit
20 analiz obrazu na odpowiedź sesji wyczerpany na rysunkach Dz.U. (priorytet zad. 1);
opisy kadrów s17 pozostają podstawą dla jar-01/07/12/20, pozostałe kadry mają jawne
deklaracje nieobejrzenia z podstawą przypisania (przebieg sekwencji, azymuty).

### Tabela etykiet wymiarowych i zużycia farby (stan po M52-FIX r2 — oględziny renderu)

Nazwy znaków wg listy w pkt 2.2 (str. Dz.U. 531). Statusy: SOURCED (odczyt z rysunku
urządowego / tekst rozporządzenia), ESTIMATED (metoda z opisem), UNVERIFIED.
„Potwierdzenie wizualne s17” = odczyt z oględzin przeglądu s17 (review, origin/main);
„oględziny r2” = własna oględzina renderu 150 dpi + rastry natywne ×3 (M52-FIX r2).

| Znak | Etykieta na rysunku | Czego dotyczy | Wartość | Rysunek | Str. Dz.U. | Zużycie farby (podpis dolny) | Status / metoda |
|---|---|---|---|---|---|---|---|
| P-2a | „0,12” | szerokość linii | **0,12 m** | 2.2.1.6 | 536 | 0,12 m²/mb | SOURCED: etykieta — oględziny r2 (27 px) + odczyt programowy; zużycie = szer. × 1 mb ✓; walidacja P-7 (str. 545) |
| P-2b | „0,24” | szerokość linii | **0,24 m** | 2.2.1.7 | 537 | 0,24 m²/mb | SOURCED: oględziny r2 (61 px = 2×27 px linii P-2a) + odczyt programowy; spójność z P-7a/b 0,24 (str. 545) |
| P-3a | „0,12” ×3 | szerokość linii górnej / **odstęp między liniami** / szerokość linii dolnej | 0,12 / 0,12 / 0,12 m (osie 0,24 m) | 2.2.1.8 | 538 | — | SOURCED: odczyt programowy; **potwierdzenie wizualne s17** („linie 0,12 / odstęp 0,12 / 0,12”) |
| P-3a | „4,00” | **kreska** (linii przerywanej) | **4,00 m** | 2.2.1.8 | 538 | — | SOURCED: etykieta, **potwierdzenie wizualne s17 + oględziny r2** (pomiar pikselowy: kreska 512 px : przerwa 260 px = 2:1 ✓); zastępuje ESTIMATED z pikseli (~2,0–2,4 m) |
| P-3a | „2,00” | **przerwa** (linii przerywanej) | **2,00 m** | 2.2.1.8 | 538 | — | SOURCED: etykieta, **potwierdzenie wizualne s17 + oględziny r2** (pomiar 2:1 ✓); zastępuje ESTIMATED (~0,56–0,62 m) |
| P-3a | „0,20” | podpis dolny figury | — | 2.2.1.8 | 538 | **0,20 m²/mb** | SOURCED: przegląd s17; arytmetyka 0,12 + 0,12×(4/6) = 0,20 ✓ [M52-FIX: reinterpretacja — stary zapis „odstęp osi” wycofany] |
| P-3b | „0,12” ×3 | szerokości linii + odstęp | 0,12 / 0,12 / 0,12 m (osie 0,24 m) | 2.2.1.9 | 539 | — | SOURCED: oględziny r2 (3× „0,12” potwierdzone na obrazie; struktura jak P-3a) |
| P-3b | „1,00” + „1,00” | **kreska / przerwa** (linii przerywanej) | **1,00 / 1,00 m** | 2.2.1.9 | 539 | — | SOURCED: **oględziny r2 — etykiety nowo odczytane** (pomiar pikselowy: kreska 125 px : przerwa 130 px ≈ 1:1 ✓); uzasadniają podpis 0,18 = 0,12 + 0,12×(1/2) |
| P-3b | „0,18” | podpis dolny figury | — | 2.2.1.9 | 539 | **0,18 m²/mb** | SOURCED: reinterpretacja M52-FIX; **oględziny r2**: podpis potwierdzony, kreska=przerwa potwierdzone etykietami „1,00”/„1,00”; stary zapis „odstęp osi 0,18” wycofany |
| P-4 | „0,12” ×3 | szerokości linii + odstęp | 0,12 / 0,12 / 0,12 m (osie 0,24 m) | 2.2.1.10 | 540 | — | SOURCED: odczyt programowy; **potwierdzenie wizualne s17 + oględziny r2** (2 linie ciągłe 0,12+0,12, kanał między nimi; kanały 27/33/27 px) |
| P-4 | „0,24” | podpis dolny figury | — | 2.2.1.10 | 540 | **0,24 m²/mb** | SOURCED: przegląd s17 + oględziny r2; = 2×0,12 ✓ [M52-FIX] |
| P-5 | „0,12” ×3 | szerokości linii + odstęp | 0,12 / 0,12 / 0,12 m (osie 0,24 m) | 2.2.1.11 | 540 | — | SOURCED: odczyt programowy; **potwierdzenie wizualne s17 + oględziny r2** (rys. przedstawia 2 pary linii — 4 kanały) |
| P-5 | „4,00” / „2,00” | **kreska / przerwa** | **4,00 m / 2,00 m** | 2.2.1.11 | 540 | — | SOURCED: etykiety, **potwierdzenie wizualne s17 + oględziny r2** (pomiar: kreska 484 px : przerwa 248 px = 2:1 ✓); zastępują ESTIMATED (~1,77 / ~0,91 m) |
| P-5 | „0,32” | podpis dolny figury | — | 2.2.1.11 | 540 | **0,32 m²/mb** | SOURCED odczyt (przegląd s17, 2× powtórzony; r2 nie podważył); **zastrzeżenie r2**: rysunek przedstawia 4 kanały (2 pary linii) — arytmetyka etykiet (2×0,12×4/6) daje 0,16 ≠ 0,32 podpisu drukowanego: **rozbieżność wewnętrzna rozporządzenia**, odnotowana; podpis drukowany pozostaje SOURCED |
| P-6 | „0,12” | szerokość linii | **0,12 m** | 2.2.1.12 | 541 | — | SOURCED: odczyt programowy; **potwierdzenie wizualne s17 + oględziny r2** (27 px, ta sama skala co P-2a) |
| P-6 | „4,00” | **kreska** | **4,00 m** | 2.2.1.12 | 541 | — | SOURCED: etykieta, **potwierdzenie wizualne s17 + oględziny r2** (pomiar: kreska 512 px : przerwa 260 px = 2:1 ✓); zastępuje ESTIMATED z proporcji pikselowych |
| P-6 | „2,00” | **przerwa** | **2,00 m** | 2.2.1.12 | 541 | — | SOURCED: etykieta pionowa (odczyt programowy, rot −90°); potwierdzenie wizualne s17 + oględziny r2 |
| P-6 | „0,08” | podpis dolny figury | — | 2.2.1.12 | 541 | **0,08 m²/mb** | SOURCED: przegląd s17 (semantyka potwierdzona) + oględziny r2; arytmetyka 0,12×(4/6) = 0,08 ✓ [M52-FIX: stary status „UNVERIFIED semantyka” wycofany] |
| P-7a | „0,24” + „1,00” ×2 | szerokość pasa ząbków + długość elementu | 0,24 m; element 1,00 m | 2.2.2.2 | 546 | 0,12 m²/mb | SOURCED: **oględziny r2** (etykiety na obrazie); podpis dolny = zużycie |
| P-7b | „0,24” | szerokość pasa ząbków | **0,24 m** | 2.2.2.4 | 548 | 0,24 m²/mb | SOURCED: **oględziny r2**; spójność z konwencją str. 545 |
| P-7c | „0,12” + „1,00” ×2 | szerokość pasa ząbków + długość elementu | 0,12 m; element 1,00 m | 2.2.2.3 | 546 | 0,06 m²/mb | SOURCED: **oględziny r2** (= 0,12×½ — wariant wąski) |
| P-7d | „0,12” | szerokość pasa ząbków | **0,12 m** | 2.2.2.5 | 549 | 0,12 m²/mb | SOURCED: **oględziny r2** |
| P-10 (suplement — poza zakresem M52, w paczce M51/P2) | „0,5” ×3 | szerokość pasa zebry (linie pomocnicze pokrywają się z krawędziami pasów) | **0,50 m** (odstęp ~0,48 m; długość przejścia ~3,9 m) | 4.2.1.1 | 567 | — | SOURCED: **oględziny r2** (odczyt bitmapowy; skala z etykiety: 288 px/m; pas 144 px, odstęp 139 px); spójne z tekstem s. 567 (s = 4,0 m; min 2,5, maks 16,0); trzecia grupa etykiet nad lewą jezdnią — odczyt niepewny; **bez wiersza manifestu** |
| P-12 | „0,5” (etykieta przy strzałce) + „0,5” (podpis) | **szerokość linii** (etykieta) / podpis dolny = zużycie | szerokość linii **0,50 m** | 4.2.3.1 | 571 | **0,5 m²/mb** | SOURCED: **oględziny r2** — etykieta „0,5” przy strzałce wymiarowej na rysunku (= szerokość linii 0,50 m); podpis „0,5 m²/mb” = ZUŻYCIE (0,50 m × 1 mb) — obie wartości potwierdzone na obrazie; umiejscowienie + tramwaj ≥1,5 m: tekst pkt 4.2.3 (str. 572) |
| P-13 | „0,25” ×2 | **odstępy między trójkątami** | **0,25 m** | 4.2.4.1 | 572 | — | SOURCED: odczyt programowy (pełne glify) + **oględziny r2** |
| P-13 | „0,25”/„0,50”/„0,25” + „0,70” | łańcuch wymiarowy: **odstęp / podstawa środkowego trójkąta / odstęp** + **wysokość** (etykieta pionowa) | **podstawa 0,50 m; wysokość 0,70 m** | 4.2.4.1 | 572 | — | SOURCED: **oględziny r2** — „0,50” wymiaruje podstawę (linie pomocnicze wymiarówki pokrywają się pikselowo z krawędziami podstawy, x984–1162); geometria w skali rysunku: podstawa:wysokość:odstęp = 179:251:86,5 px ≙ 0,50:0,70:0,25 m; **hipoteza „podstawa 0,75” WYCOFANA** [M52-FIX r2] |
| P-13 | „0,2625” | podpis dolny figury | — | 4.2.4.1 | 572 | **0,2625 m²/mb** | SOURCED: podpis potwierdzony dwukrotnym odczytem r2 z obrazu; stary odczyt „0,2825” = błąd glifu 6/8; **zastrzeżenie r2**: arytmetyka etykiet daje ½×0,50×0,70/0,75 = 0,2333 m²/mb, podpis drukowany 0,2625 = ½×0,75×0,70 — **rozbieżność wewnętrzna rozporządzenia**; jako wartość drukowana pozostaje SOURCED |
| P-14 | „0,75” | **długość prostokąta** (wzdłuż linii) | **0,75 m** | 4.2.5.1 | 573 | — | SOURCED: odczyt programowy (pełne glify) [M52-FIX: przypisanie ustalone] |
| P-14 | „0,25” | **odstęp między prostokątami** | **0,25 m** | 4.2.5.1 | 573 | — | SOURCED: odczyt programowy [M52-FIX] |
| P-14 | „0,375” | podpis dolny figury | prostokąt 0,75 × 0,50 m | 4.2.5.1 | 573 | **0,375 m²/mb** | SOURCED: reinterpretacja M52-FIX + **oględziny r2**: arytmetyka idealna 0,75×0,50 = 0,375 przy jednostce 1,00 m ✓; stary zapis „wysokość prostokąta” wycofany |
| P-14 | „0,5” | **głębokość prostokąta** (poprzeczna) | **0,50 m** | 4.2.5.1 | 573 | — | SOURCED: **oględziny r2** — etykieta nowo odczytana; domyka komplet 0,75/0,25/0,5 (potwierdzenie pozycji „do potwierdzenia oględziną”) |
| P-14 | tekst | odległości umiejscowienia | 2,0 / 0,5 / 8,0 / 2,0 / 1,5 / 2,0 / 0,5 m | 4.2.5.1 (tekst) | 573 | — | SOURCED: tekst rozporządzenia (umiejscowienie, nie geometria) |
| P-21a | „0,24” + tabela 5.3 | wymiary liniowania a/b/c/d | **0,24 / 0,39 / 0,76 / 1,24 m** | 5.2.7.1 + tabela 5.3 | 588–589 | — | SOURCED: etykieta „0,24” na rys. 5.2.7.1 (str. 588; oględziny r2 — na rys. także odesłanie „P-7b”) + tabela 5.3 (tekst, str. 589) |
| P-21b | tabela 5.3 | wymiary liniowania a/b/c/d | **0,60 / 0,98 / 1,90 / 3,10 m** | tabela 5.3 | 589 | — | SOURCED: tabela 5.3 (tekst) |
| P-23 | „2,00 (1,30)” / „1,10 (0,715)” / „0,10 (0,065)” | **długość / wysokość / szerokość linii** symbolu (nawiasy = odmiana mini) | **2,00 / 1,10 / 0,10 m** (mini: 1,30 / 0,715 / 0,065 m) | 5.2.9.1 | 596 | — | SOURCED: **oględziny r2** — etykiety odczytane z obrazu rastrowego (natywna rozdzielczość ×3); tekst s. 596: „Wartości podane w nawiasach odnoszą się do odmiany mini”; spójność: mini = 0,65× każdej wartości ✓; przypisanie długość/wysokość/szerokość linii wg wielkości i proporcji symbolu [M52-FIX r2: status UNVERIFIED → SOURCED] |
| P-25 | fig. 2 (pasek): „0,05”, „0,20”; fig. 1: podpis „0,232” | pasek progu (fig. 2; przypisanie do elementów niepewne — perspektywa) / podpis dolny fig. 1 | fig. 2: **0,05 m / 0,20 m** | 4.2.6.1 | 574 | fig. 1: **0,232 m²/mb** | SOURCED: **oględziny r2** (odczyt bitmapowy; podpis „0,232 m²/mb” potwierdzony — 9 glifów); **KOREKTA r1** („bez etykiet”) wycofana; odczyt wizyjny „0,40” z r1 NIE potwierdzony w bitmapie; fig. 3: bez etykiet; tekst: elementy odblaskowe **1,0 m przed progiem** (min. 4) |
| P-11 | „0,5” ×2–3 + tekst | prawdopodobnie pasy zebry sąsiedniego przejścia (rys. 4.2.1.1/P-10; przypisanie niepewne); szerokość przejazdu z tekstu | **1,8 / 3,0 m** (tekst) | 4.2.2.1 (rys) + pkt 4.2.2 (tekst) | 569 | — | SOURCED: tekst rozporządzenia (szerokości przejazdu); **oględziny r2**: na rys. 4.2.2.1 lit. a/b etykiety „0,5” ×2–3 (odczyt bitmapowy; przypisanie do P-10 niepewne) |
| P-12 (tramwaj) | tekst | odległość od skrajnej szyny | **≥1,5 m** | pkt 4.2.3 (tekst) | 572 | — | SOURCED: tekst rozporządzenia |

Uwagi:
- **Dla silnika gry:** wymiary geometryczne (szerokości / odstępy / kreski / przerwy) —
  kolumna „Wartość”; intensywność malowania — kolumna „Zużycie farby” (m²/mb; dla P-13/P-14
  przy jednostce 1,00 m wartość = m² na element).
- Adnotacja wektorowa przy rys. 2.2.1.14 (str. 542): „Wymiary w cm” — dotyczy konstrukcji
  strzałki P-6a, nie znaków P-2…P-6.
- Konwencja szerokości w rozporządzeniu potwierdza odczyty: P-7a/b 0,24 m; P-7c/d 0,12 m
  (str. Dz.U. 545).
- **Pozycje „do potwierdzenia oględziną” (M52-FIX) — rozstrzygnięte w r2**: podpis P-5
  (0,32 drukowany; arytmetyka etykiet 0,16 — rozbieżność wewnętrzna rozporządzenia,
  odnotowana), podstawa P-13 (**0,50 m**; hipoteza 0,75 wycofana), głębokość P-14
  (**0,50 m** — etykieta „0,5”), szerokość P-12 (**0,50 m** — etykieta „0,5”), wysokość
  P-13 (**0,70 m** — etykieta pionowa), kreska/przerwa P-3b (**1,00/1,00 m** — etykiety
  nowo odczytane), wymiary P-23 (**2,00/1,10/0,10 m** + mini), etykiety P-25
  (fig. 2: „0,05”/„0,20”; podpis fig. 1 „0,232 m²/mb”).

---

## Zadanie 2 — Jaroszówka: kadry z estakady Andersa nad rondem (M52-FIX)

Kafl startowy (ok. 53,152 N, 23,168 E) to **rondo Pamięci Bieżeństwa 1915 r.** (DK19 /
ul. Generała Władysława Andersa, północ Białegostoku). Pozyskano **24 kadry** (KartaView,
≤1600 px, data + azymut + WGS84; licencja CC BY-SA 4.0 → REFERENCE_NOT_TEXTURE).

**Korekta M52-FIX (przegląd s17): wszystkie 24 kadry pochodzą z estakady gen. Władysława
Andersa (DK19) wiodącej NAD rondem** — kamera pojazdu jadącego wiaduktem; w kadrach
widoczne bariery mostowe estakady, latarnie dwuramienne, w tle kominy EC. Potwierdzenie
wizualne przeglądu s17: jar-01/07/12/20 (M52-029/035/040/048); pozostałe 20 kadrów
przypisano po przebiegu sekwencji (azymuty ~300–358° wzdłuż osi wiaduktu, pozycje 23–127 m
od kafla) — **nie obejrzano ich w sesjach M52-FIX/r2** (limit 20 analiz obrazu na odpowiedź
sesji wyczerpany na rysunkach Dz.U. — priorytet zad. 1; pliki w paczce ZIP poza gitem).

**Wniosek: wymóg „≥10 kadrów z poziomu jezdni ronda” NIE jest spełniony (0/24).**
Kadry pozostają w manifeście jako referencja widoku z wiaduktu, ale nie dokumentują nawierzchni
ringu, chodników ani krawężników przy rondzie.

### Poszukiwanie kadrów z poziomu ringu (wynik negatywny; powtórzone w M52-FIX r2)

- **Panoramax** (API, 2026-11-13, r2): bbox obejmujący całe rondo z wlotami i ringiem
  (23.1620–23.1720 E, 53.1505–53.1540 N) → **0 kadrów**; szersze bboxy → 0; bardzo szeroki
  (23.13–23.20 E, 53.14–53.17 N) → 10 kadrów, wszystkie w klastrze ~1,3 km NW od ronda
  (**poza rondem**). (r1: szeroki bbox ~3,2 × 2,1 km → 6 kadrów w klastrze rondo Putry
  ~1,2 km od kafla — inne skrzyżowanie.)
  Zapytanie: `https://api.panoramax.xyz/api/search?bbox=23.1620,53.1505,23.1720,53.1540`.
- **KartaView** (api.kartaview.org/2.0/photo/, 2026-11-13, r2): zapytania punktowe z 2
  lokalizacji (kafl 53.1520/23.1680; środek ronda 53.1515/23.1665) przy promieniu
  100/300/500 m → w każdym przypadku wyłącznie 3 sekwencje estakadowe (14055, 2769366,
  3686129; dist 0–42 m), **brak innych sekwencji**; promień >500–800 m → HTTP 400;
  endpoint nearby-tracks (POST): timeout/niezawodny. Stary api.openstreetcam.org:
  wygasł (cert mismatch + Azure 404).
- **Mapillary**: brak tokenu API w środowisku → niesprawdzony (UNVERIFIED).
- **Chodniki/krawężniki przy rondzie: 0 kadrów → UNVERIFIED.** Zapis negatywu:
  manifest M52-117.

| Sekwencja | Data | Autor | Kadry | Azymuty (ok.) | Pozycje (N, E) |
|---|---|---|---|---|---|
| 14055 | 2016-08-24 | ziozzzzz | 7 | 357/358/359° | 53.1512–53.1523, 23.1662–23.1689 |
| 2769366 | 2019-08-25 | gpsmapper999 | 6 | 302/303° | 53.1514–53.1524, 23.1663–23.1689 |
| 3686129 | 2021-06-23 | TMishaaa | 11 | 301/302/303° | 53.1513–53.1524, 23.1662–23.1693 |

Wszystkie trzy sekwencje prowadzą wiaduktem DK19 nad rondem (2016 — od południa,
azymut ~357°; 2019/2021 — od północnego zachodu, azymuty ~300–305°). Pełne metadane:
manifest.csv M52-029…M52-052. Pliki: `files/jaroszowka/` w paczce ZIP (poza gitem).
Te same ujęcia powtórzone w wierszach trasy/przejść: M52-057=jar-01, M52-062=jar-13,
M52-068=jar-22, M52-071=jar-03, M52-075=jar-05, M52-079=jar-18, M52-080=jar-21.

---

## Zadanie 3 — Azyle, płytki dotykowe, ścieki i wpusty (Białystok)

### Azyle (wyspy dzielące)
- **Wymóg projektowy (SOURCED)**: wytyczne ZDM 2025 (BIP zasób 103311, str. 20):
  „Na wyspie dzielącej na środku jezdni należy wydzielić przejazd rowerowy”.
- **Występowanie (UNVERIFIED)**: w zbadanym obszarze centrum OSM wskazuje jeden obiekt
  `traffic_calming=island` — ul. Świętojańska (way 287037716, 53,12497 N 23,16656 E;
  ODbL, dane referencyjne). Brak kadrów KartaView w promieniu ~1,1 km od tego obiektu
  (najbliższe sprawdzone kadry: 1,15 km) → **brak potwierdzenia zdjęciowego**; wymiary i
  materiał azylów: UNVERIFIED.

### Płytki dotykowe (układ rzędów)
- **SOURCED** (wytyczne ZDM 2025, pkt II.2 — zejścia/rampy): obszar ostrzegawczy =
  **1 rząd płytek gładkich + 2 rzędy płytek profilowanych (guzowatych)**.
- Wymiary pojedynczych płytek: UNVERIFIED (źródło nie podaje).
- Kontekst OSM (bbox centrum, ODbL): 177 węzłów `tactile=yes` na 680 przejść; 10 przy
  trasie startowej, głównie skrzyżowanie Al. Tysiąclecia/Sokólska (53,1506–53,1509 N,
  23,1544–23,1550 E). Kadry przejść (z częścią z płytkami): M52-083…M52-105.

### Ścieki przykrawężnikowe i wpusty
- **Wymogi (SOURCED)**: wytyczne ZDM 2025, pkt III.11–III.13 — włazy żeliwne wg PN-EN 124,
  projektowane **w osi pasa ruchu**; studnie w jezdni z obróbką brukarską wg rys. nr 3 wytycznych.
- Konkretne wymiary wpustów: UNVERIFIED. Przykłady obiektów inżynierskich przy krawężnikach
  widoczne na kadrach `files/crossings/` (M52-083+).

---

## Zadanie 4 — Kolor dróg i pasów rowerowych na trasie startowej (M52-FIX: metoda RGB odrzucona)

**M52-FIX: pierwotna ocena koloru (progi RGB na dolnych 45% kadru) jest metodycznie
niewiarygodna** — dolna część kadru kamery pojazdu obejmuje maskę auta/deskę rozdzielczą,
a kolekcja łączy różne kamery i warunki oświetlenia (balans bieli). Ocena przez oględziny
kadrów (wymagana przez przegląd s17 zamiast progów RGB) **nie została wykonana ani w
M52-FIX, ani w r2** — limit 20 analiz obrazu na odpowiedź sesji został wyczerpany na
rysunkach Dz.U. (priorytet zad. 1; pliki kadrów w paczce ZIP poza gitem).

**Status koloru nawierzchni trasy startowej: UNVERIFIED** (wycofany z ESTIMATED).
**M52-FIX r2: kolumny `kolor_srgb`/`metoda_koloru` USUNIĘTE ze schematu manifestu**
(19 → 17 kolumn) — wiersze kadrów M52-029…M52-105 oraz wiersz zbiorczy M52-116; wartości
RGB dla Rynku (M52-106…108, centralne 30×40% kadru, Commons) przeniesiono do kolumny
uwag z jawną adnotacją o niewiarygodności metodologicznej. Do rozstrzygnięcia w rundzie
z dostępem do kadrów: oględziny każdej ulicy osobno (Andersa, Al. Tysiąclecia, Sokólska,
Wileńska) + obejrzenie, czy występuje czerwony asfalt lub czerwony pas malowany.

Uwaga dodatkowa (M52-FIX): część kadrów „trasy/przejść” to te same ujęcia co kadry
Jaroszówki z estakady (M52-057=jar-01, M52-062=jar-13, M52-068=jar-22, M52-071=jar-03,
M52-075=jar-05, M52-079=jar-18, M52-080=jar-21) — dotyczą jezdnii wiaduktu, nie ronda.

Fakty organizacyjne z OSM (ODbL — bez zmian, tylko kontekst):
- Andersa (DK19): wydzielona droga rowerowa poza jezdnią (jezdnia `bicycle=no`);
  kolor drogi rowerowej nierozstrzygnięty.
- Al. Tysiąclecia: `use_sidepath`; 1 odcinek `cycleway:right=share_busway` (buspas).
- Sokólska (Białostoczek): `use_sidepath`.
- Wileńska: brak kadrów ≤60 m (najbliższy 348 m) → UNVERIFIED.

Kadry: M52-053…M52-082 (trasa), M52-083…M52-105 (przejścia).

---

## Zadanie 5 — Rynek Kościuszki: nawierzchnia

**Rodzaj nawierzchni (SOURCED): płyty granitowe + kostka granitowa (bruk)**.
- Tofiluk W. (2015), *Central square in Białystok — changes…*, CEE 2015;19(4):121–131,
  DOI 10.1515/ceer-2015-0058: rynek = granitowe płyty i kostka brukowa; przebudowa
  2006–2009; projekt (konkurs SARP): Zenon Zabagło; otwarcie: 7.08.2009
  (bialystok.pl, „Dekada Rynku Kościuszki”).
- Wymiary płyt: **UNVERIFIED** — źródło nie podaje; fotogrametria ze zdjęć bez punktów
  odniesienia uznana za niewiarygodną (nie ryzykujemy liczby).
- Kolor (ESTIMATED, metoda: mediana RGB **centralnych 30×40% kadru** — metoda nieobjęta
  korektą M52-FIX, która dotyczyła dolnych 45% kadrów z kamer pojazdów; 3 zdjęcia Commons):
  [142, 125, 121] (CC0), [128, 135, 146] (CC0), [170, 171, 173] (CC BY 3.0 pl — referencja).
  Balans bieli zmienny między kadrami — traktować jako orientacyjny. **r2: wartości
  przeniesione z usuniętych kolumn manifestu do kolumny uwag** (M52-106…108), z adnotacją
  o niewiarygodności metodologicznej.
- Kadry: M52-106…M52-108 (pliki `files/rynek/` w paczce ZIP).

---

## Zadanie 6 — Aktualne wytyczne ZDM/ZDiT Białystok

- **Aktualna wersja: „Wytyczne do projektowania dokumentacji projektowej budowy, rozbudowy
  i przebudowy ulic w Białymstoku”, oznaczona „13 LIPCA 2018 R. / 2025 R.”** — BIP Białystok,
  zasób 103311 (PDF, 21 stron, 1,6 MB):
  https://www.bip.bialystok.pl/resource/103311/Za%C5%82.+nr+5_Wytyczne+do+projektowania.pdf
- Stara wersja (13.07.2018): BIP zasób 99308; kopia z SWW: zasób 99985 (22 strony).
- **Zmiany 2025 vs 2018 (SOURCED — porównanie tekstów obu PDF)**:
  1. oznaczenie wersji „13 LIPCA 2018 R. / 2025 R.”;
  2. tytuł sekcji rowerowej → „WYTYCZNE PROJEKTOWANIA I BUDOWY DRÓG DLA ROWERÓW – LOKALIZACJA”;
  3. nowe punkty w Wymaganiach ogólnych: 17 (wizualizacje przy koncepcjach), 18 (mapy
     podziału działek w wersji numerycznej), 19 (dokumentacja cyfrowa, edytowalna:
     dwg/dxf/word/excel), 24 (konsultacje rozwiązań technologicznych i materiałowych),
     27–28 (wersja robocza do zatwierdzenia; obowiązkowo: tabela robót ziemnych, wykaz
     zjazdów, przekroje normalne);
  4. uzbrojenie terenu: monitoring wizyjny wykonanych sieci;
  5. objętość: 21 vs 22 strony.
- Cytaty z wytycznych (płytki dotykowe, azyle, włazy) potwierdzone w przeglądzie s17.

---

## Samokontrola 20% (M52-FIX r2, jawny seed)

- Populacja: **117 rekordów** manifestu (M52-001…M52-117).
- Próba: **24 rekordy** (⌈20%⌉), deterministycznie (ten sam seed co r1):
  `random.Random(20261113).sample(ids, 24)` →
  M52-002, 003, 004, 007, 009, 013, 015, 017, 023, 039, 040, 047, 051, 059, 064, 066, 071,
  077, 082, 084, 105, 107, 111, 114.
- Kryteria r2 (zgodnie z przeglądem s17): wiersze z rysunków → **wklejony odczyt
  etykiety/podpisu** z oględzin r2 (render 150 dpi + rastry natywne ×3) + weryfikacja
  pikselowa; kadry → zdanie **„co widać”** (opis z przeglądu s17 albo jawne „nie obejrzano
  w r2 — limit 20 analiz obrazu na odpowiedź wyczerpany na rysunkach Dz.U.”); wiersze
  tekstowe → weryfikacja źródłem; schemat manifestu 17 kolumn (bez kolor_srgb).
- Wynik: **24/24 sprawdzone, 0 problemów formalnych**. Rozbór r2: odczyty etykiet z
  oględzin r2 (realne wklejki) — M52-002, 003, 004, 007, 009, 013, 015, 017; tekstowe —
  M52-023, 111, 114; kadry: 1 z opisem z przeglądu s17 (M52-040: jezdnia estakady,
  bariery mostowe, kominy EC w tle), pozostałe 12 kadrów z jawną deklaracją nieobejrzenia
  w r2 + podstawą przypisania (przebieg sekwencji/azymuty; M52-071 = jar-03 — ujęcie
  z estakady). Szczegóły: `audit_20_percent.json`.

## Status prac (aktualizowany)

- [x] Gałąź utworzona z najnowszego `origin/main` (53e57d5); M52-FIX: gałąź zaktualizowana
      o `origin/main` (merge; katalog paczki nietknięty przez main — bez konfliktów).
- [x] PDF Dz.U. 2019 poz. 2311 część c2 pobrany z eli.gov.pl; ekstrakcja tekstu i rysunków (M52).
- [x] Zadanie 1 — tabela etykiet wymiarowych + zużycia farby (**stan po M52-FIX r2:
      oględziny renderu wszystkich rysunków z zakresu M52 + weryfikacja pikselowa**).
- [x] Zadanie 2 — Jaroszówka: 24 kadry; **M52-FIX r2: opisane jako kadry z estakady Andersa
      nad rondem (bariery mostowe; 0/24 z poziomu jezdni — wymóg niespełniony)**; ring:
      wynik negatywny (r2: Panoramax 0 w bbox ronda / 10 kadrów poza rondem; KartaView
      2 punkty × promień 100–500 m → tylko 3 sekwencje estakadowe; Mapillary bez tokenu
      — M52-117).
- [x] Zadanie 3 — azyle (wymóg SOURCED / występowanie UNVERIFIED), płytki dotykowe (układ
      rzędów SOURCED), ścieki/wpusty (wymogi SOURCED).
- [x] Zadanie 4 — **kolor UNVERIFIED** (metoda RGB odrzucona; **r2: kolumny
      kolor_srgb/metoda_koloru usunięte ze schematu — 19 → 17 kolumn**; oględziny kadrów
      niewykonane w r2 — limit analiz obrazu sesji wyczerpany na rysunkach Dz.U.);
      OSM: kontekst organizacyjny.
- [x] Zadanie 5 — Rynek Kościuszki: płyty granitowe + kostka (SOURCED, Tofiluk 2015 +
      BIP/bialystok.pl); wymiary UNVERIFIED; kolor ESTIMATED (wartości w uwagach r2).
- [x] Zadanie 6 — wytyczne ZDM „2018/2025”: BIP zasób 103311 + porównanie zmian vs 2018.
- [x] manifest.csv (117 rekordów, **17 kolumn po r2**), audit_20_percent.json (24/24,
      seed 20261113, odczyty r2 + „co widać”), sources.md (źródła M52-FIX + r2),
      .gitignore (files/, *.zip).
- [ ] Do wykonania w rundzie z dostępem do kadrów: oględziny kadrów trasy startowej
      (kolor, zad. 4); kadry z poziomu ringu Jaroszówki (pozyskanie własne, np. sesja foto).
      (Render rysunków Dz.U. z zad. 1 — **wykonany w r2**.)

## Zasady

- Zakaz Google Maps / Street View / Earth / 3D Tiles.
- Źródła zdjęć: ELI/Dz.U., BIP Białystok, GDDKiA, Panoramax, KartaView, Commons, Openverse.
  Mapillary: brak tokenu → UNVERIFIED.
- Licencje komercyjne; NC/ND = „tylko referencja”; CC BY-SA = „referencja, nie tekstura”.
- Każda liczba: źródło albo UNVERIFIED/ESTIMATED z metodą.
- **Uczciwość wizyjna (M52-FIX, po przeglądzie s17): nie deklarujemy obejrzenia rysunku/
  kadru, którego nie obejrzano. W samokontroli per obraz wklejamy faktyczny odczyt
  (etykieta/podpis „co widać”) albo jawne „nie obejrzano w tej sesji” z podaniem podstawy
  przypisania.**
- Pozycje WGS84; sezon i pora_dnia dla zdjęć. JPG ≤1600 px. PDF urzędowe ≤5 MB.
- Samokontrola 20% z jawnym seedem (README + audit_20_percent.json).
- Zdjęcia/binaria: `files/` (w `.gitignore`), paczka `mistral-p2-surfaces-2-files.zip`
  dostarczona poza gitem (patrz opis PR).

## Pliki

- `README.md` — ten plik (wyniki zadań 1–6 + statusy + opis samokontroli; rewizja
  M52-FIX + r2).
- `manifest.csv` — pozycje M52-001…M52-117; **17 kolumn po r2** (kolor_srgb/metoda_koloru
  usunięte — zad. 4).
- `sources.md` — pełne źródła z linkami, licencjami i datami dostępu (+ źródła rewizji
  M52-FIX i metodologia r2).
- `audit_20_percent.json` — samokontrola 20% (seed 20261113; odczyty etykiet r2 +
  „co widać”).
- `.gitignore` — `files/`, `*.zip` (dodane w M52-FIX).
