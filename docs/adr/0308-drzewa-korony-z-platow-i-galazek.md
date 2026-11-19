# ADR 0308 — Drzewa bez „brokułów”: korony z płatów na konarach, atlasy gałązek, topola, drzewa ogrodowe z biblioteki (trees-s24)

Status: Proposed, 2026-11-19 (agent trees-s24; numer zarezerwowany przez lidera).
Powiązane: ADR 0012 (instancing drzew), 0015 / 0023 (HLOD lasu, impostory z normalną), 0088 (igły sosny, okna koron),
0132 / 0163 (drzewa ogrodowe z ortofoto: instancje → karty zestawu działek), 0170 / 0187 (ściana lasu, świerk, młodnik),
0222 (szpalery DK65), 0227 (studium lipy i wierzby w Knyszynie), D73 / ADR 0260 (Windows platformą główną).
Referencje (tylko oglądanie, poza gitem i buildem): Mapillary `Data/raw/mapillary/{knyszyn,knyszyn-dk65-b19,dw671-tykocin-01}`
(CC BY-SA 4.0), Wikimedia Commons `Data/raw/refs/commons-trees/` (CC0 / CC BY-SA, `manifest.jsonl`; Puszcza Knyszyńska —
rez. Wielki Las, pokrój klonu). Żadnych źródeł Google.

## Kontekst

Właściciel (s24): drzewa przydrożne i lasy wyglądają jak „brokuły”. Render „przed” (`artifacts/trees-s24/vqa-before-*`,
High, pogodnie) pokazał trzy niezależne przyczyny:

1. **Drzewa biblioteki** (`make_trees.py`: lipa, klon, brzoza, olsza — szpalery DK65, kępy przydrożne, las liściasty).
   Generator wieszał ~15 kart 1 × 1 m w promieniu 0,3 m od każdej z ~50 krótkich gałązek: korona była garścią gęstych kul
   na gołych konarach z niebem pomiędzy. Tekstury kart (`leaf_textures.foliage`) to okrągłe pompony płaskich krążków.
2. **Drzewa ogrodowe Knyszyna** (3243 szt., ADR 0163): na każdym poziomie treści skrzyżowane karty całej korony
   z gradientem okluzji — z ulicy kula z ciemnym krzyżem w środku.
3. **Świerk** (ADR 0187): konary jednego okółka wychodziły na tej samej wysokości, poziomo, z poziomą kartą —
   widziany z jezdni od dołu był stosem ząbkowanych talerzy.

## Decyzja

### 1. Atlasy gałązek (`tools/worldgen/streetscape/leaf_sprays.py`)
`leaves_{linden,maple,birch,alder,poplar}.png` to atlas 2 × 2 (1024 px) czterech różnych gałązek: oś z odgałęzieniami,
liście naprzemianlegle z blaszką gatunku (sercowata lipa, pięcioklapowy klon, rombowa brzoza, wcięta olsza, deltoidalna
topola), blaszka w dwóch tonach wzdłuż nerwu, ciemniejsze liście pod spodem. Podstawa gałązki leży na środku dolnej
krawędzi komórki, żaden liść nie jest przycięty brzegiem komórki, kolor pod przezroczystością = średni kolor liści (bez
czarnej obwódki w mipach). Brzoza: komórki 0–1 wzniesione gałązki, 2–3 zwisające witki. Rysunek proceduralny (numpy + PIL),
bez zdjęć i skanów. Kolory bazowe bez zmian (przygaszone zielenie, `docs/06`). Długości blaszek i wymiar karty
(`CARD_M`) to `WORKING_VALUE`.

### 2. Korona z płatów (`make_trees.grow_crown`, tabela `CROWN`)
Obwiednia korony na gatunek (promień po wysokości + nieregularność po azymucie, inna na wariant), konary szkieletowe
kończące się na obwiedni, rozgałęzienia; każdy koniec gałęzi to **płat** — karty-gałązki po jego zewnętrznej stronie,
podstawą do gałęzi, 14 % kart między płatem a pniem (brak prześwitu na wylot). Miejsca obwiedni bez płata dostają płat na
cienkiej gałązce od najbliższego konaru. Normalne cieniowania = mieszanka kierunku od środka korony i od środka płata
(bryłowatość bez ciemnego rdzenia). Okna `crown_opening` (ADR 0088) nie są wycinane — przerwy między płatami są
naturalnymi prześwitami. LOD1 jak dotąd: podzbiór kart LOD0 × 1,4 (`reuse_leaf_lod`), impostor 6 widoków.
Nowy gatunek **topola** (`tree_poplar_{0,1}`, 24 m; tylko szpalery / nadpisania — nie wchodzi do mieszanek BDOT).
Sosna: pełniejsze kępy igieł (karty 0,95 → 1,2 m, +1 karta na kępę). Świerk: każdy konar ma własny opad, wysokość
i obrót wokół osi. Stary generator liściastych zostaje pod `--legacy-crowns` (rendery porównawcze).
Wszystkie proporcje (`CROWN`) to `WORKING_VALUE` odczytane z referencji, nie dane dendrometryczne.

### 3. Drzewa ogrodowe = instancje biblioteki na High (`plantings.library_instance`)
Na poziomie High (PC) drzewo ogrodowe liściaste o promieniu korony ≥ 1,6 m jest instancją biblioteki (`tier: high`,
LOD0 / LOD1 / impostor): wysokość taka, żeby korona modelu miała promień z ortofoto, w granicach 0,8–1,3 wysokości
z G7 i pułapu gatunku. Jesion → model lipy, kasztanowiec → model klonu (`WORKING_VALUE`: brak własnych modeli).
Poziom Low zachowuje lekkie drzewo z kart (budżety A16, ADR 0163 bez zmian). Drzewa owocowe i iglaki ogrodowe bez zmian.

## Wyniki (pomiar w edytorze, High, pogodnie, 1920 × 1080; `artifacts/trees-s24/`)

WYNIKI_PLACEHOLDER

## Konsekwencje i otwarte punkty

OTWARTE_PLACEHOLDER
