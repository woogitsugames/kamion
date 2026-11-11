# Samokontrola wizualna

Obejrzałem wszystkie 20 arkuszy przed i 20 po (236 klatek każdej macierzy), wybrane Low/High lowsun, końcowe Medium clear/lowsun i oryginalne cropy. Wszystkie arkusze mają maksymalny wymiar 960 px. Osobny root obejrzał całą końcową macierz i nadał scoped PASS.

- High: zniknął regularny deseń drobnego ditheringu nieba wzmacniany LUT/RCAS. Zachowany końcowy dithering wygładza gradient; odrzuciłem wariant obu ditherów wyłączonych z widocznymi pasami.
- High clear: jasny szczyt domu zachowuje kolor i spada do 240.836/229.444/195.223. To około 240, nie ścisłe ≤240. Asfalt w stałym ROI lekko jaśnieje o około 0.23 poziomu.
- Zysk gładkości ma cenę: przy 70% proxy krawędź oznakowania jest o 0.333 piksela szersza, okno łagodniejsze; cyfra 0 pozostaje czytelna. Nie deklaruję braku utraty ostrości. Mały napis jednostki był miękki w obu wariantach.
- Hala: duże trójkątne plamy zmniejszone; wąski rzeczywisty cień ram nadal różni się o 6.59 poziomu od osobnego wariantu realtimeOff. Kontakty naczep są identyczne względem kontrolnego obrazu tej samej polityki. 12 cm było zbędnie płaskie; przyjęte 8 cm ma węższy zakres.
- Low: układ światła i chmur pozostał taki sam; pełne statystyki obu warunków są identyczne. Część PNG różni się na rzadkich krawędziach roślin, co sprawdziłem na obrazie z zaznaczonymi różnicami; nie przypisuję tym różnicom zmiany oświetlenia.
- Pod mostem już świeża baza miała silne occlusion i widoczny cień. Świeży bake ma sky-vis0.043 w osi i 1 poza mostem; pozostawiłem istniejący algorytm, żeby nie pogłębiać cieni bez przyczyny.
- Mgła wysokościowa r11 została zachowana. Kominy instancji w `photo-biezenstwa-ground` leżą około410/478m od kamery i na pełnych arkuszach są osłabione względem bliskich obiektów. Automatyczne próby pomiaru słupów zawierały przesłonięte punkty; nie używam ich jako dowodu poprawnej kalibracji kontrastu.

Referencje z lokalnego zbioru Commons: `cm121537432.jpg` (realny tynk i jasna ściana), `cmFile_Bus_lanes_in_Bia_ystok_Sienkiewicza_.jpg.jpg` (pochmurna ulica), `cm146192544.jpg` (odległe elementy przez atmosferę). To odniesienia z różnych miejsc i warunków; klatki nie są wyrównanymi rekonstrukcjami tych zdjęć. Referencje wyświetlono w `references/` i porównano z arkuszami. Zbiór statystycznych kandydatów overcast zawiera różne ekspozycje/pory roku; luka116–121 jest zakresem odniesienia, nie pomiarem identycznego dnia.

Wciąż bardziej regularne od zdjęć pozostają ściany, roślinność i część odbić. Kalibracja KP/noise-wall jest poza C i należy do lidera ADR0101; remiza do E, roślinność do B, pojazdy do F/G. Nie dodawałem sztucznego ziarna. Telefon GPU, termika, ruchome migotanie i właściwy device EASU pozostają UNVERIFIED; floor to RT/bilinear proxy. Po wspólnej integracji potrzebny jest ponowny przegląd.

Pierwsza próba odświeżenia fixture zakończyła się rzeczywistym `FileNotFoundException` brakującego ignored interiorLOD0 FBX. Uzupełniłem wyłącznie 11.5MB cache z main; retry builderów oraz pełny EditMode221/221 zakończyły się poprawnie. Macierzy dopasowanych obrazów nie nadpisano nowym cache pojazdów.
