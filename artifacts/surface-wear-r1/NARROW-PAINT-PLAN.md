# Paint width diagnostic (inactive during phone hold)

Actual material-only wearOFF reconnects P8 arm/head; topology is intact. Originalwheel.85 removes too broad a portion. The single .425 diagnostic retains morepaint but still leaves a band through the head and cleans P10 noticeably.
ROOT authorized one width experiment: holdwheel.425, age/dirt unchanged, change ONLY DECAL_PAINT wheel denominator.13 ->.085. Centres.26/.74 stay. Nominal full width at3.5m lane is.595m vs.91m. This is WORKING_VALUE contact-band calibration, not measured physical tyre data. ROADWEAR polish, oil centreband, allpalette/lighting/macro/tile/weather unchanged.

Prepared PaintNarrowDiagnostic.shader is a QA copy of pristineWorldPBR: literal change plus distinctHiddenname and equivalentabsoluteinclude. Same20 texture sample tokens, no newproductionkeyword/material/batch. Not active or rendered. PaintWearAblation assigns it only to transient paintmaterialclones, logs actualpostrender override and restores allrendererassignments/destroys clones in finally; originalmaterialSHA must remainexact.

After freshROOTrelease: finishpendingbusHighOV first. Then copy preparedartifactC# andshader into ignoredSurfaceWearQA (noUnityactive), runpaint-narrow.ps1 forLowHigh xclearOV P8+P10. Compare to half8views, no blindadoption or amplitudesweep. Judge fullrecognisablearrow+localchips, not uniformlywhitepaint. GPUcost remainsUNVERIFIED; no source/runtimeadoptionyet.
