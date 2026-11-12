"""Photo selection boundary, entrance clearance and existing collision contract (ADR0120 r3)."""
import numpy as np
import pytest

from streetscape import furniture, materials, props


@pytest.mark.parametrize('node', [5802408812, 5802408814])
def test_red_family_is_selected_for_inspected_source_nodes(node):
    assert furniture.shelter_prototype_0120(node) == 'bus_shelter_red_0120'
    assert furniture.SHELTER_RED_REFERENCES_0120[node].isdigit()


@pytest.mark.parametrize('node', [None, 5802408811, 5802408800, 3132202649])
def test_unknown_or_uninspected_stop_keeps_generic_shelter(node):
    assert furniture.shelter_prototype_0120(node) == 'bus_shelter'


def test_new_family_preserves_existing_collision_payload():
    old, new = props.bus_shelter()[2].out(), props.bus_shelter_red_0120()[2].out()
    assert len(old) == len(new)
    for a, b in zip(old, new):
        assert a['mat'] == b['mat']
        for channel in ('V', 'T', 'UV'):
            assert np.array_equal(a[channel], b[channel])


def test_new_family_leaves_entrance_open_and_has_a_closed_curved_roof():
    for mesh, segments in zip(props.bus_shelter_red_0120()[:2], (4, 2)):
        frame = mesh.prims['shelter_red_frame_0120']
        # A full-height post at local x=0,y=+0.75 would split the front entrance.
        assert not any(np.ptp(v[:, 2]) > 2 and np.max(np.abs(v[:, 0])) < .1
                       and np.min(v[:, 1]) > .6 for v in frame[0])
        points = np.concatenate(frame[0])
        assert 2.59 < points[:, 2].max() <= 2.600001
        # All five supports meet the actual polygonal roof underside for their LOD.
        ys = np.linspace(-.87, .87, segments+1)
        zs = 2.54+.06*(1-(ys/.87)**2)
        for x,y in ((-2,-.75),(0,-.75),(2,-.75),(-2,.75),(2,.75)):
            near = (np.abs(points[:,0]-x) <= .036) & (np.abs(points[:,1]-y) <= .036)
            assert near.any()
            assert points[near,2].max() == pytest.approx(np.interp(y,ys,zs)-.045)
        assert any(np.ptp(v[:, 1]) > .1 and np.ptp(v[:, 2]) > .01
                   and np.min(v[:, 2]) > 2.5 for v in frame[0])
        for primitive in mesh.out():
            assert np.isfinite(primitive['V']).all()
            assert primitive['T'].min() >= 0 and primitive['T'].max() < len(primitive['V'])


def test_shared_frame_roof_and_one_glazing_slot_bound_prototype_cost():
    high, low, _ = props.bus_shelter_red_0120()
    expected = {'shelter_red_frame_0120', 'shelter_clear_glass_0120', 'bench_wood'}
    assert {p['mat'] for p in high.out()} == expected
    assert {p['mat'] for p in low.out()} == expected
    hi = sum(len(p['T']) for p in high.out())
    lo = sum(len(p['T']) for p in low.out())
    assert lo < hi < 250  # prototype ceiling, not evidence of route draws or GPU cost


def test_generic_glass_stays_opaque_and_only_photo_family_opts_into_transmission():
    assert not materials.M['shelter_glass'].get('blend', False)
    clear = materials.M['shelter_clear_glass_0120']
    assert clear['blend'] is True and 0 < clear['alpha'] < .3
    assert 'shader' not in clear  # existing generic transparent-Lit recipe, no car/truck shader change
