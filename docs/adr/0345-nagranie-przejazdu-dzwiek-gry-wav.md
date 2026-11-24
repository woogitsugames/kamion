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

## Wyniki
(uzupełniane po teście — sekcja niżej)
