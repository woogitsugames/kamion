# Budżet kamer r0 -> r1 (visual-qa stats.txt, edytor, 1920x1080, szacunek przed SRP batching)

## High clear

| kafel | kamera | draws r0 | draws r1 | Δ | tris r0 (tys.) | tris r1 (tys.) | Δ % | inst. tris r0 -> r1 (tys.) |
|---|---|---|---|---|---|---|---|---|
| tykocin | bv_bank_close | 334 | 334 | +0 | 1279 | 1299 | +1.6 | 46 -> 46 |
| tykocin | bv_bank_n | 626 | 626 | +0 | 1163 | 1177 | +1.2 | 27 -> 27 |
| tykocin | bv_bank_se | 343 | 326 | -17 | 1110 | 1007 | -9.3 | 57 -> 23 |
| tykocin | bv_bank_sw | 122 | 240 | +118 | 446 | 872 | +95.6 | 25 -> 26 |
| tykocin | bv_cab_bridge_n | 636 | 636 | +0 | 1208 | 1213 | +0.4 | 18 -> 18 |
| tykocin | bv_cab_bridge_river | 577 | 577 | +0 | 1222 | 1226 | +0.4 | 34 -> 34 |
| tykocin | bv_cab_bridge_side | 552 | 552 | +0 | 1092 | 1106 | +1.3 | 15 -> 15 |
| tykocin | look-narew-truss-side | 377 | 377 | +0 | 1158 | 1177 | +1.7 | 25 -> 26 |
| tykocin | top-water-bridge | 182 | 182 | +0 | 577 | 581 | +0.8 | 3 -> 3 |
| tykocin | water-bank-bridge-se | 410 | 410 | +0 | 1245 | 1265 | +1.6 | 60 -> 61 |
| tykocin | water-boat-under-bridge | 318 | 318 | +0 | 841 | 849 | +1.0 | 18 -> 18 |
| tykocin | water-oblique-bridge | 341 | 341 | +0 | 1104 | 1121 | +1.6 | 13 -> 14 |
| dk65-07 | bv_air_wood | 321 | 325 | +4 | 638 | 643 | +0.8 | 14 -> 17 |
| dk65-07 | bv_cab_s242 | 281 | 285 | +4 | 593 | 598 | +0.9 | 16 -> 19 |
| dk65-07 | bv_side_wood | 281 | 268 | -13 | 594 | 619 | +4.1 | 20 -> 23 |
| dk65-07 | bv_verge_close | 293 | 297 | +4 | 664 | 669 | +0.8 | 19 -> 23 |
| dk65-07 | drive-kozince | 237 | 240 | +3 | 658 | 660 | +0.3 | 46 -> 49 |
| dk65-07 | drive-wood | 323 | 327 | +4 | 625 | 630 | +0.8 | 22 -> 27 |
| dk65-07 | rev-kozince | 240 | 244 | +4 | 676 | 682 | +0.8 | 53 -> 57 |
| dk65-07 | top-kozince | 89 | 92 | +3 | 391 | 393 | +0.5 | 4 -> 7 |
| knyszyn-w | bv_air_fields | 38 | 41 | +3 | 322 | 326 | +1.1 | 3 -> 3 |
| knyszyn-w | bv_cab_s1701 | 29 | 31 | +2 | 230 | 233 | +1.1 | 3 -> 3 |
| knyszyn-w | bv_ditch_close | 38 | 41 | +3 | 322 | 326 | +1.1 | 8 -> 8 |
| knyszyn-w | bv_side_ditch | 30 | 32 | +2 | 230 | 233 | +1.1 | 16 -> 16 |
| knyszyn-w | dk65-fields-nw | 34 | 36 | +2 | 286 | 288 | +0.6 | 4 -> 5 |
| knyszyn-w | dk65-goniadzka | 159 | 163 | +4 | 750 | 753 | +0.5 | 23 -> 23 |
| knyszyn-w | dk65-north-edge-in | 417 | 421 | +4 | 670 | 673 | +0.5 | 36 -> 36 |
| knyszyn-w | dk65-polna | 106 | 110 | +4 | 574 | 582 | +1.3 | 21 -> 22 |
| knyszyn-w | goniadzka-above | 66 | 69 | +3 | 446 | 450 | +0.8 | 4 -> 4 |
| **suma** | | 7800 | 7941 | +141 | 21113 | 21651 | +2.5 | |

