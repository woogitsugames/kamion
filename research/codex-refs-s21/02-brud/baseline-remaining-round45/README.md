# Runda 45 — sześć pozostałych źródeł P18

Po jednostkowym kontrolnym sukcesie P18-168 koordynator upoważnił wyłącznie ten obieg Commons: sześć wcześniej nieobejrzanych źródeł. P18-168 pozostaje audytem root, a błędnie mapowane stare lokalne 154/159 nie były używane. Każdy plik miał osobne oficjalne API imageinfo i licencję CC BY/BY-SA zweryfikowaną przed pobraniem. Własny User-Agent Mozilla/5.0, odstępy co najmniej 10 sekund między żądaniami, bez równoległych pobrań. Wszystkie 12 żądań zakończyło się HTTP 200, brak 429, brak ponowień i wariantów hostów. Nie jest to gwarancja zniesienia ograniczeń dla innych agentów.

SOURCED [6 plików metadata.json + candidates.csv + indywidualne view_image]: osobiście obejrzano 6 odrębnych źródłowych fotografii, ID 112/114/116/146/147/175. Ogląd 16 listopada 2026, data dzienna bez wymyślonych godzin. Surowe materiały znajdują się poza Git w udokumentowanych ścieżkach candidates.csv. Jeden oryginał 112, pięć podglądów zwróconych dokładnie przez API. Dla podglądów API przy żądaniu 800 zwróciło URL 960 i faktyczny obraz 960 — ich rozdzielczość jest jawnie oddzielona od źródłowego oryginału. Żadnej miniatury ani kopii fotografii nie dodano do pakietu Git, ponieważ są to negatywy celu.

Wynik:

- 112: czysta oliwkowa tylna burta zabytkowej ciężarówki, nie para drzwi.
- 114: Scania z naczepą na mokrej irlandzkiej N4; przód i bok, tył poza kadrem. Woda przy kołach nie jest obserwacją brudu drzwi.
- 116: sam ciągnik od tyłu z widocznym siodłem, bez naczepy.
- 146: skrzynia Enterprise z roletą ponad złożoną platformą windy; brak dwóch pionowych skrzydeł.
- 147: małe Isuzu z otwartą skrzynią, brak zamkniętego boksu i pary drzwi. Deklarowanego brązowoszarego rozbryzgu nie potwierdzono.
- 175: pusta czysta naczepa kłonicowa, brak ścian i drzwi. Deklarowany w P18 brud podwozia/belki/kół nie jest potwierdzony własnym oglądem.

**Przyrost kwalifikacji: A 0 / B 0 / zimowe 0 / Europa 0.** To nie jest wniosek o braku brudu w całym projekcie. B dodatkowo nie przechodzi nowości: wszystkie sześć to stary baseline. Nie zastosowano progu 1000 px do odrzucania starych A; treściowy brak pary drzwi lub jej widoku rozstrzyga niezależnie. Oryginalne 4193 × 2796 czy 6048 × 4032 nie tworzą drzwi, których nie ma w kadrze.

Pokrycie wejściowe po root R44/168: 71/88, pozostałych 17 NOT_REVIEWED. Te sześć rzeczywistych nowych oglądów zamyka 6 źródłowych ID: **77/88, pozostaje 11 NOT_REVIEWED**, do scalenia przez koordynatora. Bez ponownego datowania historycznego ledgeru, bez edycji P18/parenta/Git. Jednostkowe poprawki interpretacji opisano w candidates.csv zamiast nadpisywać materiał bazowy. Nie używano Chrome ani Flickr. Wymagania 20 / 12 / 6 / 6 pozostają otwarte.

Root osobnoobejrzał147 i175 lokalnie, potwierdzając brakcelowejparydrzwi i ograniczenia errat; root-peer-review.json. Nie przypisano root pozostałych4oglądów. Po integracji bieżące pokrycie77/88,11NOT_REVIEWED; A6zograniczeniami/B1 bez przyrostu.
