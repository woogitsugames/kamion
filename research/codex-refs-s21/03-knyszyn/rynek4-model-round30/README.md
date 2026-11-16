# Rynek 4 — sąsiedni model, runda 30

Odczyt i ogląd: 2026-11-16, bez odtwarzania godziny. **1 nowo przeanalizowana bryła, 1 własna obejrzana figura 800 × 480 px, 0 nowych zapytań, ZIP i fotografii.** Wykorzystano istniejącą odpowiedź PRG R29 oraz te same źródłowe archiwa modeli i lokalne BDOT, wyłącznie do odczytu.

## Adres i odrębność

SOURCED [istniejące GML PRG R29]: Knyszyn, Rynek 4, `ID_IIP=PL.PZGIK.200.PRG_896a7265-d721-41cd-bfac-9b78b6071094_2025-10-01T14:00:58+02:00`. Literalne `gml:pos` to **612326.58 760910.8**, kolejność N,E w WFS 2.0/URN EPSG:2180. Własne obliczenia i figura: E=760910.8, N=612326.58.

ESTIMATED [własny test przestrzenny]: punkt znajduje się w poligonie BDOT i przyziemiu obu modeli. **Formalny adres→buildingId UNVERIFIED** — brak urzędowego wspólnego klucza adresowego. Punkt nie jest GPS aparatu ani pomiarem naroża budynku.

SOURCED [pola BDOT oraz CityGML]: lokalny klucz **2002917F-2D30-5C99-E053-CC2BA8C01CFC**, namespace **PL.PZGiK.335.BDOT10k**. Jest inny niż analizowane wcześniej 3002, 3031 i 3066; to jedna dodatkowo przeanalizowana bryła. Brak wcześniejszego literalnego klucza w 03/K1 nie oznacza braku tej bryły w tle starszych fotografii. BDOT: `WERSJA=2025-10-16T00:00:00.000`, `IDEGIB=200804_4.0054.2462_BUD`. IDEGIB pozostaje literalnym wskaźnikiem, bez kontroli EGiB i danych właścicieli.

## Wysokości i datowanie

| Produkt | SOURCED — atrybuty | ESTIMATED — własna geometria |
|---|---|---|
| LoD2 2017 | `lod2Solid`; `wersjaId=2018-01-16T00:00:00`; `zrodloDach=ALS_I`; `aktZrodla=2016`; `roofType=1130` bez dekodowania; brak measuredHeight | min Z 126.99, max Z 136.67; zakres pionowy **9.68 m**; IoU przyziemia z BDOT około 0.99863 |
| LoD1 2024 | `lod1Solid`; `wersjaId=2023-11-10T00:00:00`; `zrodloDach=ALS_I`; `aktZrodla=2016`; `roofType=1000` bez dekodowania; **measuredHeight=7.79, uom=meter** | min Z 127.18, max Z 134.97; zakres **7.79 m**; IoU przyziemia z BDOT 1.0 |

SOURCED [srsName źródłowych dokumentów]: poziomo EPSG:2180; pionowo LoD2 **PL-KRON86-NH**, LoD1 **EPSG:9651**. Nie odejmowano bezwzględnych Z między produktami. Każdy zakres liczony osobno jako max Z minus min Z z jego geometrii.

Oba produkty wskazują źródło dachu z **2016 r.**, a nie pomiar z 2024 r. lub stan 2026. `wersjaId` nie zostało zastąpione nazwą produktu. `measuredHeight` LoD1 i zakres LoD2 są różnymi miarami modeli; **7.79–9.68 m nie jest przedziałem tolerancji rzeczywistej wysokości ani dowodem przebudowy**. Ilościowa dokładność terenowa, liczba kondygnacji i obecny stan pozostają UNVERIFIED.

## Ogląd i wykorzystanie

Osobno obejrzano [własną figurę](files/03-RM30-models.png). W rzucie punkt znajduje się wewnątrz niemal zgodnych, nieregularnych obrysów. LoD2 przedstawia spadzisty dach i mniejsze części przyziemia, LoD1 uproszczoną bryłę z poziomą górą. Pozioma góra LoD1 nie dowodzi płaskiego dachu rzeczywistego. Kolory to oznaczenia produktów, nie materiały elewacji. W rzucie północ siatkowa jest ku górze; w 3D Z każdego modelu wyzerowano od jego własnej podstawy.

Dla sesji Knyszyn jest to historyczna geometria pomocnicza pierzei z identyfikatorem 2D30, bez narzucania kondygnacji, kolorów lub materiału. Adres roboczy należy zachować wraz ze statusem ESTIMATED.

Źródła: [LoD2 GUGiK](https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD2/2008_gml.zip), [LoD1 GUGiK 2024](https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD1/2024/20/2008.zip), istniejący indeks i dokumentacja R22, odpowiedź KINA/PRG R29 i lokalne BDOT. Modele CC BY 4.0 według istniejących metadanych indeksu R22; nie przeniesiono tej licencji na BDOT i PRG. Archiwa odczytano w miejscu, porównano ich SHA256; SQLite otwarto `mode=ro`. Własne niewielkie ekstrakty i obliczenia są wyłącznie we własnym raw R30. Nie skopiowano archiwów, nie zmieniono shared Data, wcześniejszych rund i parentów; bez Chrome i git.
