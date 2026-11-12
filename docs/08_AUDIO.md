# 08 — Audio

Decyzja właściciela: na start darmowe źródła i dźwięki generowane (AI / synteza), Suno ewentualnie dla muzyki. Budżet 0 zł.

## 1. Zasady licencyjne (twarde)
- **Suno: darmowy plan nie daje praw do użytku komercyjnego** (stan na 2026 — zweryfikuj aktualny regulamin). Utwory z darmowego planu = tylko do prototypu, oznaczone `PROTOTYPE_ONLY`, do wymiany przed publikacją lub przegenerowania na planie z prawami komercyjnymi (decyzja właściciela).
- Każdy dźwięk w `docs/LICENSES.md`: źródło, autor, licencja (CC0 preferowane; CC-BY z atrybucją w credits), data, modyfikacje.
- Generatory SFX (np. narzędzia AI dostępne właścicielowi) — tylko gdy warunki pozwalają na użytek komercyjny; zapisz plan/warunki w rejestrze.
- Zakaz nagrań silników konkretnych marek z gier/filmów/YouTube.

## 2. Architektura
- FMOD for Unity (jeśli warunki darmowej licencji pasują — zweryfikuj) lub Unity Audio + własny mikser. ADR.
- **Silnik**: warstwy pętli (on-load / off-load × zakresy RPM) z crossfadem sterowanym RPM i obciążeniem z fizyki; dodatkowo: rozruch, wyłączenie, jałowy klekot, turbo (gwizd i „psst” z wastegate sterowane ciśnieniem doładowania), hamulec silnikowy, retarder, skrzynia (wycie, zmiana biegu), pneumatyka (zwolnienie hamulca, postojowy, osuszacz, kompresor), kierunkowskazy, przełączniki, wycieraczki, deszcz o dach i szyby, opony × nawierzchnia × prędkość, wiatr, zawieszenie na nierównościach, otoczenie miasta.
- Filtrowanie kabina/zewnątrz (okluzja, EQ), przestrzenne źródła na pojeździe (silnik z przodu, wydech, naczepa).
- Stan (ADR 0137/0138/0142): dwa zestawy przełączane w Ustawieniach (DŹWIĘK → Zestaw dźwięków: synteza / ElevenLabs). Zestaw ElevenLabs: silnik z nagrań, efekty B–G sterowane zdarzeniami fizyki i sterowania, turbo v2 (gwizd REGEN-02 + szum proceduralny), osobny miks kabiny (opony ≥ silnik przy 80 km/h). Wycieraczki i deszcz czekają na pogodę/przełącznik oraz nagranie z równym rytmem. Proceduralny wózek widłowy wyciszony (powodował „syrenę”, ADR 0142 §1). Opony w poślizgu (ADR 0145): dwie warstwy, **szuranie** (kąt znoszenia osi naczepy przy małej prędkości, 1–5°, 1–40 km/h) i **pisk** (poślizg kombinowany ≥ 1,3 × próg, od 18 km/h); nagrania REGEN-03 w obu zestawach, synteza tylko jako zapas.
- Głośność i dynamika dopasowane do słuchawek i głośnika telefonu (dwa profile miksu), normalizacja (np. −16 LUFS dla mobile, do ustalenia).

## 3. Produkcja przy 0 zł
1. **Synteza proceduralna** (Python numpy/scipy) silnika diesla: model harmoniczny z rzędem zapłonów R6, modulacja obciążeniem, szum spalania, rezonanse wydechu i kabiny — jako baza warstw; plus własne nagrania właściciela (np. ciężarówka na postoju/odjeżdżająca z daleka na parkingu, bez identyfikowalnych osób) jako tekstura i referencja.
2. **CC0 biblioteki** (np. Freesound z filtrem CC0 — sprawdź każdy plik) dla pneumatyki, przełączników, deszczu, otoczenia.
3. **Generatory AI** zgodnie z sekcją 1.
4. Odsłuch porównawczy: agent generuje spektrogramy i porównuje z referencją; **ostateczna ocena — ucho właściciela** na telefonie (głośnik i słuchawki).

## 4. Muzyka
Radio w kabinie (opcjonalne, później): utwory z prawami komercyjnymi; fikcyjne stacje radiowe. Muzyka menu — subtelna albo żadna; lepiej cisza i dźwięk silnika na postoju niż generyczny „epicki” utwór.

**Kandydat (2026-11-10, decyzja właściciela: notatka na później, po bramce 3):** [YuE](https://github.com/multimodal-art-projection/YuE) — otwarty model tekst → piosenka (wokal + podkład), lokalnie. Przed użyciem: zweryfikować licencję wag i kodu (`UNVERIFIED`: prawdopodobnie Apache 2.0), pochodzenie danych treningowych, jakość polskiego wokalu (próbki do oceny właściciela), wymagania GPU (nie w czasie renderów/pomiarów). Zastosowanie tylko fikcyjne stacje radia w kabinie; anti-slop jak w docs/06.

## 5. Bramka audio (Etap 5)
Wszystkie warstwy z sekcji 2 obecne, brak kliknięć/pętli słyszalnych, płynne przejścia RPM, różnica wnętrze/zewnątrz, zgodność z fizyką (obroty, obciążenie, retarder), rejestr licencji kompletny, oznaczenia `PROTOTYPE_ONLY` wypisane.
