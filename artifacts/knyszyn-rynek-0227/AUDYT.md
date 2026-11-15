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
