# Ogląd pozostałych stanów SBS r4

COMPLETE: fizycznie obejrzano wszystkie 75/75 natywnych raw (25 Low-clear, 25 High-clear, 25 High-overcast) oraz te same 25/25 zdjęć źródłowych z recognition-native-request.json. Każda partia obejmowała źródło i trzy raw jednej kamery przez view_image. Nie oglądano przyszłych arkuszy zamiast raw. SHA zdjęć zgadzają się z manifestem; pełne ścieżki i SHA wszystkich par są w other-states-visual-inspection.json. Checkpointy zapisano po 15, 30, 45 i 60 raw.

Są to stare, zamrożone piksele HEAD80159a70e7cea39146a465208da5471cb9beb915. Upstream ADR0130 nie jest w nich obecne. To ogląd pozostałych stanów, nie nowy wynik D51. Zamknięte oceny Low-overcast i rejestr pozostają bez zmian.

- High poprawia ostrość cienkich elementów, napisów, fasad i odległych kominów. Dla B227953/B837235/B297817 ma ażurową kratownicę zamiast pełnej ramy Low; B381800 nadal ma pełną ramę także High. B275528 jest ażurowy w obu tierach. To lokalnie istotne różnice charakterystycznego obiektu, nie samo niebo.
- Clear dodaje silne cienie balustrad i portali; High-overcast ma mniejszy kontrast odległych drzew, kominów i zabudowy. W obejrzanych kadrach nie stwierdzono zmiany przebiegu głównej jezdni wskutek samego przełączenia światła.
- Lepszy detal High nie rozwiązuje rozbieżności projekcji B328135/B275528/B297817, nosa/U3 B837235, pierzei B150280 ani wysokości/początku ekranów B494288/B180137. Rozróżnienie udziału pozy i świata wymaga dalszej kalibracji.

Obserwacje per kamera (obejmują wszystkie trzy stany):

