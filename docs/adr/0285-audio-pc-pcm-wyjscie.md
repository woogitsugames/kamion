# ADR 0285 — Dźwięk na PC: import PCM dla Standalone, wyjście audio playera Windows, pomiar miksu w playerze

Status: Proposed (agent audio-pc-s23, gałąź `audio-pc-s23`), 2026-11-16. **Numer do potwierdzenia przez lidera**
(0284 zajęty przez noc PC — HANDOVER 16.11 19:5x). Do scalenia przez lidera.
Powiązane: D73 / ADR 0260 (Windows platformą główną), 0261 (build/run Windows), 0266 (budżety PC), 0007 (budżet
głosów Helio G99), 0137/0142 (zestaw ElevenLabs), 0148 (przechwyt miksu w PlayMode), 0232 (synteza 0232), 0270
(głośności kanałów).

## Kontekst
Ustawienia audio były strojone pod telefon: importer (`VehicleAudioPostprocessor`) ustawiał tylko
`defaultSampleSettings` — pętle ADPCM Compressed In Memory, one-shoty ADPCM / Vorbis q 0,7 — i Windows dostawał to
samo. `AudioManager.asset` (wspólny dla platform): bufor DSP 1024, **32 głosy realne**, stereo, bez spatializera,
częstotliwość = domyślna urządzenia.

## Audyt (stan przed zmianą)
| Pozycja | Stan | Ocena na PC |
|---|---|---|
| Źródła WAV | 48 kHz mono 16-bit (synteza i ElevenLabs po `el_prepare`), 280 klipów, 105 MB PCM | OK — mono jest właściwe dla źródeł 3D; nic do „podnoszenia” |
| `forceToMono` + `normalize` | włączone; źródła już mono | test: brak normalizacji szczytu przy imporcie (poziomy komórek zachowane) |
| Kompresja pętli | ADPCM (4 bity, ok. 3,5:1) | **zmiana** — symulacja IMA ADPCM: SNR gwizdu turbo 25,8 dB, silnik ext on 1800 38,4 dB, szum płaski −83 dBFS/pasmo, ponad sygnałem > 5 kHz (`artifacts/audio-pc-s23/adpcm/`) |
| One-shoty EL | Vorbis q 0,7 | **zmiana** na PCM |
| Bufor DSP | 1024 (21,3 ms przy 48 kHz) | **512** (10,7 ms) na PC |
| Głosy realne | 32 | **64** na PC — w przebiegu 46–50 źródeł gra jednocześnie (PerspectiveLoop = zawsze 2 grające źródła, także przy głośności 0) |
| Wyjście | stereo, spatializer brak | bez zmian (5.1 — patrz „Otwarte”) |
| Render `render_all.py` | 191 WAV bit-identycznych z repo | deterministyczny; podglądy OGG różnią się bajtowo (koder Vorbis) — nie commitowane |

## Decyzja
1. **Import (kod, `VehicleAudioImporter.cs`):** override `BuildTargetGroup.Standalone` = PCM, Decompress On Load,
   oryginalna częstotliwość, preload — dla wszystkich klipów obu zestawów (pętle i one-shoty). Domyślne (Android) bez
   zmian, bez override Android. `GetVersion()` = 2 wymusza reimport w istniejącej Library. Pamięć: ok. 105 MB PCM
   (zmierzona w playerze — niżej) wobec budżetu prywatnej pamięci 4096 MB (klasa min, WORKING_VALUE). PCM zamiast
   Vorbis q 1,0: zero kosztu dekodowania na ~50 głosów, brak ryzyka szwu/seek na krótkich pętlach silnika
   wyrównywanych fazą (`timeSamples`).
2. **Wyjście (kod, `Audio/PcAudioRuntime.cs`, bez zmiany ProjectSettings):** w playerze Standalone przed załadowaniem
   pierwszej sceny `AudioSettings.Reset` z buforem DSP 512 i 64 głosami realnymi (`WORKING_VALUE`) (wirtualne ≥ realne). Argumenty
   `-audio_dsp N` / `-audio_voices N` (0 = wartość projektu) do porównań. Android/edytor bez zmian.
