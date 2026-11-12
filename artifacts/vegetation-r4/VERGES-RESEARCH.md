# Oglądanie źródeł poboczy podczas kolejki baseline

Obejrzano pięć rzeczywistych fotografii wskazanych w recenzji s10-gpt-JK. Arkusz verges-reference-overview.jpg ma szerokość 960 px; daty, autorzy, licencje i SHA oryginalnych plików są w verges-reference-research.json. To badanie wyglądu, bez zmiany produkcji. Nie są to tekstury gry ani referencje AI.

1528935774382039, strudeel, 2024-08-15: obok chodnika i krawężnika widać nierówny pas wyższych źdźbeł i roślin, a przy ogrodzeniu gęstą masę zieleni. Nie jest to jednolity, wykoszony pas od jezdni do granicy działki. Poza ma klasę C, więc obraz nie wystarcza do przypisania tych kęp do dokładnych współrzędnych świata.

500263111404933, richlv, 2020-08-15: przy barierze pod wiaduktem jest wyraźna warstwa wyższej zieleni, inna niż gładki trawnik. Ziarno i wysokość źdźbeł wymagają pokrywy i sylwetki; sama korekta tonu trawy tego nie odtwarza. Poza C ogranicza wnioski przestrzenne.

320326319617139, richlv, 2020-08-15: trójkątny narożnik przy słupkach pod wiaduktem ma jasną ziarnistą odsłoniętą powierzchnię z nierówną niską roślinnością. To jedyna poza B w tej piątce. Po zamknięciu r4 warto porównać ten konkretny fragment z własnym plantings.py i świeżym renderem, zamiast dodawać beżowy obrys do wszystkich trawników. Nie uznano jeszcze, że obecny model lub materiał tego miejsca jest błędny; potrzebne jest porównanie na aktualnym baseline.

209622370971977 i 468026894483428, richlv, 2020-08-15: wzdłuż muru oporowego widać rytm młodych drzew oraz niską, nierówną pokrywę pod nimi. Brak rytmu drzew jest osobnym problemem rozpoznawalności, którego sam odcień lub szum trawy nie naprawi. Obie pozy są C. Nie mapować nowych pni na podstawie tych kadrów; potrzebne są poprawione pozy i sprawdzenie ortofoto.

Zdjęcia nie dowodzą chemicznej natury jasnych śladów przy krawężniku. Sól pozostaje UNVERIFIED. Zestaw obejmuje lato 2020 i 2024, więc nie jest dowodem wariantu listopadowego. Widocznych różnic między miejscami nie należy zastępować jedną globalną regułą brudu lub wysokości trawy.

To przygotowanie backlogu. R4 nadal dotyczy berberysu, a produkcja czeka na ukończenie świeżego baseline. Badanie nie uruchamia GIS, World ani Unity i nie zastępuje ich walidacji.

## Kontrola na świeżym baseline r4, około 10:27

Obejrzano pełny wyprostowany obraz `references/sbs-g3-a-320326319617139.png` oraz świeży `before/Low-overcast-photo-2048x1536/sbs-g3-a-320326319617139.png`. Na fotografii przed słupkami widać jasny, ziarnisty trójkąt z drobnymi roślinami, połączony z przebiegiem chodnika pod wiaduktem. Render pokazuje w tym obszarze dużą trawiastą wyspę; nie odtwarza tego samego układu chodnika i narożnika. Różnią się także skala i położenie podpór oraz wysokość pomostu w kadrze. To podważa użycie nawet oznaczonej jako B kamery do bezpośredniego przeniesienia obrysu z pikseli na teren.

Aktualne QA plantings już zawiera wyspę `biezenstwa-plantings:island1` o `fill: gravel`, 996,9 m². Sama obecność zieleni w tym renderze nie dowodzi więc braku reguły żwiru w generatorze. Przed kolejną zmianą potrzebne jest zidentyfikowanie tej konkretnej wyspy w danych i ortofoto oraz zgodność pozy. Nie wolno zamieniać całej widocznej trawy na żwir ani poprawiać geometrii chodników należącej do Claude na podstawie tego kadru. Dokładny obrys i udział pokrywy pozostają UNVERIFIED; sól nie ma dowodu.
