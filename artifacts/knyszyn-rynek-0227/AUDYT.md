# Audyt Knyszyna — stan roboczy

Zdjęcia właściciela są lokalne i nie stanowią tekstur ani materiału do publikacji. Położenia kadrów bez GPS są ESTIMATED.

| Zdjęcie | Co widać | Co jest w danych gry | Różnica / stan weryfikacji |
|---|---|---|---|
| 20240730_190331 | Pionowe strumienie fontanny w płaskiej płycie, kostka w łukach, wysokie drzewa | Override `rynek-fountain-plate` tworzy płytę; `rynek-plaza-east` używa `yard_paving` | Strumienie i kostka łukowa nie są modelowane według opisu override; render baseline oczekuje na import. |
| 20240730_190828 | Szeroki plac z łukami kostki, fontanna, drzewa i monument | Granica placu i las parkowy jako authored overrides | Należy porównać kształt, monument, drzewa oraz nawierzchnię na renderze. |
| IMG20240729165956 | Prostokątna płyta fontanny, centralny wysoki strumień i niższe dysze, ciemne obrzeże | `yard_slabs`, brak geometrii wody według override | Układ dysz, obrzeże i materiał do sprawdzenia; wymiary WORKING_VALUE. |
| 20250729_182511 / 182513 / 182516 | Kremowo-szara elewacja, białe okna, czerwone rynny, dach i lukarny | Zabudowa generowana z BDOT/LoD; przypisanie konkretnej bryły jeszcze nieustalone | Lokalizacja i fasada ESTIMATED, wymagają dopasowania do ortofoto oraz renderu. |
| 20251031_122316(0) | Ta sama zabudowa z ulicy, chodnik, słupy i przewody | Generator ulic i zabudowy | Kadr i lokalizacja niezweryfikowane; porównanie po ustaleniu położenia. |

K1 podaje fontannę OSM 32 m² (~6 × 6 m), natomiast istniejący override przyjmuje ~9 × 7 m. Nie rozstrzygnięto rozbieżności bez pomiaru i dokładnego dopasowania ortofoto.
`paved.collect` obsługuje authored polygons w kolejności wpisów: `rynek-plaza-east` wyprzedza w pełni zawartą płytę fontanny, więc odejmowanie zajętej powierzchni usuwa płytę. Wniosek z kodu, do potwierdzenia renderem baseline; właściwa kolejność to najpierw detal, potem plac.

**P0 — położenie fontanny:** wycinki GUGiK `J_rynek_W_north.jpg` oraz `J_rynek_knyszyn_north.jpg` pokazują, że kwadratowa płyta znajduje się na okrągłym placu w zachodnim parku, a nie na wschodnim placu po drugiej stronie Grodzieńskiej. Korelacja wspólnego fragmentu obu wycinków (`align.py`, 0,1 m/px) daje orientacyjny środek fontanny EPSG:2180 ~760943,5 / 612382,3 (ESTIMATED, wymaga kontroli naroży i OSM). Dotychczasowy override ~761035,7 / 612396,9 leży około 93 m dalej. Wcześniejsze przypuszczenie o samej kolejności nakładających się pól pozostaje prawdziwe dla tego błędnego położenia, lecz nie rozwiązuje lokalizacji.

## Korekta geometrii do r2
Niezależne dopasowanie ortofoto: przesunięcie wycinków 1000/248 px, korelacja 0,929. Środek centralnego placyku wstępnie EPSG:2180 (760941, 612388), promień ~12 m, niepewność ±3–5 m; płyta fontanny (760943,5; 612382,3) nie leży w środku. Ośmiokąt roboczy: (760941,612400), (760949,5,612396,5), (760953,612388), (760949,5,612379,5), (760941,612376), (760932,5,612379,5), (760929,612388), (760932,5,612396,5). Krawędzie zasłonięte koronami; to ESTIMATED.
Osie alejek ESTIMATED: SW (760883,612375)–(760930,612383); NE (760950,612385)–(760980,612393); NW (760905,612411)–(760935,612391); N (760940,612420)–(760939,612397). Wymagają porównania renderu i oryginalnego ortofoto.

## Pierzeja — audyt zdjęć i adresów
Zdjęcia 3/4 potwierdzają urząd `bdot:2002917F-46DC-5C99-E053-CC2BA8C01CFC` i skrzydło kultury `bdot:2002917F-4817-5C99-E053-CC2BA8C01CFC`: jasny krem, żółte opaski, czerwony dach z lukarnami. Zdjęcia 5–7: kościół `bdot:2002917F-8DAE-5C99-E053-CC2BA8C01CFC`, biały, czerwony dach i hełm. Identyfikacja SOURCED obrysem i zdjęciem, proporcje detali ESTIMATED.

Pary adres OSM → obrys BDOT (położenie SOURCED, wygląd poszczególnych fasad UNVERIFIED): Rynek 1 → `2002917F-3002-5C99-E053-CC2BA8C01CFC` (LoD1 7,50 m); Rynek 2 → `2002917F-3031-5C99-E053-CC2BA8C01CFC` (5,98 m); Rynek 3 → `2002917F-3066-5C99-E053-CC2BA8C01CFC` (6,77 m); Rynek 4 → `2002917F-2D30-5C99-E053-CC2BA8C01CFC` (7,79 m); Rynek 5 → `2002917F-3078-5C99-E053-CC2BA8C01CFC` (6,18 m); Rynek 9 → `2002917F-2E16-5C99-E053-CC2BA8C01CFC`. K1-P19 może pokazywać Rynek 9, lecz geotag dotyczy aparatu, a azymut i aktualność fasady są UNVERIFIED. Nie przypisywać kolorów po samym geotagu ani niejednoznacznym tytule K1-P02.
