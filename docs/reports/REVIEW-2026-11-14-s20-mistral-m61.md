# Przegląd M61 (P18 brud tyłu naczepy) — s20, 2026-11-14

**Werdykt: FIX.** Część literaturowa jest uczciwa: cytaty istnieją, a brak liczb „pokrycie a wysokość” i brak CIELAB/albedo osadu oznaczono jako lukę. Jednak głównego produktu, czyli kadrów, nie da się w obecnej postaci użyć do kalibracji.
- **7 z 24 obejrzanych kadrów „zakwalifikowanych” nie pokazuje dwuskrzydłowych drzwi tylnych**, choć manifest wpisuje w nich szablonowo „drzwi dwuskrzydłowe POTWIERDZONE (pionowa szczelina, rygle, zawiasy)”:
  - P18-138 to pusta rama kontenerowa bez skrzyni;
  - P18-160 to ściana PRZEDNIA naczepy (podpory, złącza, skrzynki gaśnic);
  - P18-167 to solówka z windą załadowczą;
  - P18-171 i P18-172 to malowane burty ciężarówek z Indii;
  - P18-150 ma drzwi rolowane;
  - P18-111 to solówka z zamkniętą windą załadowczą (wycinek 1920 px), nie drzwi.
- **4 kadry są czyste** (P18-107, 162, 166) albo prawie czyste (P18-155), a opisano je jako brudne. W statystyce „próg brudny 31/31” jest P18-166, który sam audyt uznał za czysty.
- **Barwa P18-121** to szary film, a nie „brązowy”.
- **P18-138**: wpisano „śnieg, zima wg wizji”, a to słoneczna Kalifornia w sierpniu.
- **Opisy i audyt robiło „narzędzie wizyjne”** z pytaniem sugerującym odpowiedź („dwuskrzydłowe drzwi? pionowa szczelina?”). Audyt potwierdził 7/7, w tym kadry wadliwe.
- **Kadrów z Polski są 2** (107 czysty, 108), a zimowy kadr drzwi zabrudzonych w ruchu drogowym jest jeden (P18-121, Wielka Brytania).
- **ZIP-a nie dostarczono**: w `C:\Users\matma\Downloads` nie ma `mistral-p18*.zip`, więc katalog `research/_incoming/mistral-p18-trailer-soiling-files` nie powstał.

Blok poprawek: §8 (do wklejenia autorowi). Nic nie scalono, nic nie scommitowano, PR #58 bez komentarza. Raport nie jest scommitowany.

## 1. Zakres i metoda

- **Gałąź i diff.** Gałąź `origin/research/mistral-p18-trailer-soiling` @ `8ee634b7d` (9 commitów). `git diff --stat origin/main...` pokazuje 5 plików wyłącznie w `research/mistral/p18-trailer-soiling/` (+524 linie): README, manifest (96 wierszy: literatura 21, kadry 75, w tym 44 odrzucone), sources, audit, `.gitignore`. Pliki wyjęto `git archive` do scratcha.
- **ZIP.** Nie ma go w `Downloads` (są tylko `mistral-p17-dusk-lighting-files.zip` i starsze). Sha256 z PR (`8b34688e…6514`, 11 626 682 B) **nie sprawdzony**.
- **Obrazy.** Pobrałem je sam z Commons API (miniatury 960 px; licencja, autor, EXIF DateTimeOriginal, opis) dla 26 z 31 kadrów „zakwalifikowanych”. Miniatur 136, 142, 156, 164 i 169 nie pobrano (błąd pobierania, przyczyny nie zapisałem); ich metadane i licencje z API mam (31/31).
  - **Obejrzane (24):** 104, 105, 107, 108, 109, 111, 118, 121, 137, 138, 139, 140, 143, 149, 150, 155, 158, 160, 162, 166, 167, 171, 172, 174.
  - **Wycinki 1920 px (powiększenie 2–3×):** drzwi i próg 105, 111, 121, 143, 158.
- **Literatura.** Ponownie sprawdziłem 5 cytatów: SAE 2014-01-0610 (saemobilus), SAE 2016-01-1604 (abstrakt przez Crossref), IJERPH 2020 (abstrakt przez Crossref), The Cryosphere 2025 (strona artykułu) oraz raport FHWA-RD-79-84 (rosap.ntl.bts.gov). Wyniki w §4. Infra-Intelligence i P18-014 nie sprawdzałem.
- **Gra.** `TrailerAssetBuilder.cs` na `origin/main` (ADR 0182 r5 scalony): `_RearGrimeColor` lin. (0,17; 0,13; 0,08) ≈ sRGB (115, 100, 79), krycie 0,7 / 0,9, części nielakierowane ×0,8, klosze ×0,35, zacieki rzadkie (8 % w polu, do ~50 % przy zawiasach i uszczelce).

