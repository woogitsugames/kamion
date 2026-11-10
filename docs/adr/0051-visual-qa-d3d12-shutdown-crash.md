# ADR 0051 - visual-qa: known Unity D3D12 pipeline-cache crash on shutdown is detected explicitly, not ignored

Status: accepted (2026-11-10)

## Context
`scripts/visual-qa.ps1` occasionally ended with exit code -1073741819 (0xC0000005) although every frame had been written and
`VISUALQA_RESULT: OK rendered=N` was logged. Evidence (`artifacts/logs/vqa-crash/crashed-run-stack.log`, Unity crash dump
dir `%LOCALAPPDATA%\Temp\Unity\Editor\Crashes\Crash_2026-11-10_065114107`, Unity 6000.3.28f1, D3D12, RTX 5070):

    D3D12Core!D3D12GetInterface (access violation)
    Unity!D3D12PipelineCacheLibrary::SaveCache
    Unity!D3D12PipelineCache::~D3D12PipelineCache
    Unity!GfxDeviceD3D12::~GfxDeviceD3D12 -> DestroyGfxDevice -> Application::Exit -> EditorApplication_CUSTOM_Exit

The fault is inside the engine's graphics-device teardown (PSO cache serialisation in D3D12Core), after our runner returned
and after all managed code ran. No script, RenderTexture, ComputeBuffer, NativeArray or job of ours is on the stack; the
runner already logs its result before `EditorApplication.Exit`. Other Unity crashes seen in the same dir are different
(`CreateCommandQueue failed 8007000e` = GPU memory exhausted with several Unity processes; bad `-buildTarget`) and have no
`VISUALQA_RESULT: OK`. The crash is intermittent: 5 consecutive High/lowsun runs on an otherwise idle Unity setup did not
reproduce it (exit 0), so it looks load-dependent (concurrent Unity/GPU users).

## Decision
No fix is possible in project code. `visual-qa.ps1` accepts a run with that exit code only if ALL hold: exit == -1073741819,
log has `VISUALQA_RESULT: OK rendered=N`, the log contains `D3D12PipelineCacheLibrary::SaveCache`, and at least N PNGs
(excluding `_mask`) were written after the run started. A warning is printed and the exit becomes 0. Any other crash,
stack or frame shortfall still fails. Re-evaluate on the next Unity patch; remove the allowance if it stops occurring.
Alternative considered: `-force-d3d11` for QA (avoids the code path but changes the rendering backend used as evidence).