- sbs-g3-a-2818555625124739: High wyostrza balustrady, elewacje i kostkę; clear daje mocne ażurowe cienie. Czerwona belka i łuk drogi zachowane; duża brukowana wyspa zamiast kamienistej oraz różnice filarów pozostają we wszystkich stanach.
- sbs-g3-a-3970163613102941: High poprawia krawędzie, napis tablicy i detale fasad, clear uwydatnia cień poręczy. We wszystkich stanach tablica i rytm najbliższych podpór różnią się od zdjęcia, wyspa pozostaje brukowana.
- sbs-g3-a-149248627179406: Tablica wysunięta znacznie bliżej niż na zdjęciu w każdym stanie. High czytelniej pokazuje tekst i poręcze; clear nie zmienia układu jezdni i podpór, tylko cienie.
- sbs-g3-a-177786140912399: Ogromny bliski C9 i brak odpowiadającego mu najbliższego filara w projekcji utrzymują się w trzech stanach; High ostrzej pokazuje wieżowiec i wysepkę, bez rozwiązania zastrzeżenia pozy.
- sbs-g3-a-178689077481862: Wieżowiec, most i łuk jezdni pozostają czytelne we wszystkich stanach; High doprecyzowuje okna i balustrady. Układ bliskich filarów, C9 i brak bariery na kamienistej wyspie nie zgadzają się ze źródłem niezależnie od światła.
- sbs-g3-a-223210302566110: Układ dwóch pasów na wiadukcie trwały między stanami. High pokazuje cieńsze przewody i poręcze, overcast spłaszcza odległe bryły. Jednoramienne lampy nadal odbiegają od dwuramiennych na źródle; pora zachodu nie jest kryterium D51.
- sbs-g3-a-309664504075286: High ostrzej rysuje słup energetyczny i bariery; overcast redukuje kontrast drzew i bloków. Bliski słup z prawej i jednoramienne latarnie są wspólne stanom, bez odpowiedniej relacji do lamp źródła.
- sbs-g3-a-504348097385466: High poprawia tekst tablicy i podpory; zmiana oświetlenia nie zmienia ich projekcji. Tablica w środku zamiast przy lewej krawędzi i wyspa bez kamienia/bariery pozostają ograniczeniem porównania.
- sbs-g3-a-201270605169291: Wspólny duży otwór pod mostem zamiast najbliższych podpór zdjęcia; dalsze filary są widoczne. High i clear nie rozwiązują projekcji, tylko poprawiają ostrość i cienie. Ta para nie rozstrzyga udziału pozy i geometrii.
- sbs-g3-a-1398898753813071: Dalsze podpory są, lecz duży najbliższy filar zdjęcia nie trafia w projekcję we wszystkich stanach. High czytelniej pokazuje belki i poręcze, a prześwit i brak bariery wyspy pozostają problemem geometrii/pozy.
- sbs-g3-a-320326319617139: We wszystkich stanach trawiasta wyspa zajmuje miejsce chodnika/przejścia i bliskich znaków D3/D6 zdjęcia. High tylko wyostrza podpory i trawę; rozbieżność układu oraz ewentualnego bocznego ustawienia kamery trwa.
- sbs-g3-a-482392746429891: Bariery i most czytelne we wszystkich stanach. High wyostrza filary, odwodnienie i poręcze, ale brak odpowiedniego niebieskiego znaku oraz inny rytm podpór/fasady nie są naprawiane światłem.
- sbs-g3-a-454716650857984: Zjazd z wiaduktu i dwa pasy nie zmieniają układu. High wyostrza bariery i odległe drogi; overcast rozjaśnia/spłaszcza las. Brak zgodnego tła reklamowo-usługowego i dwuramiennych lamp pozostaje wspólny.
- sbs-g3-a-303305168125936: High pokazuje drobniejsze poręcze i dalekie bryły, clear zwiększa kontrast zieleni. Zjazd zachowany, ale bloki po lewej zastąpione gęstym drzewostanem, brak par żółtych znaków i charakterystycznego tła usługowego utrzymuje się.
- sbs-g3-a-320215796381417: Układ zjazdu identyczny między stanami, High ostrzejszy. Duży cień clear nie jest nową przeszkodą drogową; brak odpowiadających lamp dwuramiennych, znaków i części panoramy pozostaje.
- sbs-g3-b-381800493259507: Podział jezdni, U3 i portal obecne w trzech stanach. High czytelniej pokazuje napisy i ogrodzenie; portal nadal pełną szarą ramą. U3 mniejszy/dalszy niż w źródle, a stanowisko/kształt nosa nie są wyjaśnione przez światło.
- sbs-g3-b-2279538078845158: Istotna różnica LOD: Low ma pełną szarą ramę portalu, High ażurową kratownicę bliższą konstrukcji źródła. Blok po lewej, niebieski budynek po prawej i odgałęzienie wspólne. High nie rozwiązuje skali/położenia U3 i nosa wyspy.
- sbs-g3-b-837235577143499: High zmienia pełną ramę Low na ażurowy portal; to rzeczywista różnica charakterystycznego obiektu. Duży bliski U3 zdjęcia nadal nie jest w odpowiadającej projekcji w żadnym stanie, choć dalszy portal jest. Problem nosa/stanowiska nie znika.
- sbs-g3-b-3281350541967811: Najważniejszy bliski portal od tyłu po lewej zdjęcia nie jest w tej projekcji w żadnym stanie. High ujawnia dalekie kominy, słupy i portalowe obiekty, lecz nie zastępują bliskiej kotwicy. Overcast dodatkowo osłabia dalekie kominy; problem ustawienia kamery pozostaje.
- sbs-g3-b-275528677534382: Portal ażurowy w Low i High, High ostrzejszy; clear dodaje jego cień. We wszystkich stanach portal jest za blisko/za duży i obcięty u góry względem całego portalu zdjęcia. Brakuje zgodnej pary żółtych znaków; proporcje portalu i pozycja nadal wymagają kalibracji.
- sbs-g3-b-150280503737744: High ujawnia odległe kominy słabiej widoczne w Low i overcast. Nie odtwarza jednak charakterystycznej czerwonej pierzei, pylonów i żółtego ogrodzenia źródła; białe hale pozostają w każdym stanie. To istotne braki świata ponad kosmetyką.
- sbs-g3-b-297817221966185: High zastępuje pełną ramę Low kratownicą i uwidacznia kominy; overcast mocno osłabia ich kontrast. Portal nadal dużo bliższy/większy niż daleki portal źródła; dojrzałe drzewa i prawa czerwona pierzeja źródła nie są odtworzone. Brak podstaw do zamiany ID.
- sbs-g3-b-3678296072299092: High wyraźniej pokazuje słup energetyczny i ramy ekranów, także w overcast. Ekran i prawy zjazd są wspólne stanom, ale ich sylweta, początek oraz relacja do rampy zdjęcia pozostają niedopasowane. Światło tego nie rozstrzyga.
- sbs-g3-b-494288258686575: Oba źródło i raw kręcą w lewo. High wyostrza ekran i bariery, clear ich cienie; nadal inny pion drogi oraz znacznie niższa górna krawędź ekranu w kadrze. To osobne zastrzeżenia pozy i proporcji ekranu, bez uzasadnienia dużego yaw.
- sbs-g3-b-1801374876712141: High wyostrza ekran i domy, overcast osłabia daleką zieleń. We wszystkich stanach ekran zaczyna się inaczej, relacja do prawego wjazdu i pion jezdni różnią się od źródła; billboardu z lewej nie ma, domy są dużo bardziej odsłonięte. Poza nadal niepotwierdzona.

Ograniczenia:

- Ogląd statycznych natywnych PNG; bez pomiaru telefonu, testu runtime, akceptacji właściciela ani nowego wyniku D51.
- Frozen capture HEAD80159a70, upstream ADR0130 nieobecne; wnioski nie opisują przyszłego ani bieżącego po ADR0130 świata.
- Historyczna kohorta 25 B zachowana; 17 C wykluczonych, żadnej promocji lub zmiany kamer/świata. Zastrzeżenia pozy nie są usuwane przez wybór ładniejszego stanu.
- SHA identyfikuje odczytane pliki; hash nie jest potwierdzeniem rozpoznawalności. Nie wykonywano audytu epoki ani ciężkich obliczeń.

