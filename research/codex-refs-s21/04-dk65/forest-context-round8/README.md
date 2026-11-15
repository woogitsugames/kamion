# Kontekst lasu przy korytarzu DK65 — BDL

Stan odczytu: 15.11.2026, 23:23 czasu Brukseli. **Jedno rzeczywiste wydzielenie, 0 fotografii.**

Oficjalny [katalog usług BDL, pkt 1.7](https://bdl.lasy.gov.pl/portal/uslugi-ogc) wskazuje WMS mapy drzewostanów. Odczytano GetCapabilities, obejrzano mapę i wykonano jedno GetFeatureInfo w widocznym brunatnym poligonie. Dokumentację zapytań, pełne odpowiedzi tekstowe i ograniczenia zachowano obok. Obraz mapy pozostał poza gitem w Data/raw. Nie przypisano licencji CC.

## Ustalenia

- SOURCED [feature-info-response.json, obie features]: adres `01-08-2-04-232   -j   -98`, wspólne `arodes_int_num=108033211`. Rekord Drzewostany PGL LP ma `subarea_id=15725636`, Wydzielenia PGL LP `subarea_id=55156`. To dwie warstwy opisujące jedno wydzielenie.
- SOURCED [ta sama odpowiedź]: `species_cd=SO`, `species_cd_d=SO`, `species_age=129`, `a_year=2026`, `part_cd=8`, `age_class=VII`. [Słownik LP](https://drewno.lasy.gov.pl/grupy-gatunkowe/) rozwija SO jako sosnę. Bez słownika tej konkretnej struktury nie deklarujemy 80% udziału ani formalnie potwierdzonego gatunku dominującego. Wiek 129 pozostaje wartością pola danych, nie pomiarem każdego drzewa.
- ESTIMATED: środek wybranego piksela mapy to 53.254152 N, 22.987369 E. Punkt K1 km20 / dk65-08 ma 53.253363 N, 22.984289 E. To kontekst lasu obok korytarza, nie GPS drzewa ani pomiar odległości od jezdni.
- SOURCED: odpowiedź zawiera `Shape=Polygon`, ale `geometry=null`; nie pobrano geometrii granic. Nie interpretujemy innych pól powierzchni bez jednostek/słownika.

## Do generatora

Jednostka pozwala wskazać źródłowy kontekst sosnowego lasu przy tym fragmencie korytarza. Gatunek szpaleru przy jezdni, rozstaw pni, wysokość i odsunięcie od asfaltu pozostają UNVERIFIED. Dane nie dowodzą stanu terenowego w dniu odczytu.

## Kontrola metody

Pierwszy biały GetMap miał zamienione osie; po poprawieniu WMS1.3/EPSG2180 na northing/easting otrzymano rzeczywiste poligony. To nie brak lasu. WMS warstwy1/7 oznaczają drzewostany/wydzielenia; nie są tymi samymi identyfikatorami co warstwy11/12 REST z dawnych zapytań. Nie ponowiono tamtych punktów. Łącznie 1 capabilities, 2 mapy (jedna korekta osi), 1 identyfikacja obiektu; żadnego OSM/Overpass ani pobierania zdjęć.

## Uzupełnienie słownika — ograniczony wynik

Odczytano dwa dodatkowe źródła (szczegóły `dictionary-check.json`): oficjalne metadane warstwy i rozdziały o strukturze BDL w publikacji UAM2016 udostępnionej przez BULiGL. Metadane potwierdzają typy pól, lecz ich aliasy powtarzają nazwy. Publikacja opisuje różne znaczenia A_YEAR dla innych tabel oraz dwa warianty danych urządzeniowych (początek PUL i aktualizacje SILP). **Nie rozstrzyga to semantyki a_year bieżącego WMS.**

SO pozostaje źródłowo kodem sosny według słownika LP. Formalne znaczenie species_cd_d jako gatunku dominującego, odniesienie wieku129 oraz czy2026 jest rokiem planu/taksacji/aktualizacji pozostają UNVERIFIED. Nie odejmowano wieku od2026, nie wyprowadzano roku powstania lasu ani80% z part_cd8. Nie wykonano kolejnych zapytań mapowych.
