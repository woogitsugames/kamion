Diagnoza oczekiwania edge, 12.11.2026 około 15:00 CET. To informacja o centralnym zasobie, nie REPORT zakończonej rundy.

Fakty odczytane na żywo:
- Bieżący skrypt main scripts/unity-slot.ps1 ma mtime 14:49:36 i blokuje PHONE_RUN tylko dla puli unity. Pula heavy zachowuje limit 3 i FIFO.
- Nasz nowy Acquire gpt-edge-r6 działa od 14:55:45. Raportuje heavy 0/3, phone=True, queue ahead=11. Nie uruchomił Pythona ani nie posiada slotu.
- Jedenaście pozostałych procesów Acquire heavy powstało przed aktualizacją skryptu: landmarks-r4 13:53, life-r5 13:58, vegetation-r4 14:04, light-r6 14:06, frontage-r2 14:14, asphalt-r3 14:16, lowread 14:25, furniture-r3 i truck-r4 14:26, cab-r4 14:30, putry-deck 14:36.
- PowerShell wykonuje już wczytaną treść skryptu; edycja pliku nie aktualizuje instrukcji aktywnej pętli.

Wniosek: kolejka prawdopodobnie nadal ma na początku stare Acquire blokowane przez PHONE_RUN. Nowy Acquire heavy nie może ich wyprzedzić, mimo wolnej puli. Samo zapisanie nowej wersji skryptu nie wystarcza dla już działających oczekiwań.

Do koordynacji przez właściciela wspólnego mechanizmu: wznowienie starszych Acquire po aktualizacji albo normalne zakończenie PHONE_RUN zgodnie z rzeczywistym pomiarem lidera. Edge nie restartuje cudzych procesów, nie usuwa blokad ani biletów i nie używa Priority.

Osobny błąd pierwszej próby edge: centralne Set-Content własnego pliku gpt-edge-r6.wait dostało sharing violation. Stało się to przed uruchomieniem zadania, a zależne importy i audyty poprawnie się zatrzymały. Logi zachowano. Własny wrapper ponawia wyłącznie przejściową blokadę własnego biletu, zawsze przez aktualny centralny skrypt i standardowe FIFO.
