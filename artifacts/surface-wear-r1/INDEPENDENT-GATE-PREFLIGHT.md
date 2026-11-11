# D gate tyre preflight - actual source targets, read only
No Dsource/cache/Unity change; no new tracks or camera files. Source: Dchunk6_6 HighSHAd27e03668cae415545a2fc1518fa80ee9f690b4b4c977490c82b2b64ab8edd79 / LowSHA44dd89a0b4962124a8d8bbf6f0493f878eb8ae3d7850dda61694e48316c70e69, source-field-inventory + streetscapeQA/instances, gate.py/life_props.py/yard_wear.py geometry. Source coordinates below are ENU metres, Z absolute, NOT UnityY.

## The gatehouse is not the barrier line
Gate kit source override:kwadrat-park-gate-kit has entrybarrier_base[618.393,-602.133,140.896], exit[617.328,-601.486,140.896]; actualhousingmidpoint[617.8605,-601.8095]. Booms at[618.515,-601.932,141.846]/[617.206,-601.687,141.846], metadataL5.85m/open85deg. Gatehouse[642.084,-572.131,141.107] is about38.3m fromhousingline, moved independently byspace placement. Therefore distancefromgatehouse is an unreliable entry criterion.
Old tyre_near_gate target[664.481,-601.307,141.755] is36.78m fromgatehouse but46.62m fromhousingmidpoint; its large28tri footprintbounds[656.848,-608.841,141.576]..[672.114,-593.774,141.930] lies east in yard/dock vicinity, NOT across gate entry. Do not claim it proves gate tyre wear.

## Existing kerb scuffs (NOT flat twin-tread paths)
Raw bothHigh/Low have exactly152 decal_tyre triangles nearbarriers, allUV1strength2.5 (decode glTFV back toUnity). They match gate._scuffs recipe andQA gates.scuff_tris152: sixnoses xface/top pairs. No other pavement-tyre triangle CENTROIDS within20m ofhousingmidpoint. Markings are chunk6_6 geometry with samepositions/bounds inLow/High, no independentprototypeLOD. Gatehouse/barrier prototypes have their ownLOD0/1 but contain NO road-surface tyre tracks.
| Raised element/nose | Face centroid ENU / top centroid ENU | Faces/top tris | Inventorycomponent |
|---|---|---|---|
| Median noseA |[617.819,-601.881,140.833] / [617.791,-601.925,140.900]|18/18|1751/1752|
| Median noseB |[617.757,-603.475,140.833] / [617.739,-603.411,140.900]|10/10|1753/1754|
| Entryouter strip noseA |[623.777,-604.667,140.841] / [623.707,-604.716,140.907]|14/14|1755/1756|
| Entryouter strip noseB |[620.775,-611.694,140.761] / [620.766,-611.625,140.828]|14/14|1757/1758|
| Exitouter strip noseA |[612.925,-596.477,140.877] / [612.939,-596.542,140.943]|10/10|1759/1760|
| Exitouter strip noseB |[611.778,-597.824,140.837] / [611.845,-597.827,140.904]|10/10|1761/1762|
Source attribution is constrained bymatching152tris/strength/shape/kitcontext; rawmergedGLB does not retain primitive src strings. gate.py:178-220 emits2.2m aroundeachnose, topwidth.10m atcurbtop+.004, faceZtop-.11..-.015m and.004..016m outward, not stainsfloating overroad. UV0 topv.3..7/face.36..64; strength>=2.5 intentionallydisablesmacrobreakup/endfade. Actualmedian targethaspavedtop140.896/underbase140.7294 andnoroadasphalt triangle beneath itscentre; entrystrip top140.9039/underbase140.7425, scufftop140.9073. This proves raisedkerb placement, not tyre treads on carriageway. ExistingDECAL_TYRE material/keyword iscommonLow/High.

## Existing pavement twin-tread evidence belongs elsewhere
Actualyard_wear drivingbands usefour .26m treads perpass, .08m twin-gap,2.04m wheelgauge, UV0v.22/.78 andlift.008, strength<=1.5. Rawchunk6_6 contains393triangles with thissignature. Nearest matchingpaircentres[647.049,-521.116,141.423] and[647.168,-520.897,141.425],30tris each, about85.8/86.1m frombarrierline; anotherpair[642.727,-519.147,141.514]/[643.060,-519.214,141.513],10tris each. These are existingyard twins, NOT gate-entry evidence. The nearer generic tyre-family pavementcomponents startcentre-distance36.93m at[650.536,-619.023,141.584]; sourceconnectivity alone cannot label genericbands twin-treads or attributeeverylongstain to a generator. No new pavementpaths should be invented to make an entrycamera succeed.

## Two source-checked QA views to inspect actual gate scuffs
| Proposedcamera / FOV55 WORKING_VALUE | posENU | look_atENU | Purpose |
|---|---|---|---|
| gate_entry_strip_scuff |[621.000,-604.000,142.3225]|[623.707,-604.716,140.9073]|Entryouter kerb top+face,2.8m horizontal distance; actualroadtop atcamera140.7225 +1.60meye.|
| gate_median_nose_scuff |[621.500,-605.500,142.3036]|[617.739,-603.411,140.9000]|Median southnose,4.3m horizontal distance; actualroadtop140.7036 +1.60meye.|
CPUcentre-ray checks foundNO hit beforetarget against currentroad/paved/furniture/building triangles AND transformed gatehouse/base/boom prototype meshes (closed0 and raised85deg pose assumptions). Gatehouse isfar outside these short sightlines. These are source-clear proposals, NOT alreadyrendered/unobstructed fullROI PASS; finalDcapture must inspect actualdynamicbarrier/bollard/lamp edges, depth/pose andnative scuffpixels. Do not use these views to claim pavementtreads exist: show actualexistingkerbwear and retain the separate gate-road-tread gap. No extra finalcamera expansion beyond neededtargetverification.
