# Przygotowanie rundy 2 — zabrudzenia i zużycie

Runda 2 zaczyna się dopiero po końcowym GIS, raporcie i skopiowaniu artefaktów r1. W tym samym worktree należy utworzyć gpt-truck-r2, scalić main do własnej gałęzi i zrobić aktualny baseline. Nie wolno przenosić liczb r1 jako pomiaru nowej bazy po scaleniu.

Obejrzane rzeczywiste zdjęcia znajdują się w głównym repo, Data/photos/nowe. Licencje i autorzy są zapisani w docs/REFERENCES.md:

- trailer_Tony_Powell_Transport_ML02_PNZ_DAF_CF_artic_curtainsider_Port_of_Teignmouth_24_April_2012.jpg — Barry Lewis, CC BY 2.0. Mokra ulica, starsza żółta plandeka: zabrudzenie przy górnej szynie, szerokie pionowe smugi, dolne zagięcia i miejscowo wytarty osprzęt. Biały jest tylko dach kabiny, nie cała kabina.
- trailer_Richard_Westbury_Volvo_FH460_artic_curtainsider_Port_of_Teignmouth_29_March_2012.jpg — Barry Lewis, CC BY 2.0. Ciemna plandeka z naprawami przy dolnym brzegu, nierównymi smugami i miejscowo jaśniejszymi pasami. Wysoka pozycja kamery i inne światło wykluczają bezpośrednią kalibrację jasności.
- Volvo_Truck_FH-Semi-trailer_truck-03ASD.jpg — Asurnipal, CC BY-SA 4.0. Tył ciągnika: rzeczywiste matowe błotniki, delikatny kurz na odsłoniętych górnych powierzchniach, miejscowa korozja stalowego osprzętu. Nie jest to biały lakier.

Pierwsza kontrola powinna porównać _Dirt 0, 0,5 i 1 na identycznym renderze obu pojazdów, ograniczając modyfikację do tymczasowych materiałów Kamion/Truck Exterior i przywracając wartości w finally. Pozwoli oddzielić brud proceduralny od samego kształtu i tekstur. Próbki pomiarowe należy wyznaczyć na nowym baseline, poza lampami, kołami i krawędziami sylwetki.

Obecny shader ma już pas rozbryzgu od kół, model pochodzenia brudu plandeki i kurz na powierzchniach skierowanych ku górze. Nie należy dublować ich przypadkowym szumem. Low wyłącza drobne smugi przez _KamionGrimeDetailOff, ale zachowuje makroskopowy pas zabrudzenia. Ewentualna poprawka powinna zachować czytelną skalę zabrudzeń także na Low, bez dodatkowych tekstur, przebiegów ani rozbudowanych pętli.

WorldTruckInstaller.InstallBatch sam wywołuje TruckAssetBuilder.Build i TrailerAssetBuilder.Build. W kolejnych rundach wystarczy jeden taki kanoniczny krok zamiast trzech powtarzających budowanie tych samych zasobów. Przed Unity obowiązuje slot gpt-truck, ciężkie zadania Pythona muszą używać heavy z Owner gpt-truck-r2. Pełny GIS dopiero na końcu rundy; pośrednio tylko potrzebne pojedyncze pliki testowe.

Po wykonaniu backlogu r2/r3 należy wrócić do największego nadal widocznego odstępstwa. Kontrola obecnych materiałów potwierdziła: przednia szyba MI_Ext_Glass ma _ExteriorTransmission 1 i _Opacity 0,16; boczne MI_Ext_DoorGlassL/R mają dodatkowe tłumienie 0,42. Nie należy błędnie diagnozować mleczności przedniej szyby jako skutku jej parametru 0,42. Odczyt nie dowodzi przyczyny D44 i nie zastępuje przyszłej kontrolowanej próby odbicia, absorpcji i mieszania.
