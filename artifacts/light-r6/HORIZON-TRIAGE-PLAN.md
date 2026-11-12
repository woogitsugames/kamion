Diagnostyka P1 horyzontu — plan przed zmianą

Świeża baza obejmuje pięć presetów, 109 kamer i oba poziomy jakości. High używa jawnej referencji HDR z rundy 5. Baza musi zakończyć się przed zmianą źródeł i nową diagnostyką Unity.

horizon-triage.json zawiera 30 zadań, po trzy kamery: dwa kadry G3-A z wcześniejszą granicą mapy chmur i office_1. Dla każdego presetu i poziomu porównujemy istniejącą bazę z samym niebem, samym niebem bez obu rodzajów chmur i światem bez warstwy mgły przy ziemi. To 90 nowych obrazów. rq_haze=0 zostawia zwykłą mgłę; nie oznacza całkowitego braku zamglenia. SkyOnly usuwa geometrię, nie model światła.

Najpierw oglądamy te same kadry. Jeżeli pas zostaje przy samym niebie bez chmur, orientacja fotograficznej mapy nie jest wyłącznym wyjaśnieniem. Jeżeli znika dopiero po usunięciu warstwy mgły, badamy jej parametry i spójność koloru, bez zmiany globalnego EV. Bez wyniku nie wybieramy rozwiązania.

Hipoteza do osobnej ablacji: pełne dopasowanie elewacji słońca pochyla fotograficzny horyzont. Obecny clamp powtarza poprawny wiersz mapy przy granicy źródła. Obrót tylko w azymucie zachowałby horyzont i istniejący jeden odczyt tekstury, ale nie dopasowałby elewacji oświetlenia chmur. To kompromis wizualny wymagający oceny przy 9, 25, 42 i 60 stopniach. Nie jest jeszcze zaimplementowany ani wybrany.

Kontrola końcowa: stan rzeczywisty, wszystkie kamery trasy, osobne instancje, draws +0, tris do +2%. Koszt GPU pozostaje niezmierzony bez urządzenia. Nie edytujemy geometrii, shaderów kabiny/szyb ani generatora Claude.
