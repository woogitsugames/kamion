# Uwagi do następnej diagnozy szyby

To przygotowanie po odczycie istniejącego kodu, nie wynik nowego eksperymentu i nie poprawka rundy kół. Nie zmieniono shaderów ani materiałów szkła.

TruckGlassAudit.Write można uruchomić przez istniejący TruckPaintRound/adapter z -truckGlassAudit 1. Zapisuje aktywność, włączenie renderera, forceRenderingOff, LODGroup, slot i orientację trójkątów według tego samego testu inside co shader. Liczników różnych LOD-ów nie wolno sumować jako jednoczesnych warstw. sameWindingCoincident i reverseWindingCoincident dotyczą tylko jednego submesha; dedicatedPaneAabbCandidates jest szeroką fazą sprawdzenia AABB, a nie dowodem nakładających się tafli między rendererami.

Istniejące GlassDiagnostic near-transmission i near-radiance-off w TruckPaintRound podmieniają końcowy return pełnej ścieżki. Nie obejmują osobnego return pane w FragFast. Ewentualny nowy eksperyment musi objąć obie ścieżki; inaczej nie wyjaśni Low/Medium. Wyświetlane kanały diagnostyczne High przechodzą korekcję obrazu, więc nie są surowym odczytem transmittance bez osobnego potwierdzenia.

KamionTone jest funkcją toe i gain; sama jego obecność przed premultiplied blend nie dowodzi przyczyny mleczności. Dla dodatnich parametrów toe tłumi ciemne składowe. Nie należy przypisywać mu jasnej zasłony ani zmieniać kolejności bez kontrolowanego pomiaru obu profili. Trzeba rozdzielić transmisję, addytywne odbicie/film i liczbę faktycznie widocznych tafli.

W kolejnym stanie po merge main potrzebny będzie świeży baseline: rzeczywista przednia tafla / kontrola bez tej tafli / kontrola bez addytywnej radiancji przy zachowanej alfie. Dopiero taki pomiar odróżni tłumienie sceny od dodanej zasłony. Nie obniżać F0, nie zwiększać transmisji ani nie usuwać szyb na podstawie AABB lub nieporównywalnych kadrów. Wartości _Opacity, _Grime, _Wiper i inside trzeba odczytać z faktycznie użytych materiałów po renderze, nie tylko z inicjalizatora buildera.
