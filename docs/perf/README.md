# Performance Optimization Guidelines

This guide collects the practices we follow when tuning the runtime. It covers
instrumentation, reproducible capture workflows, and the triage routine used to
decide which optimizations ship.

## Instrumentation Playbook

- **CPU/GPU markers:** Use the helpers in `native/engine/render/diagnostics.*`
  to wrap expensive sections. CPU zones can be nested freely and emit timing
  stats even when external profilers are absent. GPU zones accept a
  `ID3D12GraphicsCommandList*` so PIX or RenderDoc can highlight draw calls.
- **Frame playback benchmarks:** The deterministic loop in
  `native.runtime.loop.FramePlaybackLoop` supports dependency injection for
  clocks and sleep functions. The perf tests reuse this ability to generate
  repeatable timing samples without real rendering.
- **Logging destination:** Performance runs should store JSON results under
  `logs/perf/` (configurable through `PERF_LOG_DIR`). CI jobs can collect this
  directory as an artifact for trend analysis.

## Capture Workflow

1. **RenderDoc** – Run `python -m tools.profiling.renderdoc_capture --target
   <exe> --capture <file.rdc> -- --game-flags`. The wrapper will locate
   `renderdoccmd`, inject environment overrides, and trigger a capture after the
   requested frame delay.
2. **PIX** – Run `python -m tools.profiling.pix_capture --target <exe> --mode
   gpu --capture <file.wpixcapture> -- --game-flags`. The script handles common
   options like timing versus GPU captures and optional warm-up delays.
3. **Artifacts** – Both scripts print the absolute capture path so CI logs can
   surface direct download links when the profiler binaries are available on the
   host.

## Frame-Time Benchmarks

- The pytest module `tests/perf/test_frame_time_benchmark.py` executes a
  synthetic workload representing 60 deterministic frames. It records
  per-frame timings and writes a JSON payload to `logs/perf/frame_time_benchmark.json`.
- Results are added to the pytest report via `record_property`, enabling CI to
  compare the latest FPS and frame distribution against historical builds.
- Extend these tests with additional scenarios (e.g. stress scenes, particle
  storms) by providing precomputed frame bundles and reusing the same logging
  helpers.

## Optimization Triage Checklist

- [ ] **Reproduce:** Confirm the regression with the automated frame-time
      benchmark or an external capture.
- [ ] **Characterize:** Identify whether the bottleneck is CPU, GPU, or data IO
      by toggling the scoped markers in `diagnostics`.
- [ ] **Narrow:** Use the capture scripts to isolate the suspect subsystem and
      gather RenderDoc/PIX evidence (resource usage, expensive passes, hot call
      stacks).
- [ ] **Mitigate:** Prototype fixes with feature flags or asset tweaks, keeping
      logs for before/after comparisons.
- [ ] **Verify:** Re-run the perf tests locally and ensure CI artifacts reflect
      the expected improvements.
- [ ] **Document:** Update this checklist or the relevant subsystem docs with
      lessons learned so future engineers can avoid repeating the issue.

