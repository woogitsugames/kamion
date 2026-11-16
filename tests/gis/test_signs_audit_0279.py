"""ADR 0279: sign / marking catalogue numbers re-read from Dz.U. 2019 poz. 2311 zał. 1 / zał. 2 and Dz.U. 2025
poz. 1105 (audit D21). Pure tests - no region data."""

from __future__ import annotations

import math

import pytest

from roads import standards as S
from streetscape import rail as RL
from streetscape import sign_norms as SN
from streetscape import signs as SG


def test_g_plates_from_construction_drawings():
    # rys. 9.8.1-9.8.7 (PDF s. 507-510)
    for k in "abcdef":
        assert SG.RECT[f"G-1{k}"] == pytest.approx((0.30, 1.00))
    assert SG.RECT["G-2"] == pytest.approx((0.44, 0.60))
    im = SG.g2()
    assert im.size[0] / im.size[1] == pytest.approx(440 / 600, rel=0.02)     # texture keeps the plate proportion


def test_saltire_arms_rys_9_8_8():
    assert (RL.SIGN_ARM_L, RL.SIGN_ARM_W, RL.SIGN_ARM_ANGLE) == (1.40, 0.15, 50.0)
    assert SN.G3_ARM_MM == {"l": 1400, "w": 150, "angle_deg": 50.0, "band": 175, "tip_chamfer": 40}


def test_ad_sizes_table_1_1_match_generator():
    # Tabela 1.1 (s. 9): grupa średnie = what the generator builds (standards.SIGN_SIZE)
    sr = SN.SIGN_DIM_MM["srednie"]
    assert S.SIGN_SIZE["triangle"] == sr["A"] / 1000 and S.SIGN_SIZE["disc"] == sr["B"] / 1000 == sr["C"] / 1000
    assert S.SIGN_SIZE["diamond"] == pytest.approx(sr["D"] / 1000 * math.sqrt(2))
    assert SN.SIGN_DIM_MM["duze"] == {"A": 1050, "B": 900, "C": 900, "D": 900}
    assert SN.size_group_ad(False, False, 90, "") == "srednie"       # DK65 / DW671 single carriageway
    assert SN.size_group_ad(True, False, 90, "") == "duze"
    assert SN.size_group_ad(True, True, 50, "") == "srednie"
    assert SN.size_group_ad(False, True, 50, "gminna") == "male"


def test_mount_heights_table_1_11_2022():
    assert SN.MOUNT_MIN_M["ABCDFG"]["built_up"] == S.SIGN_H_MIN == 2.00
    assert SN.MOUNT_MIN_M["ABCDFG"]["on_sidewalk"] == S.SIGN_H_SIDEWALK == 2.20
    assert SN.MOUNT_MIN_M["overhead"]["rural"] == S.SIGN_H_OVERHEAD == SN.OVERHEAD_MIN_M == 5.00
    assert SN.MOUNT_MIN_M["E1_E2_E14"]["rural"] == 1.00
    assert SN.g1_bottom_m(street=True) == 1.00 and SN.g1_bottom_m(street=False) == 0.50


def test_warning_distances_pkt_2_1_2():
    assert SN.warning_distance_m(90) == (150.0, 300.0)
    assert SN.warning_distance_m(60) == (0.0, 100.0)
    assert SN.warning_recommended_m(90) == (250.0, 300.0)
    assert SN.warning_recommended_m(50) == (50.0, 100.0)
    assert SN.A7_MAX_FROM_JUNCTION_M == {"fast": 50.0, "slow": 25.0}
    assert SN.A7_ADVANCE_T1_RANGE_M == (150.0, 300.0)
    assert SN.sign_spacing_min_m(100) == 50 and SN.sign_spacing_min_m(70) == 20 and SN.sign_spacing_min_m(50) == 10


def test_rail_rule_matches_table_2_2():
    """The distances rail_approach.rule() uses (ADR 0268) fall inside Tabela 2.2 (s. 67) of zał. 1."""
    from streetscape import rail_approach as RA
    fast = SN.G1_TABLE_2_2_M["fast"]
    slow = SN.G1_TABLE_2_2_M["slow"]
    d = RA.SIGN_DIST_FAST_M
    for code, dist in (("G-1a", d), ("G-1b", d * 2 / 3), ("G-1c", d / 3)):
        assert fast[code][0] <= dist <= fast[code][1]
    d = RA.SIGN_DIST_SLOW_M
    for code, dist in (("G-1a", d), ("G-1b", d * 2 / 3), ("G-1c", d / 3)):
        assert slow[code][0] - 1e-6 <= dist <= slow[code][1] + 1e-6


def test_markings_zal2():
    assert S.DASH["P-1a"] == (4.0, 8.0) and S.DASH["P-1b"] == (2.0, 4.0) and S.DASH["P-6"] == (4.0, 2.0)
    assert S.P6_MIN_LEN == {"le70": 50.0, "gt70": 100.0}
    assert S.P4_LINE_GAP == S.LINE_W_NARROW == 0.12
    assert S.P14_BEFORE_SIGNAL == 2.0 and S.P14_BEFORE_OVERHEAD_SIGNAL == 8.0
    assert (S.P10_WIDTH, S.P10_WIDTH_MIN_BUILT_UP, S.P10_WIDTH_MAX) == (4.0, 2.5, 16.0)


def test_rail_device_rules():
    assert SN.G3_MIN_FROM_OUTER_RAIL_M == SN.ROAD_SIGNAL_MIN_FROM_OUTER_RAIL_M == 5.0
