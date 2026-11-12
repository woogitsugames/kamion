"""Appearance semantics and geometry invariants of the real far-field generator.

The facade is a WORKING_VALUE typology, not measured window/finish data. These
checks prevent a measured building height from becoming a fictitious function,
and protect the existing merged material/topology budget and source dimensions.
"""
from copy import deepcopy

import numpy as np
import pytest

from streetscape import far_field as ff


def building(function='produkcyjny', height=23.91, typ='hall'):
    # Actual pinned candidate footprint/height; no raw archive is required here.
    rect = [[-36.2,-1169.4],[-6.0,-1229.4],[-45.3,-1249.2],[-75.5,-1189.2]]
    if typ == 'house':
        # Low deliberately prunes houses farther than 140 m; this control must
        # exercise surviving house geometry rather than fail on an empty mesh.
        rect = [[e,n+140] for e,n in rect]
    return dict(id='2BE4B431-C061-1BF0-E053-CC2BA8C0D140',
                rect=rect,
                area=1526.4, h=height, typ=typ, func=function, storeys=None,
                height_source='gugik-lod1-measuredHeight', src='bdot10k+lod1')


def render(source, tier):
    original = deepcopy(source)
    elevation = ff.BorderElevation(1024, *([140.0]*129 for _ in range(4)))
    sectors = {name:ff.SectorBuilder(name) for name in ff.SECTORS}
    ff._add_building(sectors, source, elevation, 1024, tier)
    assert source == original, 'Appearance must not rewrite the measured source data'
    primitives = [p for sector in sectors.values() for p in sector.primitives()]
    assert primitives, 'Do not turn missing geometry into an empty pass'
    assert len(primitives) == 1, 'One existing merged far-field material, no extra primitive'
    assert primitives[0]['mat'] == 'far_field_buildings'
    return primitives[0]


def panel_mask(primitive):
    alpha = np.asarray(primitive['COL'])[:,3]
    return np.isclose(alpha,0.25) | np.isclose(alpha,0.65)


@pytest.mark.parametrize('tier',['Low','High'])
def test_measured_height_does_not_invent_a_power_plant(tier):
    p = render(building(),tier)
    colors = np.asarray(p['COL'])
    assert panel_mask(p).any(), 'A declared industrial facade must carry its explicit data marker'
    assert not np.any(np.all(np.isclose(colors[:,:3],[0.24,0.10,0.07]),axis=1)), (
        'A 23.91 m production building is not a power plant merely because it is tall')


@pytest.mark.parametrize('tier',['Low','High'])
@pytest.mark.parametrize('height',[8.0,23.91])
def test_explicit_energy_function_keeps_its_own_style_at_any_height(tier,height):
    p = render(building('elektrociepłownia',height),tier)
    colors = np.asarray(p['COL'])
    assert np.any(np.all(np.isclose(colors[:,:3],[0.24,0.10,0.07]),axis=1))
    assert not panel_mask(p).any(), 'Industrial cladding marker must not replace the explicit energy style'


@pytest.mark.parametrize('tier',['Low','High'])
@pytest.mark.parametrize('function',['kościół','budynek sportowy','inny'])
def test_hall_shaped_nonindustrial_building_does_not_get_factory_cladding(tier,function):
    assert not panel_mask(render(building(function),tier)).any()


@pytest.mark.parametrize('tier',['Low','High'])
def test_industrial_style_preserves_measured_envelope_and_mesh_budget(tier):
    industrial = render(building(),tier)
    energy = render(building('elektrociepłownia'),tier)
    p = np.asarray(industrial['V'])
    other = np.asarray(energy['V'])
    np.testing.assert_allclose(p.min(axis=0),other.min(axis=0),atol=1e-6)
    np.testing.assert_allclose(p.max(axis=0),other.max(axis=0),atol=1e-6)
    assert len(industrial['V']) == len(energy['V'])
    assert len(industrial['T']) == len(energy['T'])
    assert len(industrial['T']) <= 18, 'Box walls/fascia/roof only; no panel tessellation'
    assert np.isfinite(np.asarray(industrial['UV1'])).all()


@pytest.mark.parametrize('tier',['Low','High'])
@pytest.mark.parametrize('typ',['office','block','house'])
def test_other_far_field_typologies_keep_the_legacy_window_data_contract(tier,typ):
    p = render(building(typ=typ),tier)
    assert not panel_mask(p).any()
    alpha = np.asarray(p['COL'])[:,3]
    assert np.all(np.isclose(alpha,0) | np.isclose(alpha,0.75) | np.isclose(alpha,1))
