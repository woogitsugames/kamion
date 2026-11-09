# 05 — Mapa: Białystok 1:1, dane i pipeline

## 1. Skala

| Element | Skala |
|---|---|
| Pojazdy, drogi w przekroju, pasy, znaki, budynki, promienie łuków | **1:1 zawsze** |
| Miasta (Białystok, potem kolejne miejscowości) | **1:1** — prawdziwe ulice, odległości, układ |
| Odcinki między miastami | **skracane** — współczynnik ustalany ADR-em w Etapie 7 po teście kilku wariantów (np. 1:4, 1:6, 1:8) |
| Czas w grze | przyspieszony względem realnego (ADR) |

Skracanie tras **nie** jest liniowym przeskalowaniem: zachowujemy kolejność węzłów, skrzyżowań, miejscowości, MOP-ów, charakter łuków (promienie zgodne z klasą drogi), mosty; skracamy proste i „puste” odcinki. Granica miasto↔trasa to strefa przejściowa projektowana ręcznie.

Współrzędne: dane autorytatywne w `double` (EPSG:2180 jako roboczy metryczny układ dla Polski — zweryfikuj datum poziomy i **pionowy** NMT), runtime lokalnie w `float` z **floating origin** (przesunięcie świata, pojazdu, naczepy, constraintów, kamer, AI, cząsteczek w bezpiecznym momencie kroku). Chunk streamingu: hipoteza 500 m–1 km, do benchmarku.

## 2. Start: strefa przemysłowa + wylot na trasę

Zadanie sesji (Etap 3/4): przeanalizować OSM i BDOT10k dla Białegostoku (`landuse=industrial`, magazyny, bazy logistyczne) i zaproponować **2–3 kandydatów** obszaru 2×3 km, każdy z: bazą/magazynem z placem i rampami, dużym skrzyżowaniem z sygnalizacją, rondem, wylotem na drogę krajową lub ekspresową, różnorodnym otoczeniem. Dla każdego: mapa (render z własnych danych, nie z Google), jakość tagów OSM (lanes, maxspeed, turn:lanes), dostępność LoD2, uzasadnienie. **Właściciel wybiera.**

Następnie właściciel robi **sesję zdjęciową** wybranego fragmentu (lista ujęć od Ciebie: skrzyżowania z 4 stron, nawierzchnie z bliska, krawężniki, znaki, latarnie, elewacje typowych budynków, ogrodzenia, zieleń, pobocza, wjazdy do zakładów). To jest **najcenniejsze i darmowe źródło referencji** — legalne, aktualne, dokładne.

## 3. Źródła danych (legalne)

| Dane | Źródło | Użycie | Licencja / uwagi |
|---|---|---|---|
| Sieć dróg, nazwy ulic, `ref`, klasy, pasy, `turn:lanes`, `maxspeed`, `oneway`, ronda, mosty, sygnalizacja, przejścia | OpenStreetMap — wycinek `podlaskie` z Geofabrik (`.osm.pbf`) | graf i geometria osi | **ODbL**: atrybucja „© OpenStreetMap contributors”; baza pochodna (graf, GeoJSON) może podlegać share-alike — analiza w `docs/LICENSES.md`, oznacz do przeglądu prawnego przed sklepem |
| Numeryczny Model Terenu (siatka do 1 m, z LiDAR) | GUGiK / geoportal.gov.pl | teren, niweleta drogi, nasypy | bezpłatne — sprawdź warunki konkretnego zbioru i układ wysokościowy |
| Chmury punktów LiDAR (LAZ) | GUGiK | szczegóły terenu, wysokości obiektów, krawężniki (opcjonalnie) | j.w. |
| BDOT10k | GUGiK | klasy dróg, budynki (funkcja), pokrycie terenu, lasy, wody, ogrodzenia | deklarowane bezpłatne, dowolne wykorzystanie |
| Modele 3D budynków **LoD1 (cała Polska) / LoD2 (część powiatów)**, CityGML 2.0 | GUGiK | bryły i kształty dachów | „bezpłatne, do dowolnego wykorzystania” — **sprawdź, czy Białystok jest w zasięgu LoD2** |
| Modele 3D drzew (wybrane powiaty) | GUGiK | rozmieszczenie i wysokość drzew | sprawdź zasięg i warunki |
| Ortofotomapa | GUGiK | referencja pokrycia, kolorów, rozmieszczenia (nie tekstura w grze) | sprawdź warunki |
| PRNG, TERYT, PRG | GUGiK/GUS | nazwy, granice | sprawdź warunki |
| Zdjęcia właściciela | własne | referencje wizualne, tekstury z własnych zdjęć | własność właściciela; uwaga na twarze i tablice rejestracyjne |
| Mapillary | CC BY-SA | **tylko** referencja wizualna dla człowieka/agenta, nie zasób w grze | nie mieszać z danymi ODbL w jednej bazie |

