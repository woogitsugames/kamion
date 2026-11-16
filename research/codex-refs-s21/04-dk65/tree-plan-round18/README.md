# S19/DK65 — obejrzany plan i legenda, bez tabeli drzew

Przegląd 2026-11-16, bez dokładnej godziny. **Dwa konkretne dokumenty obejrzane, 0 potwierdzonych numerowanych drzew z gatunkiem.** Cel dendrologiczny pozostaje otwarty; wynik nie jest kolejnym spisem nieotwartych URL.

Użyto istniejącego spisu tree-table-search-round10 z publicznego artykułu gminy [Opinia w sprawie S19](https://dobrzyniewo.pl/aktualnosci/2022/03/22/opinia-w-sprawie-s19/). Znany opis ogólny z tree-inventory-round9 nie został pobrany ponownie. Arkusze 2-00 i 2-01 nie były w lokalnym raw tego pakietu; pobrano je pojedynczo po HEAD potwierdzającym application/pdf i rozmiary poniżej limitu 25 MB. Bez ZIP, nowych indeksów, Google, OSM/Overpass, Commons i Chrome.

**SOURCED [rys. 2-00, jedyna strona, blok „Zieleń”, osobisty ogląd renderu]:** legenda wyróżnia zieleń do adaptacji, łąkę antysmogową, drzewa, krzewy, karpy, kłody i głazy. Drzewo oznacza zielony obwód z małym krzyżykiem wewnątrz, krzew — nieregularny zielony obwód. Arkusz nie przypisuje tym symbolom nazw gatunków, obwodów ani numerów pni. Sekcja geodezyjna oddzielnie definiuje numery działek; sekcje instalacyjne mają własne oznaczenia kolizji. Nie wolno ich przepisywać jako ID drzewa.

**SOURCED [rys. 2-01, jedyna strona, osobisty ogląd pełnego renderu]:** rzeczywisty rysunek projektowy pokazuje rondo na lewym fragmencie, osie/łącznice dróg, układ dwujezdniowy biegnący w prawo i drugie skrzyżowanie bezkolizyjne. Widać etykiety DK65, kierunki Ełk/Knyszyn oraz Dobrzyniewo/Białystok. Przy pasach dróg występują grupy i rzędy zielonych symboli drzew zgodnych z legendą. Są też powierzchnie o odrębnym zielonym kreskowaniu. **Nie odczytano przypisanych do pojedynczych symboli ID lub gatunków.** Nie wyprowadzono z rysunku liczby istniejących drzew, stanu wycinki ani rozstawu pni.

**SOURCED [metryki obu rysunków]:** marzec 2022, rewizja 00, projekt budowlany/materiały do opinii dla wniosku ZRID, inwestor GDDKiA, jednostka Value Engineering. Skala deklarowana 1:1000. Arkusz 2-01 podaje zakres projektowego km 24+800–25+950; to kilometraż projektu S19, nie państwowy kilometraż DK65. Danych osób i podpisów nie przeniesiono do repo.

Opis z round9 datował ogólną inwentaryzację zieleni na sierpień 2021. Ta data **nie dowodzi**, że każdy symbol planu 2-01 jest pomierzonym wówczas pniem, ani że plan nie pokazuje nasadzeń/projektowanych elementów. Klasyfikacja konkretnego symbolu jako istniejącego, do usunięcia lub nowego nasadzenia pozostaje UNVERIFIED bez osobnego opracowania dendrologicznego i tabeli.

Wniosek dla generatora: plan przydatny jako **historyczna dokumentacja projektowa układu drogowego i sposobu oznaczania zieleni**, nie jako źródło gatunków lub dokładnej alei DK65. Nie utożsamiać go ze stanem powykonawczym 2026.

Surowe PDF oraz pełne rendery tylko w autoryzowanym Data/raw/refs/codex-s21/04-dk65/tree-plan-round18. Do gita wyłącznie własny opis, manifest i metadane. Prawa: publiczne dokumenty udostępnione przez gminę, brak automatycznie przypisanej CC; nie redystrybuowano skanów, map ani podpisów. Ogląd według skilla PDF, read-only. Pypdf odczytał legendę; na rozbudowanym planie osiągnął limit złożoności strumienia, więc tekst i render odczytano pypdfium2 bez zmieniania PDF.
