# Odczyt istniejących atlasów podczas oczekiwania D

Obejrzano oba istniejące pliki 512 × 512: hedge_shell_berberis.png i hedge_sprig_berberis.png. Nie zmieniono tekstur ani kodu produkcji. Dokładne SHA-256 i odczyty są w atlas-cover-readonly.json. Mały odczyt Pillow oraz histogramów alpha trwał około 0,31 s; bez World, GIS, Unity i urządzeń.

Próg alpha > 127 odpowiada odczytowi surowych texeli przy nominalnym alpha_cutoff 0,5 materiału. Shell ma 72,789% takich texeli, atlas sprig 32,777%. Istniejący atlas sprig jest rzeczywiście atlasem czterech skupisk pędów z liśćmi, rzadkimi końcami i gęstszą podstawą. Kod _fill_rgb uzupełnia kolor przezroczystych texeli dla mipów, ale nie czyni ich nieprzezroczystymi. Sam podgląd RGB nie jest miarą pokrycia.

Sprawdzono także pasy atlasu odpowiadające części karty powyżej lokalnie płaskiego capu, przy a.z = 0 jak w obecnej funkcji. Dla zagłębienia C 25% jest to górne 192 wiersze komórki 256 px, a dla D 45% górne 141 wierszy po zaokrągleniu. W tych pasach udział texeli powyżej progu wynosi odpowiednio 24,46–30,37% w C i 20,24–25,94% w D, zależnie od komórki. Głębsze schowanie usuwa część gęstej podstawy, nie tylko pusty brzeg.

To są proporcje alpha we wskazanych pasach tekstury, nie udział powierzchni ekranu ani całej rabaty. Nie uwzględniają faktycznego przecięcia reliefu, projekcji, zasłaniania, mipów, klipu ani oświetlenia. Większa projekcja quada D może zwiększyć widoczne liście, ale test geometrii nie dowodzi skali tego wzrostu. Nie uznawać tych liczb za ocenę D ani za podstawę automatycznego zagęszczania kart.

Jeżeli D po renderze ograniczy sterczące pędy, lecz pozostawi gładkie odstępy, kolejny krok powinien rozważyć charakter maski/UV skupiska liści, zamiast samego zwiększania wysokości lub liczby kart. Możliwości wymagające osobnej próby to własny atlas w hedge_textures.py z kontrolą korzystających z niego pędów brzegowych albo użycie już istniejącej warstwy shell z właściwą skalą UV na niskiej pokrywie. Żadnej z tych zmian jeszcze nie wdrożono. Obecna kolejka D musi zachować swoją wersję źródeł i dostarczyć rzeczywiste obrazy.
