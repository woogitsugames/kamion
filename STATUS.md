# STATUS gps-voice-s24
- 23.11: worktree; account_get_usage = brak uprawnien konektora (wymaga ponownego polaczenia), list/estimate dzialaja (1 kredyt/znak Multilingual v2).
- Voice Design (eleven_multilingual_ttv_v2, seed 2411): 3 podglady, wybrany p2 QsH1g7itRvwZbnuW1zc5 (pelne pasmo, cisza czysta, F0 208 Hz) zapisany jako "Kamion GPS". p1 odrzucony (pasmo 4.5 kHz), p0 (8.5 kHz, F0 173).
- NASTEPNY KROK: probne klipy -> uv run --project tools/audio python tools/audio/gps/voice_qa.py <dir> --png <dir>/png
- Paczka: 13 partii + 8 pojedynczych (B12 #2-9 powtorzone: partia polknela slowa, 9-11 sylab/s) + B12#1 z probki; 96 klipow, -16 LUFS (rozrzut 0.86 LU), szczyt -1 dBFS (limiter srednio 0.3 dB, max 4.8 dB B12_03). Kredyty TTS: 3917 (+Voice Design nieznany).
- NASTEPNY KROK: odtwarzacz NavVoicePlayer + importer edytora + testy EditMode