## 2. Kryteria akceptacji M61 (MISTRAL-TASKS-9 § M61)

| Kryterium | Wynik |
|---|---|
| 1. Mechanizm z literatury: strefy → intensywność względna → źródło → status; brud a wysokość; prędkość i mokra jezdnia | **CZĘŚCIOWO.** Tabela stref jest, a źródła istnieją (SUV, bryła Windsor, praca Gaylarda). Brak liczb „pokrycie a wysokość” uczciwie zapisano jako lukę. **Błąd interpretacji:** abstrakt SAE 2016-01-1604 mówi tylko, że duże krople mają tor balistyczny i „penetrate the wake”, a małe rzadziej są w nim porywane. Nie mówi, gdzie się osadzają. „Trafiają próg i belkę” (README §1.1, P18-002) to ekstrapolacja autora i tak trzeba ją oznaczyć. Wniosek „próg najbrudniejszy” potwierdzają kadry, nie to zdanie |
| 2. Barwa i faktura PL, lato i zima, liczby tylko ze źródła | **CZĘŚCIOWO.** Opis słowny jest rozsądny. Uzasadnienie barwy pochodzi jednak z mineralogii pyłu z **Viana do Castelo (Portugalia)** i z albedo **śniegu w Norwegii** (Finse). To kontekst, a nie dane o osadzie na pojeździe. Liczby o soli pochodzą z portalu branżowego i oznaczono je jako orientacyjne ✓. Brak CIELAB/albedo osadu jest wpisany jako luka ✓ |
| 3. ≥ 20 kadrów tylnych drzwi naczep/skrzyń, lato i zima, każdy OBEJRZANY, z opisem stref, kształtu, liczby zacieków, wymytych pasów, uchwytów, koloru i krycia | **NIE.** Z 24 obejrzanych 7 nie pokazuje dwuskrzydłowych drzwi tylnych, 4 są czyste lub prawie czyste, a kilka opisów jest sprzecznych z obrazem (§3). Po moim przeglądzie zostaje **~11 użytecznych kadrów**, z tego 1 z Polski (108; 107 jest czysty). Zimowych z ruchu drogowego z drzwiami: 1 (121). Opisy są szablonowe („smugi i plamy”, „drzwi POTWIERDZONE…”) i nie zostały napisane z obrazu przez autora |
| 4. Zestawienie liczbowe z kadrów (mediana zacieków, odsetki próg/belka/lampy, górna granica filmu w m z metodą) | **NIE (niewiarygodne).** Mianownik 31 zawiera kadry bez drzwi i kadry czyste. „Próg brudny 31/31” jest sprzeczny z korektą P18-166. „Długość jako % wysokości drzwi” podało narzędzie wizyjne, a nie pomiar autora |
| Marki: „marka widoczna, tylko referencja” | **TAK** |
| Daty i sezon zgodne z plikiem | **CZĘŚCIOWO.** Data P18-166 to w EXIF 2015-06-18, a w manifeście 2016-09-16. P18-172: EXIF 2022-05-15, Hajdarabad; w manifeście 2022-02-02, „Radżastan”. P18-138: „zima wg wizji”, a to sierpień w Kalifornii bez śniegu |
| Samokontrola ≥ 20 % z jawnym seedem | **FORMALNIE TAK, MERYTORYCZNIE NIE.** Próbę wybrano deterministycznie (co piąty), a nie z seeda. „Ponowne oględziny” zrobiło to samo narzędzie, z pytaniem sugerującym odpowiedź, więc potwierdziło 104, 111 i 174, choć 104 jest nieczytelny (ciemna grafika pod światło) |
| Licencje (tylko komercyjne; BY-SA = referencja, nie tekstura) | **TAK.** 31/31 sprawdzonych na Commons API zgodnych z manifestem. Google nie użyto |
| Zmiany tylko w `research/mistral/p18-trailer-soiling/` | **TAK** |
| ZIP + nazwa, rozmiar, sha256 | **W PR TAK, u lidera NIE** — pliku nie ma w `Downloads` |

