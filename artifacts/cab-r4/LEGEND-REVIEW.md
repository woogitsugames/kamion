# Legendy Low — wybór po izolowanych próbach

Do końcowej walidacji wybrano pierwotny atlas Low 256² z mip bias −0,75 (WORKING_VALUE). Medium/High zachowują swoje atlasy i bias 0. Nie zmienia się shader, próg alpha, UV, geometria, liczba materiałów, fetch/pass ani QualityProfile. Zmiana nie zamyka całego P1: drobne symbole Low nadal nie są wszystkie jednoznaczne.

| Próba | Faktyczny punkt odniesienia | Obserwacja i decyzja |
| --- | --- | --- |
| Low atlas 512, bias 0 | baseline, Plastic bez filtra | ROI overcast: 16/48 000 zmienionych pikseli, praktycznie brak widocznej poprawy. Odrzucona. |
| Low 256, bias −0,75 | baseline, Plastic bez filtra | ROI clear/overcast/dusk: 331/332/329 zmienionych pikseli. Kontury kilku symboli miejscowo wyraźniejsze. Wybrana do pełnego gate. |
| Ogólny _Cutoff 0,4 | result-0112-hp15, bias −0,75 | Clear ROI: 0 różnic. Przeoczono osobny stały próg 0,16 w paśmie ikon; ogólny próg nie sterował ich kolorem. Próba odrzucona, przywrócono 0,5. |
| Próg samych ikon 0,28 | result-0112-hp15, bias −0,75 | Clear/overcast/dusk: po 199/48 000 zmienionych pikseli. Brak konsekwentnej korzyści, część cienkich kresek zanika. Odrzucona. Usunięto nową właściwość i helper, shader odtworzono dokładnie sprzed próby. |

Obejrzano wymienione ROI, a dla próby 0,28 także natywny pełny Low overcast cab-dash. Progi porównywano względem hp15, aby zachować identyczne normalne Plastic; wcześniejszy legendbias był sprzed integracji tych map. Liczby są różnicami obrazu, nie miarą jakości lub fotometrii. Wyniki i hashe znajdują się w odpowiadających plikach *-roi-check.json.

ROI 240×200 jest nieprzeskalowanym fragmentem eksportowanego PNG 1920×1080, pokazanym 2× najbliższym sąsiadem. Low ma w stats renderScale 0,75 i MSAA 2 (wewnętrzny render około 1440×810, następnie upscale), identycznie w baseline i próbach. Nie podnoszono skali Low. High ma renderScale 1.

Mipy Low pozostają włączone, dziewięć poziomów. Nie zmierzono migotania w ruchu ani GPU A16; sesja nie używa telefonu. Ostrzejsze filtrowanie wymaga niezależnej oceny na urządzeniu. Testy materiałów wymagają końcowego uruchomienia po wyborze wariantu Plastic i ponownej przebudowie.
