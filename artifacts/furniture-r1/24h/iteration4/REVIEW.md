# Niezależna ocena końcowej kandydatury

Obejrzano 40/40 bieżących arkuszy compare: po 10 dla Low/High oraz clear/overcast,
łącznie 220 par przed/po. Nie korzystano ze starych arkuszy iteracji 3.

Nie znaleziono nowej istotnej regresji furniture ani czarnych, pustych lub
niekompletnych kadrów. Lampy, znaki i ogrodzenia zachowują położenie; nie
zauważono nowego unoszenia, zapadania ani znikania elementów. Niskie stopnie,
rozstaw słupków i ciągłość siatki pozostały zachowane po optymalizacji.
Faktura betonowego trzonu jest krótsza i mniej włóknista niż w iteracji 3,
a pas brudu przy podstawie łagodniejszy. Nie zauważono wyraźnego szwu ani
poziomych granic powtarzania skanu w sprawdzonych zbliżeniach.

Pozostały wcześniejsze zastrzeżenia: ostry cokół i czysty kontakt z ziemią,
niepotwierdzona lokalną referencją konstrukcja ukośnego sztywnego panelu oraz
aliasing drutów na Low. Uproszczenia innych dziedzin są widoczne również w
baseline i nie przypisano ich furniture.

Status: brak nowego blokera wizualnego w sprawdzonym zakresie. To ocena
statycznych arkuszy; nie obejmuje telefonu, ruchu, nocnego oświetlenia ani
każdego miejsca regionu. Nie potwierdza czasu GPU ani braku migotania siatki.
Liczniki CPU są odrębnym dowodem z własnymi ograniczeniami.
