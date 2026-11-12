# Preflight kolejnej rundy po paletach — bez zmiany produkcji

12.11.2026 około 15:18, podczas oczekiwania na PHONE_RUN. Najpierw dokończyć r5 i przekazać REPORT, nie zamieniać jej na lakier. Pierwotny koniec doby około 21:31 pozostaje bez zmian.

Otwarta niezależna recenzja batch C: czerń clear nadal FAIL, gruby szum płatków czyta się jak papier ścierny, tył nadal czysty, ostry prostokąt pod autem wymaga oddzielenia kontaktu od podwozia. R4 zmieniła wyłącznie felgi pojazdów placowych.

Odczyt kodu: WorldInstances.RenderParams wyłącza ReflectionProbeUsage i LightProbeUsage. EnvironmentLighting tworzy globalny ReflectionCubemap ze sky/ground modelu, a nie lokalnej sceny budynków i samochodów. _CARPAINT próbkuje GlossyEnvironmentReflection dla clearcoat oraz podłoża. To wyjaśnia ograniczenie danych wejściowych: samo obniżenie albedo/flake lift nie dostarczy brakujących pionowych odbić otoczenia. Nie udawać tego losowymi ciemnymi pasami. Zmiana globalnego generatora odbić/WorldInstances nie mieści się w obecnej własności life; ewentualną integrację źródła odbić trzeba opisać liderowi, bez edycji cudzych plików.

Konkretny kandydat w zakresie własności: filtr płatków _CARPAINT (na High). WorldPbrMaterials ustawia obecnie 400 komórek/m, czyli 2,5 mm; shader tiltuje normalną hashem po floor(object position × 400). ffade wygasza tilt dopiero przy śladzie piksela równym komórce. Obejrzeć w aktualnym baseline, potem rozważyć ablacją 400/800/1600 komórek na metr wyłącznie dla osobówek i za istniejącą flagą danych. Low nie ma tego bloku. Nie zmieniać równocześnie pigmentu, roughness ani odbić, żeby można było przypisać skutek. Liczby powyżej to parametry źródła, nie pomiar poprawy ani fizyczna specyfikacja lakieru.

Kontakt: export.py emituje osobny <prototype>.contact przez life_props.contact_spec/contact_quad. Żeby rozstrzygnąć P1 prostokąta, najpierw dwa osobne diagnostyczne kadry z wyłączonym tylko kontaktem i tylko podwoziem, nie od razu zmiana shaderów cienia. Zachować kanoniczny capture bez diagnostycznego wyłączania, sceny bez zapisu i budżet draws instancji osobno. Nie zakładać przyczyny na podstawie samego JPG recenzji.

Preflight jest tylko analizą odczytanego kodu. Bez eksperymentu runtime, bez generacji, bez pomiaru GPU/A16 i bez zamknięcia żadnego P1.
