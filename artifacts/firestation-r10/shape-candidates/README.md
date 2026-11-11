# Artifact-only source-model candidate

No production source/dims/GLB/spec changes. The script asserts four source/product hashes and all192 raw world hashes remain identical to the locked CPU baseline. No Unity or Blender is invoked.

Command: `uv run --project tools/worldgen python artifacts/firestation-r10/shape_candidates.py`.

Current candidate: two foreground spruces +4u m; wing conifer unchanged. Three thuja habits use the same source-model dimensions for the comparison gallery. The layout currently retains baseline thuja positions; the separate spacing proof evaluates the proposed .25 jitter with the exact planner hash. Production terrain heights must be resampled by the normal planner when changing dims.

Plant budget: Low888?852tri, High5656?3052tri. These counts are source-model evidence, not Unity camera draws/tris or a quality score. Modelled branch volumes attach to the trunk and overlap around it; no detached leaf cards.

Material contract verified: LOD0 opaque hedge_thuja core plus separate hedge_shell_thuja alpha shell7cm outside, cutoff0.5. LOD1 opaque fire_station thuja_far atlas, no alpha. Therefore geometry must carry Low openings and alpha cannot hide the High opaque core. This projection shows opaque candidate volumes, not a simulated shell or light.

Self-criticism: the first wedges/bare poles, then sparse detached-looking spindle Low, and then a connected hourglass envelope were rejected. The current thicker overlapping Low boughs retain a recognizable crown but still read as geometric lobes; High is fuller and has gaps but is stylized. Three thuja directions are useful yet require runtime contour/material inspection. No visual PASS is claimed. Arch visibility is a placement/occlusion metric only; source-camera masking excludes mullion/reflection calibration. S10 final acceptance still requires locked true Unity before/after, measured colors, at least2 rounds, stats, tests, and independent review.
