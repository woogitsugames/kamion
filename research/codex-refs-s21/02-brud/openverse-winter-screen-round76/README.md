# R76 — jedna kwerenda Openverse, bez nowych kadrów

2026-11-16. Normalny publiczny frontend Openverse zadziałał. Wykonano **jedną frazę `trailer snow`**; przejście z „All content” do „Images” nie zmieniało frazy. [Dokładna kwerenda obrazów](https://openverse.org/search/image?q=trailer+snow&license=cc0,by,by-sa).

W panelu rzeczywiście sprawdzono zaznaczone **Zero / Attribution / Attribution-Share-Alike**. Public Domain Mark, NC i ND pozostały niezaznaczone. Sam filtr nie jest jeszcze weryfikacją licencji w pierwotnym źródle pojedynczego obrazu.

UI deklarował „Top 240 results” dla obrazów. Obejrzano **40 podglądów siatki**: pierwsze 20 i jedną dalszą partię po „Load more results”. Dominowały kempingi, namioty i pojazdy terenowe. Widoczne pojazdy ciężkie obejmowały widok od przodu/boku oraz boczną cysternę; żaden podgląd nie wskazał czytelnej brudnej pary drzwi naczepy w śniegu. Nie wybierano nietrafnych obrazów do indywidualnego opisu i nie otwierano kolejnych źródeł tylko dla liczby kandydatów.

**0 konkretnych kandydatów do przyjęcia, 0 indywidualnych pełnych oglądów, 0 nowych A/B/zimowych/europejskich, 0 AUX i 0 pobrań.** Autor, licencja i data pojedynczej fotografii nie były weryfikowane, bo żadnej nie przyjęto. Nie wolno odczytać tego logu jako negatywnego dowodu dla wszystkich 240 wyników lub całej kolekcji Openverse.

Nie ponawiano wcześniejszego API 403, nie wywoływano API, nie pobierano Flickr/Commons i nie zapisywano screenshotów. Poprzedni obieg `openverse-browser-round5` dotyczył innych fraz i błędu frontendu; niniejsza kontrola nie nadpisuje jego wyniku. Manifest zawiera jeden rekord dokumentacyjny, bez wzrostu liczby zdjęć. Bez zmian parenta i operacji Git.
