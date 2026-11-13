import bpy, sys, os
args = sys.argv[sys.argv.index("--")+1:]
for f in args:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    grp={}; emit=0
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or 'Data' not in o.data.uv_layers: continue
        d=o.data.uv_layers['Data'].data
        for p in o.data.polygons:
            uv=d[p.loop_indices[0]].uv
            g=round(uv.x)
            if g==15:
                grp[o.name]=grp.get(o.name,0)+1
                if uv.y>0.01: emit+=1
    print("FILE",os.path.basename(f),"REFLEX faces",grp,"emitting",emit)
