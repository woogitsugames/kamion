# Diagnoza przed zmianą eksportu kół

Źródłowe sześć FBX miało identyczne SHA jak kopie w projekcie. Nowy main nie zmieniał tych eksportów. Odczyt siatek oraz podglądy preworld wykonano na istniejącej scenie r2 przed świeżą budową świata; są dowodem lokalnej geometrii i kanałów, a nie jakościowym baseline sceny r3. Shader produkcyjny i FBX pozostawały wtedy bez zmian.

Przednie lewe koło ma 6718 / 1709 / 907 trójkątów w LOD0/1/2. W LOD2 brak degeneracji według progu pola 1e-12 m² i brak średnich normalnych przeciwnych do windingu według testu dot < -0,05. Nie oznacza to poprawnej orientacji całej bryły. LOD2 ma 47 trójkątów o rozpiętości UV >0,25 atlasu: 20 Metal, 27 Trim, max 0,8021; LOD0/1 mają zero. Szerokie UV nie są automatycznie błędem, ale tutaj wspierają obserwowane poszatkowanie albedo. Źródła: wheel-mesh-before.json i -metrics.json.

Duży otwarty środek przedniego koła Low pozostaje w płaskim stałym kolorze oraz po diagnostycznym Cull Off. W High środek zamyka piasta. Źródłowa lista LOD2_DROP usuwała _hubcap i _hub, pozostawiając otwartą annularną tarczę. Przywrócenie osłon jest oddzielnym problemem od UV.

Surowe albedo Low pokazuje trójkątne rozciągnięcia i poszatkowany rant także poza otworami widocznymi w flat. Funkcja reduce_round wybierała narożniki z wielu komórek atlasu bez ochrony granic wysp. Przygotowany kandydat zachowuje te granice na obu osiach i nie łączy rozłącznych chartów; dopiero test BMesh i nowe FBX potwierdzą działanie oraz koszt geometrii.

Pierwsze lewe koło naczepy ma 6321 / 1223 / 511 trójkątów. W tej mierze nie ma UV-wide, degeneracji ani przeciwnych normalnych. Szczeliny widoczne w flat i częściowo w Cull Off potwierdzają problem pokrycia formy, lecz nie ten sam dowód mapowania. Zniknięcie części szczelin przy Cull Off nie dowodzi samo w sobie błędnego windingu: mogą to być poprawne powierzchnie oglądane od tyłu.

Niezależny recenzent potwierdził powyższe ograniczenia. Zalecana kolejność: zamknięcie środka i poprawne pokrycie LOD2, mapowanie przedniej felgi, później wygładzanie i materiał opony. Bez PASS r3, bez oceny ruchu i telefonów. Zdjęcie wystawowe wspiera formę, nie jasność chromu i poziom zabrudzenia.
