# Natywny ogląd referencji C — SBS r4

PARTIAL: 20/68 raw i 5/17 źródeł. Cztery stany każdej zapisanej kamery fizycznie obejrzane przez view_image. Checkpoint po każdej kamerze.

Frozen pixels HEAD80159a70; upstream ADR0130 nie jest w nich obecne. Bez promocji C, zmian kamer, rejestru i D51. Potwierdzone 100 B pozostaje oddzielnie. SHA tylko identyfikuje plik. Ogląd nie jest zaliczeniem bramki ani pomiarem telefonu.

## sbs-g3-a-1406533339711789

Zdjęcie pokazuje jazdę po pomoście i lekkie zakrzywienie z barierą; raw mają dużo prostszy, centralny widok i inne bliskie relacje bariery/lamp. Zachód i odblaski utrudniają dalsze kotwice, lecz nie tłumaczą rozbieżności projekcji. High tylko wyostrza detale.

Kotwice: Najpierw ustalić stanowisko i orientację względem obu krawędzi pomostu; niezależnie dopasować bliski słup/bariery do stałego punktu na geometrii. Sama linia zbiegu dwóch krawędzi to jeden rodzaj ograniczenia, nie dwie niezależne kotwice.

Ograniczenie pozy: Oryginalny compass i SfM sprzeczne; aktualna wysokość na pomoście nie dowodzi heading/pitch/FOV. Pozostaje C.

## sbs-g3-a-2948595898752384

Foto i raw pokazują zjazd z pomostu, lecz foto ma znacznie niżej położony punkt zbiegu dalszej drogi i inne proporcje barier/tła. Aktualny horyzont nie daje zgodnej projekcji. High/clear wyostrzają bariery, ale nie rozwiązują kalibracji; lampy modelu są jednoramienne zamiast dwuramiennych.

Kotwice: Nie utożsamiać VP pochylonej jezdni z poziomym horyzontem. Potrzebne niezależne ograniczenie pitch/roll na pionach oraz stały bliski punkt bariery/końca pomostu o znanej pozycji; następnie daleki stały budynek/pylon (po sprawdzeniu obecności w świecie). Dwie krawędzie tej samej jezdni same nie potwierdzają pitch i wysokości.

Ograniczenie pozy: 294859: korekta z dwóch linii jezdni jest hipotezą, nie zweryfikowanym horyzontem. Wysokość, stanowisko i FOV nadal współzależne; pozostaje C.

## sbs-g3-a-500263111404933

Most i bariera wspólne, ale bliskie podpory mają inny rytm/projekcję, niebieski znak źródła nie ma odpowiednika w kadrze, a hala za mostem jest inna. High wyostrza belki, światło zmienia cień, nie te relacje.

Kotwice: Dopasować konkretną parę podpora–styk belki, identyfikując numer podpory na planie; drugą kotwicą może być słup energetyczny/budynek po przeciwnej stronie, dopiero po potwierdzeniu jego tożsamości. Sam ogólny skos mostu i bariera nie wystarczają.

Ograniczenie pozy: Skośny widok richlv nie pozwala zastąpić kierunku optycznego bearingiem jazdy. GPS/boczny offset, FOV i pitch nadal C; znak może być brakiem świata.

## sbs-g3-a-1259231227807789

Foto ma bliski filar po lewej i przyczółek dalej z prawej; raw mają przyczółek, ale brak tego filara w projekcji i wyraźnie inny skos/pion pomostu. Wszystkie stany zgodnie pokazują to niedopasowanie. Panelowanie muru i tło także uproszczone.

Kotwice: Użyć zidentyfikowanego naroża przyczółka/styku belki jako pierwszej kotwicy, a najbliższego filara jako drugiej na innej głębokości; sprawdzić czy jego geometria istnieje w odpowiednim miejscu. Dopiero potem weryfikować daleki słup energetyczny.

Ograniczenie pozy: Nie można uznać braku filara na obrazie za sam brak świata bez sprawdzenia stacji/boku i FOV; silny konflikt pozy pozostaje C.

## sbs-g3-a-751431972202262

Mur z czerwoną belką jest obecny, lecz raw pokazują znacznie mniejszy skos i inny pion całego muru niż zdjęcie. Brak panelowych fug i żółtego znaku to ograniczenia geometrii/obiektów; nie dowodzą same błędu pozy. Cztery stany mają ten sam konflikt projekcji, High tylko wyostrza.

Kotwice: Jednolita powtarzalna ściana nie daje dwóch niezależnych kotwic. Potrzebny zidentyfikowany koniec/naroże muru oraz drugi stały obiekt w innej głębokości (np. potwierdzony słup/znak), z wiarygodną pozycją w świecie. Rytm identycznych paneli bez końca muru jest niejednoznaczny.

Ograniczenie pozy: Stanowisko, kierunek optyczny i pitch/FOV pozostają C; jasny dzień nie pozwala rozstrzygnąć SfM ani bocznego offsetu.

Brakujące kamery: sbs-g3-b-962702164479831, sbs-g3-b-1528935774382039, sbs-g3-b-810896133189484, sbs-g3-b-810525063224609, sbs-g3-b-326454015490067, sbs-g3-b-209622370971977, sbs-g3-b-339463879238809, sbs-g3-b-468026894483428, sbs-g3-b-4312632558767412, sbs-g3-b-182011943700132, sbs-g3-a-cm109685822, sbs-g3-a-cm92458760.

Przerwano na polecenie użytkownika z powodu limitu tygodniowego, po ukończeniu kamery 751431972202262. Pozostałych 12 źródeł i 48 raw nie oglądano; obejmują wszystkie C z segmentu B oraz oba Commons. Następna kamera do wznowienia: sbs-g3-b-962702164479831. Nie sformułowano opinii o nieobejrzanych Commons.

