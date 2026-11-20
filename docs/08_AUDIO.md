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
- Stan (ADR 0137/0138/0142): dwa zestawy przełączane w Ustawieniach (DŹWIĘK → Zestaw dźwięków: synteza / ElevenLabs). Zestaw ElevenLabs: silnik z nagrań, efekty B–G sterowane zdarzeniami fizyki i sterowania, turbo v2 (gwizd REGEN-02 + szum proceduralny), osobny miks kabiny (opony ≥ silnik przy 80 km/h). Wycieraczki i deszcz czekają na pogodę/przełącznik oraz nagranie z równym rytmem. Proceduralny wózek widłowy wyciszony (powodował „syrenę”, ADR 0142 §1). Opony w poślizgu (ADR 0145): dwie warstwy, **szuranie** (kąt znoszenia osi naczepy przy małej prędkości, 1–5°, 1–40 km/h) i **pisk** (poślizg kombinowany ≥ 1,3 × próg, od 18 km/h); nagrania REGEN-03 w obu zestawach, synteza tylko jako zapas. Sprężarka powietrza (ADR 0148): 0,06 zamiast 0,35, bo przy 0,35 na jałowym i przy toczeniu na biegu była głośniejsza od silnika i jej „pu-pu” 14 Hz zastępowało harmoniczne zapłonu; odtwarzanie miksu z gry: `IdleAudioCaptureTests` + `tools/audio/idle_render.py`. Zestaw syntezy, model 0232 (ADR 0232): barwa silnika zależna od obciążenia, dawka regulatora na jałowym, hamulec silnikowy wg krzywej momentu z fizyki, turbo i pneumatyka z modelu wypływu; odsłuch A/B na telemetrii z `tools/physics-runner`: `cd tools/audio; uv run python render_ab0232.py` → `artifacts/audio-0232/`.
- Głośność i dynamika dopasowane do słuchawek i głośnika telefonu (dwa profile miksu), normalizacja (np. −16 LUFS dla mobile, do ustalenia).
- **PC (D73, ADR 0286):** import Standalone = PCM Decompress On Load dla wszystkich klipów (Android bez zmian: ADPCM / Vorbis 0,7); player Windows ustawia przy starcie bufor DSP 512 i 64 głosy realne (WORKING_VALUE, projekt: 1024 / 32 — wspólny z Androidem; przy 32 głosach w kabinie wyciszane są słyszalne tło, wiatr, sprężarka i wycie skrzyni — zmierzone, ADR 0286). Zmierzone w playerze (plac, zestaw ElevenLabs): kabina −20,8 LUFS, zewnątrz −29,7 LUFS, bez przesterowań (true peak ≤ −6,6 dBTP), klipy 100,4 MB. Pomiar miksu w playerze: `-audio_capture plik.wav -audio_stats 1 [-audio_view cab|chase]` → `cd tools/audio; uv run python pc_capture.py <wav> <katalog>` (LUFS BS.1770-4, true peak, przesterowane próbki, spektrogram). **Głośność kabiny (D92, ADR 0312):** −18 LUFS zintegrowane ±1 dla programu „rozpędzanie 0→50 + 50 km/h + jałowy” (DrivingLab, 40 t), true peak ≤ −1 dBTP; zewnątrz bez zmian. Realizacja: szyna słuchacza `CabinBusFilter` (jeden gain dla całego miksu w kabinie — balans warstw bez zmian; gain z pomiaru per zestaw w `CabinLoudness`, limiter look-ahead −1,5 dBFS); pomiar/kalibracja `pwsh tools/audio/lufs_runs.ps1` + `tools/audio/lufs_calibrate.py`; A/B `-audio_cab_gain_db X`.

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
