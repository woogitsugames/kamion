"""Close alloy spokes must retain two readable faces through the real exporter."""
import numpy as np
import pytest
from streetscape import life_cars as cars
from streetscape.export import crease_normals
from streetscape.props import Mesh

@pytest.mark.parametrize("style", range(5))
@pytest.mark.parametrize("side", [-1, 1])
def test_alloy_spoke_faces_survive_export_on_both_sides(style, side):
    mesh=Mesh()
    cars._wheel2(mesh, side, 0, .32, side, 22, False, 0, wst=style, rimm="rim", tyre="car_tyre")
    primitives=crease_normals(mesh.out())
    material="rim_dark" if style==3 else "rim"
    p=next(p for p in primitives if p["mat"]==material)
    triangles=p["V"][p["T"]]
    normals=p["N"][p["T"]].mean(axis=1)
    center=triangles.mean(axis=1)-np.array([side,0,.32])
    radius=np.linalg.norm(center[:,1:],axis=1)
    mask=(radius>.095)&(radius<.18)&(normals[:,0]*side>.65)
    assert mask.any()
    tangent=np.column_stack([np.zeros(mask.sum()),-center[mask,2],center[mask,1]])
    tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    shading=np.einsum("ij,ij->i",normals[mask],tangent)
    assert shading.min()<-.15 and shading.max()>.15,(style,side,shading)
    for primitive in primitives:
        v=primitive["V"][primitive["T"]]
        area=np.linalg.norm(np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]),axis=1)
        assert area.min()>1e-10