## Low clear

| kafel | kamera | draws r0 | draws r1 | Δ | tris r0 (tys.) | tris r1 (tys.) | Δ % | inst. tris r0 -> r1 (tys.) |
|---|---|---|---|---|---|---|---|---|
| tykocin | bv_bank_close | 265 | 145 | -120 | 300 | 201 | -33.1 | 12 -> 9 |
| tykocin | bv_bank_n | 393 | 393 | +0 | 222 | 227 | +2.5 | 4 -> 4 |
| tykocin | bv_bank_se | 259 | 238 | -21 | 211 | 208 | -1.9 | 16 -> 5 |
| tykocin | bv_bank_sw | 90 | 206 | +116 | 81 | 227 | +180.4 | 11 -> 11 |
| tykocin | bv_cab_bridge_n | 411 | 411 | +0 | 204 | 206 | +0.9 | 2 -> 2 |
| tykocin | bv_cab_bridge_river | 382 | 382 | +0 | 205 | 206 | +0.8 | 6 -> 6 |
| tykocin | bv_cab_bridge_side | 339 | 339 | +0 | 234 | 240 | +2.3 | 2 -> 2 |
| tykocin | look-narew-truss-side | 283 | 283 | +0 | 236 | 243 | +2.7 | 10 -> 10 |
| tykocin | top-water-bridge | 165 | 165 | +0 | 151 | 152 | +0.9 | 1 -> 1 |
| tykocin | water-bank-bridge-se | 289 | 289 | +0 | 226 | 232 | +2.9 | 15 -> 16 |
| tykocin | water-boat-under-bridge | 237 | 237 | +0 | 160 | 163 | +1.8 | 5 -> 5 |
| tykocin | water-oblique-bridge | 241 | 241 | +0 | 229 | 234 | +2.1 | 5 -> 5 |
| dk65-07 | bv_air_wood | 190 | 190 | +0 | 117 | 113 | -2.7 | 8 -> 10 |
| dk65-07 | bv_cab_s242 | 181 | 181 | +0 | 118 | 115 | -2.7 | 7 -> 9 |
| dk65-07 | bv_side_wood | 166 | 168 | +2 | 109 | 110 | +0.6 | 12 -> 15 |
| dk65-07 | bv_verge_close | 164 | 164 | +0 | 109 | 106 | -2.9 | 11 -> 14 |
| dk65-07 | drive-kozince | 166 | 166 | +0 | 124 | 120 | -2.7 | 27 -> 29 |
| dk65-07 | drive-wood | 176 | 176 | +0 | 110 | 107 | -2.9 | 9 -> 12 |
| dk65-07 | rev-kozince | 154 | 154 | +0 | 140 | 137 | -2.4 | 20 -> 23 |
| dk65-07 | top-kozince | 74 | 74 | +0 | 85 | 82 | -3.9 | 3 -> 4 |
| knyszyn-w | bv_air_fields | 27 | 27 | +0 | 68 | 65 | -4.7 | 2 -> 2 |
| knyszyn-w | bv_cab_s1701 | 21 | 21 | +0 | 51 | 48 | -4.5 | 1 -> 1 |
| knyszyn-w | bv_ditch_close | 27 | 27 | +0 | 68 | 65 | -4.7 | 7 -> 7 |
| knyszyn-w | bv_side_ditch | 19 | 19 | +0 | 48 | 46 | -4.7 | 6 -> 6 |
| knyszyn-w | dk65-fields-nw | 23 | 23 | +0 | 63 | 60 | -5.0 | 3 -> 3 |
| knyszyn-w | dk65-goniadzka | 97 | 97 | +0 | 147 | 143 | -2.2 | 17 -> 17 |
| knyszyn-w | dk65-north-edge-in | 55 | 55 | +0 | 90 | 87 | -3.5 | 14 -> 14 |
| knyszyn-w | dk65-polna | 64 | 64 | +0 | 109 | 106 | -2.4 | 14 -> 15 |
| knyszyn-w | goniadzka-above | 54 | 54 | +0 | 106 | 102 | -3.1 | 3 -> 3 |
| **suma** | | 5012 | 4989 | -23 | 4121 | 4152 | +0.7 | |

