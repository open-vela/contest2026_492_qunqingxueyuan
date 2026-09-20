# Browser live acceptance 2026-09-19

Source: running openvela candidate identified in `agent-build-provenance.md`.
Browser used `openvela 实时`, with `openvela C 核心` visible in the footer.

- Default 350 ms Agent delay, one default center-directed shot: left 0 avoided / 1 collision; right 1 avoided / 0 collisions.
- Manual backward drag and release exercised through actual pointer events.
- Clear, set Agent delay to 0 ms, repeat the default shot: both sides 1 avoided / 0 collisions.
- Fault injection: Playwright aborted `/step` requests. UI displayed `DATA CONNECTION LOST · 数据连接中断` and `仿真已暂停`. Removing the fault and using reconnect restored the live UI. This is a browser transport-failure injection, not physically unplugging a device.
- Clear, set Agent delay to 1000 ms and acceleration to 8 m/s², fire six center shots: left 0 avoided / 6 collisions; right 6 avoided / 0 collisions.

These outcomes describe only these synthetic trials, not a general avoidance
success rate or a comparison against real MiMo inference timing. No code or
result was modified to achieve the outcomes. Both arenas use identical input.

Raw browser screen recording: 101.68 seconds, 1440×960, 25 fps, VP8 WebM.
Converted to H.264 MP4 without changing timing or trial outcomes:
`submission/FlyReflex_浏览器实录素材.mp4`.
It has no narration and does not include the separate actual Agent or LVGL
demonstrations; it is a source clip, not the complete contest submission video.
Credentials were configured before recording and are not shown in this clip.
