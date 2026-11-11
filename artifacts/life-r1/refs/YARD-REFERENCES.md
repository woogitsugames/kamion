# Referencje pojazdów placowych do następnej rundy

To preflight r2, bez zmiany modeli produkcyjnych w r1. Obrazy oglądano w szerokości do 960 px. Pochodzą z istniejących lokalnych plików wymienionych w docs/REFERENCES.md; strony źródłowe sprawdzono ponownie 11 listopada 2026.

- `yard-side-reference.jpg`: Jk20301, [Krone Tautliner](https://commons.wikimedia.org/wiki/File:Krone_Tautliner.jpg), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Lokalna miniatura zmniejszona do 960 px; ta pochodna zachowuje CC BY-SA 4.0. Oglądany bok potwierdza trzy oddzielne koła, prześwity między nimi i krótkie chlapacze. Otwartej plandeki ani oznaczeń handlowych nie przenosi się do gry.
- `yard-34-reference.jpg`: Cekay, [WieltonCurtainSider](https://commons.wikimedia.org/wiki/File:WieltonCurtainSider.jpg), [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Lokalna miniatura zmniejszona do 960 px. Widać trzy oddzielne osie, ciemne szczeliny, fałdy przy górnej listwie i klamrach oraz kontakt kół z podłożem. Źródło ma logo i reklamy; służy jedynie analizie geometrii i powierzchni, nie jest teksturą gry.
- Dodatkowa istniejąca referencja: Ra Boe, [Auflieger tautliner 01](https://commons.wikimedia.org/wiki/File:Auflieger_tautliner_01.jpg), CC BY-SA 2.5; w tej fazie nie utworzono nowej kopii w artifacts.

Lokalny plik `trailer_WieltonCurtainSider.jpg` ma SHA-1 `9065b4af7c071bbe13e8840d64ada7f76c4d3948`, różny od oryginału Commons `b7b66d624d951144b08d472dde8e3c765849f89e`. docs/REFERENCES.md przypisuje lokalny plik do tej strony źródłowej. Nie ustalono zastosowanej obróbki; nie deklarujemy zgodności bajtowej z oryginałem ani kalibrowanej fotometrii.

Największy potwierdzony problem do sprawdzenia na renderze r2: LOD1 naczepy ma po jednym długim graniastosłupie opony na stronę (24 trójkąty w materiale tyre), podczas gdy na referencjach są trzy oddzielne koła. Kandydat powinien zachować jedną grupę materiałową, rozstaw osi i obrys zestawu. Koszt trójkątów należy zmierzyć dla wszystkich kamer, a nie przyjąć z oszacowania. Nie zmieniono jeszcze life_props.py ani rozmieszczenia pojazdów.
