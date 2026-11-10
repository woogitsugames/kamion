# Test wrażeń z jazdy (telefon) — instrukcja dla właściciela

Cel: ocenić, jak ciężarówka **czuje się w dłoniach** i czy odcinek wygląda jak prawdziwa ulica Białegostoku. To jest lista z `docs/reports/GATE-3-draft.md` („Test feelingu właściciela”) w wersji do zrobienia z telefonem w ręku. Zajmuje ok. 20–30 min.

## Przed startem
1. Zainstaluj APK od lidera (telefon odblokowany, ekran nie gaśnie, najlepiej ładowarka).
2. Uruchom grę. Zobaczysz **menu startowe** (zrzut: `docs/owner/img/start-menu.png`, ustawienia: `docs/owner/img/settings.png`).
3. Ustaw opcje (zmiany działają od razu i zapamiętują się):
   - **Pora dnia** (tylko trasy): Pochmurno / Niskie słońce / Zmierzch.
   - **Jakość grafiki**: Low / Medium / High / Ultra. Zalecenie: słabszy telefon Low lub Medium, flagowiec High.
   - **Limit klatek**: 30 lub 60 FPS (zalecenie: 30 na słabszym, 60 na flagowcu).
4. **Ustawienia sterowania** (też z jazdy, przycisk „Ustawienia”): zakres kierownicy, czułość, samocentrowanie, krzywe pedałów, gyro (włącz/wyłącz, czułość, kalibracja), kamera (czułość rozglądania, pole widzenia, ruch głowy). Zacznij od ustawień domyślnych; jeśli coś Ci nie pasuje, zmień **jedną rzecz naraz** i zapamiętaj co.

## Co przejechać
Każdy odcinek zrób **ręcznie** (bez autopilota), minimum 2 razy: raz w trybie kierownicy dotykowej, raz w gyro. Zmieniaj pory dnia między podejściami.

| # | Start w menu | Co robisz |
|---|---|---|
| 1 | **DrivingLab** | 3 min na placu: ruszanie, hamowanie do zera, slalom, cofanie (bieg R), zmiana kamery, rozglądanie gestem. Tu oceniasz samo sterowanie bez wpływu świata. |
| 2 | **Trasa G3-A** (Kwadrat Park, brama, Bieżeństwa, ok. 440 m) | Przejedź całość płynnie, bez zatrzymywania. Raz w pochmurno, raz w niskim słońcu. |
| 3 | **Trasa G3-B** (Andersa, Rondo Putry, ok. 490 m) | Rondo, straż pożarna przy poboczu. Raz w zmierzchu. |

Do menu wracasz przyciskiem **Menu** (górny rząd) lub klawiszem „wstecz” telefonu — **bez restartu aplikacji**; zmień opcje i startuj ponownie. Przycisk „Reset” w jeździe stawia zestaw na starcie odcinka.

## Co oceniasz (tak / nie / uwaga)
Sterowanie (najważniejsze):
- [ ] Skręt idzie **w dobrą stronę** w obu trybach (kierownica, gyro)? Kierownica wraca do środka z odpowiednią siłą?
- [ ] Brak wyczuwalnego opóźnienia między palcem a kołami? Pedały: da się delikatnie dozować gaz i hamulec?
- [ ] Ciężarówka zachowuje się jak 40 t: bezwładność, pochylanie się przy hamowaniu, zakręt z naczepą?
- [ ] Kamera z kabiny: wysokość oczu, pole widzenia, ruch głowy (bez mdłości?), rozglądanie gestem.

Wygląd i świat (jak w GATE-3):
- [ ] Pierwsze wrażenie: ulica Białegostoku czy „typowa gra mobilna”?
- [ ] Asfalt i oznakowanie; budynki (Kwadrat Park, straż pożarna, wiadukt) — rozpoznajesz miejsce? Co zdradza sztuczność?
- [ ] Światło i niebo w trzech porach dnia: wiarygodne?
- [ ] Roślinność i pobocza; skala i prędkość (2,5 m oczu, szerokość pasa).
- [ ] Płynność (rondo, wiadukt, zmiana LOD), nagrzewanie po ~2 min, czas ładowania sceny, brak zabicia procesu.
- [ ] **Decyzja:** akceptuję kierunek artystyczny i skalujemy mapę — tak / nie / tak, z poprawkami: ____

## Jak zgłosić wyniki
1. Napisz do lidera: model telefonu, profil i FPS (z menu), które odcinki i pory, odpowiedzi z listy wyżej (tak/nie/uwaga) i **3 największe problemy** własnymi słowami. Zrzuty ekranu lub krótkie nagranie ekranu mile widziane.
2. **Nie musisz nic kopiować z telefonu.** Gra zapisuje każdy ruch sterowania i każdą zmianę ustawień w logach (linie `[CONTROLS]`); lider odczyta je po podłączeniu telefonu (`adb logcat -d -s Unity | grep CONTROLS`) i odtworzy, co robiłeś: wybór menu, ustawienia, gaz/hamulec/skręt, biegi, zmiany kamery, powroty do menu. Podaj tylko **godzinę końca sesji**, żeby lider znalazł właściwy fragment. Logi wyczyszczą się po restarcie telefonu, więc nie rób go przed zgłoszeniem.
3. Jeśli gra się zawiesi lub zamknie: napisz, **co robiłeś chwilę wcześniej** i w jakim profilu graliście.
