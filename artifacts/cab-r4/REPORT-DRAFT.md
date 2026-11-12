# Runda cab r4 — szkic raportu, nie do scalenia

Runda jest otwarta. Ten szkic opisuje wyłącznie sprawdzone dotąd etapy; nie zastępuje końcowego REPORT.md, wyboru materiału, pełnych testów ani końcowego GIS. Gałąź gpt-cab-r4 powstała z cab r3 aefad847, następnie scalono main 8b74c2c5 w commit 6c5c12f8. SHA końcowe zostanie podane po zamknięciu rundy.

Wybrany wariant legend Low zachowuje atlas 256 × 256 i ustawia mip bias −0,75 za danymi cab_legend_atlas.json. Medium i High pozostają bez bias. Nie zwiększono atlasu, skali renderowania, liczby materiałów, próbek shadera, przebiegów ani geometrii. W trzech obejrzanych ROI widać miejscowo wyraźniejsze kontury kilku symboli, ale nie wszystkie małe ikony stają się jednoznaczne. P1 czytelności pozostaje częściowo otwarty; migotanie w ruchu i GPU A16 nie zostały zmierzone.

Samo przełączenie atlasu Low na istniejący Medium 512 nie przyniosło widocznej korzyści: zmieniło się 16 z 48 000 pikseli ROI overcast. Bias −0,75 zmienił odpowiednio 331, 332 i 329 pikseli w clear, overcast i dusk. To różnice obrazu, nie miara jakości. Próbę ogólnego progu alpha 0,4 odrzucono: przeoczono osobny próg 0,16 dla ikon, więc Clear ROI nie zmienił się wcale. Właściwa próba progu ikon 0,28 zmieniła po 199 pikseli w każdym stanie, lecz część cienkich kresek zanikała bez konsekwentnej poprawy. Obie zmiany progów wycofano, a CabInterior.shader odtworzono dokładnie sprzed prób. Szczegóły i hashe: LEGEND-REVIEW.md oraz pliki *-roi-check.json.

Eksportowane PNG mają 1920 × 1080. Low w każdym porównaniu ma renderScale 0,75 i MSAA 2, High renderScale 1. Wycinek nazywany natywnym jest wycinkiem pikseli pliku PNG, nie wewnętrznego RT Low. Arkusze ROI pokazują go 2× najbliższym sąsiadem. Nie podnoszono skali Low.

Dla Plastic przygotowano opcjonalny filtr normalnych normal_highpass_mm. Odejmuje on niskie częstotliwości nachyleń XY/Z, rekonstruuje jednostkowe normalne i zachowuje okresowe krawędzie. Wartość 0 zachowuje dawną ścieżkę; filtr dodatni dotyczy tylko Plastic. Nie dodaje pracy shaderowi. Odtworzenie 12 map obu materiałów zgadza się z bazą SHA256 12/12. Kandydat 1,5 mm zmienia wyłącznie trzy mapy Normal Plastic; trzy mapy Detail wraz z alpha oraz Leather pozostają identyczne. Maksymalny błąd długości normalnej po kwantyzacji wyniósł 0,00517, Z pozostaje dodatnie.

Wariant 1,5 mm obejrzany w High clear nadal przypomina skórzaste tłoczenie i nie ma przekonującej akceptacji wizualnej. Mocniejsze 0,3 i 0,6 mm oczekują na przygotowanie offline pod heavy; nie są jeszcze wynikiem gry. Parametry są WORKING_VALUE. Sigma odnosi się do kafla Plastic 10 cm; zachowane UV części 8 i 6 cm dają proporcjonalnie inne progi. Nie jest to pomiar rzeczywistych fałd ani jednolita fizyczna sigma całej deski. Plastic nadal jest jawnie opisaną pochodną skanu Brown Leather Roba Tuytela z Poly Haven, a nie skanem tworzywa deski. Wpis licencji istnieje i nie został zdublowany.

Świeży World zakończył się exit 0; log podaje 477,4 s i nie zawiera fallback=True. Po wykryciu brakującego lokalnego wejścia zdjęciowego asphalt_detail_photo skopiowano istniejący plik z main, zweryfikowano SHA i zbudowano tylko tę warstwę pod heavy. Nie zmieniano kodu świata. Pierwszą niepełną serię odłożono do baseline-without-photo i wyłączono z porównań. Poprawiony baseline oraz hp15 zawierają po 42 kadry kabiny, 36 natywnych RT i 78 kamer trasy.

