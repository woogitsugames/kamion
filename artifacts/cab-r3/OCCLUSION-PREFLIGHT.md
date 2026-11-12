# Audyt geometrii lusterek — przygotowanie kolejnej rundy

Odczyt gotowego prefabu night1, bez zmiany geometrii lub zapisu scen. Low: exterior LOD2, interior LOD0; High: exterior LOD0, interior LOD0. Szkło z rzeczywistymi UV, oko DriverEyePoint. Po 2400 próbek na cztery boczne lustra, z czego 1944 w zakresie UV 0,05–0,95 obu osi. To centralne 90% szerokości i wysokości, nie 90% pola.

Kontrolny trójkąt potwierdził działanie raycast i maski warstwy w obu stanach; w audycie zbudowano 54/58 nieprzezroczystych slotów. Użyto tymczasowej sceny Editor i wolnej warstwy zapytań, z odrzucaniem cudzych trafień. Przezroczyste szyby i dekale nie są modelowane jako pełne przeszkody. To geometria, nie GPU, piksele, procent powierzchni w projekcji ani akceptacja R46.

Wynik przednich stron trójkątów identyczny dla Low i High: MainL 64/2400, MainR 64/2400, WideL 105/2400, WideR 127/2400. We wszystkich centralny zakres ma 0/1944 trafień. WideR: 101 trafień CAB_Body/MI_Ext_Trim, 14 DOOR_R/MI_Ext_Trim, 12 CAB_Interior/MI_Cab_Rubber. Obejrzane diagramy pokazują je przy obwodzie, a gumę i trim drzwi w dolnym narożniku.

Po włączeniu trafień w tyły trójkątów WideR ma 238/2400, w tym 47/1944 centralnie; dodatkowe trafienia pochodzą z DOOR_R. Odpowiednie shadery CabInterior i TruckExterior deklarują Cull Back, więc wyniku dwustronnego nie wolno utożsamiać z obrazem renderowanym. Potrzebna jest jeszcze weryfikacja maską GPU z oka kierowcy, zanim zmienimy geometrię. Nie potwierdzono szerokiej fizycznej okluzji środka szkła przez gumowy kanał.

Diagramy uv-*-front.png i uv-*-two-sided.png są siatką UV 40×60 powiększoną bez interpolacji, nie zdjęciem lub renderem lustra. Zielone: brak trafienia przed szkłem; pomarańczowe: pozostały trim; czerwone: drzwi; niebieskie: rubber. Szczegóły i przykładowe punkty/triangles: occlusion.tsv, owners.tsv, hit-samples.tsv.

Następna runda powinna rozdzielić rzeczywiste zasłonięcie powierzchni od ciemnego elementu odbijanego w RT. Nie zmieniono położenia oka, pól widzenia, kamer, ramki ani kanału na podstawie samej recenzji lub pomiaru dwustronnego.
