# ADR 0345 — Nagranie przejazdu do publikacji: dźwięk gry zapisywany przez grę (`-record_audio`), obraz ffmpeg ddagrab

Status: **Proposed** (agent recorder-s24, gameplay-ui, 24.11.2026; gałąź `recorder-s24`). Powiązane: ADR 0286 (`-audio_capture`,
pomiar miksu PC), 0313 (szyna kabiny `CabinBusFilter`, D92), 0333 (tryb bez ramki, power throttling), 0302 (wycieczka
wielokaflowa, `-nav_log`), 0261 (uruchamianie playera Windows).

## Kontekst
Właściciel chce nagrać cały przejazd C → Tykocin (autopilot 50 km/h, ~58 min w buildzie #6) w Full HD 60 kl./s z dźwiękiem
gry i sam opublikować go na YouTube. Na maszynie dewelopera ffmpeg 9.0.2 (Gyan, winget) nie ma pętli zwrotnej WASAPI, a
Windows nie ma urządzenia „Stereo Mix” — dźwięku nie da się nagrać z systemu. Istniejący `-audio_capture` (ADR 0286) to
narzędzie pomiarowe: bufor w RAM na cały czas nagrania (godzina float stereo = 1,4 GB), zapis dopiero na końcu (upadek gry =
brak pliku), znacznik startu tylko w `realtimeSinceStartup`, bez czasu bezwzględnego do zgrania z wideo.

Sprawdzone na tej maszynie (24.11, GTX 1070, sterownik 582.78):
- `h264_nvenc` / `hevc_nvenc` w tej wersji ffmpeg **nie działają** („Required: 13.1 Found: 13.0”, wymagany sterownik ≥ 610);
- `ddagrab` (Desktop Duplication) + `h264_mf` z `-hw_encoding 1` używa „NVIDIA H.264 Encoder MFT” (ten sam sprzętowy koder
  przez Media Foundation) — działa po `hwdownload,format=bgra,format=nv12`; profil High przez `-profile:v 100`
  (nazwy profili nie są przyjmowane); `scale_d3d11=format=nv12` + wejście d3d11 do MF — błąd, odrzucone;
- `-fps_mode cfr` razem z `-copyts` i zegarem ściennym psuje się („frame duplication too large”) — czas pierwszej klatki
  bierzemy z linii `Input #0 ... start:` raportu ffmpeg (`-use_wallclock_as_timestamps 1`), wyjście bez `-copyts`.

## Decyzja
1. **Gra zapisuje własny miks** (`Game.Gameplay.GameAudioRecorder`), domyślnie wyłączone; argument
   `-record_audio <plik.wav>` [`-record_audio_format float|pcm16`, domyślnie float32].
   - Źródło: `CabinBusFilter.OnAudioFilterRead` po gainie kabiny i limiterze (`PushFromBus`) — to, co słyszy gracz; gdy
     słuchacz nie ma szyny kabiny (menu, plac), własny `GameAudioRecorderTap` na obiekcie AudioListenera (sprawdzane co
     0,5 s, podąża za zmianą kamery). Blok z tapu jest pomijany, jeśli szyna dostarczyła blok w ostatnich 200 ms — ten sam
     miks nigdy nie trafia do pliku dwa razy.
   - Wątek audio: jedna kopia do `AudioRingBuffer` (SPSC, bez blokad, bez alokacji, ~21,8 s przy 48 kHz stereo). Blok,
     który się nie mieści, jest odrzucany w całości (przeplot kanałów nie może się przesunąć) i liczony; zapis zastępuje go
     ciszą, więc długość pliku = zegar karty dźwiękowej (zgranie z wideo nie ucieka).
   - Wątek zapisu `WavStreamWriter` (BelowNormal): co 20 ms opróżnia pierścień do pliku, co 2 s przepisuje nagłówek z
     aktualnymi rozmiarami i robi `Flush(true)` — po upadku gry plik jest poprawny do ostatniego punktu kontrolnego.
     `OnApplicationQuit` / `OnDestroy`: opróżnienie, końcowy nagłówek, zamknięcie. Float32: fmt 18 B + chunk `fact`
     (nagłówek 58 B), PCM16: 44 B. Limit RIFF 4 GiB (float stereo 48 kHz ≈ 3,1 h) — po nim próbki są pomijane (`full`).
   - Synchronizacja: przy starcie para (Stopwatch, `DateTime.UtcNow`, `Time.realtimeSinceStartupAsDouble`); wątek audio
     zapisuje znacznik Stopwatch pierwszego bloku i każdego kolejnego. Log: `[RECORD] audio -> ... utc0= realtime0=`,
     `[RECORD] first block utc=... realtime=...` (= próbka 0 WAV), co 60 s stan, `[RECORD] closed ...`. Obok WAV
     `<plik>.sync.json` (przepisywany przy każdym punkcie kontrolnym, tmp + move): `firstBlockUtc`, `lastPushUtc`,
     `lastPushFramesStart`, `framesWritten`, `droppedSamples`, `zeroFilledSamples`, `channelMismatchBlocks`, `closed`.
   - Wyłączone: jedno przejrzenie argumentów przy starcie i jeden odczyt `volatile bool` na blok DSP w szynie kabiny.
   - Zmiana konfiguracji audio w trakcie (inne urządzenie, inna liczba kanałów): bloki o innej liczbie kanałów są
     pomijane i liczone (`mismatch`), ostrzeżenie w logu.
2. **`[NAV] arrived t=... text='Cel osiągnięty'`** — jedna linia, gdy ostatni etap wycieczki zgłasza przyjazd (tylko z
   `-nav_log`, `NavStreamFollower`). Skrypt nagrania kończy na niej; dla starszych buildów rozpoznaje też linię statusu
   ostatniego etapu z `remaining <= 20 m` (= `RouteTracker.ArriveM`).
3. **`scripts/record-drive.ps1`**: player bez ramki 1920x1080, High, `-fps 60`, `-autopilot route -speed 50 -stream 1
   -route_to tykocin -nav_log 5 -record_audio <Out>/audio.wav`; opt-out power throttlingu (ADR 0333); ffmpeg startuje po
   pierwszej linii `[NAV] status` (świat wczytany) + 3 s, z ddagrab monitora 0, koder wybierany próbą: h264_nvenc → h264_mf
   → libx264; 60 kl./s CFR, `u_vbr` 40 Mb/s, GOP 120, profil High, do `video.mkv` (czytelny po przerwaniu). Co 30 s
   sprawdza, czy gra jest na pierwszym planie (ddagrab nagrywa ekran) i przywraca ją, z ostrzeżeniem w `sync.log`.
   Kończy: `-AfterArrivalSeconds` (10) po przyjeździe → `q` do ffmpeg → zamknięcie gry (WAV domyka się w grze) → mux:
   `offset = próbka 0 audio − pierwsza klatka wideo` (`adelay` / `atrim`), dla nagrań ≥ 10 min korekta dryfu zegara
   karty (`asetrate` z klatek vs UTC, gdy ≥ 5 ppm), `apad` + `-shortest`, wideo kopiowane, AAC 320k 48 kHz,
   `+faststart`. Wynik `<Out>/kamion-bialystok-tykocin-1080p60.mp4` + `sync.log` + `sync.json` + `player.log` +
   `ffmpeg.log` + `mux.log`. Exit 0 = przyjazd, 2 = bez przyjazdu (limit czasu), 3 = błąd.
   `-LegacyAudioCapture` dla buildów sprzed tego ADR (np. #7): `-audio_capture` z t0 = 0, zgranie przybliżone (±0,5 s).

## Konsekwencje
- Pełne nagranie robi lider na buildzie #8 (po scaleniu tej gałęzi); komenda w raporcie agenta i niżej.
- Dokładność zgrania: oba zegary to zegar systemowy Windows (`DateTime.UtcNow` w Mono, `av_gettime` w ffmpeg) —
  rozdzielczość do ~16 ms (UNVERIFIED, nie mierzone zdarzeniem audio-wideo); dźwięk silnika nie wymaga zgrania co do klatki.
- Rozmiar: wideo ~40 Mb/s × 3500 s ≈ 17 GB MKV + MP4 tego samego rozmiaru (kopiowanie), WAV float ≈ 1,3 GB; skrypt
  nie kasuje plików pośrednich.
- Pauza (`AudioListener.pause`, pełna mapa) w autopilocie nie występuje; zachowanie `OnAudioFilterRead` w pauzie
  nieustalone (UNVERIFIED) — przy nagraniu z ręczną jazdą nie otwierać pełnej mapy.
- Koder MF (NVENC przez MFT) nie daje trybu stałej jakości jak `-cq` nvenc; `u_vbr` 40 Mb/s to WORKING_VALUE (YouTube
  zaleca 12 Mb/s dla 1080p60 SDR — zapas na ponowną kompresję). Aktualizacja sterownika NVIDIA ≥ 610 włączy h264_nvenc
  (decyzja właściciela, zmiana systemowa).
- Nie zmieniono ProjectSettings, Packages ani asmdef (logika czysta w Game.Core, komponent w Game.Gameplay).

## Uzupełnienia po teście (24.11, ta sama gałąź)
- **Przerwy w strumieniu wypełniane ciszą.** Test 1 (dev build) pokazał 0,7 s brakujących próbek przy zmianie sceny (Boot →
  WorldC: stary AudioListener ginie, tap wraca dopiero przy następnym sprawdzeniu). Bez poprawki dźwięk po wczytaniu świata
  byłby przesunięty względem wideo o tę przerwę. Teraz: gdy blok przychodzi > 0,25 s (WORKING_VALUE) później, niż wynika z
  liczby próbek od pierwszego bloku, przed nim idzie cisza o długości brakującego czasu (`gaps`, `gapFrames` w logu i
  `sync.json`); bez słuchacza recorder szuka nowego co klatkę. Mniejsze różnice = dryf zegara, korygowany w muksie.
- **Wideo końcowe.** NVENC niedostępny (sterownik), więc `-FinalVideo auto` = przechwycenie h264_mf 40 Mb/s jako materiał
  pośredni + **ponowne kodowanie offline libx264 `slow` CRF 18** (High, yuv420p, BT.709, GOP 2 s) po przejeździe — CPU nie
  konkuruje z grą. Z h264_nvenc (sterownik ≥ 610) `auto` kopiuje strumień CQ 19. `-FinalVideo copy|x264`,
  `-FinalPreset`, `-FinalCrf`; `-MuxOnly -Out <katalog>` powtarza zgranie i mux bez ponownego przejazdu.
- Czasy z `sync.json` czytane jako surowy tekst: `ConvertFrom-Json` zamienia daty ISO na DateTime i obcinał milisekundy
  (pierwszy mux testu 3 miał offset błędny o 0,925 s — naprawione, mux powtórzony `-MuxOnly`).

## Wyniki (maszyna dewelopera i5-10400F / GTX 1070 / sterownik 582.78, monitor 1920x1080)
Dowody: `artifacts/recorder-s24/` (kopie w main).
| test | build | wynik |
|---|---|---|
| EditMode `AudioRecorderTests` | — | 10/10 (nagłówki PCM16/float, pierścień: zawijanie, wątki 4 096 000 próbek bez straty, writer z punktami kontrolnymi i odczytem w trakcie, cisza za odrzucone bloki, szyna vs tap, przerwy) |
| upadek gry | dev `02aed4c673` (bez ciężarówki w worktree → brak świata) | proces zabity po 600 s: WAV float 582,7 s poprawny do ostatniego punktu kontrolnego (`closed: false`), 0 odrzuconych |
| pipeline na buildzie #7 | `a8352917be` + `-LegacyAudioCapture` | 151 s wideo, ddagrab + h264_mf High 60 kl./s, ~39 Mb/s, 9 080 klatek (558 duplikatów = 6 %, 2 odrzucone), audio −17,1 dB średnio / −1,4 dB szczyt; zgranie przybliżone (−19,5 s). Na obrazie okno zapory Windows z testu dev buildu (patrz niżej) |
| **pełny tor `-record_audio`** | release `d2933ca96a` (tylko kafel C) | gra na pierwszym planie, 151 s wideo; WAV 160,0 s, 0 odrzuconych, 1 przerwa 1,56 s (zmiana sceny przed startem wideo); offset −8,738 s (audio zaczyna się przed wideo, przycięte); x264 slow CRF 18: 277 s na 151 s materiału (1,83× czasu nagrania), MP4 248 MB, 13,8 Mb/s |
Szacunek dla pełnego przejazdu ~3 500 s (WORKING_VALUE): MKV ~17 GB, WAV ~1,3 GB, MP4 ~6 GB, kodowanie x264 slow ~1 h 45 min
po przejeździe (preset `medium` ~2× szybciej).
Okno „Zabezpieczenia Windows — zezwolić sieciom na dostęp?” pojawiło się po starcie **buildu development** (połączenie z
profilerem nasłuchuje w sieci) i zostało nad grą; buildy release go nie otwierają. Agent nie klikał (ustawienie
bezpieczeństwa należy do właściciela). Pełne nagranie robić na buildzie release.
