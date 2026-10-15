# Test report

Command: `F:\incubrix\Main\version 1\backend\incubrix_env\Scripts\python.exe -m pytest -q`

Run date: 2026-10-15 (local date)

Result: **7 passed, 0 failed, 1 warning in 15.30s**.

Measured by the integration test: requested and emitted duration 5.000 seconds at 48,000 Hz for mix and all three stems. The report includes a numerical quantized-stem reconstruction error. LUFS and true peak were not measured, so audio-quality acceptance is not established. Tests cover prompt/duration validation, close sections, exact sample duration, job creation, and idempotency. Other listed hard cases are not yet implemented or tested.