## 3. Kadry: opis Mistrala a obraz (oglądane przeze mnie)

| Kadr | M61 (skrót) | Co widać (recenzent) | Ocena |
|---|---|---|---|
| 104 | naczepa, próg, belka i dół brudne, osad szaro-czarniawy | Eksponat (MB 1850, w tle sprzęt wojskowy i flagi muzeum) fotografowany pod światło. Tył to ciemnogranatowa grafika z pantera i kołem. Brudu na drzwiach **nie da się ocenić**. Śnieg na ziemi | ✗ (nieoceniany) |
| 105 | 3 zacieki/skrzydło od zawiasów, ~30 % wysokości, osad szary | Ten sam eksponat z 3/4. Wycinek 1920 px: drzwi w ciemnej grafice, zacieków brak. Na polerowanym zderzaku i dolnej ramie drobne jasne plamki (zaschnięte krople). Pojazd wystawowy, nie po trasie | ✗ (zacieki zmyślone) |
| 107 | rozbryzg na progu, belce, dole drzwi; słabe | Nowa naczepa na placu, drzwi, próg i belka **czyste** | ✗ → wzorzec czysty |
| 108 | 3 zacieki/skrzydło, szaro-czarny, średnie | Przewóz drobiu (PL). Drzwi ciemno malowane. Rdzawe zacieki spod rygli i zawiasów, jasne pionowe ślady na prawym skrzydle, mocno brudny zderzak i dolna rama | ~✓ (zacieki to rdza i zużycie) |
| 109 | średnie, rozbryzg, szary | Drzwi jasne, prawie czyste. Lekka szarość tylko przy dolnej listwie i lampach | krycie zawyżone (słabe) |
| **111** | tył naczepy, 3 zacieki od progu ~20 % | Wycinek 1920 px (3×): **solówka z zamkniętą windą załadowczą** (panel platformy + roleta nad nim), nie dwuskrzydłowe drzwi. Jasnoszary film na platformie, szara dolna rama. Mokra B2, śnieg ✓ | ✗✗ (typ, liczby) |
| 118 | **otwarte** drzwi chłodni | Drzwi **zamknięte**; otwarte są panele aerodynamiczne TrailerTail. Szary brud na dolnej ramie i progu. Zima (gołe drzewa) ✓ | opis drzwi ✗, brud ✓ |
| 121 | **brązowy**, poziome smugi, słabe | Wycinek: **szary**, rozproszony film na całej wysokości obu skrzydeł. Pionowe szare zacieki przy prawej krawędzi prawego skrzydła (od narożnika górnego). Szara dolna rama i zderzak. Styczeń, mokra jezdnia | barwa ✗, kształt ✗ |
| 137 | zacieki 2–3/skrzydło, 50–70 % | Ciemnoszara, brudna dolna rama i belka z lampami. Na dole drzwi jasne, białawe plamy (wytarte lub wymyte, przy recyklingu). Wyraźnych długich zacieków brak | częściowo |
| **138** | „naczepa kontenerowa z drzwiami dwuskrzydłowymi… śnieg” | **Pusta rama kontenerowa** (podwozie bez kontenera) widziana z tyłu, za nią kabina ciągnika. **Drzwi brak, śniegu brak** (Kalifornia, sierpień) | ✗✗ |
| 139 | liczne zacieki 70–80 %, ciemnobrązowy | Stara naczepa kolejowa (ICR): rdzawe zacieki spod zawiasów, wgniecenia, mocno zardzewiała dolna rama. To **korozja i wiek**, nie spray drogowy | opis ✓, interpretacja ✗ |
| 140 | rozbryzg na dole drzwi i progu, słabe | Drzwi z blachy aluminiowej ryflowanej w romby (odbijają). Szara dolna rama, na drzwiach brudu prawie nie widać | ~✓ |
| 143 | rozległy rozbryzg, szaro-czarny, średnie | Wycinek: pomarańczowe drzwi z lekką szarą mgłą w dolnych ~10–15 %. Szara rama i belka. Krycie słabe–średnie | ✓ |
| 149 | zacieki 50–70 %, rdzawo-brązowy | Stara naczepa na budowie: rdza ramy, wgniecenia, graffiti. Pionowych zacieków brudu prawie brak | częściowo |
| **150** | **drzwi dwuskrzydłowe** | **Drzwi rolowane** (jedna roleta). Szara, brudna dolna rama i rygiel | ✗ (typ drzwi) |
| 155 | słabe, szary | Prawie czysta nowa naczepa, minimalnie szara rama | ✓ (słabe/≈czysty) |
| 158 | smugi i plamy, 2 zacieki | Wycinek: **pył na całej wysokości drzwi**. W pyle napisano palcem „Sigueme vamo moler” na górnej połowie prawego skrzydła. Ciemne plamy po wycieraniu dłonią przy ryglach. Szara rama. Najlepszy dowód filmu na całej powierzchni i wycierek | opis niepełny (pominięto film na górze i wycierki) |
| **160** | „drzwi dwuskrzydłowe POTWIERDZONE” | **Ściana przednia** naczepy: kanistry, skrzynki gaśnic, przewody i złącza, podpory naczepy na jezdni. Drzwi brak | ✗✗ |
| 162 | słabe, próg i dół drzwi | Ciężarówka przeprowadzkowa (solówka), tył **czysty** | ✗ → czysty |
| 166 | (po audycie) czysty | Nowa naczepa na placu producenta, czysta ✓, ale liczona w „31/31 brudny próg” | statystyka ✗ |
| **167** | „naczepa skrzyniowa, drzwi POTWIERDZONE” | Solówka z **windą załadowczą** z 3/4 tyłu, drzwi brak | ✗✗ |
| **171** | „drzwi POTWIERDZONE” | Zbliżenie malowanej klapy i zderzaka ciężarówki z Indii, drzwi brak | ✗✗ |
| **172** | „drzwi POTWIERDZONE”, Radżastan | Malowana klapa i burta ciężarówki w **Hajdarabadzie** (opis pliku), drzwi brak | ✗✗ |
| 174 | zacieki 2–3, 50–70 % | Mała skrzynia (Tajwan), drzwi dwuskrzydłowe ✓. Krótkie rdzawe zacieki spod zawiasów i uchwytów rygli (do ~20–40 %), szara dolna rama | ~✓ (długość zawyżona) |

