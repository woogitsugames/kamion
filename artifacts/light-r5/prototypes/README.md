# Kandydat nieuruchomiony — izolacja Overcast w rundzie6

Te pliki znajdują się poza game i nie są kompilowane przez Unity. Nie wnoszą dowodu działania. Stosować dopiero po zamknięciu R5, utworzeniu R6 i merge aktualnego main, z ponowną inspekcją interfejsów.

Integracja w własnym LightQaBatch: addytywna flaga job.paneIsolation; using var isolation przed renderer.Render; po renderze isolation.Write(output,count); Dispose w tym samym zakresie co grade/HDR. Utworzyć metadane dla obu własnych plików. Bez edycji TruckGlass/CabInteriorLighting lub innych właścicieli.

Pierwsza macierz: Overcast, cab-dash/cab-driver/r10_office_1, HighHDR/Lowbase/LowNative, paneIsolation OFF/ON, rq_clouds1/2 =36 PNG. Dopiero po czystym małym smoke. Native korzysta z nowego bake zgodnego z R6 (zmieniony main może zmienić look); wymaga braku podwójnej krzywej. Low q2 to kosztowniejsza diagnostyka, bez automatycznego włączenia produkcyjnego. Jeśli pozostaną różnice, oddzielnie wyrównać rq_scale1/rq_msaa2/rq_fsrsharp0 bez obniżenia skali; nie mieszać naraz wszystkich przyczyn.

Klasa zapisuje faktyczne sloty podmienione w każdej eksportowanej ControlCamera, przywraca materiały na endCamera i dla fizycznych kamer (flagaSkyCapOff). Liczbę obserwowanych fizycznych kamer raportuje, ale nie wymusza, żeby sam brak observation został uznany za dowód capture. Trzeba sprawdzić rzeczywiste nestedCamera callbacks w tej wersji URP, reload i cleanup błędu. Pełny kosztCPU/GPU tego diagnostycznego materiału nie jest budżetem produktu. Kamera zewnętrzna kontroluje, czy obserwowany problem jest związany z widokiem przez szybę. Porównanie obejmuje zmiany samego nieba, skali, geometrii i kompozycji; dopiero macierz może je zawęzić.
