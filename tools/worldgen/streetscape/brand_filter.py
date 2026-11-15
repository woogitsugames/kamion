"""Brand filter for text that the world generator prints into the game (BRAND-SWEEP-S20 #6, CLAUDE.md rule 8).

OSM `destination` values go straight onto direction boards (signs_route._arm_label). Today they name towns,
districts and generic places only ("Centrum handlowe", "Lotnisko"), but a later region may carry
"stacja paliw <brand>" or a shop name. Anything matching a company / brand / commercial-site pattern is dropped
(the board then falls back to route shields + street name) and reported, never rewritten into something invented.

Pure functions, no third-party imports (unit-tested in tests/gis/test_brand_filter_s21.py).
"""

from __future__ import annotations

import re

# Case-sensitive brand names (PCRE subset of the BRAND-SWEEP-S20 search list) plus commercial-site words.
# Generic Polish words ("stacja paliw", "centrum handlowe", "browar") are allowed on their own; the brand is not.
_BRAND_PATTERNS = [
    # fuel stations
    r"Orlen", r"Lotos", r"\bBP\b", r"\bShell\b", r"Circle ?K", r"Statoil", r"\bMoya\b", r"\bAmic\b",
    # retail, food, parcels
    r"Biedronka", r"\bLidl\b", r"Kaufland", r"Auchan", r"Carrefour", r"[ŻZ]abka", r"\bNetto\b", r"\bDino\b",
    r"Stokrotka", r"Leroy", r"Castorama", r"\bOBI\b", r"Media ?Markt", r"RTV ?Euro", r"Rossmann", r"\bHebe\b",
    r"Pepco", r"McDonald", r"\bKFC\b", r"Burger King", r"InPost", r"Paczkomat", r"\bDPD\b", r"\bDHL\b",
    # vehicles and parts
    r"Scania", r"Volvo", r"\bMAN\b", r"\bDAF\b", r"Mercedes", r"Iveco", r"Renault", r"\bKrone\b", r"Schmitz",
    r"Wielton", r"Toyota", r"Volkswagen", r"\bVW\b", r"[SŠ]koda", r"\bOpel\b", r"\bFord\b", r"\bFiat\b",
    # local companies and commercial sites seen in the Białystok regions (BRAND-SWEEP-S20 #7-#12)
    r"Kwadrat", r"Biazet", r"\bBISON\b", r"Rosti", r"Bravilor", r"Masterpress", r"Redkom", r"Browar Dojlidy",
    r"Galeria\s+\w+", r"\bS\.A\.", r"\bSp\. z o\.o\.", r"\bsp\. z o\.o\.",
]
BRAND_RE = re.compile("|".join(f"(?:{p})" for p in _BRAND_PATTERNS))


def is_branded(text: str) -> bool:
    """True when the text names a company, a brand or a commercial site."""
    return bool(text) and BRAND_RE.search(text) is not None


def neutral_destinations(dests):
    """Split OSM destination strings into (kept, dropped): dropped = branded ones (see module docstring)."""
    kept, dropped = [], []
    for d in dests:
        (dropped if is_branded(d) else kept).append(d)
    return kept, dropped