3. **Pomiar w playerze (Development lub zwykły, tylko z argumentami):** `-audio_capture plik.wav` nagrywa miks
   AudioListenera (`OnAudioFilterRead`, bufor prealokowany, zero alokacji w wątku audio) do WAV float 32;
   `-audio_stats 1` loguje co 1 s liczbę źródeł grających / wirtualnych / słyszalnych-wirtualnych; na końcu pamięć
   klipów (`Profiler.GetRuntimeMemorySizeLong`). Analiza: `tools/audio/pc_capture.py` (BS.1770-4: LUFS zintegrowane,
   short-term, LRA, true peak 4×, próbki ≥ 0 dBFS, spektrogram).

## Pomiary
Build Development Win64 `6b67d7795`, plac `DrivingLab`, autopilot `straight080` 40 t (0→80 km/h 47,9 s, jazda, hamowanie
awaryjne, postój na jałowym), okno 1600×900, Medium, 60 FPS, maszyna deweloperska (RTX 5070 — nie referencja), jeden
player naraz w slocie heavy. **Zestaw dźwięków: ElevenLabs** (zapisana preferencja tej maszyny, log
`[AUDIO] ... engine=ElevenLabs`; zestawu syntezy nie mierzono). Przechwyt 70 s od t = 10 s; odcinki z czasu autopilota
(koniec przebiegu w logu przy t ≈ 60,8 s, postój 3,5 s, jazda 4 s): rozpędzanie 0–42 s, **jazda 80 km/h 43–47 s**,
postój na jałowym 52–70 s (przebieg 32 głosów przesunięty o −1,7 s wg jego logu). Wszystko: `artifacts/audio-pc-s23/`
(WAV, `report/*.json`, spektrogramy, logi `logs/win-run-20261116-{200754,204633,204812}.log`).

| Przebieg | Głosy / DSP | LUFS zintegr. | short-term max | LRA | true peak | próbki ≥ 0 dBFS | korelacja L/P |
|---|---|---|---|---|---|---|---|
| kabina PC | 64 / 512 | **−20,8** (rozpędzanie −20,5; jazda 80 km/h −22,2; postój −37,6) | −18,7 | 18,6 LU | −6,6 dBTP | **0** | 1,00 (mono) |
| zewnątrz (chase) PC | 64 / 512 | **−29,7** (rozpędzanie −33,0; jazda −35,7; postój −25,7 — ptaki, niżej) | −22,0 | 12,8 LU | −11,9 dBTP | **0** | 0,98 |
| kabina, ustawienia projektu | 32 / 1024 | −21,0 (rozpędzanie −20,6; jazda −22,2; postój −40,5) | −19,1 | 21,2 LU | −8,0 dBTP | 0 | 1,00 |

- **Głosy:** 70 źródeł na pojeździe/otoczeniu, **46–51 grających jednocześnie**. Przy 32 głosach (ustawienie projektu,
  także Android) w **91 z 92** próbek sekundowych (pierwsza: scena jeszcze bez źródeł) co najmniej jedno **słyszalne**
  źródło było zwirtualizowane (wyciszone): `AmbientBed/cab` (91 s), `GearWhine/cab` (54), `Compressor/cab` (53),
  `Wind/cab` (53), `Ambient/Birds` (9) — PerspectiveLoop gra zawsze oba źródła (także przy głośności 0), a tło ma
  priorytet 160 (wyższa liczba = mniej ważne). Skutek w widmie kabiny na postoju (jałowy, sprężarka i tło): 200–1000 Hz
  −4,0 dB, LUFS −2,9 LU. Przy 64 głosach: 0 słyszalnych wirtualnych, szczyt 51 realnych — **zmierzone tylko na placu
  (DrivingLab); w scenach świata z ruchem/otoczeniem liczba źródeł może być większa → 64 = `WORKING_VALUE`.**
- **Pamięć klipów:** 280 klipów, wszystkie załadowane, **100,4 MB** (MiB; PCM Decompress On Load,
  `Profiler.GetRuntimeMemorySizeLong`) — zgodne z 105,4 mln bajtów plików WAV (≈ 100,5 MiB). ADPCM na Androidzie bez zmian.