**Wynik.** Obejrzano 24 kadry.
- Bez dwuskrzydłowych drzwi tylnych: 7 (138, 160, 167, 171, 172, 111 — winda załadowcza, 150 — drzwi rolowane).
- Czyste lub prawie czyste, opisane jako brudne: 4 (107, 162, 166, 155 — w 155 „słabe” jest dopuszczalne).
- Nieoceniane lub z liczbami niewykonalnymi: 104, 105.
- Z istotnie błędnym opisem: 118 (drzwi), 121 (barwa, kształt), 139 i 149 (rdza czytana jako brud drogowy).
- Zgodne lub prawie zgodne: 108, 109 (krycie zawyżone), 137, 140, 143, 158 (niepełny), 174.

Szablonowe zdanie „drzwi dwuskrzydłowe POTWIERDZONE (pionowa szczelina, rygle, zawiasy)” występuje w kadrach, w których drzwi nie ma. Opisów nie napisano więc z obrazu.

## 4. Literatura — wyrywkowa weryfikacja (5 cytatów; P18-014 i Infra-Intelligence niesprawdzone)

| Wiersz | Cytat M61 | Sprawdzenie (2026-11-14) | Ocena |
|---|---|---|---|
| P18-001 | „The rear tyres are seen to be the dominant source…” | saemobilus.sae.org: Gaylard i in. 2014, SAE 2014-01-0610, **SUV** ✓ | ✓ (SUV, nie naczepa — README to zaznacza) |
| P18-002/003 | „Large particles… ballistic trajectory and penetrate the wake”; „small particles… less likely to become entrained” | Crossref, abstrakt Kabanovs i in. 2016, SAE 2016-01-1604, bryła Windsor: oba zdania dosłownie ✓ | cytaty ✓; abstrakt nie mówi, gdzie duże krople się osadzają — **„trafiają próg i belkę” to ekstrapolacja**, do oznaczenia jako ESTIMATED |
| P18-012 | „primarily composed of quartz, but also of muscovite…” | Crossref, abstrakt IJERPH 17(5) 1563 (2020) ✓. Próbki z **Viana do Castelo, Portugalia** | cytat ✓, „podstawa barwy PL” — nadinterpretacja |
| P18-018 | „reached up to 0.13, 0.21, and 0.25…” | tc.copernicus.org ✓. Chodzi o **śnieg wokół Finse (Norwegia)**, lato 2023 | cytat ✓, dotyczy śniegu, nie osadu na blasze — tylko kontekst |
| P18-005 | „truck splash and spray generation and propagation”, testy symulatorowe, tunelowe i pełnej skali | rosap.ntl.bts.gov: Weir, Strange, Heffley 1978, FHWA-RD-79-84 ✓ | cytat ✓; „intensywność rośnie z prędkością i grubością filmu wody” nie występuje w abstrakcie — to wniosek autora |

