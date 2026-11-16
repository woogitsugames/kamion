# ADR 0284 — Dźwięk na PC: import PCM dla Standalone, wyjście audio playera Windows, pomiar miksu w playerze

Status: Proposed (agent audio-pc-s23, gałąź `audio-pc-s23`), 2026-11-16. **Numer do potwierdzenia przez lidera**
(ostatni przydzielony w HANDOVER: 0283). Do scalenia przez lidera.
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
   pierwszej sceny `AudioSettings.Reset` z buforem DSP 512 i 64 głosami realnymi (wirtualne ≥ realne). Argumenty
   `-audio_dsp N` / `-audio_voices N` (0 = wartość projektu) do porównań. Android/edytor bez zmian.
3. **Pomiar w playerze (Development lub zwykły, tylko z argumentami):** `-audio_capture plik.wav` nagrywa miks
   AudioListenera (`OnAudioFilterRead`, bufor prealokowany, zero alokacji w wątku audio) do WAV float 32;
   `-audio_stats 1` loguje co 1 s liczbę źródeł grających / wirtualnych / słyszalnych-wirtualnych; na końcu pamięć
   klipów (`Profiler.GetRuntimeMemorySizeLong`). Analiza: `tools/audio/pc_capture.py` (BS.1770-4: LUFS zintegrowane,
   short-term, LRA, true peak 4×, próbki ≥ 0 dBFS, spektrogram).

## Pomiary
Build Development Win64 `6b67d7795`, plac `DrivingLab`, autopilot `straight080` 40 t (0→80 km/h 47,9 s, jazda, hamowanie
awaryjne, postój na jałowym), okno 1600×900, Medium, 60 FPS, maszyna deweloperska (RTX 5070 — nie referencja), jeden
player naraz w slocie heavy. Przechwyt 70 s od t = 10 s. Wszystko: `artifacts/audio-pc-s23/` (WAV, `report/*.json`,
spektrogramy, logi `logs/win-run-20261116-{200754,204633,204812}.log`).

| Przebieg | Głosy / DSP | LUFS zintegr. | short-term max | LRA | true peak | próbki ≥ 0 dBFS | korelacja L/P |
|---|---|---|---|---|---|---|---|
| kabina PC | 64 / 512 | **−20,8** (jazda 80 km/h −21,8; postój −37,6) | −18,7 | 18,6 LU | −6,6 dBTP | **0** | 1,00 (mono) |
| zewnątrz (chase) PC | 64 / 512 | **−29,7** (rozpędzanie −32,8) | −22,0 | 12,8 LU | −11,9 dBTP | **0** | 0,98 |
| kabina, ustawienia projektu | 32 / 1024 | −21,0 (jazda −22,8; postój −40,5) | −19,1 | 21,2 LU | −8,0 dBTP | 0 | 1,00 |

- **Głosy:** 70 źródeł na pojeździe/otoczeniu, **46–51 grających jednocześnie**. Przy 32 głosach (ustawienie projektu,
  także Android) w 92 z 92 próbek sekundowych co najmniej jedno **słyszalne** źródło było zwirtualizowane (wyciszone):
  `AmbientBed/cab` (61 s), `GearWhine/cab` (54), `Compressor/cab` (53), `Wind/cab` (53), `Birds` (9) — PerspectiveLoop
  gra zawsze oba źródła (także przy głośności 0) z priorytetem wyższym niż tło. Skutek w widmie kabiny: jałowy
  200–1000 Hz −4,0 dB, jazda 80 km/h −0,9…−1,0 dB we wszystkich pasmach względem 64 głosów. Przy 64 głosach: 0
  słyszalnych wirtualnych, szczyt 51 realnych.
- **Pamięć klipów:** 280 klipów, wszystkie załadowane, **100,4 MB** (PCM Decompress On Load,
  `Profiler.GetRuntimeMemorySizeLong`). ADPCM na Androidzie bez zmian.
- **Wątek audio:** marker `Audio.Thread` średnio 0,25 ms / klatkę (64 głosy, DSP 512) wobec 0,14 ms (32 / 1024).
- **Clipping:** brak przesterowanych próbek i brak próbek > −0,1 dBFS w żadnym przebiegu; zapas true peak ≥ 6,6 dB.
- **Obserwacje do oceny właściciela (miksu nie zmieniano):** (a) przełączenie kabina → zewnątrz obniża głośność o ok.
  9 LU (silnik 3D, rolloff log., `minDistance` 4 m, kamera chase kilkanaście m); (b) na postoju w widoku zewnętrznym dwa
  zdarzenia ptaków osiągają −17 LUFS momentary, ok. 14 LU ponad pracujący na jałowym silnik (spektrogram 57–59 s i
  65–68 s); (c) miks kabiny jest mono (korelacja 1,00: źródła kabiny 2D, klipy mono) — stereo w kabinie wymagałoby
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
- **Zawieszenie playera przy wyjściu** (`-quit_t`): 2026-11-16 19:20–19:24 dwa przebiegi (jeden bez argumentów audio)
  nie zakończyły się w czasie, gdy na maszynie działały równolegle 3 gry; przebiegi 20:07–20:49 (pojedynczo, slot heavy)
  kończyły się kodem 0. Nie przypisuję tego audio.
- Odsłuch właściciela (głośniki PC i słuchawki): `artifacts/audio-pc-s23/player/*.wav`.
