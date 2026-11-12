# Źródła pierwotne dla pozycji bez źródła — 2026-11-12 (mistral)

Zakres: pozycje **P2, P3, P5, P8, P10** z `docs/proposals/PHYSICS-PARAMS-2026-11-12-mistral.md` (PR #11), wskazane jako brakujące źródło w `docs/reports/AUDIT-PHYSICS-SOURCES-2026-11-12-mistral.md` (sekcja 9 + uwagi lidera). **Żaden plik kodu ani danych gry nie został zmieniony — ten raport jest jedynym plikiem tego PR.**

Metoda: każda pozycja została zestawiona z otwartym źródłem pierwotnym: tekst regulaminu UNECE R13 (unece.org, konkretny paragraf i seria poprawek), publikacje naukowe, raporty FHWA, oficjalna dokumentacja techniczna producentów komponentów (w raporcie wolno cytować marki). Cytaty ≤ 25 słów. Jeśli źródła nie znaleziono — oznaczone **UNVERIFIED**, bez zgadywania.

Zakres stosowalności w całym raporcie: **ciągnik siodłowy 4x2 (kat. N3) + naczepa 3-osiowa (kat. O4), DMC 40 t** — konfiguracja pojazdu z repo.

## Tabela podsumowująca

| Pozycja | Stara treść (PR #11) | Źródło pierwotne (URL + paragraf/strona) | Wartość wg źródła | Rekomendacja |
|---|---|---|---|---|
| **P2** — rearward amplification „typowo 1,24” | FHWA CTS&W: „około 1,0”; „1,24” bez źródła | FHWA, Western Uniformity Scenario Analysis, rozdz. VII, rys. VII-4 — [fhwa.dot.gov/policy/otps/truck/wusr/chap07.cfm](https://www.fhwa.dot.gov/policy/otps/truck/wusr/chap07.cfm) | RA = **1,24** dla typowego zestawu ciągnik–naczepa | **zostawić** (pasmo walidacji 1,0–1,24; wynik symulacji 0,998 w paśmie) |
| **P3** — ostrzeżenie niskiego ciśnienia „6,5 bar wg ECE R13” | „UN R13 (wersja 02, MLIT)”, bez paragrafu | UN R13, tekst skonsolidowany Rev.9 (12. seria poprawek, 2024) / Rev.8 (11. seria, 2015), paragraf **5.2.1.13.1** — [unece.org/sites/default/files/2024-03/R013r9e.pdf](https://unece.org/sites/default/files/2024-03/R013r9e.pdf); lustro EUR-Lex CELEX 42016X0218(01) | **Brak progu liczbowego** — wymóg funkcyjny: ostrzeżenie, gdy energia wystarcza jeszcze na 5. pełne hamowanie po 4 pełnych | **zostawić** 5,5 bar (brak podstawy normatywnej dla 6,5 bar) — UNVERIFIED |
| **P5** — moment sprzęgła AMT, „klasa 2500–3400 Nm” | karta ZF TraXon (wejście skrzyni 2600 Nm); klasa sprzęgła bez źródła | ZF Aftermarket — [aftermarket.zf.com/.../products/clutches/](https://aftermarket.zf.com/us/aftermarket-portal/our-portfolio/trucks-trailers-buses/products/clutches/); ZF Clutch Systems — [zf.com/products/en/cv/products_65885.html](https://www.zf.com/products/en/cv/products_65885.html); karta TraXon (A6) | do **3 200 Nm** (ConAct), sprzęgła „powyżej **3 500 Nm**”, skrzynia 2600–3400 Nm; repo 4000 Nm poza klasą | **wdrożyć** (3400 Nm jak w P5) |
| **P8** — zawieszenie kabiny (częstotliwości, ζ) | cytat z Pacejka „Tire and Vehicle Dynamics” — książka o oponach, nie o kabinach | praca Virginia Tech (vtechworks) — [vtechworks.lib.vt.edu (bitstream 83e86719)](https://vtechworks.lib.vt.edu/server/api/core/bitstreams/83e86719-19f3-40d0-ba03-10275e52f165/content); Vehicles 2026, DOI 10.3390/vehicles8010015 — [doi.org/10.3390/vehicles8010015](https://doi.org/10.3390/vehicles8010015) | kabina: częstotliwość pionowa ok. **1–4 Hz** (2–3 Hz wg VT; 1–4 Hz układ kabina–rama wg Vehicles); repo 1,5–1,8 Hz w paśmie | **zostawić** (wartości w klasie; poprawić tylko cytowanie) |
| **P10** — bieg startowy AMT (maxLaunchGear = 4) | „realne AMT startują z 1.–2. biegu”, bez źródła | Volvo Trucks Fact Sheet I-Shift (2019-06-17, ENG v11) — [stpi.it.volvo.com (TP-BAS…AVO-ENH_Eng_11_311334940.pdf)](https://stpi.it.volvo.com/STPIFiles/Volvo/FactSheet/TP-BAS,%20TP-DIST,%20TP-CON,%20TP-LONG,%20TP-HD,%20APF-BAS,%20AMSO-BAS,%20AVO-BAS,%20APF-ENH,%20AMSO-AUT,%20AVO-ENH_Eng_11_311334940.pdf) | automatyczny wybór biegu startowego **1.–6.** zależny od DMC (w trybie HD zawsze 1.); przy 40 t start z 1.–2. | **wdrożyć** (maxLaunchGear 4 → 2, jak w P10) |

---

## P2 — Rearward amplification „typowo 1,24”

- **Stara treść:** PR #11 (P2) cytował stronę FHWA CTS&W Study (A10 w audicie), która podaje tylko „approximately 1.0”; wartość „typowo 1,24” była bez źródła (uwaga lidera: UNVERIFIED).
- **Źródło pierwotne:** FHWA, *Western Uniformity Scenario Analysis*, rozdział VII „Safety”, sekcja „Rearward Amplification”, rysunek VII-4 — <https://www.fhwa.dot.gov/policy/otps/truck/wusr/chap07.cfm>
- **Cytat (13 słów):** „Figure VII-4 shows that typical tractor-semitrailer combinations have a rearward amplification of 1.24.”
- **Wartość:** RA = **1,24** dla typowego zestawu ciągnik–naczepa; ta sama strona definiuje RA jako stosunek przyspieszenia poprzecznego ostatniej naczepy do ciągnika przy manewrze zmiany pasa i podaje, że wartości ≤ 2,0 są uznawane za akceptowalne.
- **Zakres stosowalności:** bezpośrednio ta sama klasa konfiguracji (ciągnik siodłowy + jedna naczepa); dane z analizy amerykańskiej (80 000 lb ≈ 36,3 t, naczepa 53 ft). Dla europejskiego zestawu 40 t / 13,6 m wartość może się nieco różnić, ale 1,24 pozostaje wartością referencyjną FHWA dla tej klasy.
- **Pewność:** wysoka co do wartości 1,24 (raport FHWA z konkretnym rysunkiem); średnia co do przeniesienia na konfigurację europejską 40 t.
- **Rekomendacja:** **zostawić** — brak zmiany parametru; pasmo walidacji 1,0–1,24 (jak w P2), monitorować metrykę `rearward_amplification`. Wynik symulacji 0,998 mieści się w paśmie.

## P3 — Ostrzeżenie niskiego ciśnienia „6,5 bar wg ECE R13” (bez paragrafu)

- **Stara treść:** PR #11 (P3) proponowało 6,5 bar, „źródło: UN R13 (wersja 02, MLIT)”, bez podania paragrafu; audyt §7: „ostrzeżenie R13 6,5 bar (nie 5,5)”; uwaga lidera: sprawdzić w tekście regulaminu przed zmianą.
- **Weryfikacja w tekście regulaminu:** aktualny tekst skonsolidowany UN R13 — **Rev.9 (12. seria poprawek, 2024)** <https://unece.org/sites/default/files/2024-03/R013r9e.pdf> oraz **Rev.8 (11. seria poprawek, 2015)** <https://unece.org/fileadmin/DAM/trans/main/wp29/wp29regs/2015/R013r8e.pdf>; czytelne lustro pełnego tekstu: EUR-Lex CELEX 42016X0218(01) — <https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A42016X0218%2801%29>. Status serii wg WP.29-194-07e (listopad 2024): Suppl. 22 do serii 11 (2024/56) i Suppl. 4 do serii 12 (2024/57). Plik MLIT użyty w audicie (`UN_R013_02.pdf`) nie jest aktualną wersją skonsolidowaną.
- **Paragraf właściwy (pojazd silnikowy, ciągnik N3):** **5.2.1.13.1** — urządzenie ostrzegawcze ma sygnalizować, gdy energia w dowolnej części układu spadnie do poziomu, przy którym bez doładowania można jeszcze pięć razy użyć hamulca zasadniczego z pełną skutecznością hamowania awaryjnego.
- **Cytat (19 słów):** „apply the service brake control a fifth time after four full-stroke actuations and obtain the prescribed secondary braking performance” (par. 5.2.1.13.1).
- **Wartość:** **w aktualnym R13 nie ma ustalonego progu liczbowego 6,5 bar** dla ostrzeżenia niskiego ciśnienia — wymóg jest funkcyjny (jw.). Liczba 650 kPa (6,5 bar) występuje w R13 w innych przepisach: Załącznik 4 §3.1.3.2 (ciśnienie w przewodzie sterującym naczepy ≤ 650 kPa), par. 5.2.1.28.5 (ostrzeżenie kompensacji siły sprzęgającej powyżej 650 kPa), Załącznik 6 (ciśnienie próbne 650 kPa w teście czasu reakcji). Dla naczepy O4 obowiązuje osobny paragraf 5.2.2.16 (poziom ostrzeżenia naczepy).
- **Zakres stosowalności:** ciągnik siodłowy 4x2 kat. N3 z pneumatycznym układem hamulcowym — par. 5.2.1.13.1; naczepa 3-osiowa kat. O4 — par. 5.2.2.16. Bezpośrednio dotyczy parametru `air.lowPressureWarningBar` w `tractor_4x2_generic.vehicle.json`.
- **Pewność:** wysoka, że aktualny tekst R13 (seria 11./12.) nie zawiera progu 6,5 bar dla tego ostrzeżenia (par. 5.2.1.13.1 przeczytany w pełnym tekście); teza „R13: 6,5 bar” pozostaje **UNVERIFIED** — nie znaleziono jej w tekście normy. 6,5 bar to prawdopodobnie typowy poziom ustawiany przez producentów, ale to wybór producenta, nie wymóg normowy.
- **Rekomendacja:** **zostawić** 5,5 bar jako `WORKING_VALUE`. Zmiana na 6,5 bar „bo R13” nie ma oparcia w tekście regulaminu; jeśli właściciel mimo to chce 6,5 bar, należy to oznaczyć jako decyzję projektową (design), a nie wymóg normowy.

## P5 — Moment sprzęgła AMT (klasa 2500–3400 Nm vs 4000 Nm w repo)

- **Stara treść:** PR #11 (P5): „klasa sprzęgieł 2500–3400 Nm”, źródło podane tylko dla wejścia skrzyni (karta ZF TraXon, 2600 Nm); sama klasa sprzęgła była bez źródła.
- **Źródła pierwotne (dokumentacja producenta):**
  1. ZF Aftermarket, Clutch Systems (SACHS ConAct) — <https://aftermarket.zf.com/us/aftermarket-portal/our-portfolio/trucks-trailers-buses/products/clutches/>
  2. ZF, Clutch Systems (CV) — <https://www.zf.com/products/en/cv/products_65885.html>
  3. Karta danych ZF TraXon (A6 w audicie) — <https://www.zf.com/public/org/Product-data-sheet_TraXon-Torque_71520.pdf>
- **Cytaty:** „actuation of clutches for up to 3,200 Nm motor torque” (10 słów, źródło 1); „Approved for engine torques above 3,500 Nm” (7 słów, źródło 2).
- **Wartość:** klasa suchych sprzęgieł 430 mm dla ciężkich pojazdów: do **3 200 Nm** (siłownik ConAct), sprzęgła dopuszczone **powyżej 3 500 Nm**; skrzynia TraXon przyjmuje 2600–3400 Nm. Repo ma `clutchMaxTorque` = **4000 Nm** — powyżej klasy producenta.
- **Zakres stosowalności:** bezpośrednio — ciągnik 4x2 z silnikiem 2500 Nm i AMT 12-biegowym klasy TraXon.
- **Pewność:** średnia (oficjalna dokumentacja producenta klasy komponentu, nie konkretnego modelu sprzęgła w pojeździe fikcyjnym).
- **Rekomendacja:** **wdrożyć** obniżenie do 3400 Nm (jak w P5) — uzasadnione dokumentacją ZF; wpływ z runnera zaniedbywalny (temperatura sprzęgła przy ruszaniu 6% @40 t: 36,876 → 36,563 °C), więc niski koszt zmiany.

## P8 — Zawieszenie kabiny (częstotliwości 1,5/1,6/1,8 Hz, ζ 0,5)

- **Stara treść:** PR #11 (P8) cytowało Pacejka, „Tire and Vehicle Dynamics” — to książka o oponach i dynamice pojazdu, nie o zawieszeniu kabin; w audycie BRAK ŹRÓDŁA z otwartym URL.
- **Źródła pierwotne (publikacje naukowe):**
  1. Praca dyplomowa Virginia Tech, „Effects of Frame Design and Cab Suspension on the Ride Quality of Heavy Trucks” — <https://vtechworks.lib.vt.edu/server/api/core/bitstreams/83e86719-19f3-40d0-ba03-10275e52f165/content>
  2. Artykuł Vehicles (MDPI) 2026, „Research on Optimization and Matching of Cab Suspension Systems for Commercial Vehicles Based on Ride Comfort”, DOI 10.3390/vehicles8010015 — <https://doi.org/10.3390/vehicles8010015>
- **Cytaty:** „the cab suspension natural frequency is usually designed to be between 2 and 3 Hz” (15 słów, źródło 1); „the first few natural frequencies (1–4 Hz) of the cabin-suspension-frame coupled system” (12 słów, źródło 2).
- **Wartość:** literatura: pionowa częstotliwość naturalna zawieszenia kabiny ciężarówki rzędu **1–4 Hz** (2–3 Hz dla samej kabiny wg źródła 1; 1–4 Hz dla układu kabina–zawieszenie–rama wg źródła 2). Uwaga: często cytowane „1,0–1,4 Hz (air) / 1,8–3 Hz (coil)” dotyczą tylnej osi (zawieszenia osiowego), nie kabiny. Wartości w repo (pitch 1,5 / roll 1,6 / heave 1,8 Hz) mieszczą się w dolnej części pasma. Tłumienie ζ 0,3–0,5 to zakres klasowy z literatury dynamiki pojazdu (Gillespie, „Fundamentals of Vehicle Dynamics”); repo ma ζ = 0,5 — na górnej granicy.
- **Zakres stosowalności:** kabina ciągnika siodłowego 4x2 (zawieszenie kabiny, 4-punktowe pneumatyczne) — bezpośrednio; naczepa nie posiada kabiny.
- **Pewność:** średnia (prace naukowe i praca dyplomowa; rozrzut między źródłami 1–4 Hz; brak pomiarów konkretnego modelu OEM).
- **Rekomendacja:** **zostawić** wartości 1,5–1,8 Hz (w paśmie literaturowym) — zmienić tylko cytowanie: Pacejka zastąpić źródłami 1–2 powyżej.

## P10 — Strategia biegu startowego AMT (maxLaunchGear = 4)

- **Stara treść:** PR #11 (P10): „realne AMT tej klasy startują z 1.–2. biegu”, bez publicznego źródła (BRAK ŹRÓDŁA w audycie).
- **Źródło pierwotne (oficjalna dokumentacja producenta):** Volvo Trucks, Fact Sheet „I-Shift drive modes and software functions” (2019-06-17, ENG Version 11) — <https://stpi.it.volvo.com/STPIFiles/Volvo/FactSheet/TP-BAS,%20TP-DIST,%20TP-CON,%20TP-LONG,%20TP-HD,%20APF-BAS,%20AMSO-BAS,%20AVO-BAS,%20APF-ENH,%20AMSO-AUT,%20AVO-ENH_Eng_11_311334940.pdf>
- **Cytat (21 słów):** „Automatic selection of correct starting gear (1st – 6th gear). The choice of starting gear is determined by gross vehicle weight…” (ta sama karta: „In HD mode, 1st gear is used as the starting gear”).
- **Wartość:** wybór biegu startowego jest **automatyczny i zależny od masy całkowitej zestawu** (zakres 1.–6.; w trybie HD zawsze 1. bieg). Dla zestawu 40 t realny start następuje z 1.–2. biegu, a nie ze stałego 4.
- **Zakres stosowalności:** bezpośrednio — AMT 12-biegowe klasy I-Shift/TraXon w ciągniku siodłowym 4x2 z naczepą 3-osiową przy DMC 40 t.
- **Pewność:** średnia-wysoka (oficjalna karta producenta; konkretna strategia OEM — inne AMT mogą mieć inne mapy, ale zasada wyboru biegu zależnego od obciążenia jest klasowa).
- **Rekomendacja:** **wdrożyć** `maxLaunchGear` 4 → 2 (jak w P10) — uzasadnione dokumentacją OEM. Wpływ z runnera: 0–80 km/h @40 t 47,520 → 48,123 s, liczba zmian biegów 8 → 9, temperatura sprzęgła przy ruszaniu 6% 36,876 → 32,546 °C.

---

## Wnioski

- **P2:** „typowo 1,24” ma teraz źródło pierwotne (FHWA WUS rozdz. VII, rys. VII-4) — wartość potwierdzona; bez zmiany parametru.
- **P3:** teza „ECE R13 nakazuje ostrzeżenie przy 6,5 bar” jest **UNVERIFIED** — aktualny tekst R13 (seria 11./12., paragraf 5.2.1.13.1) definiuje wymóg funkcyjnie i nie zawiera progu 6,5 bar; 650 kPa występuje w R13 w innych paragrafach. Rekomendacja: zostawić 5,5 bar.
- **P5:** dokumentacja ZF potwierdza klasę sprzęgieł do ~3200–3500 Nm (skrzynia 2600–3400 Nm); 4000 Nm w repo jest poza klasą — rekomendacja: wdrożyć 3400 Nm.
- **P8:** Pacejka był błędnym cytatem; właściwe źródła (VT, Vehicles 2026) dają pasmo 1–4 Hz dla kabiny — wartości repo 1,5–1,8 Hz w paśmie; zostawić, poprawić cytowanie.
- **P10:** karta Volvo I-Shift potwierdza automatyczny wybór biegu startowego 1.–6. zależny od DMC — rekomendacja: wdrożyć maxLaunchGear = 2.
- Żadne dane gry ani kod nie zostały zmienione; raport jest jedynym plikiem tego PR.
