# Zlecenie dla Mistral Vibe Code — pakiet badawczy „pętla S8 ↔ DW671 ↔ Tykocin” (s23, 16.11)

Wklej do Mistral Vibe Code:
```
Pracujesz dla projektu Kamion — realistycznego symulatora ciężarówki z naczepą (Unity 6 URP, Windows), świat budowany z danych OSM + GUGiK, region Podlasie. Repo: https://github.com/woogitsugames/kamion. Komunikacja po polsku. Masz własne środowisko i możesz używać wielu agentów równolegle — podziel pracę na agentów wg sekcji niżej (np. 5–8 agentów: po jednym na grupę kafli + jeden na przekroje dróg + jeden na znaki + jeden integrujący). Na końcu wszystko wypchnij na GitHub na JEDNĄ gałąź `research/mistral-s8-loop-s23` i otwórz PR typu draft do `main` (NIE scalaj).

KONTEKST (przeczytaj najpierw w repo): CLAUDE.md, docs/11_DECYZJE_WLASCICIELA.md (D63 „najpierw przejezdne”, D82 „pętla S8 ↔ DW671 ↔ Tykocin”), docs/adr/0278-*.md (plan rozbudowy mapy), docs/owner/MAP-DECISIONS-2026-11-16.md (sekcja b — 15 kafli pętli), docs/adr/0231-*.md (pierścień kafli Mońki/Tykocin), docs/adr/0272-*.md (pobocza dróg zamiejskich), docs/adr/0279-*.md (audyt znaków), docs/reports/ortho-xsec-0272/ i tools/worldgen/qa/ortho_xsec.py (jak mierzymy przekroje z ortofoto), docs/LICENSES.md.

CEL: przygotować dane referencyjne dla 15 nowych kafli pętli S8 ↔ DW671 ↔ Tykocin, żeby lider mógł je zbudować „najpierw przejezdne” (D63) z prawdziwymi przekrojami, węzłami, MOP i oznakowaniem. To jest research + dane — NIE piszesz kodu gry, NIE budujesz świata.

ZAKAZY (bezwzględne):
- ZERO Google Maps / Street View / Google Earth / 3D Tiles — nawet do „podejrzenia”. Także Bing Streetside, Apple Look Around, Yandex.
- Dozwolone źródła: OpenStreetMap (API 0.6 / Overpass, ODbL), GUGiK (Geoportal WMS/WMTS ortofoto, NMT, BDOT10k — usługi publiczne), Mapillary (CC BY-SA 4.0, tylko przez API/oficjalne linki, z autorem i id zdjęcia), GDDKiA / zarządy dróg (dokumenty publiczne, BIP), Dz.U. (rozporządzenia o znakach i warunkach technicznych dróg), Wikimedia Commons (licencja per plik).
- Do repo NIE wrzucaj zdjęć ani kadrów (tylko linki + identyfikatory + metadane); żadnych plików > 5 MB; tylko dane tekstowe (JSON/YAML/MD/CSV).
- Bez marek i logo w czymkolwiek, co miałoby trafić do gry; w researchu nazwy firm tylko jako „funkcja obiektu” (np. „stacja paliw”, „magazyn logistyczny”), bez nazw własnych.
- Każda liczba: zmierzona (z narzędziem i danymi wejściowymi w repo), zacytowana (źródło + data + strona/punkt) albo oznaczona ESTIMATED / UNVERIFIED. Nie zmyślaj.

ZAKRES (podział na agentów):
A. Lista kafli i granice: na podstawie MAP-DECISIONS (b) i ADR 0278 ustal dokładną listę 15 kafli pętli (id wg konwencji repo, np. s8-*, dw671-*), ich bbox w EPSG:2180 i kolejność jazdy; sprawdź styki z istniejącymi kaflami (dk65-01, dw671-tykocin-*, tykocin, knyszyn-w) — plik `research/mistral-s8-loop-s23/tiles.json`.
B. Przekroje dróg z ortofoto GUGiK: dla S8 (jezdnie, pasy, pas dzielący, pobocza utwardzone, bariery), DW671 i dróg łączących — co 200–500 m pomiar szerokości jezdni, pasów, poboczy, typ krawędzi (krawężnik / pobocze gruntowe / utwardzone) narzędziem tools/worldgen/qa/ortho_xsec.py (lub jego metodą, jeśli nie da się uruchomić — opisz); wyniki JSON jak w docs/reports/ortho-xsec-0272/ + README z medianami per odcinek — `research/mistral-s8-loop-s23/xsec/`.
C. Węzły i MOP na S8: dla każdego węzła na pętli — typ (WB, karo, trąbka…), układ łącznic, długości pasów włączania/wyłączania (z ortofoto, ESTIMATED), ograniczenia prędkości na łącznicach (OSM/znaki); MOP: kategoria, parkingi dla ciężarówek (liczba miejsc z ortofoto, ESTIMATED), stacje paliw (funkcja, bez marki) — `research/mistral-s8-loop-s23/junctions.json`, `mop.json`.
D. Oznakowanie: inwentarz znaków pionowych istotnych dla ciężarówki (B-5, B-18, B-19, B-20, B-33, D-42/D-43, A-7, znaki kierunku E-*, e-TOLL/opłaty, zakazy wjazdu ciężarówek do miejscowości) — z OSM (traffic_sign) i Mapillary (detekcje + zdjęcia z id/autorem/licencją), z położeniem (WGS84 + EPSG:2180) i pewnością; porównanie z wymaganiami Dz.U. (rozporządzenie o znakach — cytuj wydanie) — `research/mistral-s8-loop-s23/signs.json` + `SIGNS.md`.
E. Cele dla rozgrywki ciężarówką: zakłady przemysłowe, magazyny, bazy, stacje paliw z parkingiem TIR, elewatory/skupy w obrębie pętli i ±2 km — funkcja, położenie, wjazd dla ciężarówek (gdzie brama, z ortofoto), źródło (OSM/BDOT) — `research/mistral-s8-loop-s23/destinations.json`.
F. Typologia zabudowy wsi i miejscowości na pętli (tylko opis + statystyki z BDOT/OSM: liczba budynków, kondygnacje, typy dachów jeśli w danych) — `research/mistral-s8-loop-s23/settlements.md`.
G. Integrator: spójność plików, schematy (opisz pola w `research/mistral-s8-loop-s23/README.md`), tabela źródeł i licencji (dopisz sekcję do docs/LICENSES.md tylko dla danych tekstowych, które dodajesz), lista UNVERIFIED do potwierdzenia przez właściciela, raport końcowy.

WYNIK: gałąź `research/mistral-s8-loop-s23` z katalogiem `research/mistral-s8-loop-s23/` (wszystkie pliki powyżej), raport `research/mistral-s8-loop-s23/RAPORT.md` (≤ 40 linii po polsku: co zrobione, liczby, czego nie udało się ustalić, ryzyka), PR draft do main z tym raportem w opisie. Commituj po każdej sekcji (małe commity, opisowe komunikaty). Nie zmieniaj żadnych plików poza `research/mistral-s8-loop-s23/` i jedną sekcją docs/LICENSES.md. Na koniec napisz w PR: „Gotowe do scalenia po weryfikacji lidera: TAK/NIE”.
```
