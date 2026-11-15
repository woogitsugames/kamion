# Zimowe tyły poza dotychczasowym kręgiem — obieg 17

Cel: 1–3 odrębne brudne tyły naczep w zimowym kontekście; Kanada/USA dopuszczalne, sześć zimowych i sześć europejskich nie musi oznaczać tych samych zdjęć. **Wynik: 1 nowy pomocniczy kadr/ 1 pojazd, 0 potwierdzonych nowych FIX≥1000px drzwi, 0 potwierdzonych europejskich.** Lokalizacja tego zdjęcia pozostaje UNVERIFIED, więc nie udaję potwierdzonegoUSA. 0 pobranych fotografii/PDF i 0 zapisanych plików mediów (SOURCED: własny manifest i dziennik).

## WW17-A01 — RoadTour

[Publiczny artykuł](https://www.roadtour.net/post/leaving-snow-on-your-car-or-truck-is-dangerous) pokazuje pojedynczy obraz z podpisem **Large Ice Chunk Flying From a Semi Truck Roof - Photo: ©RoadTour.Net**. To SOURCED deklaracja typu semi-truck i fotograficznego pochodzenia przez publikatora; osobisty fotograf i EXIF UNVERIFIED. Źródło nie nazywa tego renderem, AI lub ilustracją. Nie wyciągam pewności pochodzenia z samego realizmu; zachowuję dokładny podpis i watermark. Kredyt fotografii jest jawny. Materiał wyłącznie **link-only, all rights reserved**, bez kopiowania/dystrybucji do tekstur lub datasetu.

Obejrzano osobno duży podgląd i ten sam publiczny obraz w osobnej karcie Chrome. Dwa wysokie jasne skrzydła i dwa pionowe pręty; na dolnej połowie pól szare nieregularne pionowe smugi, ciemniejsze pasma przy dolnych zewnętrznych zawiasach i okuciach. Środkowe rygle oraz dolna rama ciemniejsze; białe przyczepione fragmenty osobno od szarego filmu. Nad dachem duża biała płyta i odłamki; podpis identyfikuje je jako lód. Nie widać wielkich łuszczących płatów farby na polach. Zafarb niebieskozielony i możliwe plamki na szybie kamery ograniczają ocenę barwy. Skład chemiczny białego materiału/soli UNVERIFIED; nie przypisuję mu chemicznego składu ani procentowego pokrycia.

Typ jest **SOURCE_DECLARED_SEMI_TRUCK**, a nie ustalony wyłącznie z dwóch skrzydeł. Ciągnik/sprzęg nie mieści się w obrazie; brak widocznej konstrukcji przeczącej źródłowemu podpisowi. Brak kraju nie przekreśla samego zimowego wzorca, ale nie pozwala zwiększać licznika Europa. Publikacja UI Feb4 nie podaje roku i nie jest datą ekspozycji.

## Pułapka naturalWidth / density

SOURCED [trzy odczytyDOM, evidence.json]:

| Powierzchnia | Odczyt | Wniosek |
|---|---|---|
| Artykuł |728×770px | Mały wariant |
| Galeria fullscreen |naturalWidth2550,naturalHeight2696; currentSrc kończy się wariantem1290×1364; srcset max1290w | Nie traktować naturalWidth jako dowodu większego zakodowanego oryginału |
| DOKŁADNIE ten sam currentSrc w osobnej karcie obrazu |Tytuł 1290×1364 i DOM natural 1290×1364 | Tylko ten rozmiar jest niezależnie potwierdzony dla podanegoCDN |

[Exact publiczny wariant](https://static.wixstatic.com/media/609dc9_bae2413ee20f49e984a094efa83e2f3a~mv2.jpg/v1/fill/w_1290,h_1364,al_c,q_85,enc_auto/609dc9_bae2413ee20f49e984a094efa83e2f3a~mv2.jpg) otwarto bez modyfikowania parametrów, pobrania lub wariantów hostu. ESTIMATED wysokość drzwi 760–850px w potwierdzonym 1290×1364; większy natywny oryginał UNVERIFIED. Nie podnoszę do PASS1000 przez pozorną większą liczbę galerii. Ocena nowego FIX pozostaje PENDING_NATIVE_RESOLUTION oraz pending peer/root.

## Oddzielne kryteria A/B/C

A = użytkownik ≥20 łącznie: prawdziwa naczepa, podwójne drzwi i widoczny brud. Mniejszy obraz może spełniać treść A, ale ten kadr pozostaje **A_PENDING_PEER** do niezależnego sprawdzenia typu, fotograficznego pochodzenia i powierzchni. Nie wciskam wszystkich AUX do A.

B = FIX ≥12 NOWYCH z ≥1000 px wysokości drzwi: **B_FAIL_GE1000_AVAILABLE_RENDITION** dla zweryfikowanego 1290×1364; największy oryginał pozostaje UNVERIFIED. Nie obniżam progu B, nie zwiększam jego zimowego podzbioru. C_zimowe_A czeka na peer kontekstu; C_zimowe_B bez B_PASS nie jest zaliczone. Po recenzji root może rozstrzygnąć A i C oddzielnie od B; brak automatycznej zmiany globalnego wyniku.

## Selekcja i dalsza kontrola

Flickr sprawdzono wyłącznie publicznym filtrem licencji 4/5/9: semi snow rear, następnie jeden szerszy truck snow rear. Nie wybrano nowego obiecującego kadru; siatka nie jest oglądem pojedynczego obrazu i nie tworzy wierszy manifestu. Commons Truck stuck in the snow 2929723050 ma indeksowane 800×600 całego zdjęcia, więc nie daje1000pxdrzwi; obrazu nie pobrano i nie opisano.

Dedup URL i identyfikatora609dc9_bae2413ee20f49e984a094efa83e2f3a względemP18+s21 przed zapisem bez trafień. Nie udaję pełnej wizualnej deduplikacji nieobejrzanych 43 zdalnych rekordów P18. Nie powielono Getty Bosnia/FR4. To samo zdjęcie w artykule, galerii i CDN liczy się raz. Globalny stan 20/12/6/6 nie jest przeliczany z tej rundy.

Do peer: poproszono knyszyn po jego bieżącym UI o niezależny ogląd exact CDN i rozdzielczości; bez pobrań i bez używania większych liczb galerii bez wyjaśnienia. Artefakty: manifest.csv, evidence.json, screening.json, README.md. Zapis wyłącznie w tym nowym podkatalogu, bez git i cudzych zmian. Chrome zwolniony po completion_summary.

## Decyzja koordynatora po peer i kontroli bazowego zasobu

A=PASS_CONTENT_SOURCE_DEPENDENT_PEER, C-zima-A=1source-dependent: widoczne podwójne drzwi/film i zimowy kontekst, typsemi i statusPhoto zjawnej deklaracji źródła. Nie niezależne badanie EXIF/techniki; zafarb/szyba nie jest całybrud. B nadalFAILdla dostępnego1290×1364, drzwiEST780–850; [obieg19](../roadtour-original-check-round19/README.md) potwierdził ten sam rozmiar bazowego zasobu po2oglądach, nie znaleziono2550. Większy oryginał gdzie indziejUNVERIFIED. Nie dodano drugiego zdjęcia ani zimowegoB, nieustalonaEuropa. Własny opis/link,0kopii mediów; brak źródłowych obrazów wdatasetach/AItraining.
