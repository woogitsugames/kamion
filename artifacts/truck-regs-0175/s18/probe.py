import bpy, sys
from mathutils import Vector
args = sys.argv[sys.argv.index("--")+1:]
for f in args:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    dg = bpy.context.evaluated_depsgraph_get()
    allc=[]
    for o in bpy.context.scene.objects:
        if o.type!='MESH': continue
        for p in o.data.polygons:
            c = o.matrix_world @ p.center
            n = (o.matrix_world.to_3x3() @ p.normal).normalized()
            allc.append((c,n,p.area,o.name, o.data.materials[p.material_index].name if o.data.materials else ''))
    ys=[c.y for c,_,_,_,_ in allc]; zs=[c.z for c,_,_,_,_ in allc]
    ymin=min(ys)
    def cnt(pred):
        r=[a for a in allc if pred(a[0])]
        return len(r), round(sum(a[2] for a in r),4), sorted(set(a[4] for a in r))
    print("FILE",__import__('os').path.basename(f),"ymin",round(ymin,3),"ymax",round(max(ys),3),"zmax",round(max(zs),3))
    rear=lambda c: c.y<ymin+0.25
    print(" posts", cnt(lambda c: rear(c) and 1.17<abs(c.x)<1.26 and 1.3<c.z<3.8))
    print(" header", cnt(lambda c: rear(c) and abs(c.x)<1.1 and 3.89<c.z<3.97))
    print(" sill", cnt(lambda c: rear(c) and abs(c.x)<1.2 and 1.18<c.z<1.26))
    print(" plate", cnt(lambda c: rear(c) and abs(c.x)<0.26 and 0.81<c.z<0.924))
    print(" tri", cnt(lambda c: rear(c) and 0.5<abs(c.x)<1.2 and 0.55<c.z<0.75))
