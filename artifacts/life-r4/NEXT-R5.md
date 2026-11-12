# Następna runda: zaległy backlog palet i drobnego życia placów

Po REPORT i kopii r4 rozpocząć r5 od aktualnego main dołączonego tylko do własnej gałęzi. Palety są następnym punktem pierwotnego backlogu; nie odsuwać ich ponownie na rzecz kolejnej kosmetyki lakieru. Zachować pierwotny koniec doby około 12.11.2026 21:31 Warszawa.

Potwierdzone w źródle `life_props.pallets_empty`: LOD0 to pełne pudełko na każdą warstwę, LOD1 jeden pełny blok. Istniejące prototypy mają stosy 4/8/12/16. `pallet_load` także ma pełną podstawę. Zdjęcia CC0 W.carter z life-r2/refs pokazują duże prześwity i konstrukcję deskowo-klockową. Szczegóły źródła/licencji w PALLET-PREFLIGHT.md tej rundy. Nie wynika z nich nowe rozmieszczenie w Białymstoku; nie dodawać fikcyjnych placów lub obiektów.

Ponownie sprawdzona 12.11.2026 [oficjalna specyfikacja EPAL](https://www.epal-pallets.org/eu-en/load-carriers/epal-euro-pallet): obrys 1200×800 mm, wysokość 144 mm, 11 desek, 9 klocków; w sekcji Design features podano grubość desek 22–24 mm (dla poprzeczek do 25 mm). To punkt odniesienia wymiarów, bez użycia znaków certyfikacyjnych, pieczęci lub logo. Pozostałe proporcje modelu należy oznaczyć WORKING_VALUE, jeśli nie mają źródła.

Najpierw znaleźć czytelne kadry rzeczywistych istniejących stosów w nowym raw, ustalić natywny LOD na Low/High i baseline w czterech warunkach. Nie stosować podwyższonego wspólnego LOD jako substytutu geometrii. Uproszczenie ma zachować widoczne otwory z bliska, jedną istniejącą grupę drewna, obrys i kolizję. Budżet mierzyć na pełnej trasie oraz wszystkich kamerach, draws świata/instancji osobno +0 i tris trasy ≤+2%. LOD1 pełnego bloku także wymaga świadomej oceny wyglądu i kosztu.

Pallet_wood używa dotychczasowego materiału/tekstury; dawny brak euro_pallet_side w spec PBR nie dowodził braku BaseMap. Przed zmianą sprawdzić świeży materiał natywny. Koła/osad/czerń pozostają PARTIAL według rzeczywistych wyników; nie ogłaszać ich przy okazji pełnym PASS.
