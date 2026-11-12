"""Weryfikacja M25 pkt 3: pochylenie podluzne lacznic (ramp) vs PTB 2022 § 62 ust. 2.

Zrodlo pierwotne: rozporzadzenie Ministra Infrastruktury z dnia 24 czerwca 2022 r. w sprawie
przepisow techniczno-budowlanych dotyczacych drog publicznych (Dz.U. 2022 poz. 1518,
WDU20220001518, PDF D20221518.pdf on isap.sejm.gov.pl). § 62 ust. 2:
"Pochylenie podluzne jezdni lacznicy wezla typu WA powinno byc nie wieksze niz 6%, a jezdni
lacznicy wezla typu WB lub WC - nie wieksze niz 7%."

Test czyta gotowe dane geometrii drog z repo (generated/roads_qa.json, tylko do odczytu,
bez regeneracji swiata) i wybiera lancuchy lacznic (highway *_link). Odcinki (lancuchy) z
max_grade powyzej 6% (limit typu WA) sa raportowane jako xfail, NIE fail. Generator
uzywa limitu 7% (WB/WC, standards.MAX_GRADE_RAMP) - tego NIE zmieniamy w tym zadaniu.

Uruchomienie: uv run --project tools/worldgen pytest tests/gis/test_connector_grade_verify.py -q
"""

from __future__ import annotations

import json

import pytest

from conftest import REGION_DIR

QA = REGION_DIR / "generated" / "roads_qa.json"

pytestmark = pytest.mark.unit

# PTB 2022 (Dz.U. 2022 poz. 1518) § 62 ust. 2: lacznica wezla typu WA <= 6 %.
GRADE_LIMIT_WA = 0.06


def _link_chains():
    if not QA.exists():
        pytest.skip("roads_qa.json missing: run roads/build_world.py")
    q = json.loads(QA.read_text(encoding="utf-8"))
    return [c for c in q["chains"] if any(h.endswith("_link") for h in c["highway"])]


def test_connector_grade_vs_ptb2022_par_62_ust_2():
    links = _link_chains()
    assert links, "no *_link (lacznik) chains in roads_qa.json"
    over = sorted(
        (c for c in links if c["max_grade"] > GRADE_LIMIT_WA),
        key=lambda c: -c["max_grade"],
    )
    if over:
        pytest.xfail(
            "Lacznice z pochyleniem podluznym > 6% (PTB 2022 § 62 ust. 2, typ WA; "
            "WB/WC dopuszcza 7%): "
            + "; ".join(f"{c['id']} max_grade={c['max_grade']:.4f} hw={c['highway']}" for c in over)
        )
