# Palety — referencje kształtu do następnej rundy

To preflight life r3, bez zmiany produkcji w r2. Mapillary (lokalne 12 + nowe 16) i Panoramax nie dały użytecznych zbliżeń palet na wybranych placach. Poniższe zdjęcia są referencją ogólnej konstrukcji, nie rozmieszczenia w Białymstoku ani kalibrowanego koloru.

- pallet-stack-7-cc0.jpg: W.carter, zdjęcie z 31.03.2017, Grötö/Lysekil (Szwecja), CC0 1.0. [Strona źródłowa](https://commons.wikimedia.org/wiki/File:Wooden-pallets_stacked_7.jpg), [licencja](https://creativecommons.org/publicdomain/zero/1.0/). Pobrana miniatura Commons 960×603, SHA256 6dab6517efde79c9c64c205fe53c96665c5f9800e98951be838d48557982ae45. Widać prześwity między deskami i klockami oraz wyraźną różnicę wieku/szarzenia drewna. Nie kopiować pieczęci/logo do modelu.
- pallet-stack-1-cc0.jpg: W.carter, zdjęcie z 31.03.2017, ten sam obszar, CC0 1.0. [Strona źródłowa](https://commons.wikimedia.org/wiki/File:EUR-pallets_stacked_1.jpg). Pobrana miniatura 960×540, SHA256 415dbbbf08430d394da993b29f45b465fd39016920554112616d5634849b9759. Widać otwarte wejścia na widły z obu stron stosów, nierówną barwę i niewielkie przesunięcia warstw. Obejrzano oba obrazy.

Konstrukcja ogólna: [oficjalna strona EPAL](https://www.epal-pallets.org/eu-en/load-carriers/epal-euro-pallet) podaje 800×1200×144 mm, 11 desek i 9 klocków. To źródło wymiarów i budowy, nie zgoda na używanie oznaczeń certyfikacyjnych. Układ własnego modelu pozostanie bez marek i pieczęci. Dane rozmieszczenia istniejących stosów nie wynikają z tych fotografii.

Potwierdzone odstępstwo źródła life_props.pallets_empty: każdy LOD0 jest stosem pełnych prostopadłościanów, a LOD1 jednym pełnym blokiem. Referencje pokazują duże prześwity. Przed zmianą należy znaleźć czytelne kamery rzeczywistych instancji, zmierzyć budżet i wybrać uproszczenie, które zachowa otwory z bliska bez nowych grup materiałowych. Nie wykonano jeszcze takiej zmiany ani renderu palet.

Dodatkowy preflight materiału: M wskazuje euro_pallet_side, którego nie ma w bieżącym materials_spec. Natywny materiał używa WorldSurface i ma przypisaną BaseMap, więc sam brak zestawu PBR NIE dowodzi braku tekstury ani wyglądu bloków. Odpowiedni dowód: ../pallet-material-preflight.json. Odbiór wyglądu wymaga dopiero kamer r3.
