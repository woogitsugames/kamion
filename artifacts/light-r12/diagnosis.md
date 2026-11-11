# ADR0098 diagnostic hypotheses (before renderer edits)

- URP6000.3 package PostProcessing/Common.hlsl ApplyDithering injects triangular +/-1 sRGB level, independently of materials. QualityProfileApplier enables it on every post tier. Sky.shader injects a second +/-0.5 level before grading. Hypothesis: a universal High wall/sky pepper source. Measure original PNG ROIs and isolate rq_dither versus RCAS before choosing policy.
- URP PostProcessPass FSR path can sharpen at100% scale; final RCAS sharpness currently0.75. Test rq_fsrsharp=0 separately; do not blur wall textures to hide output noise.
- Clear D23 reaches display1 at scene0.7 while asphalt scene0.08 lies below0.18 anchor. A shoulder above0.33 can preserve road/midtones; confirm on wall plus sky and road fixed masks before acceptance. Overcast chosen toe/exposure remains unchanged unless real metrics justify changes.
- Shadow and atmospheric changes require matching camera/tier/preset frames; CPU draw count is not phone GPU evidence. All new numerical visual calibration values are WORKING_VALUE.
