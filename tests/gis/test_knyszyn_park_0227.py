from types import SimpleNamespace
import numpy as np
from streetscape import vegetation as VG
from test_house_greenery_0163 import _forest_src

def test_park_replacement_suppresses_forest_and_retains_authored_trees():
    src = _forest_src('F1:0', [[0,0],[100,0],[100,100],[0,100]])
    hf = SimpleNamespace(x0=-10., y1=110.)
    z = np.zeros((121,121))
    override = [
        {'id':'park', 'kind':'park_replacement', 'target':{'bdot':'F1'}},
        {'id':'park-trees', 'kind':'tree_groups', 'points_en':[[20,20],[80,80]],
         'species':{'linden':1}, 'height_m':[15,20]},
    ]
    report = {}
    trees, forests = VG.place(src, (0.,0.), hf, z, np.zeros_like(z,dtype=bool), report, override)
    assert not forests
    assert {t['p'] for t in trees} == {'tree_linden'}
    assert len(trees) == 2
    assert report['park_replacements'] == {'applied':['park'], 'stale':[]}
    original, unchanged = VG.place(src, (0.,0.), hf, z, np.zeros_like(z,dtype=bool), {}, [])
    assert unchanged and len(original) > len(trees)
