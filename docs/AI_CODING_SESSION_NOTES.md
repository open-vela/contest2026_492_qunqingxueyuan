# Final integration session provenance

This is a provenance/work note, **not** a contest AI Coding Log.

- session_id: `01a0b9b4-c572-7b70-b99b-35cd4196ac14`
- Original rollout: `C:\Users\29329\.codex\sessions\2026\09\19\rollout-2026-09-19T20-47-07-01a0b9b4-c572-7b70-b99b-35cd4196ac14.jsonl`
- cwd: `D:\openvela`
- Started: `2026-09-19T12:47:07.374Z` / `2026-09-19 20:47:07.374 Asia/Shanghai`
- CLI version in source metadata: `0.155.0-alpha.9.2`
- Branch: `feature/visual-story`; initial source HEAD: `70db07b10ba3c10d7d2c36c3160debaebd05ebcf`.
- Original rollout and old contest JSONL/manifest were not edited or deleted.
- An active session is not a final export. Final SHA256 must be computed after the session has finished flushing; do not label a partial hash as final.

The preceding integration session was archived: 212 events; its source SHA256 is recorded in codex_rollout_sha256.txt.

## Final release session

- session_id: `01a0b9ec-8ebc-7dc1-bd5a-b6f05daa889c`
- Original rollout: `C:/Users/29329/.codex/sessions/2026/09/19/rollout-2026-09-19T21-48-03-01a0b9ec-8ebc-7dc1-bd5a-b6f05daa889c.jsonl`
- Started: `2026-09-19T13:48:03.356Z` / `2026-09-19 21:48:03.356 Asia/Shanghai`
- cwd: `D:/openvela`
- CLI version: `0.155.0-alpha.9.2`
- Initial HEAD: `70db07b10ba3c10d7d2c36c3160debaebd05ebcf`
- Source must remain untouched. No active-session hash is represented as final.
- This session authorized a converter-based credential repair of session 1 after an external sealed backup; see AI_LOG_EXPORT_MANUAL.md.

After closing this release session:

```powershell
python -X utf8 D:/openvela/tools/finalize_last_codex_session.py 01a0b9ec-8ebc-7dc1-bd5a-b6f05daa889c --commit
```
