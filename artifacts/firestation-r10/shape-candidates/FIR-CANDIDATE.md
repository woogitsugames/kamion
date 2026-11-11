# Latest artifact-only short-needle candidate

No production edits. Actual Unity baseline is still blocked by ROOT phone hold. This is unlit/source-mesh evidence only.

Source: official Poly Haven fir_tree_01, https://polyhaven.com/a/fir_tree_01 ; CC0 https://polyhaven.com/license . Authors Rob Tuytel photography / Rico Cilliers modelling. Short-needle fir/conifer; **not verified Picea**. Diff SHA25676f6d0c0044d76bac08fbbd3d2ac1c9b66bb046de7d0b1a22aa9b319308f3833; alpha SHA2563f399629337e7ac3af27a01b08ffb9c0d60224a9dd374a1427761a5c2eea9d6e. Raw source read-only in coordination artifact cache, no hidden B code dependency.

Crop[295,400,650,805], paired-alpha connected-component filter, centred root.36 irregular-height/azimuth/roll attached bough cards per spruce + overlapping opaque branch cores + trunk. Two foreground trees+4u m; wing conifer unchanged. Candidate Low plants876?888, wholehero2816?2828. Runtime High is unchanged in the exported proxy; a production both-tier pass is not claimed.

Existing Low fire_station_alpha slot reused. New cellu[.30,.43],v[.025,.24],16px internal padding. Every baselineGLB alphaUVtriangle audited with actual GlbReader Vflip:548High/98Low/0far, zero overlaps. Old base pixels outside cell exactly preserved. Actual exportedGLB still4/2/1primitive/material slots and same3nodes; wholehero bounds identical. Runtime Flush source key retains proto+LODslot, submesh/materialStart, layer, shadow/probe policy. This predicts no new batch; actual imported meshes and route stats remain REQUIRED.

Source mip diagnostics only: BOX/LANCZOS newcell alpha coverage at0.5~10.47%base,~9.7?10.4%mip3/4,6.35%mip5,0%mip6. Old-region plainfilter alpha exact throughmip5; LANCZOS changes1sample at6,5at7; BOX unchanged. Existing import settings remain unchanged:coverage-preservationON,ref0.5,max2048Editor/1024Android,ASTC6x6. Global coverage preservation can alter old fence/letter mips despite unchanged base pixels. Actual imported-mip parity, thin needle survival/shimmer, overdraw and final lighting remain UNVERIFIED.

Self-criticism: fir needle contour is more credible than opaque wedges; sparse columns were improved with72of84available Low triangles. Still stylized and unlit; source RGB differs from the intended calibrated hero palette. Actual camera distance/coverage, old lettering/fence stability, photo7197 comparison and independent runtime review gate any promotion.

Reproduce:fir_alpha_experiment.py ? Blender export_fir_proxy.py ? audit_fir_export.py ? audit_fir_mips.py (all under this artifact parent). Export completion is verified by marker+actualGLBaudit; no Unity is invoked.
