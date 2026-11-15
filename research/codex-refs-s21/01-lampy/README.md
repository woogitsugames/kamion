# 01 — Lampy i fotometria — WIP

Cel: uzupełnić lukę M59-FIX zdjęciami lamp ciągników i naczep z czytelną homologacją oraz przepisami. Stan: **NIESPEŁNIONE**.

## Materiał

- 01-001 — SOURCED [obraz, autor Dietmar Rabich, CC BY-SA 4.0, link w manifeście]: okrągła lampa wozu strażackiego, trzy widoczne pola, czytelne E1 i S1 na wycinku. Kontekst pomocniczy; nie liczyć jako naczepy ani ciągnika siodłowego. Marka widoczna: wyłącznie referencja kształtu. Oryginał poza gitem w `Data/raw/refs/codex-s21/01-lampy/straz.jpg`; miniatury ≤ 800 px.

## Fotometria

Źródło: [UNECE R148, E/ECE/TRANS/505/Rev.3/Add.147](https://unece.org/sites/default/files/2021-05/R148e.pdf), wersja dokumentu z 2021 r.; sprawdzić aktualne poprawki przed zastosowaniem prawnym. Wartości są wymaganiami badania, nie bezpośrednimi wartościami emisji shadera.

- SOURCED [R148 pkt 4.8.11]: co najmniej 5:1 dla pomiaru obu wspólnie włączonych lamp wobec samej tylnej pozycyjnej/obrysowej, jeśli jest wzajemnie sprzężona ze stopem; w polu ±5° V i ±10° H.
- SOURCED [R148 pkt 5.5.1 tabela 7]: S1 stałe: minimum 60 cd w osi H-V, maksimum pojedynczej lampy 260 cd w dowolnym kierunku.
- SOURCED [R148 pkt 5.6.1 tabela 8]: kierunkowskaz 2a stały: minimum 50 cd w osi odniesienia, maksimum pojedynczej lampy 500 cd w dowolnym kierunku.
- SOURCED [R148 pkt 5.11.3]: dla kategorii 1a/1b/1c/2a/2b luminancja w każdym wskazanym punkcie ≥ 2,5 cd/m²; gradient między punktami ≤ 2 × B₀/cm, gdzie B₀ to najmniejsza zmierzona luminancja.

## Luki

UNVERIFIED: kształt i kolejność funkcji typowych zespołów naczep i ciągników; czytelne homologacje tych pojazdów. Brak właściwych kadrów włączonych, nocnych i lampek tablicy. Potrzeba ≥ 15 zbliżeń tylnych, ≥ 4 włączonych, ≥ 3 zmierzch/noc i ≥ 5 lampek tablicy według M59-FIX. 01-001 nie jest zaliczany do tych progów. Drugi obejrzany kandydat `CombinedLampReflector.jpg` przedstawia małą przyczepę o nieustalonej kategorii; nie jest podstawą wniosków o naczepach.

Dalszy krok: wyszukiwać osobno fotografie tylnych lamp zespołów drogowych i zbliżenia kloszy, weryfikując E-numery na oryginale.

## Dalszy przegląd

01-002…004: trzy europejskie ciężarówki, fotografie Cjp24 (CC BY-SA 4.0). Obejrzano całe kadry i osobno wycinki oryginałów. Żaden nie umożliwia odczytania homologacji. Materiał pomocniczy dla kształtów przednich lamp; nie zwiększa liczników M59-FIX. Liczba komór funkcjonalnych pozostaje UNVERIFIED. Zachowane są miniatury całych kadrów oraz wycinki.

01-005 — SOURCED [obraz w manifeście]: cztery pola poziomego klosza naczepy, widoczna rozetowa i żebrowana optyka. Góra lampy ucięta. E-numer pozostaje UNVERIFIED; biała obudowa przy tablicy nie potwierdza funkcji lampki. Wycinek obejrzany osobno.


## Uzupełnienie agentowe — sterowanie i odczyt znaków (15.11.2026)

`regulations.csv`: trzy wpisy o kierunkowskazach i awaryjnych zweryfikowano w pełnej istniejącej kopii UNECE **R48 Rev.12, seria06 (snapshot2015)**: `research/gptpro/p4-truck-regulations/files/P4-001.pdf`, s48. Stronę48 odczytano tekstowo i obejrzano w renderze. Rytm90±30/min, emisja do1s, pierwsze zgaśnięcie do1,5s, awaryjne w fazie. Dodatkowo s20 rozróżnia homologację pojazdu R48, a s42 określa obowiązkowość, ilość i zakres wysokości lamp cofania. KategoriaO1 ma opcjonalność z6.4.1; nie wolno wyprowadzać obowiązku z samej długości w6.4.2. Dokładne warunki w CSV. SHA256 lokalnej kopii w `regulation-evidence.json`. **To zweryfikowany starszy snapshot, nie deklaracja aktualności prawa2026.** Nie dodano kopii PDF do tego pakietu.

Wpis01-N04 przeniesiono z niezweryfikowanego R148Amend.5 na pełny tekst bazowego R148Add.147 z2021r.: ponownie otwarto zachowany pełny tekst web (2865linii), pkt3.3.2.1–4. Nie jest to fragment wyników wyszukiwania. Tą samą drogą odczytano tabelę10 pkt5.8.1 (01-N08): cofania80cd minHV; maksima300/600/8000cd zależnie od kierunku — dokładne warunki wCSV. Bezpośrednie pobranie i screenshotPDF nadal403, więc nie deklarujemy nowej kopii PDF ani obejrzenia składu strony. Bezpośredni R48Rev13 zwracał403. Próba odczytu urzędowej publikacji R48 w EUR-Lex zwróciła ekran weryfikacji człowieka; nie podejmowano CAPTCHA. Nie podstawiono starszej Rev12 jako potwierdzenia treści Rev13.

Dodatkowy kandydat `Lorrylights.jpg` (Rxj, CC BY-SA3.0) obejrzany osobno w1191×842: wąski, przepalony, rozmyty widok tyłu; oznaczenia nieczytelne. Odrzucony, poza głównym manifestem i licznikiem kadrów użytecznych. `Grecja tablica.jpg` obejrzany w700×467: okrągły bursztynowy klosz przy przedniej kratce i czerwonej tablicy, płytka głębia ostrości; E i funkcja lampy nieczytelne — także poza licznikiem. Dowody w `agent-lamps-search-log.json`; oryginały poza gitem. `Kippauflieger...` nadal niepobrany:HTTP429, domenę wstrzymano. **Nowe kwalifikowane kadry E:0**.

###01-006 —konkretny kontekst tylnej lampy ciągnika

Ponownie obejrzana istniejąca kopia Commons zData/photos/nowe (Asurnipal, CCBY-SA4.0, EXIF2022-06-08) oraz osobno wycinek lewej lampy. Zbliżenie ma lampę około690px szerokości woryginale (ESTIMATED odczyt pikselowy), aleE jest nieczytelne. Materiał pomaga odtworzyć klosz, barwne wstawki, żebrowanie, mocowanie na błotniku i pusty uchwyt tablicy. Nie potwierdza liczby funkcji ani świecenia. To1kadr z2plikami, bez nowego pobrania i bez kopii oryginału wgicie. Łącznie6kadrów pomocniczych, kwalifikowaneEciągnika/naczepy nadal0.

Flickr obieg2:3wyszukiwania zfiltramiCC4/5/9 (75metadanych),1indywidualnafotostrona potwierdzaCCBY2.0; oryginałHTTP429, domena wstrzymana. Próba fotostrony wChrome przerwana przed nawigacją, gdy wykryto wejście użytkownika. **Zero nowych obserwacji obrazu Flickr i zero kwalifikowanych kadrów**; wyniki nie zostały włączone do manifestu. Szczegóły w `flickr-screening-2026-11-15.json`.
