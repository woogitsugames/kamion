# Niezależny visual-critic — runda 4

**Werdykt: FAIL dla deklaracji dużego skoku realizmu całej sceny / fotograficznej bramki docs/06. Lokalna poprawa materiałów i detali z kamery jazdy: PASS.** Nie jest to potwierdzenie pełnego DoD zadania.

Obejrzano arkusze wszystkich 28+28 pełnych kadrów Low/High, porównania przed/po, wybrane pełne kadry w szerokości960px oraz sześć rzeczywistych par detali (trzy kamery × dwa tiery) i pomocnicze wycinki. Referencja: dwa zdjęcia CC0 Rakoon z reference.jpg. Oceniano obrazy, nie sam sukces generatora.

| Priorytet / stan | Lokalizacja i ocena | Wniosek |
|---|---|---|
| P1 — pozostały próg jakości | Zwykłe kadry cab-gate, stretch-01, DK8 oraz Andersa/Putry nadal są zdominowane przez bardzo regularne duże powierzchnie i uproszczone korony. | Zmiany nie uzasadniają deklaracji, że cały świat uzyskał fotograficzny realizm lub duży skok jakości. Potrzebny dalszy osobny look-development; nie należy maskować tego zwiększeniem liczby śmieci/roślin. |
| Lokalna poprawa — PASS | Trawa przy route-putry-approach, driver-andersa-to-putry i trzech kamerach detali: fotograficzna baza zastępuje dawną grubą zieloną modulację drobniejszą niejednorodnością zieleni/brązu. | Zmiana jest teraz widoczna również w pełnym kadrze jazdy; najsilniejszy efekt rundy4. Pozostaje powierzchnią płaską i nie odtwarza wszystkich źdźbeł ani rozległych łat odkrytej ziemi ze zdjęć. |
| Lokalna poprawa — PASS z ograniczeniem Low | Wpust przy krawężniku zachowuje rozmiar/pozycję i ma fotograficzną kratę. Studzienka w pasie jest czytelna na High, na Low ma mały kontrast luminancji. | Low studzienka **jest obecna** jako blady brązowy owal; początkową hipotezę braku obiektu z małej miniatury odrzucono po kontroli rzeczywistego PNG i ROI. Nie zwiększać wymiarów dla efektu. |
| P2 — Low uproszczenie roślinności | Elderberry przy kamerze verge: po kalibracji ma rozpoznawalną roślinną teksturę; Low daje gęstszy, ciemniejszy kontur od bardziej ażurowego High. | Lokalnie lepiej od jednolitej czarnej plamy; nadal widoczny kompromis LOD. Pojedyncze nieruchome kadry nie potwierdzają płynnego przejścia LOD podczas jazdy. |
| Regresja rundy1 — usunięta | Najbliższy krawężnik/niska ściana w g3b-rondo-putry-approach ponownie zachowuje PBR relief, brud i rytm podziałów. | Nie ma już rażącego pogorszenia do sterylnej jasnej belki. |

Kontrola studzienki w oryginalnych PNG, środekROI(1170,760): średnieRGB Low86,9/78,3/70,5 przy sąsiednim asfalcie81,9/80,2/77,5; High62,0/53,0/44,7 przy88,2/87,0/85,2. To porównanie zapisanych pikseli w różnych profilach renderingu, nie pomiar fizycznego albedo.

Zdjęcia pokazują niskie krawężniki, lokalnie przesuszoną/skoszoną trawę, odsłoniętą ziemię oraz smukłe nieregularne drzewa. Nowe drobne zróżnicowanie trawy i oszczędne detale idą w tym kierunku. Ciemne uproszczone korony i powtarzalna struktura otoczenia pozostają widocznym ograniczeniem całej sceny. Mokry maj i słoneczny czerwiec służą tu do porównania geometrii/rozmieszczenia, nie narzucają koloru odbicia dla overcast.

W obejrzanych kadrach nie stwierdzono oczywistego nowego olbrzymiego skanu, blokady jezdni, unoszącego się krzaka, neonu ani jawnego logo. Ta obserwacja nie sprawdza każdego obiektu w regionie. Brak telefonu w zakresie zadania: jakość i stabilność klatek na SamsunguA16 pozostają UNVERIFIED.

Koszt: Low szczyt zestawu pozostaje956draw/333ktris, ale pojedyncze kadry rosną do+4draw/+4ktris; High lokalnie do+8draw/+20ktris. Są to szacunkiCPU przed SRP, nie licznikiGPU. Niezmieniony szczyt zestawu nie oznacza zerowej regresji każdego kadru. Odziedziczone porażkiGIS pozostają oddzielną niespełnioną bramką; ten raport ich nie znosi.