## 5. Licencje, pliki, zakres

- **Licencje.** 31/31 kadrów sprawdzonych przez Commons API zgodnych z manifestem. CC0 104/105 (Spielvogel), PD 167, CC BY 142/143, reszta BY-SA = referencja ✓. Google nie ma.
- **Duplikaty.** P18-139 i P18-153 to ten sam pojazd, z tą samą sekundą EXIF (oznaczone jako para ✓). Każdy liczony osobno w statystyce, co dubluje ten sam pojazd.
- **Rozdzielczość.** Wg PR miniatury mają 640–1280 px ✓ (≤ 1600).
- **Zmiany wyłącznie w katalogu zadania** ✓. **ZIP-a lider nie ma.**

## 6. Porównanie z grą (ADR 0182 r5, `TrailerAssetBuilder.cs`) i REVIEW s19-0182

Z M61 do gry przenoszę tylko to, co potwierdziłem na obrazach sam. Liczby M61 z §4 README są niewiarygodne (mianownik z błędnymi kadrami).

| Element (0182 / recenzja s19) | Gra dziś (r5) | Kadry (własna ocena, ESTIMATED) | Działanie |
|---|---|---|---|
| P1-1 barwa osadu | `_RearGrimeColor` lin. (0,17; 0,13; 0,08) ≈ sRGB (115, 100, 79), ciepły szarobrązowy | Jedyny dobrze widoczny kadr białych drzwi z brudem drogowym (121, wycinek) ma osad **szary, prawie neutralny**. Na 143 (drzwi pomarańczowe) i 158 (czerwone) barwy osadu nie da się oddzielić od lakieru. Brąz i rdza tylko na starych naczepach (139, 149, 108 — rdza spod okuć). W renderze `doors-r5-ovc.jpg` (panele 2 i 4) osad przy dole drzwi i tak czyta się jako ciemnoszary | **sygnał, n = 1** — bez zmiany teraz. Nie robić osadu bardziej brązowego; decyzję o odbarwieniu podjąć po M61-FIX (≥ 6 kadrów białych drzwi zimą). Rdzawy odcień tylko jako rzadki akcent spod zawiasów i rygli (P2) |
| P1-2 próg, belka, lampy | nielakierowane ×0,8, klosze ×0,35 | Dolna rama pod drzwiami (aluminiowa belka z lampami) i belka RUPD to w **każdym** brudnym kadrze najciemniejsza strefa (137, 140, 143, 150, 158, 121). Klosze lamp czerwone i czytelne, lekko zmatowione | **potwierdza r5.** Dla ramy i belki rozważyć ×0,9–1,0 zamiast ×0,8; klosze ×0,35 zostają |
| Rozkład z wysokością (film dolny) | film najgęstszy przy progu, falujący górny brzeg; w `doors-r5-ovc.jpg` górna część drzwi ma lekko szary ton i rzadkie zacieki — czy to film, czy oświetlenie, z 960 px nie rozstrzygnę | Dwa typy. (a) Flotowe, czyste naczepy: lekka mgła w dolnych ~10–15 % drzwi (143, 155, 109). (b) Po dłuższej jeździe: **cienki film pyłu na całej wysokości** + mocniejszy dół (121, 158 — napis palcem w pyle na górnej połowie) | sprawdzić w shaderze `RearGrime`, czy jest składnik filmu na całej powierzchni. Jeśli go nie ma — dodać bardzo słaby (krycie ~0,1–0,15, WORKING_VALUE) pod gradientem od progu |
| P1-3 zacieki | rzadkie (8 %), klastrowane przy zawiasach i uszczelce, 15–70 %, ~25 % wymytych | Zacieki rzadkie: 0–3 na skrzydło, od narożników i krawędzi (121), od zawiasów i rygli (174, 108 — rdzawe, krótkie 20–40 %). Długich, równych pasów przez całe drzwi nie ma w żadnym kadrze drogowym | **potwierdza r5**, bez zmian. Długości > 50 % tylko jako rzadki wariant |
| P2-10 wycierki | rygle i uchwyty ×0,7 | **158: wyraźne ciemniejsze plamy wytarte dłonią przy uchwytach rygli** (czysta farba spod pyłu); 137: białawe plamy na dole drzwi | potwierdza P2-10. Wycierki jako plamy o średnicy ~20–40 cm wokół uchwytów (WORKING_VALUE) |
| Rozbryzg przy krawędzi (14 cm) | rozbryzg ~1 cm w ostatnich 14 cm | 105: drobne jasne plamki zaschniętych kropel na zderzaku i ramie (zima, sól). Na drzwiach rozbryzgu kropel w kadrach drogowych nie widać (rozdzielczość) | bez zmian; zimą rozbryzg może być **jaśniejszy od tła** (sól) — zadanie P2, bez danych liczbowych |
| Zima: białe zacieki solne | — | Żaden obejrzany kadr ich nie pokazuje (jedyny kadr zimowy z drogi to 121, szary) | **brak dowodów** — nie wprowadzać bez kadrów (luka do FIX) |