| Sprawdzenie | Dotychczasowy dowód | Status końca rundy |
| --- | --- | --- |
| Filtr normalnych, małe testy numeryczne | 7/7, 1,00 s, normal-highpass-unit.log | Zaliczone dla kodu filtra |
| Reprodukcja map bazowych | 12/12 identycznych SHA256 | Zaliczone |
| Budżet hp15 i bias-only | comparison-0112-r4.json PASS; wszystkie delty regular/shadow/instanced draws oraz regular/instanced tris 0 | Dotyczy hp15, nie nieuruchomionych mocniejszych wariantów |
| Wnętrze w lustrach | 36/36 RT hp15, interiorPixels 0; pełna konfiguracja porównana | Powtórzyć dla wybranego końcowego wariantu |
| Pełny EditMode | 346/346 w XML 20261112-135542, przed próbami progów | Wymagane końcowe uruchomienie |
| Aktualność Fidelity | 23/23 hashów zgodnych w kontroli 12:16 po World | Ponownie sprawdzić przed końcowym GIS |
| Pełny GIS r4 | Jeszcze nie uruchomiono | Obowiązkowy na końcu rundy |
| Produkty generowane świata i Settings | Settings cofane po każdym Unity; produkty World zachowane do GIS | Końcowe sprzątanie po terminalnym GIS |
| Kopia artifacts do main | Jeszcze nie wykonano dla r4 | Po końcowym REPORT.md |

Dodatkowo zapisano i obejrzano sześć kadrów Low/High na istniejącym Night z sesji light. Ekrany są oddzielone od ciemnych obudów, lecz świecenie legend nadal wypada słabo względem prywatnej referencji Volvo Trucks / Jonatan Fernström z 2017 roku. Inny pojazd, poza, reflektory i ekspozycja nie pozwalają wyprowadzać docelowego RGB ani cd/m². Preset Night sam opisuje ograniczenia modelu zmierzchu; nie jest dopasowaniem astronomicznej nocy. Nie zmieniano luminancji, palet ekranów ani światła otoczenia. Obejrzany prywatny arkusz ma 960 × 350: private-night-reference-vs-render-960.jpg; źródło i prawa w cab-r2/NIGHT-REFERENCE.md. Fotografie i pochodne panele z logo lub prawami autorskimi pozostają poza git. Pary materiału z wybranym końcowym wariantem trzeba jeszcze przygotować i obejrzeć.

Znaczną część czasu zajęło oczekiwanie na zasoby, a nie obliczenia. Wszystkie Unity używają owner gpt-cab, ciężkie zadania owner gpt-cab-r4, z natychmiastowym zwalnianiem po kroku. Zapisano błąd współdzielenia pliku kolejki oraz ograniczone ponowienie samego acquire bez duplikowania workera. Po zmianie skryptu main z 14:49 odświeżono własne pozyskanie, potwierdzając wcześniej brak workera i własnego slotu; istniejący ticket z 14:30 został zachowany przez skrypt. Starsze aktywne pozyskania nadal poprzedzają cab w FIFO przy pustej puli. Szczegóły: acquire-policy-refresh.json, resource-queue-diagnosis.json i resource-wait-events.jsonl. Cudzych procesów, ticketów, priorytetów i PHONE_RUN nie zmieniano.

Otwarte pozostają ciemne pasmo AO deski, zużycie kontaktowe i pełna czytelność drobnych ikon Low. R4 nie zmienia kamer, pola widzenia, położenia oka, rozdzielczości i częstotliwości RT ani geometrii luster. Nie dotyka shaderów zewnętrza lub szyb, nie używa telefonu/adb, nie scala do main i nie pushuje. Oczekiwane konflikty integracji dotyczą wnętrza TruckAssetBuilder.cs, konfiguracji i trzech map normalnych Plastic; kod innych części buildera należy zachować. Końcowy raport musi uzupełnić wybór materiału, aktualne testy, obejrzane pary, SHA i potwierdzenie kopii do main.
