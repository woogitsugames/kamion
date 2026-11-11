"""Keep unrelated paint fields and repeat padding while replacing lower film."""
from pathlib import Path
import importlib
import sys
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]


def test_clean_car_map_preserves_upper_pixels_and_legacy_wrap_padding(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'art-source/world/materials/_src'))
    facade=importlib.import_module('sets_facade')
    kit=importlib.import_module('pbrkit')
    legacy=facade.car_grime(n=1024)
    clean=facade.car_grime(n=1024,lower_film=False)
    _,y=legacy.c.xy()
    v=2.5-y
    for field in ('height','elem_id','joint'):
        assert np.array_equal(getattr(legacy,field),getattr(clean,field)),field
    for mask in (v<.05,v>1.1):
        assert np.array_equal(legacy.albedo[mask],clean.albedo[mask])
        assert np.array_equal(legacy.rough[mask],clean.rough[mask])
    assert np.any(clean.albedo!=legacy.albedo)
    legacy.name='legacy'
    clean.name='clean'
    kit.write_set(legacy,tmp_path)
    kit.write_set(clean,tmp_path)
    checked=[]
    for tier in ('High','Medium','Low'):
        for suffix in ('BaseColor','Normal','MaskMap','Var'):
            before=np.asarray(Image.open(tmp_path/'legacy'/tier/f'T_legacy_{suffix}.png'))
            after=np.asarray(Image.open(tmp_path/'clean'/tier/f'T_clean_{suffix}.png'))
            assert before.shape==after.shape
            height=2.5*(1-(np.arange(before.shape[0])+.5)/before.shape[0])
            assert np.array_equal(before[height>1.1],after[height>1.1]),(tier,suffix)
            if suffix in ('Normal','Var'):
                assert np.array_equal(before,after),(tier,suffix)
            checked.append((tier,suffix))
    assert len(checked)==12