- **Kliknięcia:** skan nieciągłości (`pc_capture.py`: górnoprzepustowo 12 kHz, ramki 128 próbek, +20 dB ponad medianę
  1 s; wykrywa skok −34 dBFS na sygnale silnikowym, nie wykrywa −46 dBFS): kabina 64 i 32 głosy — **0 zdarzeń**; chase —
  19 trafień, wszystkie w zdarzeniach ptaków (57,8–58,6 s, 66,0–66,8 s), na końcu hamowania (49,9 s) i na ostatniej
  ramce (69,8 s); żadne nie leży na szwie pętli silnika.
- **Wątek audio:** marker `Audio.Thread` średnio 0,25 ms / klatkę (64 głosy, DSP 512) wobec 0,14 ms (32 / 1024).
- **Clipping:** brak przesterowanych próbek i brak próbek > −0,1 dBFS w żadnym przebiegu; zapas true peak ≥ 6,6 dB.
- **Obserwacje do oceny właściciela (miksu nie zmieniano):** (a) przełączenie kabina → zewnątrz obniża głośność o ok.
  **12–13 LU** w tych samych fazach (rozpędzanie −20,5 → −33,0, jazda −22,2 → −35,7; silnik 3D, rolloff log.,
  `minDistance` 4 m, kamera chase kilkanaście m); (b) na postoju w widoku zewnętrznym dwa zdarzenia osiągają −17 LUFS
  momentary, ok. 14 LU ponad silnik na jałowym — to **sikora (`bird_tit.wav`)**: korelacja nadwyżki widma zdarzenia
  57,7–58,8 s z widmem klipu 0,88 (następny kandydat `bird_sparrow` 0,34; pneumatyka ≤ 0,28); (c) miks kabiny jest mono (korelacja 1,00: źródła kabiny 2D, klipy mono) — stereo w kabinie wymagałoby
  panoramy/źródeł stereo, osobna decyzja; (d) zmiany biegu w kabinie to krótkie spadki do ok. −33 LUFS momentary.
- Symulacja ADPCM (nie enkoder Unity): `tools/audio/pc_adpcm_sim.py` → SNR gwizdu turbo 25,8 dB, silnik ext on
  1800 38,4 dB, EL gwizd w kabinie 34,2 dB; szum ADPCM ponad sygnałem powyżej ok. 5 kHz.

## Otwarte
- **Docelowa głośność miksu PC** — decyzja właściciela (docs/08 §2: „−16 LUFS dla mobile, do ustalenia”). Propozycja
  `WORKING_VALUE`: kabina, jazda ze stałą prędkością, master 1,0: −18 LUFS ±2, true peak ≤ −1 dBTP. Miksu nie
  przestrajano w tym ADR.
- **5.1/7.1:** wyjście zostaje stereo (słuchawki i głośniki PC); `AudioSettings.driverCapabilities` pozwala później
  przełączyć tryb głośników w Ustawieniach (UI poza zakresem).
- **Android ma ten sam problem 32 głosów** (wyciszone tło/wiatr/sprężarka/wycie skrzyni w kabinie). Do decyzji lidera:
  podnieść `m_RealVoiceCount` w `ProjectSetup` (koszt CPU na Helio G99, ADR 0007, do zmierzenia na telefonie) albo
  zatrzymywać niesłyszalne źródła `PerspectiveLoop` / poprawić priorytety (zmiana miksu — osobne zadanie audio).
- **Zawieszenie playera** (`-quit_t`): 2026-11-16 19:20–19:24 dwa przebiegi (jeden bez argumentów audio) nie zakończyły
  się w czasie, gdy na maszynie działały równolegle 3 gry; przebiegi 20:07–20:49 (pojedynczo, slot heavy, kod bez
  rejestratorów wszystkich markerów audio) kończyły się kodem 0. **Nie odtworzone z końcowym kodem, przyczyna
  nieustalona** (zmieniły się naraz dwie rzeczy).
- **Reimport:** `GetVersion()` = 2 → jednorazowy reimport 280 klipów audio w każdym checkoucie po scaleniu.
- Odsłuch właściciela (głośniki PC i słuchawki): `artifacts/audio-pc-s23/player/*.wav`.
