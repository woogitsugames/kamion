"""R2 contracts: unchanged sign coverage, controlled wear and Low mounts without a material draw."""
import numpy as np
import pytest
from PIL import Image

from roads import standards as S
from streetscape import props, signs


def face(code="B-33_70"):
    return signs.face(code)[1].resize((256, 256), Image.Resampling.LANCZOS)


def test_zero_wear_preserves_the_rgba_source_exactly():
    source = face()
    assert np.array_equal(np.asarray(signs.weather(source, "B-33_70", 0)), np.asarray(source))


@pytest.mark.parametrize("code", ["A-7", "B-33_70", "D-6"])
def test_wear_keeps_alpha_and_uncovered_pixels(code):
    source = np.asarray(face(code))
    worn = np.asarray(signs.weather(Image.fromarray(source), code))
    assert np.array_equal(worn[..., 3], source[..., 3])
    empty = source[..., 3] == 0
    assert np.array_equal(worn[empty], source[empty])


def test_wear_is_stable_per_plate_but_varies_between_keys():
    source = face()
    a = np.asarray(signs.weather(source, "B-33_70"))
    assert np.array_equal(a, np.asarray(signs.weather(source, "B-33_70")))
    assert not np.array_equal(a, np.asarray(signs.weather(source, "B-33_30")))


def test_rectangular_board_edge_does_not_wrap_to_the_other_side():
    source = Image.new("RGBA", (512, 128), (240, 240, 240, 255))
    worn = np.asarray(signs.weather(source, "direction-board"))
    assert worn[4:32, 0, 0].mean() < worn[4:32, 256, 0].mean()
    assert worn[4:32, -1, 0].mean() < worn[4:32, 256, 0].mean()


@pytest.mark.parametrize("code", ["A-7", "B-33_70", "C-12", "D-15"])
def test_low_mounts_keep_two_materials_and_a_bounded_triangle_cost(code):
    high, low, collision = props.plate(code)
    assert collision is None
    parts = {p["mat"]: p for p in low.out()}
    assert set(parts) == {"plate_back", "sign_" + code}
    assert set(p["mat"] for p in high.out()) == {"plate_back", "sign_" + code, "steel_galv"}
    back = parts["plate_back"]
    # The hardware reaches behind the post and touches the back of the plate.
    assert back["V"][:, 1].min() < -S.SIGN_POST_D / 2
    assert np.isclose(back["V"][:, 1].max(), S.SIGN_POST_D / 2 + .012 + .025 - .004)
    front_triangles = len(parts["sign_" + code]["T"])
    total_triangles = sum(len(p["T"]) for p in parts.values())
    assert 2 * front_triangles < total_triangles <= 2 * front_triangles + 24
    assert np.all((back["UV"] >= 0) & (back["UV"] <= 1))
