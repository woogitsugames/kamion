"""GPS voice pack: every sentence NavVoice (game/Assets/_Project/Core/Navigation/NavVoice.cs) can order, keyed GPS_Bxx #i
exactly as docs/owner/ELEVENLABS-GPS-VOICE.md numbers them (ADR 0328). Only the sentences the code can play are listed:
B01..B05 #1..8, B06 #1..10, B07 #1..7, B08 #1..7, B09 #1..5, B10 #5 and #11, B12 #1..12, B13 #1..11, B14 #1..2.
Unused sentences of the prompt pack (B01 #9, B10 others, B11) are not generated until code orders them.
"""
from __future__ import annotations

BREAK = ' <break time="1.5s" /> '

_MAN = ["skręć w prawo.", "skręć w lewo.", "trzymaj się prawej.", "trzymaj się lewej.", "skręć ostro w prawo.",
        "skręć ostro w lewo.", "zawróć.", "wjedź na rondo."]
_KM = ["skręć w prawo.", "skręć w lewo.", "trzymaj się prawej.", "trzymaj się lewej.", "wjedź na rondo."]


def _band(prefix: str) -> list[str]:
    return [f"{prefix} {m}" for m in _MAN]


# block -> list of (index, text) in prompt-pack order
PACK: dict[int, list[tuple[int, str]]] = {
    1: list(enumerate(_band("Teraz"), 1)),
    2: list(enumerate(_band("Za sto metrów"), 1)),
    3: list(enumerate(_band("Za dwieście metrów"), 1)),
    4: list(enumerate(_band("Za trzysta metrów"), 1)),
    5: list(enumerate(_band("Za pięćset metrów"), 1)),
    6: list(enumerate([f"Za kilometr {m}" for m in _KM] + [f"Za dwa kilometry {m}" for m in _KM], 1)),
    7: list(enumerate(["Na rondzie zjedź pierwszym zjazdem.", "Na rondzie zjedź drugim zjazdem.",
                       "Na rondzie zjedź trzecim zjazdem.", "Na rondzie zjedź czwartym zjazdem.",
                       "Na rondzie zjedź piątym zjazdem.", "Na rondzie zawróć.", "Na rondzie jedź prosto."], 1)),
    8: list(enumerate(["a następnie skręć w prawo.", "a następnie skręć w lewo.", "a następnie trzymaj się prawej.",
                       "a następnie trzymaj się lewej.", "a następnie wjedź na rondo.", "a następnie zawróć.",
                       "a następnie jesteś u celu."], 1)),
    9: list(enumerate(["Trzymaj się prawego pasa.", "Trzymaj się lewego pasa.", "Trzymaj się środkowego pasa.",
                       "Jedź jednym z dwóch prawych pasów.", "Jedź jednym z dwóch lewych pasów."], 1)),
    10: [(5, "Jedź prosto."), (11, "Jesteś u celu.")],
    12: list(enumerate(["w ulicę Generała Władysława Andersa.", "w ulicę Generała Stanisława Maczka.",
                        "w aleję Tysiąclecia Państwa Polskiego.", "w ulicę Bitwy Białostockiej.", "w ulicę Białostoczek.",
                        "w ulicę Kombatantów.", "w ulicę Michała Motoszko.", "w ulicę Stefana Batorego.",
                        "w ulicę Władysława Bełzy.", "w Wileńską.", "w Sokólską.", "w Grodzieńską."], 1)),
    13: list(enumerate(["w Brzeską.", "w Buską.", "w Kowieńską.", "w Lidzką.", "w Olsztyńską.", "w Racławicką.",
                        "w Sitarską.", "w Skidelską.", "w Wołkowyską.", "w Łańcucką.", "w Świsłocką."], 1)),
    14: [(1, "na rondzie Putry."), (2, "na rondzie Pamięci Bieżeństwa.")],
}


def key(block: int, index: int) -> str:
    return f"GPS_B{block:02d}_{index:02d}"


def batch_prompt(block: int) -> str:
    return BREAK.join(t for _, t in PACK[block])


def all_keys() -> list[str]:
    return [key(b, i) for b in sorted(PACK) for i, _ in PACK[b]]


if __name__ == "__main__":
    total = 0
    for b in sorted(PACK):
        p = batch_prompt(b)
        total += len(p)
        print(f"B{b:02d} n={len(PACK[b])} chars={len(p)}\n{p}\n")
    print("clips", len(all_keys()), "chars", total)
