# Sąsiednia bryła przy punkcie PRG Rynek 2 — runda 25

Odczyt: 2026-11-16, bez podawania niezmierzonej godziny. **1 nowo przeanalizowany obiekt, 2 istniejące produkty, 1 własna figura 800 × 480 px, 0 nowych fotografii, ZIP i zapytań sieciowych.**

## Identyfikacja i status

SOURCED [literalne pola CityGML/BDOT]: `buildingId` i `LOKALNYID` **2002917F-3031-5C99-E053-CC2BA8C01CFC**, przestrzeń `PL.PZGiK.335.BDOT10k`. CityGML `gml:id` ma prefiks `ID-2008-`. Lokalny BDOT podaje `WERSJA=2025-10-16T00:00:00.000` i `IDEGIB=200804_4.0054.2456_BUD`; to odczyt identyfikatora, bez kontroli ewidencji lub danych właściciela.

Oficjalny punkt PRG **Knyszyn, Rynek 2** z istniejącej odpowiedzi R23 ma E=760878.4, N=612347.75 w EPSG:2180. **ESTIMATED [własny test przestrzenny]**: leży wewnątrz tego obrysu BDOT oraz obu modeli. Przyziemie LoD1 pokrywa się z tym rekordem BDOT (IoU 1.0). **Formalny adres→buildingId UNVERIFIED:** PRG i CityGML nie zawierają odczytanego wspólnego klucza adresowego. Nie jest to GPS aparatu.

Przed analizą wyszukano ID, IDEGIB i Rynek 2 w dotychczasowych 03/K1. Nie znaleziono opisu tej bryły po tych kluczach; Rynek 2 był w R23 tylko punktem kontrolnym poza sąsiednim modelem 3002. Nie wyklucza to wcześniejszego występowania domu w tle fotografii.

## Dane i ostrożna wysokość

| Produkt | SOURCED — pola źródłowe | ESTIMATED — obliczenie na geometrii |
|---|---|---|
| LoD2 2017 | `zrodloDach=ALS_I`, `aktZrodla=2016`, `wersjaId=2013-01-01T00:00:00`; geometria `lod2Solid`, `roofType=1130` bez dekodowania | min Z 127.32, max Z 134.94; pionowy zasięg około **7.62 m** od własnej podstawy |
| LoD1 2024 | `zrodloDach=ALS_I`, `aktZrodla=2016`, `wersjaId=2023-11-10T00:00:00`; `lod1Solid`, `roofType=1000`; **`measuredHeight=5.98`, `uom=meter`** | min Z 127.54, max Z 133.52; zasięg około **5.98 m** od własnej podstawy |

LoD1 ma wysokość przybliżonego uproszczonego modelu; nie jest ona automatycznie wysokością kalenicy. **5.98–7.62 m nie stanowi dowiedzionego przedziału wysokości terenowej ani tolerancji pomiaru.** Nie ustalono liczbowej dokładności tego obiektu. W obu produktach dach pochodzi ze źródła 2016: produkt 2024 nie jest nowym pomiarem dachu. Różnice obrysu i wysokości nie dowodzą przebudowy ani aktualnego stanu 2026.

Pionowe układy odniesienia są odmienne: LoD2 ma PL-KRON86-NH, LoD1 EPSG:9651. Nie odejmowano bezwzględnych wysokości między produktami. Każdą bryłę na figurze przesunięto do jej własnej podstawy. Nie wyprowadzono kondygnacji, materiałów pokrycia ani kolorów elewacji.

## Własny ogląd geometrii i źródła

Osobno obejrzano [figurę 800 × 480 px](files/03-RM25-models.png): lewy panel pokazuje punkt PRG wewnątrz obrysów; LoD2 zawiera kilka spadzistych połaci i nieregularne przyziemie, a LoD1 jest blokiem o poziomej górnej powierzchni. Płaska góra LoD1 nie dowodzi płaskiego rzeczywistego dachu. Barwy oznaczają produkty, a nie materiały. Rzut ma północ siatkową ku górze.

Oficjalne źródła istniejących archiwów: [LoD2](https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD2/2008_gml.zip), [LoD1 2024](https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD1/2024/20/2008.zip). Metadane indeksu i [dokumentacja GUGiK](https://www.geoportal.gov.pl/pl/dane/inne-dane/modele-3d-budynkow/) były odczytane w R22; nie pobierano ich ponownie. Licencja modeli CC BY 4.0 pochodzi z tamtych metadanych. PRG i BDOT nie otrzymały automatycznie licencji CC.

Dokładne nazwy członków ZIP, ich zweryfikowane SHA256 i pola źródłowe znajdują się w `geometry-summary.json`. Własny raw zawiera tylko dwa małe ekstrakty obiektu, obliczenia i skrypt badawczy. Oba wspólne ZIP, BDOT SQLite i R23 PRG pozostały niezmienione. Brak zdjęć właściciela, 3D Tiles, Google, nowych API i zmian parentów.