**Wniosek dla lidera.** Z gałęzi nic nie wymaga pilnej zmiany w grze. Kadry potwierdzają kierunek r5: najbrudniejsza dolna rama i belka, rzadkie zacieki, wycierki przy uchwytach. Jedna tania poprawka wynika z mojej oceny kadrów 121 i 158 (CC BY-SA, jako referencja): bardzo słaby film na całej wysokości drzwi — o ile shader go jeszcze nie ma.

Obie wykonać z pętlą `visual-qa` (doors-r6, dusk i overcast), na tych samych kamerach co 0182.

## 7. Dla lidera

- **Nie scalać** w obecnej postaci. Blok poprawek: §8. Można go skopiować do `docs/owner/MISTRAL-FIXES-12.md` jako § M61-FIX.
- **ZIP:** poprosić właściciela o `mistral-p18-trailer-soiling-files.zip` (sha256 z PR `8b34688e…6514`). Po FIX zastąpić go nowym.
- Do gry (opcjonalnie, WORKING_VALUE): rama i belka ×0,9–1,0; słaby film na całych drzwiach (~0,1–0,15), jeśli go brak. Barwy osadu nie zmieniać przed M61-FIX. Dowód: render `doors-r6` przy referencjach 121, 143 i 158.
- **Pliki recenzenta (scratch sesji, tymczasowe):**
  - `C:\Users\matma\AppData\Local\Temp\claude\65a86252f72ba2de\44810253-4f54-463a-b591-9868ed7d4a4f\scratchpad\m61\img\P18-*.jpg` (960 px) i `meta.json` (Commons API);
  - wycinki `…\m61\img\c105.jpg`, `c121.jpg`, `c143.jpg`, `c158.jpg`;
  - skrypt `…\tools\m61fetch.py`.

## 8. Blok poprawek M61-FIX (do wklejenia autorowi, nowa sesja)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p18-trailer-soiling (ISTNIEJĄCA, PR #58) — dopisujesz do niej, NIE twórz nowej. Piszesz po polsku. NIE ZMIENIAJ niczego poza research/mistral/p18-trailer-soiling/.

Recenzja (docs/reports/REVIEW-2026-11-14-s20-mistral-m61.md) odrzuciła kadry: opisy nie są napisane z obrazu. Poprawki:

1. USUŃ z kwalifikacji (status ODRZUCONY + powód „brak dwuskrzydłowych drzwi tylnych”): P18-138 (pusta rama kontenerowa, kabina w tle, Kalifornia, sierpień — bez śniegu), P18-160 (ściana PRZEDNIA naczepy: kanistry, skrzynki gaśnic, złącza, podpory), P18-167 (solówka z windą załadowczą), P18-171 i P18-172 (malowane klapy ciężarówek z Indii; 172 = Hajdarabad, EXIF 2022-05-15), P18-111 (winda załadowcza, pkt 4), P18-150 (drzwi rolowane — może zostać jako „drzwi rolowane, brud dolnej ramy”, ale nie w statystyce drzwi dwuskrzydłowych).
2. PRZEKWALIFIKUJ na wzorzec CZYSTY (osobna kategoria, poza statystyką brudu): P18-107, P18-162, P18-166 (+ popraw datę 166 na EXIF 2015-06-18).
3. P18-104 i P18-105 (eksponat muzealny, ciemna grafika, pod światło): brud drzwi NIEOCENIANY. Usuń „3 zacieki/skrzydło ~30 %” z 105 — na wycinku 1920 px zacieków nie ma. Zostaw tylko „drobne jasne plamki zaschniętych kropel na zderzaku/ramie”.
4. P18-111: to solówka z ZAMKNIĘTĄ WINDĄ ZAŁADOWCZĄ (platforma + roleta), nie drzwi dwuskrzydłowe — status ODRZUCONY jak w pkt 1 (ewentualnie „kontekst: zima, mokra jezdnia”).
5. P18-121: kolor = SZARY (nie brązowy). Kształt: rozproszony szary film na całej wysokości obu skrzydeł + pionowe szare zacieki przy prawej krawędzi prawego skrzydła od górnego narożnika + szara dolna rama/zderzak.
6. P18-118: drzwi są ZAMKNIĘTE, otwarte są panele aerodynamiczne. P18-139/149/153: brud = korozja i wiek (rdzawe zacieki spod zawiasów), nie spray drogowy — osobna kategoria „rdza/wiek”; 139 i 153 to ten sam pojazd (licz raz).
7. P18-158: dopisz to, co najważniejsze — pył na CAŁEJ wysokości drzwi (napis palcem „Sigueme vamo moler” w pyle na górnej połowie prawego skrzydła), ciemne wytarte plamy dłoni przy uchwytach rygli.
8. DOŁÓŻ ≥ 12 NOWYCH kadrów: tylne DWUSKRZYDŁOWE drzwi naczep/skrzyń W RUCHU lub zaraz po trasie, z widocznym brudem drogowym, w tym ≥ 6 zimowych (sól, błoto) i ≥ 6 z Europy (najlepiej PL/DE/CZ/LT). Źródła: Commons (np. kategorie tylnych widoków ciężarówek i naczep, naczep w Polsce, ciężarówek zimą — sprawdź nazwy kategorii), Openverse, Panoramax. Rozdzielczość ≥ 1000 px na wysokość drzwi, żeby było widać detal.
9. Każdy opis kadru PISZESZ SAM z obrazu (pobierz, pomniejsz ≤ 960 px, wycinek drzwi i progu w 2–3×). NIE używaj narzędzia wizyjnego z pytaniem sugerującym („czy są dwuskrzydłowe drzwi?”). Zabronione szablony zdań powtarzane w wielu wierszach. W uwagach: „rozdzielczość drzwi w px”, „wycinek obejrzany: tak/nie”.
10. Literatura: P18-002 — abstrakt mówi tylko, że duże krople mają tor balistyczny i „penetrate the wake”; nie mówi, gdzie się osadzają. Zdanie „trafiają próg i belkę” oznacz jako ekstrapolację (status ESTIMATED), nie jako treść źródła. P18-012 — próbki z Portugalii (Viana do Castelo); P18-018 — śnieg w Norwegii; oba = „kontekst, nie dane o osadzie na pojeździe”.
11. Przelicz §4 README na NOWYM mianowniku (tylko kadry z drzwiami dwuskrzydłowymi i brudem drogowym): próg/rama, belka, lampy, film na całej wysokości (tak/nie), liczba zacieków na skrzydło (mediana, n), skąd startują, wycierki (tak/nie), kolor słownie, sezon. Kadry czyste i „rdza/wiek” osobno.
12. Samokontrola: ≥ 20 % LOSOWO z jawnym seedem (random.Random(20261115).sample), ponownie obejrzane PRZEZ CIEBIE obrazy wylosowanych wierszy; zapisz w audit_20_percent.json, co poprawiłeś.
13. ZIP: mistral-p18-trailer-soiling-files-v2.zip (wszystkie kadry z manifestu, JPG ≤ 1600 px); w PR nazwa, rozmiar, sha256.

KRYTERIA: ≥ 20 kadrów z dwuskrzydłowymi drzwiami tylnymi i brudem drogowym (po usunięciach), ≥ 6 zimowych, ≥ 6 europejskich; 0 szablonowych opisów; statystyka bez kadrów czystych/bez drzwi.
ODDANIE: commit + push, komentarz w PR #58 „M61-FIX gotowe” + SUROWE `git diff --stat origin/main`. NIE scalaj.
```