**Zakaz**: Google Maps, Street View, Google Earth, Photorealistic 3D Tiles, Google Elevation — ani jako źródło geometrii, tekstur, wysokości, ani jako podkład, ani „tylko do obrysowania”. Regulamin Map Tiles API zabrania m.in. przechowywania/cache'owania, użycia offline, ekstrakcji geodanych i tworzenia obiektów wyprowadzonych z kafli. Do repo nie trafia żaden plik, zrzut ani mesh z Google.

Nie używaj publicznych serwerów kafli/Overpass jako masowego źródła — pobieraj wycinki plikowe.

## 4. Pipeline `tools/worldgen` (Python) → importer Unity (C# Editor)

1. **Ingest**: pobranie, `Data/SourceManifests/*.json` (URL, data, licencja, SHA256, CRS, zakres, dokładność). Surowe dane w `data/raw/` poza gitem.
2. **Normalizacja**: reprojekcja do EPSG:2180, harmonizacja wysokości, czyszczenie błędów OSM, łączenie z BDOT10k (konflikty raportowane, nie cicho rozstrzygane).
3. **Kanoniczny graf dróg**: stabilne ID (OSM ID + własny UUID), węzły, krawędzie, pasy z kierunkami, `turn:lanes`, zakazy skrętu, ograniczenia (prędkość, masa, wysokość), mosty/tunele/warstwy, priorytety. Każde pole z `provenance` (`source` / `derived` / `default` / `authored_override`) i `confidence`.
4. **Geometria drogi**: oś jako krzywe (klotoidy/łuki), przekrój wg klasy i liczby pasów (szerokości pasów, pobocza, krawężniki, chodniki, ścieżki rowerowe, zatoki autobusowe, rowy), niweleta z NMT wygładzona z limitami pochyleń, przechyłki z uzasadnieniem, **skrzyżowania i ronda generowane jako osobne „junction meshes”** z poprawnymi łukami wyokrąglającymi dla ciężarówki.
5. **Oznakowanie**: poziome (linie, strzałki, przejścia, linie zatrzymania — zgodnie z polskim rozporządzeniem w sprawie znaków i sygnałów drogowych; zweryfikuj aktualny akt) jako decale bez z-fightingu; pionowe z tagów i reguł (pierwszeństwo, limity, kierunkowe z prawdziwymi nazwami), sygnalizacja z fazami.
6. **Teren**: heightfield z NMT, wysoka rozdzielczość tylko przy drodze, wcięcia/nasypy, skarpy, dopasowanie do krawędzi drogi (zero szczelin).
7. **Budynki**: LoD2/LoD1 → bryły + **generator fasad wg typologii** (wielka płyta, kamienica, dom jednorodzinny, drewniany dom podlaski, hala, biurowiec, galeria) z prawdziwą liczbą kondygnacji, rytmem okien, materiałami z referencji. Obiekty charakterystyczne — modelowane osobno (tor A/ŚRODOWISKO).
8. **Otoczenie**: drzewa (gatunki: sosna, brzoza, lipa, klon, kasztanowiec w mieście; olsza i świerk poza nim), trawniki, żywopłoty, ogrodzenia, latarnie (typy białostockie z referencji), wiaty przystankowe, słupy, hydranty, kosze, reklamy (fikcyjne marki).
9. **Kolizje**: osobny, gładki mesh kolizyjny jezdni i krawężników (nie wizualny LOD0), proste collidery budynków.
10. **Metadane nawigacji/AI**: graf pasów (środek pasa, nie oś drogi), połączenia na skrzyżowaniach, sygnalizacja, ograniczenia dla ciężarówek.
11. **Chunki, LOD/HLOD, impostory**, Addressables, manifest regionu.
12. **Raport QA**: brakujące tagi, ostre kąty, zerowe długości, mosty bez `layer`, rozłączone ważne drogi, odchyłki geometrii, szczeliny teren/droga, dziury kolizji — z listą punktów do ręcznej weryfikacji.

Ręczne poprawki: osobne pliki `authored_overrides` (np. GeoJSON/YAML z ID), aplikowane po generacji. **Jeśli generator kłamie — popraw generator**, nie łataj wyniku ręcznie po cichu.

## 5. Kontrola jakości mapy (każdy fragment)
- % sieci zgodnej ze źródłem, rozłączenia, błędy topologii.
- Odchyłka osi drogi od danych (cel: ≤ 1–2 m w mieście; zapisz realny wynik).
- Szerokości pasów sprawdzone liczbą.
- 10–20 punktów kontrolnych: render z gry vs zdjęcie właściciela, status „zgodne / niepewne / odstępstwo + powód” w `docs/map-decisions.md`.
- Streaming: brak dziur i przycięć przy jeździe z prędkością dopuszczalną.
