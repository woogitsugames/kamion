# ADR 0109 — Roślinność w cyklu 24 h

## Runda r1

Stan: praca w toku, bez deklaracji PASS wyglądu ani wydajności telefonu.

Recenzja 0088 wskazała trawę bez wariacji w skali metrów, prześwietlone korony Putry, walcowate żywopłoty i uproszczone sosny. Punktem odniesienia jest aktualny main 4c9905b1, nie dawna macierz 0088.

Najpierw odtwarzamy baseline Low/High w clear/overcast. Maska B opisuje stan koszenia i suchości, a nie zinwentaryzowane uszkodzenia. Zmiana nie może tworzyć jednolitej piaskowej obwódki wokół każdego trawnika. Pola mają skalę metrów i są zakotwiczone w świecie. Zachowujemy R (odległość), G (las) i A (zmapowane odsłonięte podłoże).

Budżet Low: brak dodatkowych draw calls, trójkąty do +2 procent względem tej samej kamery. Zmiany podłoża wykorzystają istniejące maski i próbki tekstur. Szybka ścieżka lasu pozostaje aktywna. Wartości artystyczne są WORKING_VALUE; wyniki telefonu są UNVERIFIED, ponieważ telefony należą do lidera.

Dowody i kolejne kroki: artifacts/vegetation-r1/STATUS.md. Raport rundy powstanie po kontroli obrazów i testach.

### Doprecyzowanie po baseline r1

Baseline z własnej regeneracji main 4c9905b1 obejmuje 268 obrazów kontrolnych (67 kamer razy Low/High i clear/overcast) oraz 54 kadry fotograficzne. Zdjęcia zachowują proporcje, źródło i licencję. Pozy pozostają UNVERIFIED.

W B rozdzielono jawne trawniki OSM od poboczy; pole 8 m i 2,5 m opisuje wyłącznie roboczą suchość i koszenie. Sucha materia w VegetationGround.hlsl korzysta z istniejących sampli i jest dodana za istniejącymi flagami gruntu w WorldPBR oraz WorldSurface. W WorldPBR obie gałęzie mieszania otrzymują liniowe _Tint i _AlbedoScale dokładnie raz. Parametry suchego pigmentu i amplitudy pozostają WORKING_VALUE do obejrzenia after.

Lokalna wysokość pokrywy i rdzenia jest włączona flagą danych wyłącznie dla aktywnych berberysów rond. Inne prototypy żywopłotu zachowują wcześniejsze wzory. Syntetyczne narożniki ligustru i tui ujawniły osobne defekty; nie deklarujemy ich naprawy. Liczba trójkątów czterech aktywnych żywopłotów: 18402 przed i po generacji.

Samocień kart liściastych w Vegetation.shader wzmacnia istniejące _CrownShade powyżej polityki sosny 0,25. Nie zmienia impostorów, HLOD, hero z wartością 0 ani sosnowych kart. Kod jest wspólny dla VEG_FAST i pełnej ścieżki. Ocena wymaga aktualnych obrazów; koszt GPU A16 pozostaje UNVERIFIED.

Stary ROI koron Putry zawierał również zielony słup i fasadę. Nowy stały ROI to (0.80,0.32,0.96,0.42); baseline p50 wynosi Low 58,106 i High 76,567. Obszar trawy pomiędzy chodnikiem a jezdnią opisuje stały wielokąt w review_images.py; Low-overcast ma odchylenie średnich pełnych bloków 32 px 3,614 (18 bloków). Starszy mieszany ROI zostaje w danych audytowych, bez utożsamiania go z samą trawą.

Zgodnie z pilną aktualizacją właściciela wszystkie dalsze ciężkie generacje i testy Pythona wymagają puli heavy (3 zadania), a pełny GIS uruchamia się dopiero na końcu rundy. import-safe.ps1 blokuje niegotowe wejścia, aby importer nie uruchamiał ukrytego build_all poza tą pulą.

### Odrzucony wariant A

Pe?ne 322 obrazy po zmianie zachowano w artifacts/vegetation-r1/candidate-a-rejected. Mieszanie albedo ze sta?ym suchym kolorem sp?aszcza?o detal: grass-only Low-overcast std blok?w 3,614 ? 1,841, High 2,981 ? 1,066. Wariant B zachowuje detal mno?eniem; pr?ba o?miu kamer Low-overcast da?a 5,170 w tym samym obszarze (18 blok?w). To wska?nik wariacji sRGB, nie pomiar wilgotno?ci ani samodzielny dow?d realizmu.

Surowe hashe 64 asset?w kolizji r??ni? si? po imporcie. Importer usuwa i tworzy zasoby z nowymi identyfikatorami podzasob?w; hash pliku nie weryfikuje wi?c r?wno?ci geometrii. Kod dr?g i fizyki nie jest zmieniany. Nie deklarujemy bitowej identyczno?ci kolizji.
