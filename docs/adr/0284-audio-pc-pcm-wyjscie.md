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
POMIARY_TUTAJ

## Otwarte
- **Docelowa głośność miksu PC** — decyzja właściciela (docs/08 §2: „−16 LUFS dla mobile, do ustalenia”). Propozycja
  `WORKING_VALUE`: kabina, jazda ze stałą prędkością, master 1,0: −18 LUFS ±2, true peak ≤ −1 dBTP. Miksu nie
  przestrajano w tym ADR.
- **5.1/7.1:** wyjście zostaje stereo (słuchawki i głośniki PC); `AudioSettings.driverCapabilities` pozwala później
  przełączyć tryb głośników w Ustawieniach (UI poza zakresem).
- **Zawieszenie playera przy wyjściu** (`-quit_t`): występuje także bez argumentów audio (przebieg bazowy
  2026-11-16 19:24) — poza audio, do diagnozy (crash/zawieszenie D3D12, ADR 0277?).
- Odsłuch właściciela (głośniki PC i słuchawki): `artifacts/audio-pc-s23/player/*.wav`.
